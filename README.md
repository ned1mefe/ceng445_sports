# Real-Time Sports Catalog Dashboard

This project is a concurrent, real-time sports tournament management application. It features a robust Object-Oriented Python backend communicating via WebSockets to a rich, interactive frontend dashboard. 

The system allows multiple users to collaboratively create, manage, and monitor sports entities like Teams, Games, and Cups (League, Elimination, and Group stages) in real time.

## 🚀 Features

* **Real-Time Synchronization:** All connected users instantly see updates. If one user creates a team, scores a game, or deletes a cup, the DOM updates across all clients automatically via WebSocket broadcasts.
* **Complex Object Management:**
  * **Teams:** Create teams with names, countries, and founding years.
  * **Games:** Schedule games between teams and manage their lifecycles (Start, Pause, Resume, End, and Score tracking).
  * **Cups:** Form complex tournaments including Elimination Cups, Group Cups, and League Cups. 
* **State Persistence:** The server automatically saves the catalog state (`server_state.pkl`) upon exit and reloads it upon restart.
* **Rich Frontend Interface:** Built with Bootstrap 5 and Tabulator, the dashboard presents clean data grids, forms that abstract away raw internal IDs, and modal-based game management.

## 🛠️ Tech Stack

**Backend:**
* Python 3.12+
* `websockets` (for concurrent WebSocket server implementation)
* `pickle` (for object state persistence)
* Custom OOP Model Library (`class_library/`)

**Frontend:**
* HTML5 / CSS3
* Bootstrap 5 (Styling & Modals)
* jQuery (DOM manipulation and event handling)
* Tabulator (Interactive data grids/tables)

## 📁 Project Structure

```text
├── server.py                 # Main entry point. Handles WebSocket connections & state persistence.
├── session.py                # Session handler for individual client connections and message routing.
├── class_library/
│   ├── catalog.py            # Central data store and event broadcaster.
│   ├── models/               # Domain models (Team, Game, Player).
│   └── cup_types/            # Complex cup logic (EliminationCup, GroupCup, LeagueCup).
├── index.html                # Single-Page Application frontend dashboard.
├── server_state.pkl          # Pickled database (generated automatically).
└── README.md
