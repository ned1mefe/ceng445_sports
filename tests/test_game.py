import pytest
from models.game import Game

class DummyTeam:
    def __init__(self, name, players=None):
        self.name = name
        self.players = players or {}

class DummyObserver:
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


@pytest.fixture
def basic_game():
    home = DummyTeam("TeamA", players={"Alice": 0, "Bob": 0})
    away = DummyTeam("TeamB", players={"Carol": 0, "Dave": 0})
    return Game(home, away, "2025-01-01 20:00")


def test_initialization_sets_correct_fields(basic_game):
    assert basic_game.home().name == "TeamA"
    assert basic_game.away().name == "TeamB"
    assert not basic_game.is_running
    assert not basic_game.is_ended
    assert isinstance(basic_game.id(), str)
    assert basic_game._stats["Home"]["score"] == 0
    assert basic_game._stats["Away"]["score"] == 0


def test_start_pause_resume_end_sequence(basic_game):
    obs = DummyObserver()
    basic_game.watch(obs)

    basic_game.start()
    assert basic_game.is_running
    assert not basic_game.is_ended
    assert obs.events[-1]["type"] == "game_started"

    basic_game.pause()
    assert not basic_game.is_running
    assert obs.events[-1]["type"] == "game_paused"

    basic_game.resume()
    assert basic_game.is_running
    assert obs.events[-1]["type"] == "game_resumed"

    basic_game.end()
    assert not basic_game.is_running
    assert basic_game.is_ended
    assert obs.events[-1]["type"] == "game_ended"


def test_cannot_start_twice_or_after_end(basic_game):
    basic_game.start()
    with pytest.raises(ValueError):
        basic_game.start()
    basic_game.end()
    with pytest.raises(ValueError):
        basic_game.start()


def test_pause_without_running_fails(basic_game):
    with pytest.raises(ValueError):
        basic_game.pause()


def test_resume_after_end_fails(basic_game):
    basic_game.end()
    with pytest.raises(ValueError):
        basic_game.resume()


def test_score_updates_stats_and_timeline(basic_game):
    basic_game.start()
    home = basic_game.home()
    away = basic_game.away()

    basic_game.score(2, home, "Alice")
    assert basic_game._stats["Home"]["score"] == 2
    assert basic_game._stats["Home"]["Alice"] == 2
    assert basic_game.timeline[-1][2] == "Alice"

    basic_game.score(3, away, "Carol")
    assert basic_game._stats["Away"]["score"] == 3
    assert basic_game._stats["Away"]["Carol"] == 3
    assert len(basic_game.timeline) == 2


def test_score_with_invalid_team_or_player_raises(basic_game):
    rogue_team = DummyTeam("Intruder", players={"Hacker": 0})
    home = basic_game.home()
    basic_game.start()

    with pytest.raises(ValueError):
        basic_game.score(1, rogue_team, "Hacker")

    with pytest.raises(ValueError):
        basic_game.score(1, home, "Nonexistent")


def test_observer_notification_on_score(basic_game):
    obs = DummyObserver()
    basic_game.watch(obs)
    basic_game.start()

    basic_game.score(1, basic_game.home(), "Alice")

    last_event = obs.events[-1]
    assert last_event["type"] == "score"
    assert last_event["points"] == 1
    assert last_event["team"].name == "TeamA"
    assert last_event["player"] == "Alice"


def test_watch_and_unwatch_behavior(basic_game):
    obs = DummyObserver()
    basic_game.watch(obs)
    assert obs in basic_game.observers

    basic_game.unwatch(obs)
    assert obs not in basic_game.observers

    # Removing twice shouldn't raise
    basic_game.unwatch(obs)


def test_stats_structure_and_values(basic_game):
    basic_game.start()
    basic_game.score(2, basic_game.home(), "Alice")
    result = basic_game.stats()

    assert result["Home"]["Pts"] == 2
    assert result["Home"]["Players"]["Alice"] == 2
    assert result["Away"]["Pts"] == 0
    assert isinstance(result["Timeline"], list)

    basic_game.end()
    result_after = basic_game.stats()
    assert result_after["Time"] == "Full Time"


def test_str_and_description(basic_game):
    desc = str(basic_game)
    assert "TeamA" in desc and "TeamB" in desc
    assert basic_game.description() == desc


def test_init_with_missing_players_gracefully_handles():
    # Missing players should not raise errors
    home = DummyTeam("SoloTeam")
    away = DummyTeam("Opponent")
    game = Game(home, away, "2025-01-01 20:00")
    assert "score" in game._stats["Home"]
    assert "score" in game._stats["Away"]
