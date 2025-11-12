import pytest
import datetime
from models.cup import Cup
from models.team import Team
from models.game import Game


class DummyObserver:
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


@pytest.fixture
def sample_teams():
    teams = [Team(f"Team{i}") for i in range(1, 5)]
    for t in teams:
        t.addplayer(f"Player{t.name}_A",1)
        t.addplayer(f"Player{t.name}_B",2)
    return teams


@pytest.fixture
def sample_interval():
    return [datetime.datetime(2025, 1, 1), datetime.datetime(2025, 12, 31)]



def test_cup_create_game_and_access(sample_teams, sample_interval):
    cup = Cup(sample_teams, sample_interval)
    game = cup._create_game(sample_teams[0], sample_teams[1], sample_interval[0])

    # game should be stored by ID and retrievable
    assert cup[game.id()] is game
    assert isinstance(game, Game)


def test_cup_getitem_invalid(sample_teams, sample_interval):
    cup = Cup(sample_teams, sample_interval)
    with pytest.raises(KeyError):
        _ = cup["nonexistent-id"]


def test_cup_watch_and_unwatch(sample_teams, sample_interval):
    cup = Cup(sample_teams, sample_interval)
    observer = DummyObserver()

    cup.watch(observer)
    assert observer in cup.observers

    cup.unwatch(observer)
    assert observer not in cup.observers


def test_cup_notify_triggers_observer(sample_teams, sample_interval):
    cup = Cup(sample_teams, sample_interval)
    observer = DummyObserver()
    cup.watch(observer)

    event = {"type": "test_event"}
    cup._notify(event)

    assert event in observer.events


def test_cup_search_by_team_name(sample_teams, sample_interval):
    cup = Cup(sample_teams, sample_interval)
    g1 = cup._create_game(sample_teams[0], sample_teams[1], sample_interval[0])
    g2 = cup._create_game(sample_teams[2], sample_teams[3], sample_interval[0])

    result = cup.search(tname="Team1")
    assert g1 in result
    assert g2 not in result


def test_search_between_filter(sample_teams, sample_interval):
    cup = Cup(sample_teams, sample_interval)

    past_date = datetime.datetime(2024, 6, 15)
    old_game = cup._create_game(sample_teams[0], sample_teams[1], past_date)

    valid_date = datetime.datetime(2025, 6, 15)
    valid_game = cup._create_game(sample_teams[2], sample_teams[3], valid_date)

    result = cup.search(between=sample_interval)

    assert valid_game in result
    assert old_game not in result


