from pyarchrules.core.rules.checks.imports import collect_imports


def test_collect_imports_finds_nested_statements_and_type_checking(tmp_path):
    source = tmp_path / "m.py"
    source.write_text(
        "import a\n"
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    import tc\n"
        "else:\n"
        "    import runtime\n"
        "def f():\n"
        "    import in_func\n"
        "class C:\n"
        "    def g(self):\n"
        "        from . import in_method\n"
        "try:\n"
        "    import t\n"
        "except ImportError:\n"
        "    import fallback\n"
        "finally:\n"
        "    import fin\n"
        "match 1:\n"
        "    case 1:\n"
        "        import in_case\n",
        encoding="utf-8",
    )

    found = {imp.module: imp.type_checking for imp in collect_imports(source)}

    assert found == {
        "a": False,
        "typing": False,
        "tc": True,
        "runtime": False,
        "in_func": False,
        ".": False,
        "t": False,
        "fallback": False,
        "fin": False,
        "in_case": False,
    }
