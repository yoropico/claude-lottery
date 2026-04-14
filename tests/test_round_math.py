import datetime

import pytest

from lotto645 import compute_next_round


@pytest.mark.parametrize(
    "today, expected",
    [
        # Anchor: 2024-12-28 (Sat) = round 1152
        (datetime.datetime(2024, 12, 28), 1152),
        # Sunday after anchor -> next Saturday is 1153
        (datetime.datetime(2024, 12, 29), 1153),
        # Monday of anchor week -> upcoming Sat is still 1152
        (datetime.datetime(2024, 12, 23), 1152),
        # One year later (52 weeks)
        (datetime.datetime(2025, 12, 27), 1152 + 52),
    ],
)
def test_compute_next_round(today, expected):
    assert compute_next_round(today) == expected


def test_compute_next_round_friday_before_draw():
    # Friday 2025-01-03 -> Saturday 2025-01-04 is 1 week after anchor
    assert compute_next_round(datetime.datetime(2025, 1, 3)) == 1153
