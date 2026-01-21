Tôi không thể tưởng tượng được chất lượng mapping tên thuốc lại tệ hại đến mức này.



Test thuốc giống hệ thì được: {
  "diagnoses": [
    {
      "code": "K60.0",
      "name": "Nứt kẽ hậu môn cấp tính",
      "type": "MAIN"
    }
  ],
  "items": [
    {
      "id": "77395a1c-8b21-4f5e-9c3d-1a2b3c4d5e6f",
      "name": "proct 03 5ml"
    }
  ],
  "request_id": "BT/56789",
  "symptom": "Nứt kẽ hậu môn cấp - Đau rát vùng hậu môn"
}


Kết quả:

{
  "results": [
    {
      "id": "77395a1c-8b21-4f5e-9c3d-1a2b3c4d5e6f",
      "name": "proct 03 5ml",
      "category": "drug",
      "validity": "valid",
      "role": "medical equipment",
      "explanation": "Expert Verified: Classified as 'medical equipment' bởi TĐV.",
      "source": "INTERNAL_KB_TDV"
    }
  ]
}

Test thử thay tên:proct 03 5ml thành proct 03 05ml

Đầu vào:

{
  "diagnoses": [
    {
      "code": "K60.0",
      "name": "Nứt kẽ hậu môn cấp tính",
      "type": "MAIN"
    }
  ],
  "items": [
    {
      "id": "77395a1c-8b21-4f5e-9c3d-1a2b3c4d5e6f",
      "name": "proct 03 05ml"
    }
  ],
  "request_id": "BT/56789",
  "symptom": "Nứt kẽ hậu môn cấp - Đau rát vùng hậu môn"
}


Đầu ra:

{
  "results": [
    {
      "id": "77395a1c-8b21-4f5e-9c3d-1a2b3c4d5e6f",
      "name": "proct 03 05ml",
      "category": "drug",
      "validity": "unknown",
      "role": "",
      "explanation": "Không tìm thấy thông tin trong cơ sở dữ liệu.",
      "source": "INTERNAL_KB_EMPTY"
    }
  ]
}
