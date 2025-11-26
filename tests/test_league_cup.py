import pytest
from datetime import datetime
from models.team import Team
from models.cup_types.league_cup import LeagueCup


class DummyObserver:
    def __init__(self):
        self.events = []
    def update(self, event):
        self.events.append(event)


@pytest.fixture
def sample_teams():
    teams = [Team(f"Team{i}") for i in range(1, 5)]
    for t in teams:
        t.addplayer(f"Player{t.name}_A", 1)
        t.addplayer(f"Player{t.name}_B", 2)
    return teams


@pytest.fixture
def sample_interval():
    return (datetime.timedelta(days=1))


def test_leaguecup_initialization(sample_teams, sample_interval):
    cup = LeagueCup(sample_teams, sample_interval)
    assert len(cup._teams) == 4
    assert isinstance(cup._table, dict)
    assert all(isinstance(v, dict) for v in cup._table.values())
    assert cup._rematch_enabled is False
    assert all(stat["Points"] == 0 for stat in cup._table.values())


def test_leaguecup_initialize_games_creates_unique_pairs(sample_teams, sample_interval):
    cup = LeagueCup(sample_teams, sample_interval)
    cup.initialize_games()

    pairs = {(g.home().name, g.away().name) for g in cup._games.values()}
    assert len(pairs) == len(cup._games)
    assert all(t in [tm.name for tm in sample_teams] for pair in pairs for t in pair)


def test_leaguecup_update_and_table_points(sample_teams, sample_interval):
    obs = DummyObserver()
    cup = LeagueCup(sample_teams, sample_interval)
    cup.watch(obs)
    cup.initialize_games()

    for game in cup._games.values():
        game.score(3, game.home(), list(game.home().players.keys())[0])
        game.score(1, game.away(), list(game.away().players.keys())[0])
        game.end()

    standings = cup.standings()
    winner_name, winner_stats = standings[0]
    assert winner_stats["Points"] >= 2
    assert any(e["type"] == "cup_ended" for e in obs.events)
    assert all(game.is_ended for game in cup._games.values())


def test_leaguecup_draw_case(sample_teams, sample_interval):
    cup = LeagueCup(sample_teams, sample_interval)
    cup.initialize_games()

    for game in cup._games.values():
        game.score(2, game.home(), list(game.home().players.keys())[0])
        game.score(2, game.away(), list(game.away().players.keys())[0])
        game.end()

    standings = cup.standings()
    first_points = standings[0][1]["Points"]
    assert all(stats["Points"] == first_points for _, stats in standings)
    assert all(stats["Draw"] > 0 for _, stats in standings)


def test_leaguecup_rematch_enabled_creates_double_games(sample_teams, sample_interval):
    cup = LeagueCup(sample_teams, sample_interval, rematch_enabled=True)
    cup.initialize_games()
    
    unique_pairs = {frozenset([g.home().name, g.away().name]) for g in cup._games.values()}
        
    assert len(cup._games) == len(unique_pairs) * 2


def test_leaguecup_score_based_sorting(sample_teams, sample_interval):
    cup = LeagueCup(sample_teams, sample_interval)
    table = cup._table

    table["Team1"]["Points"] = 6
    table["Team2"]["Points"] = 4
    table["Team3"]["Points"] = 4
    table["Team3"]["Diff"] = 5  
    table["Team4"]["Points"] = 2

    sorted_list = cup.score_based_sorting()
    names_in_order = [name for name, _ in sorted_list]
    assert names_in_order == ["Team1", "Team3", "Team2", "Team4"]


def test_leaguecup_str_variants(sample_teams, sample_interval):
    cup1 = LeagueCup(sample_teams, sample_interval)
    assert str(cup1) == "LeagueCup"

    cup2 = LeagueCup(sample_teams, sample_interval, rematch_enabled=True)
    assert str(cup2) == "League2Cup"

    cup2._groupName = "A"
    assert str(cup2) == "Group :A"
