import json
import threading
import queue
import pprint
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
            # Use a custom encoder or default string conversion for non-serializable objects
            self.wsock.send(json.dumps(data, default=str))
        except:
            self.running = False

    def send_success(self, value, meta=None):
        response = {"status": "success", "value": value}
        if meta: response.update(meta)
        self.send_json(response)

    def send_error(self, reason):
        self.send_json({"status": "fail", "reason": reason})

    def update(self, event):
        # Prepare structured real-time events
        payload = {"type": event.get("type", "unknown")}
        
        # Handle game-related events
        if 'game' in event:
            payload['game_id'] = event['game'].id()
            payload['game_desc'] = event['game'].description()
        
        # Handle creation events
        if event['type'].endswith('_created'):
            payload['id'] = event.get('id')
            payload['description'] = event.get('description')
        # Handle deletion events
        elif event['type'].endswith('_deleted'):
            payload['id'] = event.get('id')
        # Handle score events
        elif event['type'] == 'score':
            payload.update({
                "team": event['team'].name,
                "points": event['points'],
                "new_score": event.get("new_score_str", "")
            })
        # Handle cup ended events
        elif event['type'] == 'cup_ended':
            payload["winner"] = event['winner'].description()
        # Handle other game state events (game_started, game_paused, game_resumed, game_ended)
        elif event['type'] in ['game_started', 'game_paused', 'game_resumed', 'game_ended']:
            if 'game' in event:
                payload['game_id'] = event['game'].id()
                payload['game_desc'] = event['game'].description()

        # Add raw event details for generic display
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
                    # Enhanced LIST: Returns basic metadata for rendering cards
                    items = []
                    for oid, obj in self.catalog.objectDict.items():
                        # Determine type based on class name or internal properties
                        obj_type = obj.__class__.__name__.lower() # e.g., 'game', 'team', 'leaguecup'
                        if 'Cup' in obj_type: obj_type = 'cup'
                        
                        items.append({
                            "id": oid,
                            "type": obj_type,
                            "description": obj.description(),
                            "details": str(obj)
                        })
                    self.send_success(items)

                elif cmd == "DELETE":
                    self.catalog.delete(data.get("id") or obj_id)
                    self.send_success("Deleted")

                # Object Commands
                elif obj_id:
                    obj = self.catalog.objectDict[obj_id]
                    
                    if cmd == "WATCH":
                        self.catalog.attach(obj_id, self)
                        self.send_success(f"Watching {obj_id}")
                    
                    elif cmd == "START":
                        obj.start()
                        self.send_success("Started")
                    
                    elif cmd == "PAUSE":
                        obj.pause()
                        self.send_success("Paused")
                        
                    elif cmd == "RESUME":
                        obj.resume()
                        self.send_success("Resumed")
                        
                    elif cmd == "END":
                        obj.end()
                        self.send_success("Ended")
                        
                    elif cmd == "STATS":
                        # Return raw dict, not pprint string
                        self.send_success(obj.stats())
                        
                    elif cmd == "STANDINGS":
                        # Return raw dict/list
                        self.send_success(obj.standings())

                    elif cmd == "SCORE":
                        pts = int(data.get("points", 1))
                        # Resolve team ID to object
                        team_obj = self.catalog.objectDict[data.get("team")]
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