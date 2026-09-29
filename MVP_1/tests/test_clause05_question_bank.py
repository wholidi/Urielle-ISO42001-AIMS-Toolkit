from agentic_assessment.clause05.config import load_question_bank

def test_question_bank_has_stable_atomic_distribution():
    bank = load_question_bank()
    questions = bank["questions"]
    assert len(questions) == 21
    ids = [q["question_id"] for q in questions]
    assert len(ids) == len(set(ids))
    assert sum(q["clause_ref"] == "5.1" for q in questions) == 6
    assert sum(q["clause_ref"] == "5.2" for q in questions) == 8
    assert sum(q["clause_ref"] == "5.3" for q in questions) == 7
    assert all(q["human_acceptance_required"] is True for q in questions)
