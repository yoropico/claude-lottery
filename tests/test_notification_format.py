from notification import Notification


def test_make_lotto_number_message_strips_suffix_and_pipes():
    notify = Notification()
    raw = [
        "A|01|02|03|04|05|06|1",
        "B|07|08|09|10|11|12|2",
    ]

    # Current behavior: drops the last char (genType digit), then replaces
    # pipes with spaces, which leaves a trailing space on each line.
    result = notify.make_lotto_number_message(raw)

    assert result == "A 01 02 03 04 05 06 \nB 07 08 09 10 11 12 "


def test_make_win720_number_message_splits_group_digit():
    notify = Notification()
    raw_ticket = "312345,467890"

    result = notify.make_win720_number_message(raw_ticket)

    assert result == "3조 1 2 3 4 5\n4조 6 7 8 9 0"


def test_make_lotto_number_message_handles_single_row():
    notify = Notification()
    raw = ["A|01|02|03|04|05|06|1"]

    assert notify.make_lotto_number_message(raw) == "A 01 02 03 04 05 06 "
