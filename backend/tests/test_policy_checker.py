from __future__ import annotations

from backend.app.services.policy_checker import validate_code


def test_policy_blocks_forbidden_import():
    issues = validate_code("import os\nprint('x')")
    assert any(issue["code"] == "blocked_import" for issue in issues)


def test_policy_blocks_forbidden_call():
    issues = validate_code("eval('1+1')")
    assert any(issue["code"] == "blocked_call" for issue in issues)


def test_policy_blocks_df_mutation():
    issues = validate_code("df['new_col'] = 1")
    assert any(issue["code"] == "dataset_mutation" for issue in issues)


def test_policy_blocks_output_outside_outputs_dir():
    issues = validate_code("import matplotlib.pyplot as plt\nplt.savefig('chart.png')")
    assert any(issue["code"] == "unsafe_output_path" for issue in issues)


def test_policy_blocks_extra_data_reads():
    issues = validate_code("import pandas as pd\npd.read_csv('other.csv')")
    assert any(issue["code"] == "unsafe_data_read" for issue in issues)


def test_policy_accepts_safe_code_pattern():
    code = """
import pandas as pd
import matplotlib.pyplot as plt
work_df = df.copy()
summary = work_df.groupby('Tinh_Thanh', as_index=False)['Gia_Trieu_VND'].mean()
summary.to_csv(outputs_dir / 'summary.csv', index=False)
plt.figure(figsize=(6, 4))
plt.plot(summary['Tinh_Thanh'], summary['Gia_Trieu_VND'])
plt.savefig(outputs_dir / 'chart.png')
print(summary.head().to_string(index=False))
"""
    issues = validate_code(code)
    assert issues == []
