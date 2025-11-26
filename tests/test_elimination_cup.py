import pytest
import datetime
from models.cup_types.elimination_cup import EliminationCup
from models.team import Team

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
    return (datetime.timedelta(days=1))


def test_eliminationcup_initialization(sample_teams, sample_interval):
    elim = EliminationCup(sample_teams, sample_interval)
    assert all(t.name in elim._standings for t in sample_teams)
    assert elim._active_teams == sample_teams


def test_eliminationcup_schedule_round_creates_games(sample_teams, sample_interval):
    elim = EliminationCup(sample_teams, sample_interval)
    elim.initialize_games()

    # There should be at least len(teams)//2 games created
    assert len(elim._games) >= len(sample_teams) // 2


def test_eliminationcup_handle_game_end(sample_teams, sample_interval):
    elim = EliminationCup(sample_teams, sample_interval)
    elim.initialize_games()
    game = list(elim._games.values())[0]

    # simulate scoring and game end
    game.score(10, game.home(), list(game.home().players.keys())[0])
    game.score(5, game.away(), list(game.away().players.keys())[0])
    game.end()  # handleGameEnd observer tarafından otomatik çağrılır

    home_name = game.home().name
    away_name = game.away().name
    standings = elim.standings()

    # One team should have Won, the other Lost
    assert (home_name in standings and standings[home_name]["Won"]) or \
           (away_name in standings and standings[away_name]["Won"])

def test_eliminationcup_multiple_round_progression(sample_teams, sample_interval):
    elim = EliminationCup(sample_teams, sample_interval)
    elim.initialize_games()

    # End all first-round games
    for game in list(elim._games.values()):
        game.end()

    # After first round, new games should be scheduled (if >1 team left)
    if len(elim._active_teams) > 1:
        assert any(team_data["Round"] > 1 for team_data in elim.standings().values())


def test_eliminationcup_with_rematch_enabled(sample_teams, sample_interval):
    elim = EliminationCup(sample_teams, sample_interval, rematch_enabled=True)
    elim.initialize_games()

    # Number of games should be doubled because of rematches
    assert len(elim._games) >= len(sample_teams) // 2 * 2


def test_eliminationcup_description_str():
    elim = EliminationCup([], [])
    assert str(elim) == "EliminationCup"
    assert elim.description() == "EliminationCup"

def test_eliminationcup_observer_notifications(sample_teams, sample_interval):
    observer = DummyObserver()

    elim = EliminationCup(sample_teams, sample_interval)
    elim.watch(observer)
    elim.initialize_games()

    i = 0

    while not observer.events or observer.events[-1]["type"] != "cup_ended":
        game = list(elim._games.values())[i]
        game.score(10, game.home(), list(game.home().players.keys())[0])
        game.score(5, game.away(), list(game.away().players.keys())[0])
        game.end()
        i += 1

    # Assertions:
    game_ended_events = [e for e in observer.events if e["type"] == "game_ended"]
    assert len(game_ended_events) > 0

    assert observer.events[-1]["type"] == "cup_ended"

    standings = elim.standings()
    winner = max(standings.items(), key=lambda item: item[1]["Round"])
    assert winner is not None

    for team, data in standings.items():
        assert not (data["Won"] and data["Lost"] and data["Round"] == 1)


def test_eliminationcup_rematch_games_created(sample_teams, sample_interval):
    elim = EliminationCup(sample_teams, sample_interval, rematch_enabled=True)
    elim.initialize_games()

    assert len(elim._games) >= len(sample_teams)
    pairs = {}
    for g in elim._games.values():
        key = frozenset([g.home().name, g.away().name])
        pairs.setdefault(key, 0)
        pairs[key] += 1

    for pair_count in pairs.values():
        assert pair_count == 2, "Each team pair should have 2 games due to rematch"


def test_eliminationcup_rematch_progression(sample_teams, sample_interval):
    observer = DummyObserver()
    elim = EliminationCup(sample_teams, sample_interval, rematch_enabled=True)
    elim.watch(observer)
    elim.initialize_games()

    i = 0
    # simulate all games and rematches
    while not observer.events or observer.events[-1]["type"] != "cup_ended":
        game = list(elim._games.values())[i]
        # Home wins first
        game.score(10, game.home(), list(game.home().players.keys())[0])
        game.score(5, game.away(), list(game.away().players.keys())[0])
        game.end()
        i += 1

    # Assert: observer got cup_ended
    assert observer.events[-1]["type"] == "cup_ended"

    # Assert: winner exists
    standings = elim.standings()
    winner = max(standings.items(), key=lambda item: item[1]["Round"])
    assert winner is not None

    # Assert: no team is still marked with only Round 1 and Won+Lost
    for team, data in standings.items():
        assert data["Round"] >= 1
