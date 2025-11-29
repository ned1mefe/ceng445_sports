from datetime import datetime, timedelta
import pickle
import queue
import shlex
import threading

class Session(threading.Thread):
    def __init__(self, sock, addr,catalog,catalog_lock,datafile):
        super().__init__()
        self.sock = sock
        self.addr = addr
        self.username = "Guest"
        self.running = True

        self.catalog = catalog
        self.catalog_lock = catalog_lock
        self.DATA_FILE = datafile
        
        self.msg_queue = queue.Queue()

    def run(self):
        agent = threading.Thread(target=self.notification_agent)
        agent.daemon = True
        agent.start()

        self.send_message(f"Welcome to the Tournament Server, {self.username}!")

        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_command(line.strip())

            except ConnectionResetError:
                break
            except Exception as e:
                print(f"Error: {e}")
                break
            
            
        self.cleanup()

    def notification_agent(self):
        while self.running:
            try:
                msg = self.msg_queue.get(timeout=1) 
                try:
                    self.sock.sendall((f"[UPDATE] {msg}\n").encode('utf-8'))
                except OSError:
                    break
            except queue.Empty:
                continue 

    def update(self, event):
        if event['type'] == 'score':
            msg = f"GOAL! {event['team']} scored {event['points']} points!"
        elif event['type'] == 'game_ended':
            msg = f"Game Over: {event['game'].description()}"
        else:
            msg = str(event)
            
        self.msg_queue.put(msg)

    def handle_command(self, cmd_str):
        if not cmd_str: return
        
        try:
            parts = shlex.split(cmd_str)
            cmd = parts[0].upper()
            args = parts[1:]
        except:
            self.send_message("ERROR: Invalid command format")
            return

        with self.catalog_lock: 
            try:
                response = "OK"
                
                if cmd == "USER":
                    self.username = args[0]
                    response = f"Hello {self.username}"
                
                elif cmd == "CREATE_TEAM":
                    # Usage: CREATE_TEAM <Name> <Year> <Country>
                    tid = self.catalog.create(type="team", name=args[0], year=args[1], country=args[2])
                    response = f"Team Created. ID: {tid}"

                # Usage: CREATE_GAME <HomeID> <AwayID> "YYYY-MM-DD HH:MM"
                elif cmd == "CREATE_GAME":
                    if len(args) < 3: raise ValueError("Usage: CREATE_GAME <home_id> <away_id> <datetime>")
                    home_id = args[0]
                    away_id = args[1]
                    dt_str = args[2]

                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                    
                    gid = self.catalog.create(type="game", home=home_id, away=away_id, datetime=dt)
                    response = f"Game Created. ID: {gid}"

                # --- CREATE CUP ---
                # Usage: CREATE_CUP <Type> <Interval_Minutes> <TeamID1> <TeamID2> ...
                # Types: LEAGUE, LEAGUE2, ELIMINATION, ELIMINATION2, GROUP, GROUP2
                elif cmd == "CREATE_CUP":
                    if len(args) < 3: raise ValueError("Usage: CREATE_CUP <type> <days> <team_ids...>")
                    cup_type = args[0].upper()
                    
                    interval = timedelta(days=int(args[1]))
                    
                    team_ids = args[2:]
                    
                    cid = self.catalog.create(type="cup", cup_type=cup_type, interval=interval, teams=team_ids)
                    response = f"{cup_type} Created. ID: {cid}"

                elif cmd == "LIST":
                    items = self.catalog.list() # List of (id, desc)
                    response = "\n".join([f"{i[0]}: {i[1]}" for i in items])

                elif cmd == "WATCH":
                    # watch <id>
                    obj_id = args[0]
                    self.catalog.attach(obj_id, self) # session is the observer
                    response = f"Watching {obj_id}"

                elif cmd == "START":
                    # start <game_id>
                    game = self.catalog.objectDict[args[0]]
                    game.start()
                    response = "Game Started"

                elif cmd == "SCORE":
                    # score <game_id> <points> <team_id> <playername>
                    game = self.catalog.objectDict[args[0]]
                    pts = int(args[1])
                    team = self.catalog.objectDict[args[2]]
                    player = args[3] if len(args) > 3 else None

                    game.score(pts,team,player)
                    response = "Score updated"

                elif cmd == "SAVE":
                    self.save_state()
                    response = "State saved."

                else:
                    response = "UNKNOWN COMMAND"

                self.send_message(response)

            except Exception as e:
                self.send_message(f"ERROR: {str(e)}")

    def send_message(self, msg):
        try:
            self.sock.sendall((msg + "\n").encode('utf-8'))
        except:
            self.running = False

    def cleanup(self):
        print(f"Disconnecting {self.addr}")
        self.running = False
        self.sock.close()
        with self.catalog_lock:
            self.catalog.detachAll(self)
    
    def save_state(self):
        with open(self.DATA_FILE, 'wb') as f:
            pickle.dump(self.catalog, f)