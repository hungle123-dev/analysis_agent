from __future__ import annotations

from backend.app.schemas import CreateProposalRequest, DatasetContext
from backend.app.services.llm_provider import ProposalDraft


class MockLLMProvider:
    name = "mock"

    def create_proposal(self, payload: CreateProposalRequest, context: DatasetContext) -> ProposalDraft:
        return ProposalDraft(
            summary=f"Generate local analysis code for: {payload.user_request}",
            code=generate_mock_code(context.id),
            explanation=(
                "Code tao ban sao dataframe, chuan hoa cot date neu co, tinh bang tong hop, "
                "ve chart bang matplotlib va luu artifact vao outputs_dir."
            ),
            assumptions=[
                "Input dataframe is available as df",
                "outputs_dir is provided by local runner",
                "Generated code must be reviewed and approved by a human before execution",
            ],
            risk_flags=["creates_chart_file", "creates_table_stdout"],
            expected_outputs=["table", "chart", "log"],
            metadata={"provider": self.name, "model": "mock", "llm_duration_ms": 0},
        )


def generate_mock_code(dataset_id: str) -> str:
    if dataset_id == "sales_2025":
        return '''# Doan code nay tao ban sao dataframe de khong thay doi du lieu goc.
work_df = df.copy()

# Doan code nay chuyen cot date sang kieu ngay thang de co the nhom theo thang.
work_df["date"] = pd.to_datetime(work_df["date"])

# Doan code nay tao cot month va tinh tong revenue theo tung thang.
work_df["month"] = work_df["date"].dt.to_period("M").astype(str)
monthly = work_df.groupby("month", as_index=False)["revenue"].sum()

# Doan code nay ve bieu do duong va luu vao thu muc outputs cua lan chay.
plt.figure(figsize=(10, 5))
plt.plot(monthly["month"], monthly["revenue"], marker="o")
plt.title("Monthly revenue")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(outputs_dir / "revenue_by_month.png")

# Doan code nay in bang tong hop de frontend co the hien thi stdout.
print(monthly.to_string(index=False))

# === Nhan xet dua tren ket qua in (khong dua so ngoai bang monthly) ===
# - Chuoi temporal theo cot month; moi hang la tong revenue trong thang do nhu trong bang print.
# - Bieu do line noi lien cac diem chronology; chenh lech giua cac cot co the nhin tu bang va hinh PNG sau khi chay duoc phe duyet.
'''

    return '''# Doan code nay tao ban sao dataframe de khong thay doi du lieu goc.
work_df = df.copy()

# Doan code nay tinh thong ke mo ta cho cac cot so.
summary = work_df.describe(numeric_only=True)

# Doan code nay luu bang thong ke ra stdout de frontend hien thi.
print(summary.to_string())

# === Nhan xet dinh luong (chi lap lai thong tin trong bang summarize phia tren) ===
# - So luong bien so (count) trong bang la so quan sat co trong work_df doi voi moi cot numeric.
# - mean/std/min/max la thong ke mo ta tien bo theo cot; khong suy luong sai lech khi cot co nhieu NaN hay gia tri ngoai pham vi nghiep vu.
'''
