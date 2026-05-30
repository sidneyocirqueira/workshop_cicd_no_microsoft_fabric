"""Static analysis tests for the Sales PBIR report (visual.json files)."""

import json
import re
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_REPORT_DEF = _ROOT / "src" / "Reports" / "Sales Report.Report" / "definition"
_MEDIDAS_TMDL = (
    _ROOT / "src" / "Semantic Models" / "Sales.SemanticModel" / "definition" / "tables" / "Medidas.tmdl"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_visual_files() -> list[Path]:
    return list(_REPORT_DEF.rglob("visual.json"))


def _model_measure_names() -> set[str]:
    """Return all measure names declared in Medidas.tmdl."""
    text = _MEDIDAS_TMDL.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*measure\s+'([^']+)'", text, re.MULTILINE))


def _extract_measure_refs(obj: object) -> set[str]:
    """Recursively collect every ``Measure.Property`` value in a JSON object."""
    refs: set[str] = set()
    if isinstance(obj, dict):
        measure = obj.get("Measure")
        if isinstance(measure, dict) and "Property" in measure:
            refs.add(measure["Property"])
        for v in obj.values():
            refs |= _extract_measure_refs(v)
    elif isinstance(obj, list):
        for item in obj:
            refs |= _extract_measure_refs(item)
    return refs


# ---------------------------------------------------------------------------
# Report structure tests
# ---------------------------------------------------------------------------


class TestReportStructure:
    """Validate the presence and completeness of report definition files."""

    def test_report_definition_exists(self) -> None:
        assert (_REPORT_DEF / "report.json").exists(), (
            "src/Gerencial.Report/definition/report.json not found"
        )

    def test_pages_file_exists(self) -> None:
        assert (_REPORT_DEF / "pages" / "pages.json").exists(), (
            "pages/pages.json not found in report definition"
        )

    def test_visual_files_exist(self) -> None:
        visuals = _all_visual_files()
        assert visuals, "No visual.json files found under Gerencial.Report/definition"

    def test_all_visual_json_have_schema(self) -> None:
        """Every visual.json must declare a ``$schema`` for version tracking."""
        missing: list[str] = []
        for path in _all_visual_files():
            visual = json.loads(path.read_text(encoding="utf-8"))
            if "$schema" not in visual:
                missing.append(str(path.relative_to(_ROOT)))
        assert not missing, f"visual.json files missing $schema: {missing}"

    def test_all_visuals_have_visual_type(self) -> None:
        """Every visual container must declare a ``visualType``."""
        missing: list[str] = []
        for path in _all_visual_files():
            visual = json.loads(path.read_text(encoding="utf-8"))
            if not visual.get("visual", {}).get("visualType"):
                missing.append(str(path.relative_to(_ROOT)))
        assert not missing, f"Visuals without visualType: {missing}"


# ---------------------------------------------------------------------------
# Cross-model validation
# ---------------------------------------------------------------------------


class TestMeasureConsistency:
    """Validate that measure references in visuals exist in the semantic model."""

    def test_all_referenced_measures_exist_in_model(self) -> None:
        """Measures used in report visuals must be defined in Medidas.tmdl."""
        model_measures = _model_measure_names()
        assert model_measures, "No measures found in Medidas.tmdl — check parsing"

        broken: dict[str, set[str]] = {}
        for path in _all_visual_files():
            visual = json.loads(path.read_text(encoding="utf-8"))
            refs = _extract_measure_refs(visual)
            unknown = refs - model_measures
            if unknown:
                broken[str(path.relative_to(_ROOT))] = unknown

        if broken:
            lines = "\n".join(
                f"  {file}: {sorted(names)}" for file, names in sorted(broken.items())
            )
            assert False, f"Unknown measure references in report visuals:\n{lines}"

    def test_no_duplicate_measure_names_in_model(self) -> None:
        """Duplicate measure names in Medidas.tmdl cause ambiguous references."""
        text = _MEDIDAS_TMDL.read_text(encoding="utf-8")
        all_names = re.findall(r"^\s*measure\s+'([^']+)'", text, re.MULTILINE)
        seen: set[str] = set()
        duplicates: list[str] = []
        for name in all_names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)
        assert not duplicates, f"Duplicate measure names in Medidas.tmdl: {duplicates}"
