"""Test the exact boundaries of the absolute humidity comfort scale."""

import pytest
from custom_components.absolute_humidity.sensor import assess_comfort


@pytest.mark.parametrize(
    ("absolute_humidity", "expected"),
    [
        pytest.param(0.0, "very_dry", id="zero"),
        pytest.param(4.99, "very_dry", id="below-five"),
        pytest.param(5.0, "dry", id="five"),
        pytest.param(6.99, "dry", id="below-seven"),
        pytest.param(7.0, "comfortable", id="seven"),
        pytest.param(9.99, "comfortable", id="below-ten"),
        pytest.param(10.0, "humid", id="ten"),
        pytest.param(12.0, "humid", id="twelve"),
        pytest.param(12.01, "very_humid", id="above-twelve"),
    ],
)
def test_comfort_boundaries(absolute_humidity: float, expected: str) -> None:
    """Boundary values select exactly one assessment band."""
    assert assess_comfort(absolute_humidity) == expected
