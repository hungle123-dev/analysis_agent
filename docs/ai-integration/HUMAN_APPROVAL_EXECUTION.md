# Human Approval And Local Execution

## Nguyen tac trung tam

AI sinh code khong co nghia la code duoc chay. Code chi la de xuat. Con nguoi moi la nguoi quyet dinh.

## Workflow UI

```text
User request
  -> AI proposal
  -> Pending review
  -> User edits code
  -> Approve
  -> Run locally
  -> Show result
  -> Save log
```

## Trang thai

| Trang thai | Y nghia |
| --- | --- |
| `draft` | Moi nhan yeu cau |
| `pending_review` | AI da sinh code, dang cho nguoi dung xem |
| `edited` | Nguoi dung da sua code |
| `approved` | Nguoi dung da phe duyet |
| `running` | Dang chay local |
| `succeeded` | Chay thanh cong |
| `failed` | Loi khi validate/chay |
| `rejected` | Nguoi dung tu choi |

## UI can co

- Badge trang thai: `Pending review`, `Approved`, `Executed`.
- Code editor.
- Vung giai thich code.
- Canh bao neu code co thao tac loc/xoa/doi kieu du lieu.
- Nut `Reject`.
- Nut `Approve`.
- Nut `Run locally` chi bat sau approve.

## Policy checker toi thieu

Truoc khi chay code, backend nen parse code va chan:

- `eval`
- `exec`
- `open`
- `__import__`
- `os.system`
- `subprocess`
- `socket`
- `requests`
- `urllib`
- import ngoai whitelist
- ghi file ngoai `outputs/`

Whitelist de demo:

- `pandas`
- `numpy`
- `matplotlib`
- `seaborn`
- `scipy.stats`, `scipy.optimize`, `scipy.signal`
- `sklearn.metrics`, `sklearn.model_selection`, `sklearn.preprocessing`, `sklearn.linear_model`
- `statsmodels.api`, `statsmodels.formula.api`, `statsmodels.tsa`
- `math`
- `statistics`

Các nhánh có thể đọc dữ liệu ngoài hoặc tải dataset mẫu như `scipy.io`, `sklearn.datasets`, `statsmodels.datasets` không nằm trong whitelist.

## Runner local toi thieu

Moi lan run:

1. Tao `runs/{run_id}/`.
2. Tao `outputs/{run_id}/`.
3. Load dataset thanh dataframe `df`.
4. Chay code da approve bang process rieng.
5. Timeout 30-60 giay.
6. Capture stdout/stderr.
7. Chi lay artifact trong output directory.
8. Ghi log.

## Docker neu muon chac hon

Neu nhom co Docker, co the chay local trong container:

```bash
docker run --rm \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --memory 512m \
  --cpus 1 \
  --pids-limit 128 \
  -v job-input:/input:ro \
  -v job-output:/output:rw \
  ai-executor-python
```

Khong bat buoc phai dung Docker neu do an chi demo local, nhung neu khong dung Docker thi phai noi ro co policy checker, timeout va thu muc output rieng.

## Dieu can noi khi van dap

Neu thay hoi "AI co tu chay code khong?", cau tra loi nen la:

> Khong. AI API chi tao proposal. Proposal o trang thai pending_review. Nguoi dung phai xem, co the sua, roi approve. Execution API chi chay proposal da approve va code_hash phai khop voi ban da duyet.
