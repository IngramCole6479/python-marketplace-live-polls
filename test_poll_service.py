from poll_service import PollChoice, winning_choice


def test_winning_choice_returns_highest_vote_and_keeps_tie_order():
    choices = [PollChoice("red", 3), PollChoice("blue", 5), PollChoice("green", 5)]
    assert winning_choice(choices) == PollChoice("blue", 5)
