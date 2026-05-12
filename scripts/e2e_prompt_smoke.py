from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
DATASET_ID = "vietnam_real_estate_cleaned"

PROMPTS = [
    "Hãy vẽ biểu đồ giá trung bình theo tỉnh/thành và nhận xét các điểm nổi bật.",
    "Hãy kiểm tra mối quan hệ giữa diện tích và giá bán, vẽ scatter plot hoặc biểu đồ phù hợp rồi nhận xét xu hướng.",
    "Hãy vẽ biểu đồ doanh thu theo tháng và nhận xét xu hướng.",
    "Hãy vẽ phân bố Gia_Trieu_VND bằng histogram và nhận xét dữ liệu có bị lệch hoặc có outlier không.",
    "Hãy so sánh giá trung bình giữa nhóm Mat_Tien=True và Mat_Tien=False, vẽ biểu đồ và nhận xét.",
    "Hãy phân tích giá trung bình theo Loai_Hinh, vẽ biểu đồ và nhận xét sự khác biệt giữa mua bán và cho thuê.",
    "Hãy tìm top 10 quận/huyện có số lượng tin đăng nhiều nhất, vẽ biểu đồ cột và nhận xét.",
    "Hãy tính giá trung bình trên m2 theo tỉnh/thành bằng cột Gia_Tren_m2_Trieu, vẽ biểu đồ top 10 và nhận xét.",
    "Hãy kiểm tra các giá trị bất thường trong Dien_Tich_m2 và Gia_Trieu_VND, in thống kê mô tả và vẽ boxplot.",
    "Hãy phân tích lợi nhuận theo quý và dự báo quý tiếp theo.",
    "Hãy vẽ top 10 tỉnh/thành có số lượng tin đăng nhiều nhất và nhận xét mức độ tập trung.",
    "Hãy so sánh giá trung vị theo Loai_Hinh và Mat_Tien, vẽ biểu đồ nhóm và nhận xét.",
    "Hãy phân tích giá trung bình theo số phòng ngủ, chỉ lấy nhóm có ít nhất 100 tin, vẽ biểu đồ.",
    "Hãy phân tích giá theo số tầng, lọc các giá trị So_Tang bất thường nếu cần, vẽ biểu đồ và nhận xét.",
    "Hãy chia Dien_Tich_m2 thành các khoảng diện tích hợp lý và so sánh giá trung vị giữa các khoảng.",
    "Hãy kiểm tra Gia_Tren_m2_Trieu có outlier không, vẽ histogram hoặc boxplot và nhận xét.",
    "Hãy phân tích top 15 quận/huyện có giá trung vị cao nhất, chỉ lấy nhóm có ít nhất 50 tin.",
    "Hãy so sánh số lượng tin đăng giữa Mua Bán và Cho Thuê theo top 10 tỉnh/thành nhiều tin nhất.",
    "Hãy tìm các từ khóa xuất hiện nhiều trong Tieu_De và vẽ top 15 từ khóa phổ biến.",
    "Hãy dự báo doanh số năm sau và lợi nhuận theo chiến dịch marketing.",
    "Hãy tính tương quan giữa Dien_Tich_m2, So_Phong_Ngu, So_Phong_Tam, So_Tang và Gia_Trieu_VND, vẽ heatmap hoặc bảng tương quan rồi nhận xét.",
    "Hãy kiểm tra tỷ lệ thiếu dữ liệu theo từng cột, vẽ biểu đồ top cột thiếu nhiều nhất và gợi ý cột nào cần chú ý.",
    "Hãy so sánh phân bố Gia_Trieu_VND giữa Mua Bán và Cho Thuê bằng boxplot, có xử lý outlier để biểu đồ dễ đọc.",
    "Hãy phân nhóm bất động sản theo diện tích nhỏ, vừa, lớn rồi so sánh số lượng tin và giá trung vị theo từng nhóm.",
    "Hãy phân tích tỷ lệ chuyển đổi khách hàng theo kênh quảng cáo và vẽ funnel conversion.",
    "Hãy chỉ phân tích nhóm Cho Thuê: vẽ phân bố Gia_Trieu_VND và in các thống kê trung vị, Q1, Q3.",
    "Hãy chỉ phân tích nhóm Mua Bán: top 10 tỉnh/thành có giá trung vị cao nhất, chỉ lấy nhóm có ít nhất 100 tin.",
    "Hãy tính tỷ lệ tin có Mat_Tien=True theo từng tỉnh/thành trong top 10 tỉnh nhiều tin nhất và vẽ biểu đồ.",
    "Hãy kiểm tra mối quan hệ giữa So_Phong_Tam và Gia_Trieu_VND, vẽ biểu đồ phù hợp và nhận xét.",
    "Hãy tìm các dòng có Dien_Tich_m2 hoặc Gia_Trieu_VND bằng 0, in số lượng và vẽ biểu đồ tỷ lệ theo cột.",
    "Hãy phân tích độ dài Tieu_De có liên quan đến Gia_Trieu_VND không, vẽ scatter hoặc boxplot phù hợp.",
    "Hãy so sánh Gia_Tren_m2_Trieu giữa các nhóm Loai_Hinh và Mat_Tien bằng biểu đồ phù hợp.",
    "Hãy phân tích phân bố số phòng ngủ theo Loai_Hinh và vẽ biểu đồ stacked bar.",
    "Hãy vẽ bản đồ nhiệt theo tọa độ latitude/longitude để thể hiện giá bất động sản.",
    "Hãy phân tích retention khách hàng theo cohort tháng đăng ký.",
]


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> {exc.code}: {body}") from exc


def run_prompt(prompt: str, index: int) -> dict:
    print(f"\n===== TEST {index} =====", flush=True)
    print("Câu hỏi:", prompt, flush=True)
    job = request(
        "POST",
        "/api/ai/proposals/jobs",
        {
            "session_id": "test_tieng_viet_co_dau",
            "dataset_id": DATASET_ID,
            "user_request": prompt,
            "mode": "generate_code",
        },
    )
    print("Job:", job["job_id"], job["status"], flush=True)

    final_job = job
    started = time.time()
    while time.time() - started < 150:
        final_job = request("GET", f"/api/ai/proposals/jobs/{job['job_id']}")
        if final_job["status"] in {"succeeded", "failed"}:
            break
        time.sleep(2)

    print(
        "Job cuối:",
        final_job["status"],
        "proposal_id=",
        final_job.get("proposal_id"),
        "error=",
        final_job.get("error"),
        flush=True,
    )
    if final_job["status"] != "succeeded":
        return {"prompt": prompt, "job": final_job, "ok": False}

    proposal = request("GET", f"/api/ai/proposals/{final_job['proposal_id']}")
    print("Tóm tắt:", proposal["summary"][:240], flush=True)
    print("Expected outputs:", proposal["expected_outputs"], flush=True)
    print("Số dòng code:", len(proposal["code"].splitlines()), flush=True)

    approval = request(
        "POST",
        f"/api/ai/proposals/{proposal['proposal_id']}/approve",
        {
            "approved_by": "codex_test",
            "approval_note": "Phê duyệt tự động trong kịch bản test do người dùng yêu cầu.",
        },
    )
    execution = request(
        "POST",
        "/api/executions",
        {
            "proposal_id": proposal["proposal_id"],
            "dataset_id": DATASET_ID,
            "code_hash": approval["code_hash"],
            "requested_by": "codex_test",
        },
    )
    print(
        "Run:",
        execution["run_id"],
        execution["status"],
        "return_code=",
        execution["return_code"],
        "duration_ms=",
        execution["duration_ms"],
        flush=True,
    )
    print("Artifacts:", [(item["type"], item["name"]) for item in execution["artifacts"]], flush=True)
    print("Insight:", execution["ai_insight_status"], flush=True)
    print("Stdout đầu:", (execution.get("stdout") or "")[:300].replace("\n", " | "), flush=True)
    print(
        "Nhận xét đầu:",
        (execution.get("ai_insight") or execution.get("ai_insight_error") or "")[:400].replace("\n", " | "),
        flush=True,
    )
    return {
        "prompt": prompt,
        "proposal_id": proposal["proposal_id"],
        "run_id": execution["run_id"],
        "status": execution["status"],
        "artifacts": execution["artifacts"],
        "ai_insight_status": execution["ai_insight_status"],
        "ok": execution["status"] == "succeeded",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=0, help="Run one prompt by 1-based index.")
    parser.add_argument("--start", type=int, default=0, help="Run prompts from this 1-based index.")
    parser.add_argument("--end", type=int, default=0, help="Run prompts through this 1-based index.")
    args = parser.parse_args()

    selected = PROMPTS
    start_index = 1
    if args.index:
        selected = [PROMPTS[args.index - 1]]
        start_index = args.index
    elif args.start or args.end:
        start_index = max(1, args.start or 1)
        end_index = min(len(PROMPTS), args.end or len(PROMPTS))
        selected = PROMPTS[start_index - 1 : end_index]

    results = []
    for index, prompt in enumerate(selected, start_index):
        try:
            results.append(run_prompt(prompt, index))
        except Exception as exc:
            print(f"\nTEST {index} LỖI: {exc}", flush=True)
            results.append({"prompt": prompt, "ok": False, "error": str(exc)})
    print("\n===== TỔNG KẾT =====", flush=True)
    for item in results:
        print(json.dumps(item, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
