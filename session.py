import json
import threading
import queue
from datetime import datetime, timedelta
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

class Session:
    def __init__(self, wsock, addr, catalog, catalog_lock, datafile):
        self.wsock = wsock
        self.addr = addr
        self.username = "Guest"
        self.running = True
        self.catalog = catalog
        self.catalog_lock = catalog_lock
        self.DATA_FILE = datafile
        self.msg_queue = queue.Queue()
        
        # FIX: Track recently processed event IDs to prevent double-notifications
        # (Diamond problem: Game->Session AND Game->Catalog->Session)
        self._processed_events = [] 

        with self.catalog_lock:
            self.catalog.attach_observer(self)

    def run(self):
        notifier = threading.Thread(target=self.notification_agent)
        notifier.daemon = True
        notifier.start()
        self.send_json({"status": "success", "message": f"Connected as {self.username}"})
        try:
            while True:
                message = self.wsock.recv()
                try:
                    data = json.loads(message)
                    self.handle_command(data)
                except json.JSONDecodeError:
                    self.send_error("Invalid JSON")
        except (ConnectionClosedOK, ConnectionClosedError):
            pass
        except Exception as e:
            print(f"Session Error: {e}")
        finally:
            self.cleanup()

    def notification_agent(self):
        while self.running:
            try:
                msg = self.msg_queue.get(timeout=1) 
                self.send_json({"status": "notification", "data": msg})
            except queue.Empty:
                continue
            except Exception:
                break

    def send_json(self, data):
        try:
            self.wsock.send(json.dumps(data, default=str))
        except:
            self.running = False

    def send_success(self, value, meta=None):
        response = {"status": "success", "value": value}
        if meta: response.update(meta)
        self.send_json(response)

    def send_error(self, reason):
        self.send_json({"status": "fail", "reason": str(reason)})

    def update(self, event):
        # FIX: Check if we have already processed this exact event object
        event_id = id(event)
        if event_id in self._processed_events:
            return # Skip duplicate
        
        # Add to history and keep size small (buffer of last 20 events is sufficient)
        self._processed_events.append(event_id)
        if len(self._processed_events) > 20:
            self._processed_events.pop(0)

        payload = {"type": event.get("type", "unknown")}
        
        if payload["type"] == "catalog_update":
            payload.update(event)
        
        if 'game' in event:
            payload['game_id'] = event['game'].id()
            payload['game_desc'] = event['game'].description()
        if event['type'] == 'score':
            payload.update({"team": event['team'].name, "points": event['points']})
        elif event['type'] == 'cup_ended':
            payload["winner"] = event['winner'].description()
            
        payload["details"] = str(event)
        self.msg_queue.put(payload)

    def handle_command(self, data):
        cmd = data.get("method", "").upper()
        obj_id = data.get("obj")

        with self.catalog_lock: 
            try:
                if cmd == "USER":
                    self.username = data.get("username", "Guest")
                    self.send_success(f"Hello {self.username}")

                elif cmd == "CREATE_TEAM":
                    tid = self.catalog.create(type="team", name=data.get("name"), year=data.get("year"), country=data.get("country"))
                    self.send_success({"id": tid}, meta={"action": "created"})

                elif cmd == "CREATE_GAME":
                    dt_str = data.get("datetime")
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M") if dt_str else datetime.now()
                    gid = self.catalog.create(type="game", home=data.get("home"), away=data.get("away"), datetime=dt)
                    self.send_success({"id": gid}, meta={"action": "created"})

                elif cmd == "CREATE_CUP":
                    cid = self.catalog.create(
                        type="cup", 
                        cup_type=data.get("cup_type", "").upper(), 
                        interval=timedelta(days=int(data.get("interval", 1))), 
                        teams=data.get("teams", [])
                    )
                    self.send_success({"id": cid}, meta={"action": "created"})

                elif cmd == "LIST":
                    items = []
                    for oid, obj in self.catalog.objectDict.items():
                        obj_type = obj.__class__.__name__.lower()
                        if 'cup' in obj_type: obj_type = 'cup'
                        
                        extra = {}
                        if obj_type == 'team':
                            extra['players'] = list(obj.players.keys()) if hasattr(obj, 'players') else []
                        
                        if obj_type == 'game':
                            try:
                                stats = obj.stats()
                                extra['home_name'] = stats['Home']['Name']
                                extra['away_name'] = stats['Away']['Name']
                                extra['home_score'] = stats['Home']['Pts']
                                extra['away_score'] = stats['Away']['Pts']
                                extra['home_id'] = obj.home().id()
                                extra['away_id'] = obj.away().id()
                                # --- FIX: Send Datetime and flags ---
                                extra['datetime_str'] = obj._datetime.strftime("%Y-%m-%d %H:%M")
                                extra['is_running'] = obj.is_running
                                extra['is_ended'] = obj.is_ended
                                extra['is_paused'] = obj.is_paused
                                # ------------------------------------
                            except:
                                pass 

                        items.append({
                            "id": oid,
                            "type": obj_type,
                            "description": obj.description(),
                            "extra": extra
                        })
                    self.send_success(items)

                elif cmd == "DELETE":
                    target_id = data.get("id") or obj_id
                    if not target_id: raise ValueError("No ID provided for deletion")
                    self.catalog.delete(target_id)
                    self.send_success("Deleted " + str(target_id))

                elif obj_id:
                    if obj_id not in self.catalog.objectDict: raise ValueError("Object not found")
                    obj = self.catalog.objectDict[obj_id]
                    
                    if cmd == "WATCH":
                        self.catalog.attach(obj_id, self)
                        self.send_success(f"Watching {obj_id}", meta={"action": "watch_confirmed", "id": obj_id})

                    elif cmd == "UNWATCH":
                        self.catalog.detach(obj_id, self)
                        self.send_success(f"Unwatched {obj_id}", meta={"action": "unwatch_confirmed", "id": obj_id})

                    elif cmd == "ADD_PLAYER":
                        if hasattr(obj, 'addplayer'):
                            obj.addplayer(data.get('name'), int(data.get('number', 0)))
                            current_players = list(obj.players.keys()) if hasattr(obj, 'players') else []
                            self.send_success(
                                {"message": f"Player {data.get('name')} added", "players": current_players}, 
                                meta={"action": "player_added", "obj_id": obj_id}
                            )
                        else: raise ValueError("This object cannot add players")
                    
                    elif cmd == "START": obj.start(); self.send_success("Started")
                    elif cmd == "PAUSE": obj.pause(); self.send_success("Paused")
                    elif cmd == "RESUME": obj.resume(); self.send_success("Resumed")
                    elif cmd == "END": obj.end(); self.send_success("Ended")
                        
                    elif cmd == "STATS":
                        if hasattr(obj, 'stats'): self.send_success(obj.stats())
                        else: self.send_success({"info": str(obj)})
                        
                    elif cmd == "STANDINGS": self.send_success(obj.standings())

                    elif cmd == "SCORE":
                        pts = int(data.get("points", 1))
                        team_id = data.get("team")
                        team_obj = None
                        if team_id in self.catalog.objectDict:
                            team_obj = self.catalog.objectDict[team_id]
                        
                        if not team_obj:
                             raise ValueError("Invalid Team ID")

                        obj.score(pts, team_obj, data.get("player"))
                        self.send_success("Score Updated")
                else:
                    self.send_error("Unknown Command")

            except Exception as e:
                self.send_error(str(e))

    def cleanup(self):
        print(f"Disconnecting {self.addr}")
        self.running = False
        try:
            self.wsock.close()
        except: pass
        with self.catalog_lock:
            self.catalog.detachAll(self)
            self.catalog.detach_observer(self)