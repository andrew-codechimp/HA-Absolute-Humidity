"""Test the boundaries of the absolute humidity condensation risk scale."""

import pytest
from custom_components.absolute_humidity.sensor import assess_condensation_risk


@pytest.mark.parametrize(
    ("absolute_humidity", "expected"),
    [
        pytest.param(0.0, "low", id="zero"),
        pytest.param(7.0, "low", id="seven"),
        pytest.param(8.6, "low", id="eight-point-six"),
        pytest.param(10.399, "low", id="below-ten-point-four"),
        pytest.param(10.4, "moderate", id="ten-point-four"),
        pytest.param(12.099, "moderate", id="below-twelve-point-one"),
        pytest.param(12.1, "high", id="twelve-point-one"),
        pytest.param(15.0, "high", id="above-twelve-point-one"),
    ],
)
def test_condensation_risk_boundaries(absolute_humidity: float, expected: str) -> None:
    """Each boundary value selects the requested risk band."""
    assert assess_condensation_risk(absolute_humidity) == expected
