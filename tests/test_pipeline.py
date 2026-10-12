"""Fast checks for the parts that must not silently break. Run: python -m pytest -q"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import classify_api  # noqa: E402
import labels_io  # noqa: E402
import rules  # noqa: E402
from analyze import wilson  # noqa: E402


def test_rules_tell_signin_from_shift_trip():
    # "logout" is usually the evening trip, not signing out.
    assert "J1.session" not in rules.classify("my logout cab was 40 minutes late", 1)["stages"]
    assert "J1.session" in rules.classify("app keeps logging me out every day", 1)["stages"]
    assert "J1.otp" in rules.classify("not getting otp on email or phone", 1)["stages"]


def test_rules_safety_ignores_praise():
    assert not rules.classify("super safe, love it", 5)["safety_flag"]
    assert rules.classify("driver was rash and drunk at night", 1)["safety_flag"]


def test_label_validation_rejects_bad_codes():
    ids = {"1": "abc"}
    good = {"i": 1, "st": ["J3.fail"], "d": "booking fails", "a": "app", "se": "neg", "sf": False}
    assert labels_io.validate_line(good, ids) == []
    bad = dict(good, st=["J99"], a="vendor")
    errs = labels_io.validate_line(bad, ids)
    assert any("stages" in e for e in errs) and any("attribution" in e for e in errs)


def test_api_parser_handles_success_refusal_and_garbage():
    ok = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps(
        {"labels": [{"i": 1, "st": ["X1.crash"], "d": "crashes", "a": "app", "se": "neg", "sf": False}]}))])
    labels, problem = classify_api.parse_message(ok)
    assert problem is None and labels[0]["st"] == ["X1.crash"]
    assert classify_api.parse_message(SimpleNamespace(stop_reason="refusal", content=[]))[1] == "refusal"
    garbled = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="not json")])
    assert classify_api.parse_message(garbled)[1].startswith("unparseable")


def test_api_requests_use_schema_and_budget_estimate():
    reqs = classify_api.build_requests([("chunk_x", [{"i": 1, "s": 1, "t": "otp not received"}])])
    params = reqs[0]["params"]
    assert params["model"] == "claude-sonnet-5-5"
    assert params["output_config"]["format"]["type"] == "json_schema"
    est = classify_api.estimate(reqs)
    assert est["reviews"] == 1 and est["usd"] < 0.01


def test_wilson_interval_is_sane():
    lo, hi = wilson(31, 100)
    assert 0.22 < lo < 0.31 < hi < 0.41
