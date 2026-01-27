"""
Claims vs Medicine Matching Service
====================================
Logic nghiệp vụ chính: So khớp Claims với Medicine.
"""

import time
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from .matcher import DrugMatcher
from .normalizer import normalize_for_matching
from .models import (
    ClaimItem, MedicineItem, MatchingRequest, MatchingResponse,
    MatchedPair, MatchEvidence, Anomaly, AnomaliesReport, 
    MatchingSummary, AuditTrail
)

# Try# Lazy imports để tránh lỗi khi chưa cài thư viện
_rapidfuzz_available = False
_sklearn_available = False
_ai_matcher_available = False

try:
    from .ai_matcher import AISemanticMatcher
    _ai_matcher_available = True
except ImportError:
    pass

# Setup logging
logger = logging.getLogger("mapping_drugs.service")
logger.setLevel(logging.DEBUG)

# File handler for service logs
# Use /app/logs/mapping which syncs to host via Docker volume mount
_log_dir = "/app/logs/mapping"
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, f"service_{datetime.now().strftime('%Y%m%d')}.log")

if not logger.handlers:
    fh = logging.FileHandler(_log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class ClaimsMedicineMatchingService:
    """
    Service chính để so khớp Claims vs Medicine.
    
    Flow:
    1. Chuẩn hóa tên thuốc trong cả 2 danh sách
    2. Map từng thuốc với Database (lấy thông tin chuẩn)
    3. So khớp Claims với Medicine dựa trên:
       - ID (nếu có)
       - Tên chuẩn hóa
       - Hoạt chất
       - Giá (hỗ trợ)
    4. Phát hiện gian lận (Claim không có mua)
    5. Tổng hợp kết quả
    """
    
    # Thresholds
    CONFIDENCE_AUTO_APPROVE = 0.85
    CONFIDENCE_MANUAL_REVIEW = 0.70
    AMOUNT_TOLERANCE = 0.20  # ±20% giá
    
    def __init__(self, db_path: Optional[str] = None):
        # DrugMatcher tự quản lý DatabaseCore, không cần truyền db_path
        self.matcher = DrugMatcher()
    
    async def process(self, request: MatchingRequest) -> MatchingResponse:
        """
        Xử lý matching request.
        
        Args:
            request: MatchingRequest với claims và medicine lists
            
        Returns:
            MatchingResponse với kết quả chi tiết
        """
        start_time = time.time()
        
        # Generate request_id nếu chưa có
        request_id = request.request_id or f"req-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"[SERVICE] ========== NEW MATCHING REQUEST ==========")
        logger.info(f"[SERVICE] Request ID: {request_id}")
        logger.info(f"[SERVICE] Claims Count: {len(request.claims)}")
        logger.info(f"[SERVICE] Medicine Count: {len(request.medicine)}")
        logger.info(f"{'='*60}")
        
        # Step 1: Enrich claims và medicine với DB info
        logger.info(f"[SERVICE] Step 1: Enriching Claims with DB info...")
        enrich_start = time.time()
        enriched_claims = self._enrich_items(request.claims, "claim")
        logger.info(f"[SERVICE] Step 1a: Claims enriched in {(time.time()-enrich_start)*1000:.0f}ms")
        
        enrich_start = time.time()
        enriched_medicine = self._enrich_items(request.medicine, "medicine")
        logger.info(f"[SERVICE] Step 1b: Medicine enriched in {(time.time()-enrich_start)*1000:.0f}ms")
        
        # Log enrichment results
        claims_found = sum(1 for c in enriched_claims if c.get('_db_status') == 'FOUND')
        medicine_found = sum(1 for m in enriched_medicine if m.get('_db_status') == 'FOUND')
        logger.info(f"[SERVICE] Step 1 Summary: Claims DB matches: {claims_found}/{len(enriched_claims)}, Medicine DB matches: {medicine_found}/{len(enriched_medicine)}")
        
        # Step 2: Build medicine lookup (normalized_name -> medicine_item)
        logger.info(f"[SERVICE] Step 2: Building medicine lookup dict...")
        medicine_lookup = self._build_lookup(enriched_medicine)
        logger.info(f"[SERVICE] Step 2: Lookup dict built with {len(medicine_lookup)} keys")
        
        # Step 3: Match từng claim với medicine
        logger.info(f"[SERVICE] Step 3: Matching Claims to Medicine...")
        matched_pairs: List[MatchedPair] = []
        matched_medicine_ids = set()
        
        for i, claim in enumerate(enriched_claims):
            claim_service = claim.get('service', '')
            logger.debug(f"[SERVICE] Step 3.{i+1}: Matching Claim '{claim_service}'")
            
            pair, medicine_id = self._match_claim_to_medicine(
                claim, enriched_medicine, medicine_lookup
            )
            matched_pairs.append(pair)
            
            if medicine_id:
                matched_medicine_ids.add(medicine_id)
                logger.info(f"[SERVICE] Step 3.{i+1}: ✅ MATCHED '{claim_service}' -> '{pair.medicine_service}' (conf={pair.confidence_score})")
            else:
                logger.warning(f"[SERVICE] Step 3.{i+1}: ❌ NO MATCH for '{claim_service}'")
        
        # Step 3.5: AI Fallback (Level 6)
        # Nếu có claim chưa match, nhờ AI xem xét
        unmatched_indices = [i for i, r in enumerate(matched_pairs) if r.match_status == "no_match"]
        logger.info(f"[SERVICE] Debug AI Fallback: Available={_ai_matcher_available}, Unmatched Count={len(unmatched_indices)}")
        
        if unmatched_indices and _ai_matcher_available:
            logger.info(f"[SERVICE] Step 3.5: AI Fallback triggered for {len(unmatched_indices)} unmatched claims...")
            
            # Prepare data for AI
            batch_claims = [enriched_claims[i] for i in unmatched_indices]
            
            # Call AI (Async directly)
            try:
                # Use a fresh instance
                matcher = AISemanticMatcher()
                ai_result = await matcher.match_claims_medicine(
                    claims=batch_claims,
                    medicine=enriched_medicine,
                    db_enrichment={"context": "AI Fallback from statistical matching failure"}
                )
                
                # Update matched_pairs with AI results
                # Update matched_pairs with AI results
                ai_matches = ai_result.get("matches", [])
                for ai_match in ai_matches:
                    # Find corresponding index in original list
                    claim_id = ai_match.get("claim_id")
                    found_idx = None
                    
                    for idx in unmatched_indices:
                        if matched_pairs[idx].claim_id == claim_id:
                            found_idx = idx
                            break
                    
                    if found_idx is not None:
                        # Construct new MatchedPair from AI result
                        med_id = ai_match.get("medicine_id")
                        med_service = ai_match.get("medicine_service")
                        
                        if med_id:
                            matched_medicine_ids.add(med_id)
                        
                        # Normalize match_status
                        raw_status = ai_match.get("match_status", "uncertain").lower()
                        if raw_status == "equivalent":
                            status = "matched"
                        elif "partial" in raw_status:
                            status = "partially_matched"
                        elif raw_status in ["matched", "weak_match", "no_match"]:
                            status = raw_status
                        else:
                            status = "weak_match"  # Default fallback
                            
                        # Get claim service name either from AI or original data (Robust Fallback)
                        ai_claim_service = ai_match.get("claim_service")
                        if not ai_claim_service:
                            ai_claim_service = matched_pairs[found_idx].claim_service
                        
                        # Normalize confidence score (handle 0-100 vs 0-1)
                        conf = ai_match.get("confidence_score", 0.0)
                        if conf > 1.0:
                            conf = conf / 100.0
                        conf = max(0.0, min(1.0, conf))
                            
                        try:
                            matched_pairs[found_idx] = MatchedPair(
                                claim_id=claim_id,
                                medicine_id=med_id,
                                claim_service=ai_claim_service,
                                medicine_service=med_service,
                                match_status=status,
                                confidence_score=conf,
                                decision="manual_review", # AI matches always suggest review
                                evidence=MatchEvidence(
                                    text_similarity=0.0, # AI semantic match
                                    amount_similarity=0.0,
                                    drug_knowledge_match=True, # AI knowledge
                                    method=f"AI_MATCH ({ai_result.get('ai_model')})",
                                    notes=ai_match.get("reasoning", "AI Match")
                                )
                            )
                        except Exception as ve:
                            logger.error(f"[SERVICE] Validation error creating MatchedPair from AI: {ve}")
                            logger.error(f"[SERVICE] AI Match data: {ai_match}")
                        logger.info(f"[SERVICE] Step 3.5: 🤖 AI RESCUED '{claim_id}' -> '{med_service}'")
                    else:
                        logger.warning(f"[SERVICE] Step 3.5: AI returned result for unknown claim_id='{claim_id}'")
            except Exception as e:
                logger.error(f"[SERVICE] AI Fallback failed: {e}")
        elif unmatched_indices:
             logger.info(f"[SERVICE] Step 3.5: AI Fallback skipped (AI not available or disabled)")
        anomalies = self._detect_anomalies(
            enriched_claims, 
            enriched_medicine, 
            matched_pairs
        )
        logger.info(f"[SERVICE] Step 4: Found {len(anomalies.claim_without_purchase)} claims without purchase, {len(anomalies.purchase_without_claim)} purchases without claim")
        
        # Step 5: Tổng hợp summary
        summary = self._build_summary(matched_pairs, request.claims, request.medicine)
        
        # Step 6: Audit trail
        processing_time = (time.time() - start_time) * 1000  # ms
        audit = AuditTrail(
            normalization_applied=True,
            fuzzy_matching=True,
            drug_ontology_used=True,
            amount_used_as_supporting_signal=True,
            processing_time_ms=round(processing_time, 2)
        )
        
        logger.info(f"[SERVICE] ========== MATCHING COMPLETE ==========")
        logger.info(f"[SERVICE] Total Time: {processing_time:.0f}ms")
        logger.info(f"[SERVICE] Matched: {summary.matched_items}/{len(request.claims)}")
        logger.info(f"[SERVICE] Unmatched: {summary.unmatched_claims}")
        logger.info(f"[SERVICE] Need Review: {summary.need_manual_review}")
        logger.info(f"[SERVICE] Risk Level: {summary.risk_level}")
        logger.info(f"{'='*60}")
        
        try:
            return MatchingResponse(
                request_id=request_id,
                status="processed",
                processing_timestamp=datetime.utcnow(),
                summary=summary,
                results=[r for r in matched_pairs if r.match_status != "no_match"],
                anomalies=anomalies,
                audit_trail=audit
            )
        except Exception as e:
            logger.error(f"[SERVICE] Failed to create MatchingResponse: {e}")
            raise e
        
    async def process_v2(self, request: MatchingRequest) -> MatchingResponse:
        """
        Xử lý matching request v2 - TRỰC TIẾP QUA AI.
        Bỏ qua mọi bước chuẩn hóa và database enrichment.
        """
        start_time = time.time()
        request_id = request.request_id or f"req-v2-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"")
        logger.info(f"{'='*60}")
        logger.info(f"[SERVICE] ========== NEW MATCH_V2 REQUEST (AI DIRECT) ==========")
        logger.info(f"[SERVICE] Request ID: {request_id}")
        logger.info(f"[SERVICE] Claims Count: {len(request.claims)}")
        logger.info(f"[SERVICE] Medicine Count: {len(request.medicine)}")
        logger.info(f"{'='*60}")
        
        if not _ai_matcher_available:
            logger.error("[SERVICE] AI Matcher not available for match_v2")
            raise Exception("AI Matcher is not available. Please check environment variables and library installation.")

        # Prepare raw data for AI
        raw_claims = [c.model_dump() if hasattr(c, 'model_dump') else dict(c) for c in request.claims]
        raw_medicine = [m.model_dump() if hasattr(m, 'model_dump') else dict(m) for m in request.medicine]
        
        # Call AI directly
        try:
            matcher = AISemanticMatcher()
            
            ai_result = await matcher.match_claims_medicine(
                claims=raw_claims,
                medicine=raw_medicine,
                db_enrichment={"context": "DIRECT_AI_MATCH_V2"}
            )
            
            ai_matches = ai_result.get("matches", [])
            matched_pairs = []
            
            for ai_match in ai_matches:
                # Find original claim to get its service name if AI didn't return it
                cid = ai_match.get("claim_id")
                mid = ai_match.get("medicine_id")
                
                # Get claim service name either from AI or original data
                claim_service = ai_match.get("claim_service")
                if not claim_service:
                    original_claim = next((c for c in raw_claims if (c.get('id') or c.get('claim_id')) == cid), None)
                    if original_claim:
                        claim_service = original_claim.get('service') or original_claim.get('service_name')
                
                # Get medicine service name either from AI or original data
                medicine_service = ai_match.get("medicine_service")
                if not medicine_service and mid:
                    original_med = next((m for m in raw_medicine if (m.get('id') or m.get('medicine_id')) == mid), None)
                    if original_med:
                        medicine_service = original_med.get('service') or original_med.get('service_name')

                # Construct MatchedPair from AI result
                raw_status = ai_match.get("match_status", "uncertain").lower()
                if raw_status == "equivalent" or raw_status == "matched":
                    status = "matched"
                elif "partial" in raw_status:
                    status = "partially_matched"
                else:
                    status = raw_status if raw_status in ["matched", "partially_matched", "weak_match", "no_match"] else "weak_match"
                
                matched_pairs.append(MatchedPair(
                    claim_id=cid,
                    medicine_id=mid,
                    claim_service=claim_service or "Unknown",
                    medicine_service=medicine_service,
                    match_status=status,
                    confidence_score=ai_match.get("confidence_score", 0.0),
                    decision="manual_review", # AI results always suggest review in v2 as well
                    evidence=MatchEvidence(
                        text_similarity=0.0,
                        amount_similarity=0.0,
                        drug_knowledge_match=True,
                        method=f"DIRECT_AI ({ai_result.get('ai_model')})",
                        notes=ai_match.get("reasoning", "Direct AI Match")
                    )
                ))
            
            # Anomalies detection (simplified for v2)
            anomalies = self._detect_anomalies(
                raw_claims, 
                raw_medicine, 
                matched_pairs
            )
            
            # Summary
            summary = self._build_summary(matched_pairs, request.claims, request.medicine)
            
            # Audit trail
            processing_time = (time.time() - start_time) * 1000
            audit = AuditTrail(
                normalization_applied=False,
                fuzzy_matching=False,
                drug_ontology_used=False,
                amount_used_as_supporting_signal=False,
                processing_time_ms=round(processing_time, 2)
            )
            
            logger.info(f"[SERVICE] ========== MATCH_V2 COMPLETE ==========")
            return MatchingResponse(
                request_id=request_id,
                status="processed",
                processing_timestamp=datetime.utcnow(),
                summary=summary,
                results=[r for r in matched_pairs if r.match_status != "no_match"],
                anomalies=anomalies,
                audit_trail=audit
            )
            
        except Exception as e:
            logger.error(f"[SERVICE] match_v2 AI process failed: {e}")
            raise e
    
    def _enrich_items(self, items: list, item_type: str) -> List[Dict]:
        """Làm giàu items với DB info."""
        enriched = []
        for item in items:
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else dict(item)
            
            # Match với DB
            service_name = item_dict.get('service', '')
            db_result = self.matcher.match(service_name)
            
            item_dict['_type'] = item_type
            item_dict['_normalized'] = normalize_for_matching(service_name)
            item_dict['_db_status'] = db_result['status']
            item_dict['_db_confidence'] = db_result['confidence']
            item_dict['_db_method'] = db_result['method']
            
            if db_result['data']:
                item_dict['_db_name'] = db_result['data'].get('ten_thuoc')
                item_dict['_db_sdk'] = db_result['data'].get('so_dang_ky')
                item_dict['_db_hoat_chat'] = db_result['data'].get('hoat_chat')
            else:
                item_dict['_db_name'] = None
                item_dict['_db_sdk'] = None
                item_dict['_db_hoat_chat'] = None
            
            enriched.append(item_dict)
        
        return enriched
    
    def _build_lookup(self, medicine_items: List[Dict]) -> Dict[str, Dict]:
        """Build lookup dict từ medicine items."""
        lookup = {}
        
        for med in medicine_items:
            # Key 1: Normalized name
            norm_name = med.get('_normalized', '')
            if norm_name:
                lookup[norm_name] = med
            
            # Key 2: DB standard name (nếu có)
            db_name = med.get('_db_name')
            if db_name:
                lookup[normalize_for_matching(db_name)] = med
            
            # Key 3: SDK (nếu có)
            sdk = med.get('_db_sdk')
            if sdk:
                lookup[sdk.lower()] = med
        
        return lookup
    
    def _match_claim_to_medicine(
        self, 
        claim: Dict, 
        medicines: List[Dict],
        lookup: Dict[str, Dict]
    ) -> Tuple[MatchedPair, Optional[str]]:
        """
        Match một claim với medicine tương ứng.
        
        Returns:
            (MatchedPair, matched_medicine_id or None)
        """
        claim_id = claim.get('id') or claim.get('claim_id', '')
        claim_service = claim.get('service', '')
        claim_normalized = claim.get('_normalized', '')
        claim_amount = claim.get('amount', 0) or 0
        
        # === Strategy 1: Match by normalized name ===
        matched_med = lookup.get(claim_normalized)
        
        # === Strategy 2: Match by DB standard name ===
        if not matched_med and claim.get('_db_name'):
            db_name_norm = normalize_for_matching(claim['_db_name'])
            matched_med = lookup.get(db_name_norm)
        
        # === Strategy 3: Match by SDK ===
        if not matched_med and claim.get('_db_sdk'):
            matched_med = lookup.get(claim['_db_sdk'].lower())
        
        # === Strategy 4: Fuzzy match in medicine list ===
        if not matched_med:
            matched_med = self._fuzzy_match_in_list(claim, medicines)
        
        # Build result
        if matched_med:
            medicine_id = matched_med.get('medicine_id', '')
            medicine_service = matched_med.get('service', '')
            medicine_amount = matched_med.get('amount', 0) or 0
            
            # Tính similarity scores
            text_sim = self._calculate_text_similarity(claim_service, medicine_service)
            amount_sim = self._calculate_amount_similarity(claim_amount, medicine_amount)
            
            # Tính confidence tổng hợp
            confidence = self._calculate_confidence(claim, matched_med, text_sim, amount_sim)
            
            # Quyết định
            match_status, decision = self._decide(confidence)
            
            return MatchedPair(
                claim_id=claim_id,
                medicine_id=medicine_id,
                claim_service=claim_service,
                medicine_service=medicine_service,
                match_status=match_status,
                confidence_score=round(confidence, 2),
                decision=decision,
                evidence=MatchEvidence(
                    text_similarity=round(text_sim, 2),
                    amount_similarity=round(amount_sim, 2),
                    drug_knowledge_match=claim.get('_db_status') == 'FOUND',
                    method=claim.get('_db_method', 'DIRECT'),
                    notes=self._build_notes(claim, matched_med)
                )
            ), medicine_id
        
        else:
            # Không tìm thấy medicine tương ứng
            return MatchedPair(
                claim_id=claim_id,
                medicine_id=None,
                claim_service=claim_service,
                medicine_service=None,
                match_status="no_match",
                confidence_score=0.0,
                decision="rejected",
                evidence=MatchEvidence(
                    text_similarity=0.0,
                    amount_similarity=0.0,
                    drug_knowledge_match=False,
                    method="NO_MATCH",
                    notes="Không tìm thấy thuốc tương ứng trong danh sách mua"
                )
            ), None
    
    def _fuzzy_match_in_list(self, claim: Dict, medicines: List[Dict]) -> Optional[Dict]:
        """Fuzzy match claim với medicine list."""
        try:
            from rapidfuzz import fuzz
            
            claim_norm = claim.get('_normalized', '')
            if not claim_norm:
                return None
            
            best_match = None
            best_score = 0
            
            for med in medicines:
                med_norm = med.get('_normalized', '')
                if med_norm:
                    score = fuzz.token_sort_ratio(claim_norm, med_norm)
                    if score > best_score and score >= 70:
                        best_score = score
                        best_match = med
            
            return best_match
        except ImportError:
            return None
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Tính độ tương đồng text."""
        try:
            from rapidfuzz import fuzz
            return fuzz.token_sort_ratio(text1, text2) / 100.0
        except ImportError:
            # Fallback: simple comparison
            norm1 = normalize_for_matching(text1)
            norm2 = normalize_for_matching(text2)
            if norm1 == norm2:
                return 1.0
            elif norm1 in norm2 or norm2 in norm1:
                return 0.8
            return 0.0
    
    def _calculate_amount_similarity(self, amount1: float, amount2: float) -> float:
        """Tính độ tương đồng giá."""
        if amount1 == 0 and amount2 == 0:
            return 1.0
        if amount1 == 0 or amount2 == 0:
            return 0.5  # Không có thông tin giá
        
        diff_ratio = abs(amount1 - amount2) / max(amount1, amount2)
        if diff_ratio <= self.AMOUNT_TOLERANCE:
            return 1.0 - diff_ratio
        return max(0.0, 1.0 - diff_ratio)
    
    def _calculate_confidence(
        self, 
        claim: Dict, 
        medicine: Dict, 
        text_sim: float, 
        amount_sim: float
    ) -> float:
        """Tính confidence score tổng hợp."""
        # Weights
        W_TEXT = 0.5
        W_DB = 0.35
        W_AMOUNT = 0.15
        
        # DB match bonus
        db_score = 0.0
        if claim.get('_db_status') == 'FOUND':
            db_score = claim.get('_db_confidence', 0.8)
            
            # Extra bonus nếu cả 2 match cùng SDK
            if claim.get('_db_sdk') and claim.get('_db_sdk') == medicine.get('_db_sdk'):
                db_score = 1.0
        
        confidence = (W_TEXT * text_sim) + (W_DB * db_score) + (W_AMOUNT * amount_sim)
        return min(1.0, confidence)
    
    def _decide(self, confidence: float) -> Tuple[str, str]:
        """Quyết định match status và decision."""
        if confidence >= self.CONFIDENCE_AUTO_APPROVE:
            return "matched", "auto_approved"
        elif confidence >= self.CONFIDENCE_MANUAL_REVIEW:
            return "partially_matched", "manual_review"
        elif confidence > 0.5:
            return "weak_match", "manual_review"
        else:
            return "no_match", "rejected"
    
    def _build_notes(self, claim: Dict, medicine: Dict) -> str:
        """Tạo ghi chú giải thích."""
        notes = []
        
        if claim.get('_db_name') and medicine.get('_db_name'):
            if claim['_db_name'] == medicine['_db_name']:
                notes.append("Cùng tên chuẩn trong DB")
            else:
                notes.append(f"Claim: {claim['_db_name']}, Medicine: {medicine['_db_name']}")
        
        if claim.get('_db_hoat_chat') and medicine.get('_db_hoat_chat'):
            if claim['_db_hoat_chat'] == medicine['_db_hoat_chat']:
                notes.append("Cùng hoạt chất")
        
        return "; ".join(notes) if notes else "Match dựa trên tên thuốc"
    
    def _detect_anomalies(
        self, 
        claims: List[Dict], 
        medicines: List[Dict],
        matched_pairs: List[MatchedPair]
    ) -> AnomaliesReport:
        """Phát hiện các bất thường dựa trên kết quả matching."""
        claim_without_purchase = []
        purchase_without_claim = []
        
        # 1. Claims không tìm thấy thuốc tương ứng
        # Lấy tập hợp IDs của các claims đã được match (Status != no_match)
        matched_claim_ids = {p.claim_id for p in matched_pairs if p.match_status != "no_match"}
        
        for claim in claims:
            cid = claim.get('id') or claim.get('claim_id', '')
            if cid not in matched_claim_ids:
                claim_without_purchase.append(Anomaly(
                    id=cid,
                    service=claim.get('service', ''),
                    amount=claim.get('amount'),
                    risk_flag="high",
                    reason="Không tìm thấy thuốc tương ứng trong danh sách mua"
                ))
        
        # 2. Medicine không được sử dụng để bồi thường
        used_medicine_ids = {p.medicine_id for p in matched_pairs if p.medicine_id}
        
        for med in medicines:
            med_id = med.get('medicine_id', '')
            if med_id not in used_medicine_ids:
                purchase_without_claim.append(Anomaly(
                    id=med_id,
                    service=med.get('service', ''),
                    amount=med.get('amount'),
                    risk_flag="low",
                    reason="Thuốc đã mua nhưng không yêu cầu bồi thường"
                ))
        
        return AnomaliesReport(
            claim_without_purchase=claim_without_purchase,
            purchase_without_claim=purchase_without_claim
        )
    
    def _build_summary(
        self, 
        results: List[MatchedPair], 
        claims: list, 
        medicines: list
    ) -> MatchingSummary:
        """Tổng hợp summary."""
        matched = sum(1 for r in results if r.match_status in ["matched", "partially_matched"])
        unmatched = sum(1 for r in results if r.match_status == "no_match")
        need_review = sum(1 for r in results if r.decision == "manual_review")
        
        # Risk level
        high_risk_count = sum(1 for r in results if r.match_status == "no_match")
        if high_risk_count > len(claims) * 0.3:
            risk_level = "high"
        elif high_risk_count > len(claims) * 0.1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        matched_medicine_ids = {r.medicine_id for r in results if r.medicine_id}
        unclaimed = len(medicines) - len(matched_medicine_ids)
        
        return MatchingSummary(
            total_claim_items=len(claims),
            total_medicine_items=len(medicines),
            matched_items=matched,
            unmatched_claims=unmatched,
            unclaimed_purchases=unclaimed,
            need_manual_review=need_review,
            risk_level=risk_level
        )
