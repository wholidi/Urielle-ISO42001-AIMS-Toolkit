from pathlib import Path
import re
import agentic_assessment.clause05 as clause05

def test_phase04_has_no_workflow_or_supervisor_module():
    root = Path(clause05.__file__).resolve().parent
    assert not (root / "workflow.py").exists()
    assert not (root / "supervisor.py").exists()

def test_configuration_contains_no_model_or_permission_authority():
    root = Path(clause05.__file__).resolve().parent
    text = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*") if p.suffix in {".py", ".json"})
    forbidden = [
        r"\bpermission_matrix\b",
        r"\bagent_registry\b",
        r"\bmodel_use_record\b",
        r"\binvoke_model\b",
        r"\bllm\b",
    ]
    lowered = text.lower()
    assert not any(re.search(pattern, lowered) for pattern in forbidden)
