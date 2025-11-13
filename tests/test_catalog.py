import pytest
import datetime
from catalog import Catalog
from models.team import Team
from models.game import Game
from models.cup_types.league_cup import LeagueCup


@pytest.fixture
def sample_catalog():
    return Catalog()


@pytest.fixture
def sample_team_ids(sample_catalog):
    t1 = sample_catalog.create(type='team', name='Team1', year=2020, country='TR')
    t2 = sample_catalog.create(type='team', name='Team2', year=2021, country='US')
    return [t1, t2]


@pytest.fixture
def sample_interval():
    return [datetime.datetime(2025, 1, 1), datetime.datetime(2025, 12, 31)]


class DummyUser:
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


def test_user_receives_notifications_from_attached_objects(sample_catalog, sample_team_ids, sample_interval):
    user = DummyUser()

    cup_id = sample_catalog.create(
        type='cup',
        teams=sample_team_ids,
        cup_type='LEAGUE',
        interval=sample_interval
    )
    cup = sample_catalog.objectDict[cup_id]

    sample_catalog.attach(cup_id, user)

    dummy_event = {"type": "test_event", "msg": "Cup update!"}
    cup._notify(dummy_event)

    assert len(user.events) == 1
    assert user.events[0]["type"] == "test_event"
    assert "Cup update" in user.events[0]["msg"]



def test_create_team_adds_to_objectdict(sample_catalog):
    team_id = sample_catalog.create(type='team', name='X', year=2022, country='UK')
    assert team_id in sample_catalog.objectDict
    team = sample_catalog.objectDict[team_id]
    assert isinstance(team, Team)
    assert team.name == 'X'


def test_create_game_resolves_teams(sample_catalog, sample_team_ids):
    dt = datetime.datetime(2025, 6, 1)
    game_id = sample_catalog.create(type='game', home=sample_team_ids[0], away=sample_team_ids[1], datetime=dt)
    assert game_id in sample_catalog.objectDict
    game = sample_catalog.objectDict[game_id]
    assert isinstance(game, Game)
    assert game.home().name == 'Team1'
    assert game.away().name == 'Team2'


def test_create_cup_creates_and_initializes_games(sample_catalog, sample_team_ids, sample_interval):
    cup_id = sample_catalog.create(
        type='cup',
        teams=sample_team_ids,
        cup_type='LEAGUE',
        interval=sample_interval
    )
    cup = sample_catalog.objectDict[cup_id]
    assert isinstance(cup, LeagueCup)
    assert hasattr(cup, "_games")
    assert len(cup._games) > 0


def test_attach_and_detach_user(sample_catalog, sample_team_ids):
    user = "test_user"
    team_id = sample_team_ids[0]
    sample_catalog.attach(team_id, user)
    assert user in sample_catalog.attachDict
    assert team_id in sample_catalog.attachDict[user]
    sample_catalog.detach(team_id, user)
    assert team_id not in sample_catalog.attachDict[user]


def test_delete_unattached_object(sample_catalog, sample_team_ids):
    team_id = sample_team_ids[0]
    sample_catalog.delete(team_id)
    assert team_id not in sample_catalog.objectDict


def test_delete_attached_object_raises_error(sample_catalog, sample_team_ids):
    user = "userX"
    team_id = sample_team_ids[0]
    sample_catalog.attach(team_id, user)
    with pytest.raises(ValueError):
        sample_catalog.delete(team_id)


def test_update_adds_new_game_and_group(sample_catalog, sample_team_ids):
    t1, t2 = [sample_catalog.objectDict[i] for i in sample_team_ids]
    g = Game(t1, t2, datetime.datetime(2025, 5, 1))
    sample_catalog.update({"type": "new_game", "game": g})
    assert g.id() in sample_catalog.objectDict

    class DummyGroup:
        def __init__(self):
            self._id = "g123"
        def id(self):
            return self._id
    grp = DummyGroup()
    sample_catalog.update({"type": "new_group", "group": grp})
    assert grp.id() in sample_catalog.objectDict
