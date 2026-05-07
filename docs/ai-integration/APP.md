# APP.md - Huong Di Module AI Cho Do An Data Visualization

## 1. Cach hieu dung yeu cau cua thay

Day khong phai la bai tap "gan chatbot vao dashboard cho vui". Day la bai tap xay mot **quy trinh lam viec co AI nhung con nguoi van la nguoi quyet dinh**.

Module AI can chung minh duoc 5 diem:

1. AI co the nhan yeu cau phan tich tu nguoi dung.
2. AI co the de xuat y tuong hoac tao code phan tich dua tren du lieu co san.
3. Code AI sinh ra phai hien thi ro, co comment/giai thich, va o trang thai cho duyet.
4. Nguoi dung co the sua code va chi khi approve thi code moi duoc chay tren may local.
5. Tat ca request, code, giai thich, approve, ket qua, loi va bieu do phai duoc luu lai.

Vay san pham nen la mot **AI Analysis Workbench** nho, co the gan vao dashboard hien co, thay vi mot agent tu dong lam het.

## 2. Huong san pham nen lam

Ten goi de bao cao/demo: **AI Analysis Workbench**.

No la mot module gom:

- Khung chat/form de nguoi dung nhap cau hoi.
- Khung hien code AI tao ra.
- Code editor de nguoi dung sua code.
- Nut `Approve` va `Run locally`.
- Khu vuc hien ket qua: text, bang, bieu do, stdout/stderr.
- Man hinh lich su/log de truy xuat lai toan bo qua trinh.

## 3. Kien truc chot nen dung

```text
React JavaScript frontend kieu VSCode
  - sidebar dataset/logs
  - chat/request panel
  - Monaco code editor
  - result/chart panel
        |
        v
FastAPI backend
  - AI Proposal API
  - Approval API
  - Local Execution API
  - Logs API
        |
        v
Local Python runner
  - pandas/numpy/matplotlib/seaborn/plotly
  - timeout
  - thu muc output rieng
  - khong sua dataset goc
        |
        v
SQLite + outputs/
```

Huong nay oke hon Streamlit/Gradio neu nhom muon giao dien dep va giong san pham that. Diem manh nhat la code editor: dung Monaco Editor, cung dong editor browser-based voi VS Code, nen rat hop voi yeu cau "AI sinh code -> nguoi dung xem/sua -> approve".

## 4. Neu khong muon cai lai tu dau

Neu nhom da co dashboard React:

- Giu dashboard hien co.
- Them tab/panel `AI Assistant`.
- Goi FastAPI backend qua HTTP.
- AI module chi can biet `dataset_id`, schema cot va duong dan output.

Neu nhom chua co frontend:

- Dung React + Vite + JavaScript.
- Dung Monaco Editor cho code editor.
- Dung layout 3 cot kieu VSCode: Explorer/History ben trai, editor o giua, result/log ben phai.
- Dung FastAPI lam backend local.

## 5. Stack khuyen nghi

Ban chot de lam va de bao ve:

- `FastAPI`: tao API local, tu sinh OpenAPI docs.
- `Pydantic`: validate request/response va structured output cua AI.
- `SQLite`: luu proposals, approvals, executions, logs.
- `React + Vite + JavaScript`: frontend nhanh, dep, de tach component.
- `Monaco Editor`: code editor giong VSCode de xem/sua code AI sinh.
- `pandas`, `matplotlib`, `seaborn`, `plotly`: phan tich va ve bieu do.
- `TanStack Query` hoac `fetch` thuong: goi API. Neu muon toi gian, dung `fetch` la du.

Provider AI nen viet dang adapter:

- Gemini API neu nhom quen Google.
- OpenAI API neu co key va muon structured output manh.
- Ollama/local model neu thay yeu cau "local model", nhung can test ky vi structured output co the kem on dinh hon.

## 6. Nguyen tac khong duoc pha

- AI khong duoc tu chay code.
- AI khong duoc bia so lieu, cot, hinh anh, bieu do.
- Code phai hien thi truoc khi chay.
- Code phai co comment giai thich bang ngon ngu tu nhien.
- Nguoi dung phai co quyen sua code.
- Execution API phai tu choi code chua approve.
- Ket qua phai chay local.
- Log phai truy xuat lai duoc.

## 7. Bo tai lieu moi

- `APP.md`: cach hieu dung va huong san pham.
- `IMPLEMENTATION_GUIDE.md`: cach lam tung buoc, uu tien khong cai lai tu dau.
- `API_CONTRACT.md`: API can co de frontend/backend noi chuyen.
- `AI_PROMPTS_AND_SCHEMA.md`: prompt va JSON schema de AI tra code/giai thich dung format.
- `HUMAN_APPROVAL_EXECUTION.md`: quy trinh cho duyet va chay local.
- `LOGS_REPORTING.md`: log, bao cao, bang minh chung.
- `DEMO_QA.md`: kich ban demo va cau hoi van dap.
- `REQUIREMENT_TRACEABILITY.md`: bang doi chieu tung yeu cau cua thay voi thiet ke/API/UI.
- `REFERENCES.md`: tai lieu, repo, pattern tham khao.

## 8. Ket luan de noi voi thay

Module AI cua nhom khong thay con nguoi ra quyet dinh. AI chi dong vai tro tro ly sinh de xuat/code/giai thich. Con nguoi xem, sua, phe duyet. He thong chi chay code da duyet tren local va luu day du log de kiem tra lai.
