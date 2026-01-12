import os
import json
import threading
from datetime import datetime

class TokenTracker:
    _lock = threading.Lock()
    _log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "trace_token_openai")
    
    # Cost constants (USD per 1M tokens) - GPT-4o-mini default
    COST_INPUT_PER_1M = 0.15
    COST_OUTPUT_PER_1M = 0.60

    @classmethod
    def get_log_file_path(cls):
        now = datetime.now()
        filename = f"{now.strftime('%d_%m_%Y')}_total_tokens.json"
        if not os.path.exists(cls._log_dir):
            os.makedirs(cls._log_dir, exist_ok=True)
        return os.path.join(cls._log_dir, filename)

    @classmethod
    def log_usage(cls, context: str, model: str, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        """
        Logs a single usage event to the daily JSON file.
        Thread-safe.
        """
        cost = (
            (prompt_tokens / 1_000_000 * cls.COST_INPUT_PER_1M) + 
            (completion_tokens / 1_000_000 * cls.COST_OUTPUT_PER_1M)
        )
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "model": model,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(cost, 8)
        }

        with cls._lock:
            file_path = cls.get_log_file_path()
            data = {"date": datetime.now().strftime("%d-%m-%Y"), "summary": {}, "details": []}
            
            # Read existing
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"[TokenTracker] Error reading log file: {e}")
            
            # Init summary if needed
            if "summary" not in data:
                data["summary"] = {
                    "total_calls": 0, "total_input_tokens": 0, 
                    "total_output_tokens": 0, "total_cost_usd": 0.0, "currency": "USD"
                }
            if "details" not in data:
                data["details"] = []

            # Update
            data["details"].append(entry)
            
            s = data["summary"]
            s["total_calls"] = s.get("total_calls", 0) + 1
            s["total_input_tokens"] = s.get("total_input_tokens", 0) + prompt_tokens
            s["total_output_tokens"] = s.get("total_output_tokens", 0) + completion_tokens
            s["total_cost_usd"] = s.get("total_cost_usd", 0) + cost
            
            # Write back
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[TokenTracker] Error writing log file: {e}")

# Global instance (optional, but class methods are static-ish)
token_tracker = TokenTracker()
