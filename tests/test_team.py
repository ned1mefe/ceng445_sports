import pytest
from team import Team
from player import Player

@pytest.fixture
def team():
    return Team(name="Fenerbahçe", year=2024, country="Turkey")


def test_constructor(team):
    assert team.info["name"] == "Fenerbahçe"
    assert team.info["year"] == 2024
    assert team.info["country"] == "Turkey"
    assert team.players == {}
    assert team.numbers == {}


def test_set_get_attr(team):
    team["stadium"] = "Ülker Arena"
    assert team.stadium == "Ülker Arena"

    del team.stadium
    assert team.info["stadium"] is None


def test_add_player(team):
    team.addplayer("Baldwin", 5)
    assert "Baldwin" in team.players
    assert 5 in team.numbers
    player = team.players["Baldwin"]
    assert isinstance(player, Player)
    assert player.team == team
    assert player.number == 5


def test_add_existing_player_raises(team):
    team.addplayer("Baldwin", 5)
    with pytest.raises(ValueError, match="Player already in team"):
        team.addplayer("Baldwin", 8)


def test_add_player_with_taken_number_raises(team):
    team.addplayer("Baldwin", 5)
    with pytest.raises(ValueError, match="Jersey number taken"):
        team.addplayer("Wilbekin", 5)


def test_del_player(team):
    team.addplayer("Baldwin", 5)
    team.delplayer("Baldwin")

    assert "Baldwin" not in team.players
    assert 5 not in team.numbers


def test_del_nonexistent_player_raises(team):
    with pytest.raises(ValueError, match="Player not in team"):
        team.delplayer("Nonexistent")
