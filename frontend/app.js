let socket = null;
let currentViewId = null; 
let currentViewType = null;
let watchedIds = new Set(); 
let catalogCache = []; 

const HOST = "ws://localhost:12345"; 

function connect() {
    const username = document.getElementById('username').value;
    socket = new WebSocket(HOST);

    socket.onopen = () => {
        document.getElementById('status-indicator').textContent = "Connected";
        document.getElementById('status-indicator').className = "connected";
        document.getElementById('main-app').classList.remove('hidden');
        document.getElementById('connection-panel').classList.add('hidden');
        sendJson({ method: "USER", username: username });
        refreshCatalog();
    };

    socket.onmessage = (event) => {
        const response = JSON.parse(event.data);
        handleResponse(response);
    };

    socket.onclose = () => {
        alert("Connection lost. Please refresh.");
    };
}

function sendJson(data) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(data));
    }
}

function handleResponse(res) {
    if (res.status === "notification") {
        
        if (res.data.type === "catalog_update") {
            if (res.data.action === "delete") {
                 if (currentViewId === res.data.id) {
                     document.getElementById('active-object-container').innerHTML = "<p>Object deleted.</p>";
                     currentViewId = null;
                 }
                 watchedIds.delete(res.data.id);
            }
            if(res.data.action === "create" || res.data.action === "delete") {
                showToast(`${res.data.action.toUpperCase()}: ${res.data.id}`);
                refreshCatalog(); 
            }
            return;
        }

        // --- FIX: Handle Cup Ended ---
        if (res.data.type === 'cup_ended') {
            if (watchedIds.has(res.data.cup_id)) {
                showToast(`🏆 Cup ${res.data.cup_id} Ended! Winner: ${res.data.winner}`);
                logNotification(res.data);
            }
            return;
        }
        // -----------------------------

        const type = res.data.type;
        if (['game_started', 'game_paused', 'game_resumed', 'game_ended'].includes(type)) {
             const gid = res.data.game_id;
             const cached = catalogCache.find(x => x.id === gid);
             
             if (cached && cached.extra) {
                 if (type === 'game_started' || type === 'game_resumed') {
                     cached.extra.is_running = true;
                     cached.extra.is_paused = false;
                 }
                 else if (type === 'game_paused') {
                     cached.extra.is_running = false;
                     cached.extra.is_paused = true;
                 }
                 else if (type === 'game_ended') {
                     cached.extra.is_running = false;
                     cached.extra.is_ended = true;
                     cached.extra.is_paused = false;
                 }
             }

             const statusEl = document.getElementById(`status-${gid}`);
             if (statusEl && cached && cached.extra) {
                 let txt = cached.extra.datetime_str;
                 if (cached.extra.is_running) txt = "<span style='color:green; font-weight:bold'>Running</span>";
                 else if (cached.extra.is_ended) txt = "<span style='color:red'>Final</span>";
                 else if (cached.extra.is_paused) txt = "<span style='color:orange; font-weight:bold'>Paused</span>";
                 statusEl.innerHTML = txt;
             }

             if (currentViewId === gid) {
                 sendJson({ method: "STATS", obj: gid });
             }
             
             // FIX: Check if we are watching Game OR Team OR Parent Cup
             const isRelated = res.data.related_ids && res.data.related_ids.some(id => watchedIds.has(id));
             if (watchedIds.has(gid) || watchedIds.has(res.data.home_id) || watchedIds.has(res.data.away_id) || isRelated) {
                 logNotification(res.data);
             }
             return; 
        }
        
        if (res.data.type === 'score') {
            const homeScoreEl = document.getElementById(`score-home-${res.data.game_id}`);
            const awayScoreEl = document.getElementById(`score-away-${res.data.game_id}`);
            
            const gameInCache = catalogCache.find(x => x.id === res.data.game_id);
            if(gameInCache && gameInCache.extra) {
                if (res.data.team === gameInCache.extra.home_name) {
                    if(homeScoreEl) homeScoreEl.innerText = parseInt(homeScoreEl.innerText) + parseInt(res.data.points);
                } else {
                    if(awayScoreEl) awayScoreEl.innerText = parseInt(awayScoreEl.innerText) + parseInt(res.data.points);
                }
            }

            if (res.data.game_id === currentViewId) {
                 sendJson({ method: "STATS", obj: currentViewId });
            }
        }
        
        // FIX: Check related IDs (Cups) for score updates too
        const isRelated = res.data.related_ids && res.data.related_ids.some(id => watchedIds.has(id));
        if (watchedIds.has(res.data.game_id) || watchedIds.has(res.data.id) || watchedIds.has(res.data.home_id) || watchedIds.has(res.data.away_id) || isRelated) {
             logNotification(res.data);
        }
        
        return;
    }

    if (res.status === "success") {
        if (res.action === "watch_confirmed") {
            watchedIds.add(res.id);
            refreshCatalog(); 
        }
        else if (res.action === "unwatch_confirmed") {
            watchedIds.delete(res.id);
            refreshCatalog(); 
        }
        else if (Array.isArray(res.value)) {
            updateCatalogUI(res.value);
        }
        else if (res.action === "player_added") {
            showToast(res.value.message);
            const cachedItem = catalogCache.find(x => x.id === res.obj_id);
            if(cachedItem) {
                if(!cachedItem.extra) cachedItem.extra = {};
                cachedItem.extra.players = res.value.players;
            }
            if (currentViewId === res.obj_id) updateTeamViewUI(res.obj_id, res.value.players);
        }
        else if (res.value && typeof res.value === 'object' && res.value.home_score !== undefined) {
            updateGameHUD(res.value);
        }
        else if (res.value && typeof res.value === 'object' && res.value.Timeline) {
            renderGameStats(res.value);
            updateGameHUD({home_score: res.value.Home.Pts, away_score: res.value.Away.Pts});
        }
    } else if (res.status === "fail") {
        alert("Server Error: " + res.reason);
    }
}

// --- UI Actions ---

function refreshCatalog() {
    sendJson({ method: "LIST" });
}

function createTeam() { sendJson({ method: "CREATE_TEAM", name: document.getElementById('team-name').value, country: document.getElementById('team-country').value, year: document.getElementById('team-year').value }); }
function createGame() { sendJson({ method: "CREATE_GAME", home: document.getElementById('game-home-select').value, away: document.getElementById('game-away-select').value, datetime: document.getElementById('game-date').value.replace("T", " ") }); }
function createCup() { const teams = Array.from(document.getElementById('cup-teams-select').selectedOptions).map(opt => opt.value); sendJson({ method: "CREATE_CUP", cup_type: document.getElementById('cup-type').value, interval: document.getElementById('cup-interval').value, teams: teams }); }
function deleteObj(id) { if(confirm("Delete " + id + "?")) sendJson({ method: "DELETE", id: id }); }
function toggleWatch(id) { if (watchedIds.has(id)) sendJson({ method: "UNWATCH", obj: id }); else sendJson({ method: "WATCH", obj: id }); }

// --- Viewing & Stats ---

function viewObj(id, type) {
    currentViewId = id;
    currentViewType = type;
    
    const container = document.getElementById('active-object-container');
    container.innerHTML = "Loading Details...";

    if (type === 'game') {
        const template = document.getElementById('game-controls-template').cloneNode(true);
        template.classList.remove('hidden');
        template.id = "active-game-ui";
        const obj = catalogCache.find(x => x.id === id);
        if(obj) template.querySelector('#hud-desc').textContent = obj.description;
        
        container.innerHTML = "";
        container.appendChild(template);
        
        const statsDiv = document.createElement("div");
        statsDiv.id = "game-stats-container";
        statsDiv.innerHTML = "<p>Fetching Stats...</p>";
        container.appendChild(statsDiv);

        populateGameSelectors();
        sendJson({ method: "STATS", obj: id });
    } else if (type === 'team') {
        const obj = catalogCache.find(x => x.id === id);
        updateTeamViewUI(id, obj && obj.extra ? obj.extra.players : []);
    } else {
        container.innerHTML = `<h4>Details for ${type} (${id})</h4>`;
    }
}

function renderGameStats(stats) {
    const container = document.getElementById("game-stats-container");
    if(!container) return;

    let html = `
        <table style="width:100%; font-size:0.9em; margin-top:10px; border-top:1px solid #ccc;">
            <tr>
                <th width="50%">${stats.Home.Name}</th>
                <th width="50%">${stats.Away.Name}</th>
            </tr>
            <tr>
                <td valign="top">
                    <ul>${Object.entries(stats.Home.Players).map(([p, s]) => `<li>${p}: ${s}</li>`).join('')}</ul>
                </td>
                <td valign="top">
                    <ul>${Object.entries(stats.Away.Players).map(([p, s]) => `<li>${p}: ${s}</li>`).join('')}</ul>
                </td>
            </tr>
            <tr>
                <td colspan="2" style="text-align:center; background:#eee;"><strong>Game Time: ${stats.Time}</strong></td>
            </tr>
        </table>
    `;
    container.innerHTML = html;
}

function updateTeamViewUI(id, players) {
    const container = document.getElementById('active-object-container');
    const playersHtml = (players && players.length > 0) ? players.join(", ") : "No players found";
    container.innerHTML = `
        <div class="card" style="width:100%">
            <h4>Team: ${id}</h4>
            <p><strong>Players:</strong> ${playersHtml}</p>
            <button onclick="promptAddPlayer('${id}')">Add Player</button>
        </div>`;
}

function logNotification(data) {
    const log = document.getElementById('notification-log');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    let content = (data.type === 'score') ? `<strong>GOAL!</strong> ${data.team} (+${data.points})` : JSON.stringify(data);
    if(data.type === 'cup_ended') content = `<strong>🏆 WINNER:</strong> ${data.winner}`;
    entry.innerHTML = `${content} <small>${new Date().toLocaleTimeString()}</small>`;
    log.insertBefore(entry, log.firstChild);
}

function gameControl(id, action) { if(!id) return; sendJson({ method: action, obj: id }); }

function sendScore() {
    if(!currentViewId) return;
    const teamId = document.getElementById('score-team-select').value;
    const pts = document.getElementById('score-points').value;
    const player = document.getElementById('score-player').value;
    sendJson({ method: "SCORE", obj: currentViewId, team: teamId, points: pts, player: player });
}

function promptAddPlayer(teamId) {
    const name = prompt("Name:");
    if(name) sendJson({ method: "ADD_PLAYER", obj: teamId, name: name });
}

function updateCatalogUI(items) {
    catalogCache = items;
    const tbody = document.querySelector("#catalog-table tbody");
    tbody.innerHTML = "";
    
    const homeSel = document.getElementById('game-home-select');
    const awaySel = document.getElementById('game-away-select');
    const cupSel = document.getElementById('cup-teams-select');
    homeSel.length = 1; awaySel.length = 1; cupSel.innerHTML = "";

    items.forEach(item => {
        const isWatched = watchedIds.has(item.id);
        const watchBtn = `<button onclick="toggleWatch('${item.id}')" style="background:${isWatched ? "#6c757d" : "#28a745"}">${isWatched ? "Unwatch" : "Watch"}</button>`;
        
        let desc = item.description;
        
        let buttons = `
            ${watchBtn}
            <button onclick="viewObj('${item.id}', '${item.type}')" style="background:#007bff">Details</button>
            <button onclick="deleteObj('${item.id}')" style="background:#dc3545">Del</button>
        `;

        if (item.type === 'game' && item.extra && item.extra.home_name) {
             const e = item.extra;
             let statusText = e.datetime_str; 
             if (e.is_running) statusText = "<span style='color:green; font-weight:bold'>Running</span>";
             else if (e.is_ended) statusText = "<span style='color:red'>Final</span>";
             else if (e.is_paused) statusText = "<span style='color:orange; font-weight:bold'>Paused</span>";

             desc = `
                <div class="game-row-header">
                    <strong>${e.home_name}</strong> <span id="score-home-${item.id}" class="score-badge">${e.home_score}</span>
                    - 
                    <span id="score-away-${item.id}" class="score-badge">${e.away_score}</span> <strong>${e.away_name}</strong>
                    <br><small id="status-${item.id}">${statusText}</small>
                </div>
            `;
            
            buttons = `
                ${watchBtn}
                <button onclick="viewObj('${item.id}', 'game')" style="background:#007bff">Stats/Control</button>
                <div class="btn-group" style="margin-top:2px;">
                    <button onclick="gameControl('${item.id}', 'START')" title="Start">▶</button>
                    <button onclick="gameControl('${item.id}', 'PAUSE')" title="Pause">⏸</button>
                </div>
                <div class="btn-group" style="margin-top:2px;">
                    <button onclick="gameControl('${item.id}', 'END')" style="background:#ffc107; color:black; width:100%">End Game</button>
                </div>
                <button onclick="deleteObj('${item.id}')" style="background:#dc3545; margin-top:4px;">Del</button>
            `;
        }

        if (item.type === 'team') {
            const opt = new Option(item.description, item.id);
            homeSel.add(opt.cloneNode(true));
            awaySel.add(opt.cloneNode(true));
            cupSel.add(opt.cloneNode(true));
        }

        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${item.id}</td><td>${item.type}</td><td>${desc}</td><td style="display:flex; flex-direction:column; gap:2px;">${buttons}</td>`;
        tbody.appendChild(tr);
    });
}

function updateGameHUD(stats) {
    const homeScore = document.getElementById('hud-home-score');
    const awayScore = document.getElementById('hud-away-score');
    if(homeScore && stats.home_score !== undefined) homeScore.innerText = stats.home_score;
    if(awayScore && stats.away_score !== undefined) awayScore.innerText = stats.away_score;
}

function populateGameSelectors() {
    const scoreSel = document.getElementById('score-team-select');
    if(scoreSel) {
        scoreSel.innerHTML = "";
        catalogCache.filter(x => x.type === 'team').forEach(t => {
            scoreSel.add(new Option(t.description, t.id));
        });
    }
}

function showToast(msg) {
    const area = document.getElementById('notification-area');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerText = msg;
    area.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}