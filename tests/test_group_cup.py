from cmath import log
from math import ceil
import pytest
from datetime import datetime, timedelta
from models.cup_types.group_cup import GroupCup
from models.team import Team


class DummyObserver:
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


@pytest.fixture
def sample_teams():
    teams = [Team(f"Team{i}") for i in range(1, 9)]  # 8 teams for 4 groups
    for t in teams:
        t.addplayer(f"Player{t.name}_A", 1)
        t.addplayer(f"Player{t.name}_B", 2)
    return teams


@pytest.fixture
def sample_interval():
    return (timedelta(days=1))


def test_groupcup_initialization(sample_teams, sample_interval):
    cup = GroupCup(sample_teams, sample_interval)
    assert len(cup._groups) == 0
    assert cup._playOffs is None
    assert cup._groupCount == 4
    assert cup._playOffCount == 8


def test_groupcup_initialize_groups_creates_leaguecups(sample_teams, sample_interval):
    cup = GroupCup(sample_teams, sample_interval)
    cup.initialize_groups()
    assert len(cup._groups) == 4
    assert all(hasattr(g, "initialize_games") for g in cup._groups.values())

    assigned = [team for g in cup._groups.values() for team in g._teams]
    assert sorted(t.name for t in assigned) == sorted(t.name for t in sample_teams)


def test_groupcup_standings_include_all_groups(sample_teams, sample_interval):
    cup = GroupCup(sample_teams, sample_interval)
    cup.initialize_groups()
    standings = cup.standings()
    assert len(standings) == 4  # Groups A-D
    for name in ["Group A", "Group B", "Group C", "Group D"]:
        assert name in standings


def test_groupcup_playoffs_trigger_after_all_groups_end(sample_teams, sample_interval):
    cup = GroupCup(sample_teams, sample_interval)
    cup.initialize_groups()

    # Simulate all group games ending
    for group_cup in cup._groups.values():
        for game in group_cup._games.values():
            game.score(3, game.home(), list(game.home().players.keys())[0])
            game.score(1, game.away(), list(game.away().players.keys())[0])
            game.end()

    assert cup._playOffs is not None
    assert isinstance(cup._playOffs._teams, list)
    assert len(cup._playOffs._teams) == cup._playOffCount


def test_groupcup_observer_notifications(sample_teams, sample_interval):
    obs = DummyObserver()
    cup = GroupCup(sample_teams, sample_interval)
    cup.watch(obs)
    cup.initialize_groups()

    for group_cup in cup._groups.values():
        for game in group_cup._games.values():
            game.score(2, game.home(), list(game.home().players.keys())[0])
            game.score(1, game.away(), list(game.away().players.keys())[0])
            game.end()

    if cup._playOffs:
        for _ in range(ceil(log(cup._playOffCount, 2).real)): 
            for game in list(game for game in cup._playOffs._games.values() if not game.is_ended):
                game.score(3, game.home(), list(game.home().players.keys())[0])
                game.score(2, game.away(), list(game.away().players.keys())[0])
                game.end()
    assert obs.events and obs.events[-1]["type"] == "cup_ended"


def test_groupcup_playoff_selection_logic(sample_teams, sample_interval):
    cup = GroupCup(sample_teams, sample_interval)
    cup.initialize_groups()

    for group in cup._groups.values():
        fake_standings = [(t.name, {"Points": i}) for i, t in enumerate(group._teams, start=1)]
        group.standings = lambda s=fake_standings: s 
        group._teams = list(group._teams)

    cup._initialize_playoffs()

    assert cup._playOffs is not None
    assert len(cup._playOffs._teams) == cup._playOffCount
    assert all(isinstance(t, Team) for t in cup._playOffs._teams)


def test_groupcup_description_and_str(sample_teams, sample_interval):
    cup = GroupCup(sample_teams, sample_interval)
    assert str(cup) == "GroupCup"

    cup2 = GroupCup(sample_teams, sample_interval, rematch_enabled=True)
    assert str(cup2) == "Group2Cup"
