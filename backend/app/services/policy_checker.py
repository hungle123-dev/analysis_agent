from __future__ import annotations

import ast

ALLOWED_IMPORTS = {
    "math",
    "statistics",
    "numpy",
    "numpy as np",
    "pandas",
    "pandas as pd",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.pyplot as plt",
    "seaborn",
    "seaborn as sns",
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
    "open",
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
    "rename",
    "replace",
    "request",
    "rmdir",
    "send",
    "spawn",
    "system",
    "unlink",
    "write",
    "write_bytes",
    "write_text",
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


def validate_code(code: str) -> list[str]:
    errors: list[str] = []

    def add(message: str) -> None:
        if message not in errors:
            errors.append(message)

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"Syntax error: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_name = _format_import(alias.name, alias.asname)
                if _is_forbidden_module(alias.name) or import_name not in ALLOWED_IMPORTS:
                    add(f"Import khong duoc phep: {import_name}")

        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_forbidden_module(module):
                add(f"Import khong duoc phep: from {module}")
            else:
                for alias in node.names:
                    import_name = f"{module}.{alias.name}" if module else alias.name
                    if import_name not in ALLOWED_IMPORTS:
                        add(f"Import khong duoc phep: from {module} import {alias.name}")

        if isinstance(node, ast.Call):
            _validate_call(node, add)

        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = _assignment_targets(node)
            if any(_touches_original_df(target) for target in targets):
                add("Khong duoc gan truc tiep vao df goc. Hay tao work_df = df.copy() truoc khi bien doi.")

        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            add(f"Khong duoc truy cap thuoc tinh noi bo: {node.attr}")

        if isinstance(node, ast.Name) and node.id.startswith("__"):
            add(f"Khong duoc truy cap ten noi bo: {node.id}")

    return errors


def _validate_call(node: ast.Call, add) -> None:
    func = node.func
    if isinstance(func, ast.Name):
        if func.id in FORBIDDEN_CALL_NAMES:
            add(f"Lenh goi khong an toan bi chan: {func.id}()")
        if func.id in {"Path"}:
            add("Khong duoc tao duong dan tuy y. Hay dung outputs_dir duoc backend cung cap.")
        return

    if not isinstance(func, ast.Attribute):
        return

    attr = func.attr
    if attr in FORBIDDEN_ATTR_CALLS:
        add(f"Lenh goi khong an toan bi chan: .{attr}()")
    if attr in DATA_READER_CALLS:
        add(f"Khong duoc doc them du lieu bang .{attr}(). Backend da nap dataset vao df.")
    if attr in OUTPUT_WRITER_CALLS and not _call_uses_outputs_dir(node):
        add(f"Lenh .{attr}() chi duoc ghi vao outputs_dir.")
    if attr in MUTATING_DF_CALLS and _is_name(func.value, "df"):
        add(f"Khong duoc goi df.{attr}() truc tiep tren du lieu goc. Hay dung work_df = df.copy().")
    if _is_name(func.value, "df") and any(
        keyword.arg == "inplace" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
        for keyword in node.keywords
    ):
        add("Khong duoc bien doi df goc voi inplace=True. Hay thao tac tren work_df.")


def _format_import(name: str, asname: str | None) -> str:
    return f"{name} as {asname}" if asname else name


def _is_forbidden_module(module: str) -> bool:
    root = module.split(".", 1)[0]
    return root in FORBIDDEN_MODULE_PREFIXES


def _assignment_targets(node: ast.Assign | ast.AnnAssign | ast.AugAssign) -> list[ast.AST]:
    if isinstance(node, ast.Assign):
        return list(node.targets)
    return [node.target]


def _touches_original_df(node: ast.AST) -> bool:
    if _is_name(node, "df"):
        return True
    if isinstance(node, ast.Subscript):
        return _touches_original_df(node.value)
    if isinstance(node, ast.Attribute):
        return _touches_original_df(node.value)
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_touches_original_df(element) for element in node.elts)
    return False


def _call_uses_outputs_dir(node: ast.Call) -> bool:
    return any(_contains_name(arg, "outputs_dir") for arg in [*node.args, *[kw.value for kw in node.keywords]])


def _contains_name(node: ast.AST, name: str) -> bool:
    if _is_name(node, name):
        return True
    return any(_contains_name(child, name) for child in ast.iter_child_nodes(node))


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name
