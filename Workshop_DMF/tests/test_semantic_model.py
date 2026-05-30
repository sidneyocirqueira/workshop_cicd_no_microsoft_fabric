"""Static analysis tests for the Sales semantic model (TMDL format)."""

import re
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_TABLES = _ROOT / "src" / "Semantic Models" / "Sales.SemanticModel" / "definition" / "tables"
_MEDIDAS = _TABLES / "Medidas.tmdl"
_CALC_GROUP = _TABLES / "Inteligência de Tempo.tmdl"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MEASURE_BLOCK_RE = re.compile(r"(?=^\tmeasure\s+')", re.MULTILINE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _split_measure_blocks(tmdl: str) -> list[tuple[str, str]]:
    """Return ``(name, block_text)`` for every measure in *tmdl*.

    Each block spans from the ``measure`` keyword to just before the next
    measure declaration.  Use :func:`_measures_without_description` for the
    description check, which requires a look-behind across block boundaries.
    """
    parts = _MEASURE_BLOCK_RE.split(tmdl)
    blocks: list[tuple[str, str]] = []
    for part in parts:
        m = re.search(r"measure\s+'([^']+)'", part)
        if m:
            blocks.append((m.group(1), part))
    return blocks


def _measures_without_description(tmdl: str) -> list[str]:
    """Return measure names that have no preceding ``///`` comment."""
    all_names = re.findall(r"^\tmeasure\s+'([^']+)'", tmdl, re.MULTILINE)
    with_desc = set(re.findall(r"///[^\n]+\n\t+measure\s+'([^']+)'", tmdl))
    return [n for n in all_names if n not in with_desc]


# ---------------------------------------------------------------------------
# Medidas table
# ---------------------------------------------------------------------------


class TestMedidas:
    """Tests scoped to the *Medidas* measures table."""

    def test_measures_tmdl_exists(self) -> None:
        assert _MEDIDAS.exists(), f"Expected file not found: {_MEDIDAS}"

    def test_all_measures_have_description(self) -> None:
        """Every measure must have a ``///`` documentation comment."""
        text = _read(_MEDIDAS)
        blocks = _split_measure_blocks(text)
        assert blocks, "No measures found in Medidas.tmdl"
        missing = _measures_without_description(text)
        assert not missing, f"Measures missing /// description: {missing}"

    def test_all_measures_have_display_folder(self) -> None:
        """Every measure must declare a ``displayFolder`` for discoverability."""
        blocks = _split_measure_blocks(_read(_MEDIDAS))
        missing = [name for name, block in blocks if "displayFolder:" not in block]
        assert not missing, f"Measures missing displayFolder: {missing}"

    def test_all_measures_have_lineage_tag(self) -> None:
        """Every measure must have a ``lineageTag`` for change tracking."""
        blocks = _split_measure_blocks(_read(_MEDIDAS))
        missing = [name for name, block in blocks if "lineageTag:" not in block]
        assert not missing, f"Measures missing lineageTag: {missing}"

    def test_special_char_tables_are_quoted(self) -> None:
        """Table names with accented chars must be wrapped in single quotes.

        Unquoted references such as ``Logística[col]`` or ``Calendário[col]``
        cause DAX syntax errors because of the special characters.
        """
        text = _read(_MEDIDAS)
        # Match TableName[ where the character directly before the name is NOT '
        unquoted = re.findall(r"(?<!')\b(Logística|Calendário)\[", text)
        assert not unquoted, (
            f"Unquoted table references found (wrap in single quotes): {unquoted}"
        )


# ---------------------------------------------------------------------------
# Inteligência de Tempo calculation group
# ---------------------------------------------------------------------------


class TestCalculationGroup:
    """Tests for the *Inteligência de Tempo* calculation group."""

    def test_calc_group_tmdl_exists(self) -> None:
        assert _CALC_GROUP.exists(), f"Expected file not found: {_CALC_GROUP}"

    def test_table_has_lineage_tag(self) -> None:
        text = _read(_CALC_GROUP)
        assert re.search(r"^\tlineageTag:", text, re.MULTILINE), (
            "Table 'Inteligência de Tempo' is missing a top-level lineageTag"
        )

    def test_all_calc_items_have_format_string(self) -> None:
        """Every calculationItem (and noSelectionExpression) must define a format."""
        text = _read(_CALC_GROUP)
        items = re.findall(
            r"^\t\t(?:calculationItem|noSelectionExpression)", text, re.MULTILINE
        )
        format_defs = re.findall(
            r"^\t\t\tformatStringDefinition\s*=", text, re.MULTILINE
        )
        assert len(format_defs) >= len(items), (
            f"Expected at least {len(items)} formatStringDefinition entries, "
            f"found {len(format_defs)}"
        )

    def test_calendário_references_are_quoted(self) -> None:
        """'Calendário'[Data] must be quoted everywhere in the calc group."""
        text = _read(_CALC_GROUP)
        unquoted = re.findall(r"(?<!')\bCalendário\[", text)
        assert not unquoted, f"Unquoted 'Calendário' column references: {unquoted}"
