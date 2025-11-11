from player import Player

class Team():
    def __init__(self, name = None, year = None, country = None):
        self.info = {
            "name": name,
            "year": year,
            "country": country
        }
        self.numbers = {} # given jersey numbers to players
        self.players = {} # player name to player object
    
    def __setitem__(self, key, value):
        self.info[key] = value
    def __getattr__(self, key):
        return self.info[key]
    def __delattr__(self, key):
        self.info[key] = None

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

