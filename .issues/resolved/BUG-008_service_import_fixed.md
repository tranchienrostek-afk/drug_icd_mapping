# ISSUE: [BUG-008] - [Error Service]
**Status:** Open
**Severity:** High
**Affected Component:** [Service]

## 1. Mô tả lỗi (Description)
Sau khi sửa các file liên quan đến search và scrapper dữ liệu. Nhưng chưa sửa đồng bộ ở file service.py

## 2. Logs & Error Message (QUAN TRỌNG)
*Copy paste nguyên văn log lỗi vào đây. AI cần cái này nhất.*
```text
Traceback (most recent call last):
  File "services.py", line 45, in create_drug
    return db.add(new_drug)
IntegrityError: duplicate key value violates unique constraint "drugs_sdk_key"

web-1  | INFO:     Finished server process [1694]
web-1  | Process SpawnProcess-9:
web-1  | Traceback (most recent call last):
web-1  |   File "/usr/local/lib/python3.11/multiprocessing/process.py", line 314, in _bootstrap  
web-1  |     self.run()
web-1  |   File "/usr/local/lib/python3.11/multiprocessing/process.py", line 108, in run
web-1  |     self._target(*self._args, **self._kwargs)
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/_subprocess.py", line 80, in subprocess_started
web-1  |     target(sockets=sockets)
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 67, in run     
web-1  |     return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
web-1  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/_compat.py", line 30, in asyncio_run
web-1  |     return runner.run(main)
web-1  |            ^^^^^^^^^^^^^^^^
web-1  |   File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
web-1  |     return self._loop.run_until_complete(task)
web-1  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1  |   File "/usr/local/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
web-1  |     return future.result()
web-1  |            ^^^^^^^^^^^^^^^
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 71, in serve   
web-1  |     await self._serve(sockets)
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 78, in _serve  
web-1  |     config.load()
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/config.py", line 439, in load   
web-1  |     self.loaded_app = import_from_string(self.app)
web-1  |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/importer.py", line 22, in import_from_string
web-1  |     raise exc from None
web-1  |   File "/usr/local/lib/python3.11/site-packages/uvicorn/importer.py", line 19, in import_from_string
web-1  |     module = importlib.import_module(module_str)
web-1  |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1  |   File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module    
web-1  |     return _bootstrap._gcd_import(name[level:], package, level)
web-1  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
web-1  |   File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
web-1  |   File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
web-1  |   File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
web-1  |   File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
web-1  |   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
web-1  |   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
web-1  |   File "/app/app/main.py", line 4, in <module>
web-1  |     from app.api import drugs, diseases, analysis, admin
web-1  |   File "/app/app/api/drugs.py", line 4, in <module>
web-1  |     from app.services import DrugDbEngine
web-1  |   File "/app/app/services.py", line 1169, in <module>
web-1  |     from app.service.web_crawler import search_icd_online
web-1  | ModuleNotFoundError: No module named 'app.service.web_crawler'
PS C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app> 

---
# RESOLUTION NOTE (2026-01-07)
**Status:** Fixed & Resolved
**Fix Method:** Corrected import in `app/services.py` from `app.service.web_crawler` to `app.service.crawler`.
**Verification:** Verified via `scripts/verify_services_import.py`.
**Report:** [report_2026_01_07_BUG_008.md](file:///C:/Users/Admin/Desktop/drug_icd_mapping/.ai_planning/.implementation_rules/.ai_reports/2026-01/report_2026_01_07_BUG_008.md) 