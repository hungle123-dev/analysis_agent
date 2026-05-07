# Requirement Traceability

File nay doi chieu truc tiep yeu cau cua thay voi thiet ke module AI. Muc tieu la de nhom co the tu tin noi: moi yeu cau bat buoc deu co noi thuc hien ro rang trong UI/API/logs.

## Bang doi chieu

| Yeu cau cua thay | Thiet ke dap ung | File/API lien quan |
| --- | --- | --- |
| Tich hop AI vao phan tich du lieu | Xay AI Analysis Workbench de nhan yeu cau, sinh code/giai thich, hien ket qua phan tich | `APP.md`, `IMPLEMENTATION_GUIDE.md` |
| Co the la app doc lap, dashboard, hoac API | Chot FastAPI backend + React frontend; backend API-first nen app khac goi duoc | `API_CONTRACT.md` |
| Khuyen khich tao API | Tach Dataset API, AI Proposal API, Approval API, Execution API, Logs API | `API_CONTRACT.md` |
| AI tro giup de xuat y tuong | Co mode goi y phan tich dua tren schema dataset | `AI_PROMPTS_AND_SCHEMA.md`, `DEMO_QA.md` |
| AI viet code theo yeu cau nguoi dung | `POST /api/ai/proposals` tra proposal gom code va explanation | `API_CONTRACT.md` |
| AI trinh bay ket qua dua tren so lieu/hinh/bieu do duoc cung cap | Chi cho AI explain result sau khi co execution artifact; khong cho AI tu tao so lieu | `AI_PROMPTS_AND_SCHEMA.md`, `LOGS_REPORTING.md` |
| AI khong tu them so lieu/hinh anh khac | Prompt/schema cam invent data; backend chi gui dataset schema/artifact context | `AI_PROMPTS_AND_SCHEMA.md` |
| Con nguoi dinh huong va quyet dinh thuc thi code | UI co code editor, approve/reject, run local chi bat sau approve | `HUMAN_APPROVAL_EXECUTION.md` |
| Neu chua co y tuong co the yeu cau AI goi y | Co prompt/mode suggestion sinh danh sach cau hoi phan tich | `AI_PROMPTS_AND_SCHEMA.md`, `DEMO_QA.md` |
| Code phai chay local | ExecutionRunner chay code tren may local, output vao `outputs/{run_id}` | `HUMAN_APPROVAL_EXECUTION.md` |
| Khong thuc thi online | AI provider co the tao text/code, nhung execution khong nam tren cloud | `SOFTWARE_DESIGN_PRINCIPLES.md` |
| AI khong tu thay doi du lieu goc | Code dung `df.copy()`, runner khong ghi dataset goc, policy chan ghi file nguy hiem | `HUMAN_APPROVAL_EXECUTION.md` |
| Khong am tham chay thuat toan | AI API chi tao `pending_review`; Execution API reject proposal chua approved | `API_CONTRACT.md` |
| Hien thi code bat buoc | Frontend dung Monaco Editor de hien/sua code | `IMPLEMENTATION_GUIDE.md`, `AGENTS.md` |
| Code co comment/giai thich tu nhien | System prompt bat buoc comment tieng Viet trong code va explanation rieng | `AI_PROMPTS_AND_SCHEMA.md` |
| Code ban dau o trang thai cho duyet | State `pending_review` la trang thai mac dinh cua proposal | `HUMAN_APPROVAL_EXECUTION.md` |
| Con nguoi sua tham so/code | Monaco Editor cho sua code; `PATCH /api/ai/proposals/{id}` luu ban edit | `API_CONTRACT.md` |
| Chi chay khi con nguoi chap thuan | `POST /approve` tao `code_hash`; execution can code_hash khop | `API_CONTRACT.md` |
| Luu tat ca yeu cau, code, ket qua, giai thich | SQLite/log store luu request/proposal/approval/execution/artifact | `LOGS_REPORTING.md` |
| Van dap can dung module AI tra loi cau hoi du lieu nhom | `DEMO_QA.md` co danh sach cau hoi mau va checklist test truoc | `DEMO_QA.md` |
| So cau hoi toi thieu bang so thanh vien | Checklist nhac chuan bi so cau hoi bang so thanh vien | `DEMO_QA.md` |
| Bao cao tom tat qua trinh dung AI | `LOGS_REPORTING.md` co mau bang bao cao request/result/change/comment | `LOGS_REPORTING.md` |
| Frontend co o chat/form nhap yeu cau | Prompt panel trong React frontend | `IMPLEMENTATION_GUIDE.md` |
| Frontend xem & chinh sua ma nguon | Monaco Editor | `IMPLEMENTATION_GUIDE.md` |
| Frontend phe duyet | Approval bar voi Approve/Reject/Run local | `HUMAN_APPROVAL_EXECUTION.md` |
| Frontend hien thi ket qua | Result panel hien table/chart/stdout/stderr/artifacts | `API_CONTRACT.md` |
| API AI bat buoc | `POST /api/ai/proposals` | `API_CONTRACT.md` |
| API Thuc thi bat buoc | `POST /api/executions` | `API_CONTRACT.md` |
| API Logs bat buoc | `GET /api/logs`, `GET /api/logs/{trace_id}` | `API_CONTRACT.md` |

## Ket luan audit

Bo tai lieu hien tai da dung huong voi yeu cau. Phan can canh giac khi implement la backend phai enforce approval va logs that, khong chi lam giao dien gia lap. Frontend dep se giup demo, nhung diem an chinh nam o viec state machine va log truy xuat duoc.
