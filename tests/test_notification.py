import pytest
from catalog import Catalog
from models.game import Game
from models.cup import Cup
from models.team import Team
from datetime import datetime, timedelta

class MockUser:
    def __init__(self, name):
        self.name = name
        self.notifications = []

    def update(self, event):
        self.notifications.append(event)

    def clear_notifications(self):
        self.notifications = []

    def has_received(self, event_type, **kwargs):
        """
        Check if an event of event_type was received.
        Optional kwargs match keys in the event dictionary.
        """
        for event in self.notifications:
            if event['type'] == event_type:
                # Check if all provided kwargs match the event data
                match = True
                for key, val in kwargs.items():
                    if key not in event or event[key] != val:
                        match = False
                        break
                if match:
                    return True
        return False

@pytest.fixture
def catalog():
    return Catalog()

@pytest.fixture
def user():
    return MockUser("TestUser")

@pytest.fixture
def teams(catalog):
    t1_id = catalog.create(type="team", name="Team A", year=2023, country="TR")
    t2_id = catalog.create(type="team", name="Team B", year=2023, country="TR")
    return t1_id, t2_id

@pytest.fixture
def teams_list(catalog):
    teams = []
    for i in range(8):
        tid = catalog.create(type="team", name=f"Team_{i}", year=2023, country="TestLand")
        teams.append(catalog.objectDict[tid])
    return teams

def test_attach_game_notifications(catalog, user, teams):
    t1_id, t2_id = teams
    
    game_id = catalog.create(type="game", home=t1_id, away=t2_id, datetime="2023-01-01")
    
    catalog.attach(game_id, user)
    
    game = catalog.objectDict[game_id]
    
    game.start()
    
    assert user.has_received("game_started")
    assert user.notifications[-1]['game'].id() == game_id

    t1 = catalog.objectDict[t1_id]
    game.score(2, t1)

    assert user.has_received("score")
    assert user.notifications[-1]['points'] == 2

def test_attach_team_notifications(catalog, user, teams):
    t1_id, t2_id = teams
    

    catalog.attach(t1_id, user)

    game_id = catalog.create(type="game", home=t1_id, away=t2_id, datetime= datetime.now())
    
    game = catalog.objectDict[game_id]
    
    game.start()

    assert user.has_received("game_started")

def test_detach_stops_notifications(catalog, user, teams):
    t1_id, t2_id = teams
    game_id = catalog.create(type="game", home=t1_id, away=t2_id, datetime="2023-01-01")
    
    catalog.attach(game_id, user)
    game = catalog.objectDict[game_id]
    
    game.start()
    assert user.has_received("game_started")
    
    user.clear_notifications()
    catalog.detach(game_id, user)
    
    game.end()
    
    assert not user.has_received("game_ended")

def test_elimination_cup_game_started_notification(catalog, user, teams_list):
    
    cup_id = catalog.create(
        type="cup", 
        cup_type="ELIMINATION", 
        teams=[t.id() for t in teams_list], 
        interval= timedelta(days=1)
    )
    cup = catalog.objectDict[cup_id]

    cup.watch(user)

    games = list(cup._games.values())
    assert len(games) > 0, "Cup should have scheduled games"
    
    target_game = games[0]

    target_game.start()

    assert user.has_received("game_started", game=target_game)


def test_elimination_cup_score_notification(catalog, user, teams_list):
    """
    Test that a user watching an EliminationCup gets 'score' 
    notifications when points are scored in a match.
    """
    cup_id = catalog.create(
        type="cup", 
        cup_type="ELIMINATION", 
        teams=[t.id() for t in teams_list], 
        interval= timedelta(days=1)
    )
    cup = catalog.objectDict[cup_id]
    cup.watch(user)

    target_game = list(cup._games.values())[0]
    target_game.start() # Must start to run typically, though score() doesn't strictly check is_running in some implementations
    
    # Action: Score points
    home_team = target_game.home()
    target_game.score(3, home_team)

    # Assert: User received 'score'
    assert user.has_received("score", game=target_game, team=home_team, points=3)


def test_league_cup_notifications(catalog, user, teams_list):
    """
    Test that LeagueCup (Round Robin) correctly propagates game events.
    """
    # Reduce teams for League to avoid too many games in test
    small_team_list = teams_list[:4] 
    
    cup_id = catalog.create(
        type="cup", 
        cup_type="LEAGUE", 
        teams=[t.id() for t in small_team_list], 
        interval= timedelta(days=1)
    )
    cup = catalog.objectDict[cup_id]
    
    # Attach User
    cup.watch(user)
    
    # League initializes ALL games at start
    games = list(cup._games.values())
    target_game = games[0]
    
    # Action 1: Start Game
    target_game.start()
    assert user.has_received("game_started", game=target_game)
    
    # Action 2: Score
    away_team = target_game.away()
    target_game.score(2, away_team)
    assert user.has_received("score", game=target_game, points=2)
    
    # Action 3: End Game (Should trigger Cup update logic too, but we check user notif)
    target_game.end()
    assert user.has_received("game_ended", game=target_game)


def test_group_cup_propagation(catalog, user, teams_list):
    """
    Test GroupCup. This is tricky because GroupCup contains sub-cups (LeagueCups).
    Standard Cup.watch might not descend into sub-cups depending on implementation.
    """
    # GroupCup requires enough teams (at least groupCount * 2 = 8 usually)
    cup_id = catalog.create(
        type="cup", 
        cup_type="GROUP", 
        teams=[t.id() for t in teams_list], 
        interval= timedelta(days=1)
    )
    group_cup = catalog.objectDict[cup_id]
    
    # Attach user to the main GroupCup
    group_cup.watch(user)
    
    # We need to find a game inside one of the groups.
    # GroupCup structure: group_cup._groups['A'] -> LeagueCup -> _games
    first_group = list(group_cup._groups.values())[0]
    first_game = list(first_group._games.values())[0]
    
    # Note: If GroupCup.watch() does NOT propagate the observer to the sub-cups' games,
    # this test will fail, revealing a need to update GroupCup.watch or how games are stored.
    
    # Action: Start a game deep inside a group
    first_game.start()
    
    # Assert
    # If this fails, it means GroupCup isn't linking the User to the inner games.
    assert user.has_received("game_started", game=first_game)