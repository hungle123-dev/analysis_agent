# Implementation Guide

## Muc tieu

Lam module AI theo cach nho gon, de gan vao app hien co, va de demo dung yeu cau cua thay. Uu tien xay duoc workflow dung truoc, lam UI dep sau.

## Lo trinh 5 buoc

### Buoc 1: Dang ky dataset

Backend can biet dataset nao duoc phep dung. Moi dataset nen co:

- `dataset_id`
- ten file
- duong dan local
- schema cot
- so dong
- null count tung cot
- sample 5 dong dau

AI chi nhan schema va sample nho, khong can gui ca dataset len model.

### Buoc 2: AI sinh proposal

Nguoi dung nhap cau hoi, backend gui cho AI:

- yeu cau nguoi dung
- dataset schema
- danh sach cot hop le
- thu vien duoc phep dung
- quy tac khong bia so lieu
- yeu cau tra JSON dung schema

Ket qua tra ve la proposal, khong phai ket qua phan tich da chay.

### Buoc 3: Nguoi dung xem va sua

Frontend hien:

- summary
- code
- explanation
- canh bao rui ro
- output du kien

Nguoi dung co the sua code truc tiep, vi du doi nguong outlier, doi ten bieu do, doi cot phan tich.

### Buoc 4: Approve va run local

Khi nguoi dung approve, backend luu:

- ai code goc
- edited code
- `approved_by`
- `approved_at`
- `code_hash`

Execution API chi chay neu `code_hash` cua request khop voi code da approve.

### Buoc 5: Luu va hien ket qua

Ket qua gom:

- stdout
- stderr
- bang output neu co
- anh bieu do neu co
- loi neu co
- thoi gian chay
- artifact path

Frontend hien ket qua va logs co the truy xuat lai.

## Cau truc thu muc de xuat

```text
project/
  app/
    api/
      ai.py
      approvals.py
      executions.py
      logs.py
      datasets.py
    services/
      llm_provider.py
      proposal_service.py
      execution_service.py
      log_service.py
      policy_checker.py
    models/
      schemas.py
      database.py
  frontend/
    streamlit_app.py
  data/
    raw/
    working/
  outputs/
  runs/
  ai_logs.db
```

Neu project hien co da co cau truc rieng, khong can doi het. Chi can gan cac module tren vao dung vi tri tuong ung.

## Frontend chot: React JavaScript kieu VSCode

Huong FastAPI + React JavaScript la oke va nen chot neu nhom muon san pham nhin nghiem tuc. React cho phep chia UI thanh component ro rang, con FastAPI tao API local co docs tu dong de test.

### Layout de xuat

```text
┌────────────────────┬──────────────────────────────┬─────────────────────┐
│ Dataset / History  │ AI Request + Code Editor      │ Result / Logs       │
│ - datasets         │ - prompt box                  │ - chart preview     │
│ - sessions         │ - proposal summary            │ - table preview     │
│ - traces           │ - Monaco Python editor        │ - stdout/stderr     │
└────────────────────┴──────────────────────────────┴─────────────────────┘
```

### Thu vien frontend nen dung

- `react`
- `vite`
- `@monaco-editor/react`
- `lucide-react` cho icon
- `recharts` hoac `plotly.js` neu muon chart tren frontend
- `tailwindcss` + `@tailwindcss/vite` de style nhanh bang utility classes, khong viet CSS thu cong lon

### Mau component

- `DatasetSidebar.jsx`
- `PromptPanel.jsx`
- `ProposalEditor.jsx`
- `ApprovalBar.jsx`
- `ResultViewer.jsx`
- `LogTimeline.jsx`
- `api.js`

## Viec nen lam truoc

1. Tao API proposal tra code mau tu mock AI.
2. Tao UI hien code + approve.
3. Tao execution local chay code approved.
4. Tao log truy xuat lai.
5. Sau do moi gan DeepSeek/ds2api, OpenAI-compatible hoac Ollama that.

Lam theo thu tu nay se tranh bi ket o API key/model trong khi workflow chinh chua xong.

## Streamlit/Gradio con can khong?

Khong can neu da chot React. Streamlit/Gradio chi la fallback neu can demo cuc nhanh. Voi yeu cau giao dien dep kieu VSCode, React + Monaco la dung bai hon.

## Viec can tranh

- Dung PandasAI/LangChain agent roi cho no tu chay code truc tiep.
- De AI tu doc file tuy y tren may.
- De AI tu tao bieu do minh hoa khong den tu dataset.
- Chi lam chatbot tra loi text ma khong co approve/run/log.
- Luu log qua loa bang screenshot, khong co du lieu truy xuat.
