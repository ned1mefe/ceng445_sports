# 1. Implementation - Correction (55 points):
    # A. General Mehods (20 points)
    # * create(**kw) - 3
    # * list() - 2
    # * listattached(user) - 2
    # * attach(id, user) - 2
    # * detach(id, user) - 2
    # * delete(id) - 4
    # * observer notifications work correctly - 5

    # B. General CRUD (10 points)
    # - For each class:
    #     * Constructor - 5
    #     * delete() - 5

    # * Team Class (2 points)
    #     * __setitem__(key, value), __getattr__(key), __delattr__(key) - 1
    #     * addplayer(name, no), delplayer(name) - 1
    # * Game Class (8 points)
    #     * id(), home(), away() properties - 1
    #     * start(), pause(), resume(), end() - 1
    #     * score(points, team, player) - 1
    #     * stats() - 5
    # * Cup Class (9 points)
    #     * search(tname, group, between) - 4
    #     * __getitem__(gameid) - 1
    #     * gametree() - 1
    #     * standing() - 3
    # * each individual game type logics were implemented correctly - (6 points)


# 2.Unit Tests (20 points)
    # * Write tests that cover all implemented methods and edge cases.

# 3. Individual Understanding (25 points)
    # * You are expected to explain your code during your grading session.
    # * If you cannot adequately explain your work, even if your code functions correctly, 
    # your score for this component will be capped at 40% of the points (i.e., 10 points max).

def Singleton(cls,*p,**kw):
	'''generic python decorator to make any class
	singleton.'''
	_instances = {}	  # keep classname vs. instance
	def getinstance(*p,**kw):
		'''if cls is not in _instances create it
		and store. return the stored instance'''
		print(_instances)
		if cls not in _instances:
			_instances[cls] = cls(*p,**kw)
		return _instances[cls]
	return getinstance



class Team():
    def __init__(self, name = None, year = None, country = None):
        self.attributes = {
            "name": name,
            "year": year,
            "country": country
        }
        self.numbers = {} # given jersey numbers to players
        self.players = {} # player name to player object
    
    def __setitem__(self, key, value):
        self.attributes[key] = value
    def __getattr__(self, key):
        return self.attributes[key]
    def __delattr__(self, key):
        self.attributes[key] = None

    def addplayer(self, pname, pno):
        if pname in self.players:
            raise ValueError("Player already in team")
        if pno in self.numbers:
            raise ValueError("Jersey number taken")
        
        player = Player(pname)
        player.team = self
        player.number = pno

        self.numbers[pno] = player
        self.players[pname] = player

    def delplayer(self, name):
        if name in self.players:
            player = self.players[name]

            del self.numbers[player.number]
            del self.players[name]
            
            player.team = None
            player.number = None
        
        else:
            raise ValueError("Player not in team")


class Player():
    def __init__(self, name):
        self.name = name
        self.team = None
        self.number = None



Spurs = Team()
Rockets = Team("Houston Rockets", 1967, "USA")
print(Spurs.attributes)
print(Rockets.attributes)

Spurs["name"] = "San Antonio Spurs"
Spurs["year"] = 1967
Spurs["country"] = "USA"
print(Spurs.attributes)


