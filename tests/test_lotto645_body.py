import json

import pytest

from lotto645 import Lotto645


@pytest.fixture
def lotto() -> Lotto645:
    return Lotto645()


@pytest.fixture
def requirements() -> list:
    # [direct, draw_date, tlmt_date, current_round]
    return ["1.2.3.4", "2026-04-18", "2027-04-18", "1167"]


def test_auto_body_sets_round_and_amount(lotto, requirements):
    body = lotto._generate_body_for_auto_mode(3, requirements)

    assert body["round"] == "1167"
    assert body["direct"] == "1.2.3.4"
    assert body["nBuyAmount"] == "3000"
    assert body["gameCnt"] == 3
    assert body["saleMdaDcd"] == "10"
    assert body["ROUND_DRAW_DATE"] == "2026-04-18"
    assert body["WAMT_PAY_TLMT_END_DT"] == "2027-04-18"


def test_auto_body_param_slots_match_count(lotto, requirements):
    body = lotto._generate_body_for_auto_mode(2, requirements)

    param = json.loads(body["param"])
    assert [slot["alpabet"] for slot in param] == ["A", "B"]
    assert all(slot["genType"] == "0" for slot in param)
    assert all(slot["arrGameChoiceNum"] is None for slot in param)


def test_auto_body_max_five_games(lotto, requirements):
    body = lotto._generate_body_for_auto_mode(5, requirements)

    assert body["nBuyAmount"] == "5000"
    param = json.loads(body["param"])
    assert len(param) == 5
    assert [slot["alpabet"] for slot in param] == ["A", "B", "C", "D", "E"]


@pytest.mark.parametrize("invalid_count", [0, 6, 10, -1])
def test_auto_body_rejects_out_of_range_count(lotto, requirements, invalid_count):
    with pytest.raises(AssertionError):
        lotto._generate_body_for_auto_mode(invalid_count, requirements)
