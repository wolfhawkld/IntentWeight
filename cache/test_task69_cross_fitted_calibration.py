import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "paper" / "experiments" / "scripts" / "task69_cross_fitted_calibration.py"


def load_module():
    spec = importlib.util.spec_from_file_location("task69_crossfit_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_resolve_recorded_artifact_path_accepts_project_relative_path(tmp_path):
    module = load_module()
    module.ROOT = tmp_path
    relative = Path("paper/experiments/data/artifacts/dense.json")
    expected = tmp_path / relative
    expected.parent.mkdir(parents=True)
    expected.write_text("{}\n", encoding="utf-8")

    actual = module.resolve_recorded_artifact_path(
        relative,
        fallback_dir=tmp_path / "fallback",
    )

    assert actual == expected.resolve()
