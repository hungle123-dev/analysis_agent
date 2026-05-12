from __future__ import annotations

import ast
from pathlib import PurePath
from typing import Literal, TypedDict


class PolicyIssue(TypedDict):
    code: Literal["blocked_import", "blocked_call", "dataset_mutation", "unsafe_output_path", "unsafe_data_read", "syntax_error", "unsafe_internal_access"]
    message: str
    severity: Literal["error", "warning"]

ALLOWED_IMPORTS = {
    "collections",
    "math",
    "re",
    "statistics",
    "unicodedata",
    "warnings",
    "numpy",
    "numpy as np",
    "pandas",
    "pandas as pd",
    "matplotlib",
    "matplotlib.dates",
    "matplotlib.dates as mdates",
    "matplotlib.pyplot",
    "matplotlib.pyplot as plt",
    "matplotlib.ticker",
    "matplotlib.ticker as mtick",
    "seaborn",
    "seaborn as sns",
    "scipy.stats",
    "scipy.stats as stats",
    "datetime",
    "datetime.date",
    "datetime.datetime",
    "datetime.timedelta",
    "datetime.timezone",
}

SAFE_IMPORT_MODULE_PREFIXES = {
    "numpy",
    "pandas",
    "matplotlib",
    "seaborn",
    "scipy.cluster",
    "scipy.interpolate",
    "scipy.linalg",
    "scipy.optimize",
    "scipy.signal",
    "scipy.spatial",
    "scipy.special",
    "scipy.stats",
    "sklearn.cluster",
    "sklearn.compose",
    "sklearn.decomposition",
    "sklearn.ensemble",
    "sklearn.impute",
    "sklearn.linear_model",
    "sklearn.metrics",
    "sklearn.model_selection",
    "sklearn.naive_bayes",
    "sklearn.neighbors",
    "sklearn.pipeline",
    "sklearn.preprocessing",
    "sklearn.svm",
    "sklearn.tree",
    "statsmodels.api",
    "statsmodels.formula.api",
    "statsmodels.tsa",
}

ALLOWED_IMPORT_MODULES = {item.split(" as ", 1)[0] for item in ALLOWED_IMPORTS} | SAFE_IMPORT_MODULE_PREFIXES

ALLOWED_FROM_IMPORTS = {
    "collections": {"Counter", "defaultdict"},
    "datetime": {"date", "datetime", "timedelta", "timezone"},
    "matplotlib.dates": {"AutoDateLocator", "ConciseDateFormatter", "DateFormatter", "MonthLocator", "YearLocator"},
    "matplotlib.ticker": {"FuncFormatter", "MaxNLocator", "PercentFormatter", "StrMethodFormatter"},
    "scipy": {"cluster", "interpolate", "linalg", "optimize", "signal", "spatial", "special", "stats"},
    "sklearn": {
        "cluster",
        "compose",
        "decomposition",
        "ensemble",
        "impute",
        "linear_model",
        "metrics",
        "model_selection",
        "naive_bayes",
        "neighbors",
        "pipeline",
        "preprocessing",
        "svm",
        "tree",
    },
}

FORBIDDEN_MODULE_PREFIXES = {
    "builtins",
    "ctypes",
    "ftplib",
    "glob",
    "http",
    "importlib",
    "os",
    "pathlib",
    "pickle",
    "requests",
    "shutil",
    "socket",
    "sqlite3",
    "ssl",
    "subprocess",
    "sys",
    "urllib",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "breakpoint",
    "compile",
    "eval",
    "exec",
    "exit",
    "getattr",
    "globals",
    "input",
    "locals",
    "quit",
    "setattr",
    "vars",
}

FORBIDDEN_ATTR_CALLS = {
    "chmod",
    "copyfile",
    "dump",
    "dumps",
    "load",
    "loads",
    "mkdir",
    "open",
    "popen",
    "read_bytes",
    "read_text",
    "remove",
    "request",
    "rmdir",
    "send",
    "spawn",
    "system",
    "unlink",
    "write_bytes",
    "write_text",
}

PATH_DANGEROUS_ATTR_CALLS = {
    "rename",
    "replace",
}

DATA_READER_CALLS = {
    "read_csv",
    "read_excel",
    "read_feather",
    "read_fwf",
    "read_hdf",
    "read_json",
    "read_orc",
    "read_parquet",
    "read_pickle",
    "read_sas",
    "read_spss",
    "read_sql",
    "read_stata",
    "read_table",
    "read_xml",
}

OUTPUT_WRITER_CALLS = {
    "savefig",
    "to_csv",
    "to_excel",
    "to_html",
    "to_json",
    "to_markdown",
    "to_parquet",
}

OUTPUT_WRITER_EXTENSIONS = {
    "savefig": {".png", ".jpg", ".jpeg", ".webp"},
    "to_csv": {".csv"},
    "to_excel": {".xlsx"},
    "to_html": {".html"},
    "to_json": {".json"},
    "to_markdown": {".md"},
    "to_parquet": {".parquet"},
}

TEXT_OUTPUT_EXTENSIONS = {".txt", ".log", ".md", ".json"}

MUTATING_DF_CALLS = {
    "drop",
    "drop_duplicates",
    "dropna",
    "fillna",
    "insert",
    "mask",
    "pop",
    "rename",
    "replace",
    "set_index",
    "sort_values",
    "update",
    "where",
}


def validate_code(code: str) -> list[PolicyIssue]:
    errors: list[PolicyIssue] = []

    def add(issue_code: PolicyIssue["code"], message: str, severity: PolicyIssue["severity"] = "error") -> None:
        issue = {"code": issue_code, "message": message, "severity": severity}
        if issue not in errors:
            errors.append(issue)

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [{"code": "syntax_error", "message": f"Syntax error: {exc}", "severity": "error"}]

    df_aliases = _collect_df_aliases(tree)
    safe_outputs = _collect_safe_outputs(tree)
    safe_file_handles = _collect_safe_file_handles(tree, safe_outputs)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_name = _format_import(alias.name, alias.asname)
                if _is_forbidden_module(alias.name) or not _is_allowed_import_module(alias.name):
                    add("blocked_import", f"Import khong duoc phep: {import_name}")

        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_forbidden_module(module):
                add("blocked_import", f"Import khong duoc phep: from {module}")
            else:
                for alias in node.names:
                    import_name = f"{module}.{alias.name}" if module else alias.name
                    if (
                        not _is_allowed_from_import(module, alias.name)
                        and not _is_allowed_import_module(module)
                        and not _is_allowed_import_module(import_name)
                    ):
                        add("blocked_import", f"Import khong duoc phep: from {module} import {alias.name}")

        if isinstance(node, ast.Call):
            _validate_call(node, add, df_aliases, safe_outputs, safe_file_handles)

        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = _assignment_targets(node)
            if any(_touches_original_df(target, df_aliases) for target in targets):
                add("dataset_mutation", "Khong duoc gan truc tiep vao df goc. Hay tao work_df = df.copy() truoc khi bien doi.")

        if isinstance(node, ast.Delete) and any(_touches_original_df(target, df_aliases) for target in node.targets):
            add("dataset_mutation", "Khong duoc xoa cot/dong truc tiep tren df goc. Hay tao work_df = df.copy() truoc khi bien doi.")

        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            add("unsafe_internal_access", f"Khong duoc truy cap thuoc tinh noi bo: {node.attr}")

        if isinstance(node, ast.Name) and node.id.startswith("__"):
            add("unsafe_internal_access", f"Khong duoc truy cap ten noi bo: {node.id}")

    return errors


def _validate_call(
    node: ast.Call,
    add,
    df_aliases: set[str],
    safe_outputs: dict[str, str],
    safe_file_handles: set[str],
) -> None:
    func = node.func
    if isinstance(func, ast.Name):
        if func.id == "open":
            if not _is_safe_open_call(node, safe_outputs):
                add("blocked_call", "Lenh open() chi duoc ghi file text vao outputs_dir / 'ten_file.txt'.")
            return
        if func.id in FORBIDDEN_CALL_NAMES:
            add("blocked_call", f"Lenh goi khong an toan bi chan: {func.id}()")
        if func.id in {"Path"}:
            add("unsafe_output_path", "Khong duoc tao duong dan tuy y. Hay dung outputs_dir duoc backend cung cap.")
        return

    if not isinstance(func, ast.Attribute):
        return

    attr = func.attr
    if attr == "write":
        if not _is_name_in(func.value, safe_file_handles):
            add("blocked_call", "Lenh .write() chi duoc phep tren file handle mo bang open(outputs_dir / 'ten_file.txt', 'w').")
        return
    if attr in PATH_DANGEROUS_ATTR_CALLS and _touches_managed_output_path(func.value, safe_outputs):
        add("blocked_call", f"Khong duoc goi .{attr}() tren outputs_dir hoac output path da quan ly.")
    if attr in FORBIDDEN_ATTR_CALLS:
        add("blocked_call", f"Lenh goi khong an toan bi chan: .{attr}()")
    if attr in DATA_READER_CALLS:
        add("unsafe_data_read", f"Khong duoc doc them du lieu bang .{attr}(). Backend da nap dataset vao df.")
    if attr in OUTPUT_WRITER_CALLS and not _call_has_safe_output_target(node, safe_outputs, OUTPUT_WRITER_EXTENSIONS[attr]):
        allowed = ", ".join(sorted(OUTPUT_WRITER_EXTENSIONS[attr]))
        add("unsafe_output_path", f"Lenh .{attr}() chi duoc ghi bang outputs_dir / 'ten_file.ext' voi dinh dang: {allowed}.")
    if attr in MUTATING_DF_CALLS and _touches_original_df(func.value, df_aliases):
        add("dataset_mutation", f"Khong duoc goi df.{attr}() truc tiep tren du lieu goc. Hay dung work_df = df.copy().")
    if _touches_original_df(func.value, df_aliases) and any(
        keyword.arg == "inplace" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
        for keyword in node.keywords
    ):
        add("dataset_mutation", "Khong duoc bien doi df goc voi inplace=True. Hay thao tac tren work_df.")


def _collect_df_aliases(tree: ast.AST) -> set[str]:
    aliases = {"df"}
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and _is_name_in(node.value, aliases):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id not in aliases:
                        aliases.add(target.id)
                        changed = True
            if isinstance(node, ast.AnnAssign) and node.value is not None and _is_name_in(node.value, aliases):
                if isinstance(node.target, ast.Name) and node.target.id not in aliases:
                    aliases.add(node.target.id)
                    changed = True
    return aliases


def _collect_safe_file_handles(tree: ast.AST, safe_outputs: dict[str, str]) -> set[str]:
    handles: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            if _is_safe_open_call(item.context_expr, safe_outputs) and isinstance(item.optional_vars, ast.Name):
                handles.add(item.optional_vars.id)
    return handles


def _format_import(name: str, asname: str | None) -> str:
    return f"{name} as {asname}" if asname else name


def _is_forbidden_module(module: str) -> bool:
    root = module.split(".", 1)[0]
    return root in FORBIDDEN_MODULE_PREFIXES


def _is_allowed_import_module(module: str) -> bool:
    return any(module == allowed or module.startswith(f"{allowed}.") for allowed in ALLOWED_IMPORT_MODULES)


def _is_allowed_from_import(module: str, name: str) -> bool:
    return name in ALLOWED_FROM_IMPORTS.get(module, set())


def _assignment_targets(node: ast.Assign | ast.AnnAssign | ast.AugAssign) -> list[ast.AST]:
    if isinstance(node, ast.Assign):
        return list(node.targets)
    return [node.target]


def _touches_original_df(node: ast.AST, df_aliases: set[str]) -> bool:
    if _is_name_in(node, df_aliases):
        return True
    if isinstance(node, ast.Subscript):
        return _touches_original_df(node.value, df_aliases)
    if isinstance(node, ast.Attribute):
        return _touches_original_df(node.value, df_aliases)
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_touches_original_df(element, df_aliases) for element in node.elts)
    return False


def _touches_managed_output_path(node: ast.AST, safe_outputs: dict[str, str]) -> bool:
    if _is_name(node, "outputs_dir"):
        return True
    if _is_name_in(node, set(safe_outputs)):
        return True
    if isinstance(node, ast.Attribute):
        return _touches_managed_output_path(node.value, safe_outputs)
    if isinstance(node, ast.Subscript):
        return _touches_managed_output_path(node.value, safe_outputs)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _touches_managed_output_path(node.left, safe_outputs)
    return False


def _call_has_safe_output_target(node: ast.Call, safe_outputs: dict[str, str], allowed_extensions: set[str]) -> bool:
    values = [*node.args, *[kw.value for kw in node.keywords]]
    return any(_is_safe_output_path(value, safe_outputs, allowed_extensions) for value in values)


def _is_safe_output_path(
    node: ast.AST,
    safe_outputs: dict[str, str] | None = None,
    allowed_extensions: set[str] | None = None,
) -> bool:
    filename = _safe_output_filename(node, safe_outputs or {})
    return filename is not None and _has_allowed_extension(filename, allowed_extensions)


def _safe_output_filename(node: ast.AST, safe_outputs: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name) and node.id in safe_outputs:
        return safe_outputs[node.id]
    parts = _literal_parts_from_outputs_dir(node, safe_outputs)
    if parts is None or len(parts) != 1 or not _is_safe_output_segment(parts[0]):
        return None
    return parts[0]


def _literal_parts_from_outputs_dir(node: ast.AST, safe_outputs: dict[str, str]) -> list[str] | None:
    if _is_name(node, "outputs_dir"):
        return []
    if isinstance(node, ast.Name) and node.id in safe_outputs:
        return [safe_outputs[node.id]]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left_parts = _literal_parts_from_outputs_dir(node.left, safe_outputs)
        right_part = _literal_path_segment(node.right)
        if left_parts is None or right_part is None:
            return None
        return [*left_parts, right_part]
    return None


def _literal_path_segment(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_safe_output_segment(value: str) -> bool:
    segment = value.strip()
    return bool(segment) and segment not in {".", ".."} and "/" not in segment and "\\" not in segment


def _has_allowed_extension(filename: str, allowed_extensions: set[str] | None) -> bool:
    if not allowed_extensions:
        return True
    return PurePath(filename).suffix.lower() in allowed_extensions


def _is_safe_open_call(node: ast.AST, safe_outputs: dict[str, str]) -> bool:
    if not isinstance(node, ast.Call) or not _is_name(node.func, "open") or not node.args:
        return False
    if not _is_safe_output_path(node.args[0], safe_outputs, TEXT_OUTPUT_EXTENSIONS):
        return False
    if len(node.args) < 2:
        return False
    mode = node.args[1]
    if not isinstance(mode, ast.Constant) or not isinstance(mode.value, str):
        return False
    return mode.value in {"w", "wt", "a", "at"}


def _collect_safe_outputs(tree: ast.AST) -> dict[str, str]:
    assignments: dict[str, list[ast.AST]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            assignments.setdefault(node.target.id, []).append(node.value)

    safe_outputs: dict[str, str] = {}
    changed = True
    while changed:
        changed = False
        for name, values in assignments.items():
            filenames = [_safe_output_filename(value, safe_outputs) for value in values]
            if values and all(filename is not None for filename in filenames) and len(set(filenames)) == 1:
                filename = filenames[0]
                if filename is not None and safe_outputs.get(name) != filename:
                    safe_outputs[name] = filename
                    changed = True
    return safe_outputs


def _is_name_in(node: ast.AST, names: set[str]) -> bool:
    return isinstance(node, ast.Name) and node.id in names


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name
