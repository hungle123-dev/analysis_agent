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


def test_policy_accepts_datetime_imports():
    issues = validate_code("from datetime import datetime, timedelta\nprint(datetime.now() + timedelta(days=1))")
    assert issues == []


def test_policy_accepts_common_safe_analysis_imports():
    code = """
from collections import Counter
from matplotlib.ticker import FuncFormatter
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from sklearn import metrics, preprocessing
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import scipy.stats as scipy_stats
import sklearn.linear_model as linear_model
import statsmodels.api as sm
import seaborn as sb
import warnings
import re
import unicodedata
warnings.filterwarnings("ignore")
print(Counter(["a", "b", "a"]))
print(re.sub(r"\\s+", " ", "a   b"))
print(unicodedata.normalize("NFC", "test"))
print(FuncFormatter)
print(mdates.DateFormatter)
print(ticker.FuncFormatter)
print(stats.pearsonr([1, 2, 3], [1, 3, 5]))
print(pearsonr([1, 2, 3], [1, 3, 5]))
print(spearmanr([1, 2, 3], [1, 3, 5]))
print(scipy_stats.spearmanr([1, 2, 3], [1, 3, 5]))
print(metrics.r2_score([1, 2, 3], [1, 2, 4]))
print(preprocessing.StandardScaler)
print(r2_score([1, 2, 3], [1, 2, 4]))
print(train_test_split)
print(seasonal_decompose)
print(linear_model.LinearRegression)
print(sm.OLS)
print(sb)
"""
    issues = validate_code(code)
    assert issues == []


def test_policy_blocks_analysis_imports_that_can_bypass_dataset_rule():
    code = """
from scipy.io import loadmat
from sklearn.datasets import load_iris
from statsmodels.datasets import get_rdataset
"""
    issues = validate_code(code)
    messages = "\n".join(issue["message"] for issue in issues)
    assert "from scipy.io import loadmat" in messages
    assert "from sklearn.datasets import load_iris" in messages
    assert "from statsmodels.datasets import get_rdataset" in messages


def test_policy_accepts_safe_output_path_variables():
    code = """
import matplotlib.pyplot as plt
work_df = df.copy()
summary = work_df.head()
chart_path = outputs_dir / "chart.png"
table_path = outputs_dir / "summary.csv"
summary.to_csv(table_path, index=False)
plt.figure()
plt.savefig(chart_path)
"""
    issues = validate_code(code)
    assert issues == []


def test_policy_blocks_outputs_dir_parent_escape():
    issues = validate_code("df.to_csv(outputs_dir.parent / 'leak.csv', index=False)")
    assert any(issue["code"] == "unsafe_output_path" for issue in issues)


def test_policy_blocks_unsafe_output_path_variables():
    code = """
bad_path = outputs_dir.parent / "leak.csv"
df.to_csv(bad_path, index=False)
"""
    issues = validate_code(code)
    assert any(issue["code"] == "unsafe_output_path" for issue in issues)


def test_policy_blocks_wrong_output_extension_for_writer():
    issues = validate_code("work_df = df.copy()\nwork_df.to_csv(outputs_dir / 'summary.txt', index=False)")
    assert any(issue["code"] == "unsafe_output_path" for issue in issues)


def test_policy_blocks_non_image_chart_outputs():
    issues = validate_code("import matplotlib.pyplot as plt\nplt.savefig(outputs_dir / 'chart.pdf')")
    assert any(issue["code"] == "unsafe_output_path" for issue in issues)


def test_policy_blocks_alias_mutation_of_df():
    issues = validate_code("work_df = df\nwork_df['new_col'] = 1")
    assert any(issue["code"] == "dataset_mutation" for issue in issues)


def test_policy_blocks_delete_on_original_df():
    issues = validate_code("del df['Doanh Thu']")
    assert any(issue["code"] == "dataset_mutation" for issue in issues)


def test_policy_blocks_extra_data_reads():
    issues = validate_code("import pandas as pd\npd.read_csv('other.csv')")
    assert any(issue["code"] == "unsafe_data_read" for issue in issues)


def test_policy_accepts_replace_and_rename_on_working_copy():
    code = """
work_df = df.copy()
work_df = work_df.rename(columns={"Gia": "Gia_clean"})
work_df["Gia_clean"] = work_df["Gia_clean"].astype(str).str.replace(",", "", regex=False)
"""
    issues = validate_code(code)
    assert issues == []


def test_policy_blocks_replace_and_rename_on_managed_paths():
    code = """
chart_path = outputs_dir / "chart.png"
chart_path.replace(outputs_dir / "other.png")
outputs_dir.rename(outputs_dir / "renamed")
"""
    issues = validate_code(code)
    assert sum(issue["code"] == "blocked_call" for issue in issues) == 2


def test_policy_accepts_safe_text_output_open_write():
    code = """
notes_path = outputs_dir / "notes.txt"
with open(notes_path, "w", encoding="utf-8") as f:
    f.write("Nhan xet ngan gon")
"""
    issues = validate_code(code)
    assert issues == []


def test_policy_blocks_open_with_non_text_extension():
    code = """
with open(outputs_dir / "chart.png", "w", encoding="utf-8") as f:
    f.write("bad")
"""
    issues = validate_code(code)
    assert any(issue["code"] == "blocked_call" for issue in issues)


def test_policy_blocks_open_write_outside_outputs_dir():
    code = """
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("bad")
"""
    issues = validate_code(code)
    assert any(issue["code"] == "blocked_call" for issue in issues)


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
