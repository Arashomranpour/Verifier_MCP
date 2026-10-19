"""Unit tests for the verifier tools (no protocol, no network)."""

from verifier_mcp import tools


# ---- verify_math ---------------------------------------------------------------
def test_math_identity_true():
    assert tools.verify_math("sin(x)**2 + cos(x)**2 = 1")["verified"] is True


def test_math_catches_false_claim():
    r = tools.verify_math("(x+1)**2", "x**2 + 1")
    assert r["verified"] is False
    assert "not" in r["detail"]


def test_math_correct_claim():
    assert tools.verify_math("(x+1)**2", "x**2 + 2*x + 1")["verified"] is True


def test_math_bad_input_reports_error():
    assert tools.verify_math("@@@")["verified"] is False


# ---- run_code ------------------------------------------------------------------
def test_code_runs_and_captures_stdout():
    r = tools.run_code("print(sum(range(101)))")
    assert r["ok"] and r["stdout"].strip() == "5050"


def test_code_timeout():
    r = tools.run_code("while True: pass", timeout=1)
    assert r["timed_out"] is True and r["ok"] is False


def test_code_nonzero_exit_is_not_ok():
    r = tools.run_code("raise SystemExit(3)")
    assert r["ok"] is False and r["return_code"] == 3


# ---- validate_schema -----------------------------------------------------------
def test_schema_valid():
    r = tools.validate_schema({"age": 40}, {"type": "object", "properties": {"age": {"type": "integer"}}})
    assert r["valid"] is True and r["errors"] == []


def test_schema_invalid_reports_path():
    r = tools.validate_schema('{"age":"forty"}',
                              '{"type":"object","required":["age"],"properties":{"age":{"type":"integer"}}}')
    assert r["valid"] is False
    assert r["errors"][0]["path"] == "age"


# ---- check_units ---------------------------------------------------------------
def test_units_evaluate():
    r = tools.check_units("5 meter / second * 2 second", expected_unit="meter")
    assert r["ok"] and r["magnitude"] == 10.0 and r["matches_expected"] is True


def test_units_inconsistent():
    assert tools.units_consistent("5 meter", "3 second")["consistent"] is False


def test_units_wrong_expected():
    r = tools.check_units("5 meter", expected_unit="second")
    assert r["matches_expected"] is False


# ---- test_regex ----------------------------------------------------------------
def test_regex_all_pass_with_groups():
    r = tools.test_regex(r"^(\d{3})-(\d{4})$",
                         [{"text": "123-4567", "should_match": True},
                          {"text": "12-4567", "should_match": False}])
    assert r["all_passed"] is True
    assert r["results"][0]["groups"] == ["123", "4567"]


def test_regex_detects_failure():
    r = tools.test_regex(r"\d+", [{"text": "abc", "should_match": True}])
    assert r["all_passed"] is False


def test_regex_invalid_pattern():
    assert "error" in tools.test_regex("(", [{"text": "x", "should_match": True}])
