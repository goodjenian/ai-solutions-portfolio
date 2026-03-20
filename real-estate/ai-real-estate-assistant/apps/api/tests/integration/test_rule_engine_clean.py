from rules.engine import RuleEngine


def test_no_error_level_violations_in_core():
    eng = RuleEngine()
    roots = [
        "agents",
        "api",
        "vector_store",
        "data",
        "analytics",
        "models",
        "utils",
        "notifications",
        "config",
        "tools",
        "i18n",
    ]
    error_count = 0
    for root in roots:
        import os

        for r, _, fnames in os.walk(root):
            for f in fnames:
                if f.endswith(".py"):
                    vs = eng.validate_file(os.path.join(r, f))
                    error_count += sum(1 for v in vs if v.severity == "error")
    assert error_count == 0
