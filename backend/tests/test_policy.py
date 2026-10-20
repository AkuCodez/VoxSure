from app.core.policy import PolicyParams, decide
from conftest import dist

P = PolicyParams()


def test_confident_in_scope_answers():
    d = decide(dist(library_hours=0.95), P)
    assert (d.action, d.intent) == ("answer", "library_hours")


def test_competing_intents_clarify_with_options():
    d = decide(dist(library_hours=0.45, hostel_info=0.40), P)
    assert d.action == "clarify" and d.clarify_kind == "disambiguate"
    assert d.options[:2] == ["library_hours", "hostel_info"]


def test_high_prob_but_small_margin_still_clarifies():
    d = decide(dist(library_hours=0.82, fee_payment=0.15), P)  # margin .67 -> answer
    assert d.action == "answer"
    d = decide({"library_hours": 0.81, "fee_payment": 0.79 - 0.0, "out_of_scope": 0.0}, P)
    assert d.action == "clarify"


def test_low_confidence_triggers_repair():
    d = decide(dist(library_hours=0.2, fee_payment=0.19, exam_info=0.18), P)
    assert d.action == "clarify" and d.clarify_kind == "repair"


def test_out_of_scope_fallback():
    d = decide(dist(out_of_scope=0.95), P)
    assert (d.action, d.reason) == ("fallback", "out_of_scope")


def test_uncertain_oos_is_not_a_blind_fallback():
    d = decide(dist(out_of_scope=0.35, library_hours=0.3), P)
    assert d.action == "clarify" and d.clarify_kind == "repair"


def test_smalltalk_answers_without_margin():
    assert decide(dist(greeting=0.9), P).action == "answer"


def test_doubtful_asr_forces_repair_unless_very_sure():
    assert decide(dist(library_hours=0.9), P, asr_conf=0.2).clarify_kind == "repair"
    assert decide(dist(library_hours=0.99), P, asr_conf=0.2).action == "answer"


def test_repeated_failure_stops_the_loop():
    d = decide(dist(library_hours=0.45, hostel_info=0.40), P, attempts=2)
    assert (d.action, d.reason) == ("fallback", "repeated_failure")
    assert decide(dist(library_hours=0.95), P, attempts=5).action == "answer"  # confident still answers
