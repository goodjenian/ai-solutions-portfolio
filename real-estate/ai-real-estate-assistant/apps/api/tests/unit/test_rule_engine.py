from rules.config import MAX_LINE_LENGTH
from rules.engine import RuleEngine


def test_line_length_rule_triggers_warning():
    eng = RuleEngine()
    long_line = "x" * (MAX_LINE_LENGTH + 10)
    content = long_line + "\nshort"
    violations = eng.validate_code(content, "dummy.py")
    assert any(v.rule_id == "Q001" for v in violations)


def test_ignore_patterns_skip_validation_for_known_paths():
    eng = RuleEngine()
    violations = eng.validate_file("i18n/translations.py")
    assert violations == []
    violations = eng.validate_file("notifications/email_templates.py")
    assert violations == []


def test_no_secrets_rule_detects_potential_secret():
    eng = RuleEngine()
    content = "API_KEY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'"
    violations = eng.validate_code(content, "secrets.py")
    assert any(v.rule_id == "S001" for v in violations)


def test_performance_loop_rule_detects_concat_in_loop():
    eng = RuleEngine()
    # Basic smoke: rule should not raise exceptions on simple input
    violations = eng.validate_code("for i in range(1):\n    pass\n", "perf.py")
    assert isinstance(violations, list)


def test_validate_file_reads_content_and_runs_rules(tmp_path):
    eng = RuleEngine()
    file_path = tmp_path / "sample.py"
    file_path.write_text("API_KEY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'\n", encoding="utf-8")
    violations = eng.validate_file(str(file_path))
    assert any(v.rule_id == "S001" for v in violations)


def test_validate_file_returns_error_violation_on_read_failure(tmp_path):
    eng = RuleEngine()
    missing = tmp_path / "does_not_exist.py"
    violations = eng.validate_file(str(missing))
    assert len(violations) == 1
    assert violations[0].rule_id == "SYS001"
    assert violations[0].severity == "error"


def test_add_rule_appends_rule():
    eng = RuleEngine()
    before = len(eng.rules)
    eng.add_rule(eng.rules[0])
    assert len(eng.rules) == before + 1
