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
        
        populateCupTypes();
        
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
                 const msg = `🗑️ <strong>Deleted</strong>`;
                 showToast(msg);
                //  logNotification({ type: 'catalog_delete', text: msg });
            }
            if(res.data.action === "create") {
                // FIX: Styled "Created" notification
                let icon = "🆕";
                let text = "Created";
                if (res.data.id.startsWith("game")) { icon = "🎮"; text = "Game Created"; }
                else if (res.data.id.startsWith("team")) { icon = "👕"; text = "Team Created"; }
                else if (res.data.id.startsWith("cup")) { icon = "🏆"; text = "Cup Created"; }

                const msg = `${icon} <strong>${text}</strong><br>${res.data.description}`;
                showToast(msg);
                
                // Add to Log Panel
                // logNotification({
                //     type: 'catalog_create', 
                //     htmlContent: msg
                // });
                
                refreshCatalog(); 
            } else if (res.data.action === "delete") {
                refreshCatalog();
            }
            return;
        }

        if (res.data.type === 'cup_ended') {
            if (watchedIds.has(res.data.cup_id)) {
                showToast(`🏆 <strong>Cup Ended!</strong><br>Winner: ${res.data.winner}`);
                logNotification(res.data);
            }
            if (currentViewId === res.data.cup_id) {
                sendJson({ method: "STANDINGS", obj: currentViewId });
            }
            return;
        }

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
             
             const isRelated = res.data.related_ids && res.data.related_ids.includes(currentViewId);
             if (currentViewType === 'cup' && isRelated) {
                 sendJson({ method: "STANDINGS", obj: currentViewId });
             }

             // FIX: Styled Game State Notifications
             if (watchedIds.has(gid) || watchedIds.has(res.data.home_id) || watchedIds.has(res.data.away_id) || (res.data.related_ids && res.data.related_ids.some(id => watchedIds.has(id)))) {
                 const desc = res.data.game_desc || ("Game " + gid);
                 let msg = "";
                 
                 if (type === 'game_started') msg = `▶️ <strong>Game Started</strong><br>${desc}`;
                 else if (type === 'game_paused') msg = `⏸️ <strong>Game Paused</strong><br>${desc}`;
                 else if (type === 'game_resumed') msg = `▶️ <strong>Game Resumed</strong><br>${desc}`;
                 else if (type === 'game_ended') msg = `🏁 <strong>Game Ended</strong><br>${desc}`;
                 
                 showToast(msg);
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

            const isRelated = res.data.related_ids && res.data.related_ids.includes(currentViewId);
            if (currentViewType === 'cup' && isRelated) {
                sendJson({ method: "STANDINGS", obj: currentViewId });
            }
        }
        
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
        else if (res.action === "standings") {
            if (currentViewId === res.id) {
                renderCupStandings(res.value);
            }
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
    } else if (type === 'cup') {
        container.innerHTML = `<h4>Cup: ${id}</h4><div id="cup-standings-area">Fetching Standings...</div>`;
        sendJson({ method: "STANDINGS", obj: id });
    } else {
        container.innerHTML = `<h4>Details for ${type} (${id})</h4>`;
    }
}

function populateCupTypes() {
    const sel = document.getElementById('cup-type');
    if (!sel) return;
    sel.innerHTML = "";
    const types = ["ELIMINATION", "ELIMINATION2", "LEAGUE", "LEAGUE2", "GROUP", "GROUP2"];
    types.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t;
        opt.text = t;
        sel.appendChild(opt);
    });
}
function renderCupStandings(dataWrapper) {
    const area = document.getElementById('cup-standings-area');
    if (!area) return;
    area.innerHTML = "";

    let data = dataWrapper.standings;
    const games = dataWrapper.games;
    let html = "";

    // 1. Helper to render a League-style table (Used for LeagueCup and GroupCup Groups)
    // Columns: Team, Won, Lost, Draw, Avg (Diff), Scored, Conceded, Points
    const renderLeagueTable = (standingsData) => {
        let t = `
        <table class='table'>
            <thead>
                <tr>
                    <th>Team</th>
                    <th>Won</th>
                    <th>Lost</th>
                    <th>Draw</th>
                    <th>Avg</th>
                    <th>Scored</th>
                    <th>Conceded</th>
                    <th>Points</th>
                </tr>
            </thead>
            <tbody>`;
            
        standingsData.forEach(row => {
             const name = row[0];
             const s = row[1];
             if(s) {
                 t += `<tr>
                    <td><strong>${name}</strong></td>
                    <td>${s.Won}</td>
                    <td>${s.Lost}</td>
                    <td>${s.Draw}</td>
                    <td>${s.Diff}</td> 
                    <td>${s.Scored}</td>
                    <td>${s.Conceded}</td>
                    <td><strong>${s.Points}</strong></td>
                 </tr>`;
             } else {
                 t += `<tr><td>${name}</td><td colspan='7'>N/A</td></tr>`;
             }
        });
        t += "</tbody></table>";
        return t;
    };

    // 2. Helper to render an Elimination-style table (Used for EliminationCup and GroupCup PlayOffs)
    const renderEliminationTable = (standingsData) => {
        let t = `
        <table class='table'>
            <thead>
                <tr>
                    <th>Team</th>
                    <th>Round</th>
                    <th>Won Against</th>
                    <th>Lost Against</th>
                </tr>
            </thead>
            <tbody>`;
            
        Object.entries(standingsData || {}).forEach(([name, info]) => {
             const wonStr = info.Won ? info.Won.map(w => `${w[0]} (${w[1]}-${w[2]})`).join(", ") : "";
             const lostStr = info.Lost ? info.Lost.map(l => `${l[0]} (${l[1]}-${l[2]})`).join(", ") : "";

             t += `<tr>
                <td><strong>${name}</strong></td>
                <td>${info.Round}</td>
                <td style="color:green; font-size:0.9em">${wonStr}</td>
                <td style="color:red; font-size:0.9em">${lostStr}</td>
             </tr>`;
        });
        t += "</tbody></table>";
        return t;
    };

    html += "<h5>Standings</h5>";

    // 3. Main Logic to select the correct renderer
    if (Array.isArray(data)) {
        // --- LEAGUE CUP ---
        html += renderLeagueTable(data);
    } else {
        const keys = Object.keys(data || {});
        // Check if this looks like a Group Cup (has "Group X" or "PlayOffs" keys)
        const isGroupCup = keys.some(k => k.startsWith("Group") || k === "PlayOffs");

        if (isGroupCup) {
            // --- GROUP CUP ---
            // Sort to ensure Groups A, B... appear before PlayOffs
            keys.sort(); 
            
            keys.forEach(k => {
                 html += `<h6>${k}</h6>`;
                 if (Array.isArray(data[k])) {
                     // Groups use the League format
                     html += renderLeagueTable(data[k]);
                 } else if (typeof data[k] === 'object') {
                     // PlayOffs use the Elimination format
                     html += renderEliminationTable(data[k]);
                 }
             });
        } else {
            // --- ELIMINATION CUP (Standalone) ---
            html += renderEliminationTable(data);
        }
    }
    
    // 4. Render Matches List (Shared across all cups)
    if (games && games.length > 0) {
        html += "<h5 style='margin-top:15px;'>Matches</h5>";
        html += "<table class='table table-striped' style='font-size:0.9em;'><thead><tr><th>Date</th><th>Home</th><th>Score</th><th>Away</th><th>Status</th></tr></thead><tbody>";
        games.forEach(g => {
            const status = g.is_ended ? "Final" : "Scheduled";
            html += `<tr>
                <td>${g.datetime}</td>
                <td>${g.home}</td>
                <td style="font-weight:bold;">${g.score_home} - ${g.score_away}</td>
                <td>${g.away}</td>
                <td>${status}</td>
            </tr>`;
        });
        html += "</tbody></table>";
    }

    area.innerHTML = html;
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
    
    // Create a list of players with their numbers
    let playersHtml = "<ul>";
    if (players && players.length > 0) {
        players.forEach(playerStr => {
            // playerStr is already formatted as "Name (Number)" by the backend
            playersHtml += `<li>${playerStr}</li>`;
        });
    } else {
        playersHtml += "<li>No players found</li>";
    }
    playersHtml += "</ul>";

    container.innerHTML = `
        <div class="card" style="width:100%">
            <h4>Team: ${id}</h4>
            <p><strong>Roster:</strong></p>
            ${playersHtml}
            <button onclick="promptAddPlayer('${id}')">Add Player</button>
        </div>`;
}

// FIX: Improved Logger to handle formatted HTML and Icons
function logNotification(data) {
    const log = document.getElementById('notification-log');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    let content = "";
    
    if (data.htmlContent) {
        // Direct HTML pass-through from handleResponse
        content = data.htmlContent;
    }
    else if (data.type === 'score') {
        content = `<strong>⚽ GOAL!</strong> ${data.team} (+${data.points})`;
    } 
    else if (data.type === 'cup_ended') {
        content = `<strong>🏆 WINNER:</strong> ${data.winner}`;
    }
    else if (['game_started', 'game_paused', 'game_resumed', 'game_ended'].includes(data.type)) {
        let icon = "🔔";
        let title = "Update";
        if (data.type === 'game_started') { icon = "▶️"; title = "Started"; }
        if (data.type === 'game_paused') { icon = "⏸️"; title = "Paused"; }
        if (data.type === 'game_resumed') { icon = "▶️"; title = "Resumed"; }
        if (data.type === 'game_ended') { icon = "🏁"; title = "Ended"; }
        
        content = `<strong>${icon} Game ${title}</strong><br><small>${data.game_desc || data.game_id}</small>`;
    }
    else if (data.type === 'catalog_delete') {
        content = data.text;
    }
    else if (data.type === 'player_added') {
        content = `<strong>👤 Player Added</strong><br>${data.players[data.players.length-1]}`;
    }
    else {
        content = JSON.stringify(data);
    }

    const time = new Date().toLocaleTimeString();
    entry.innerHTML = `${content} <div style="font-size:0.7em; color:#888; margin-top:2px;">${time}</div>`;
    log.insertBefore(entry, log.firstChild);
}

function gameControl(id, action) { 
    if(!id) return; 
    sendJson({ method: action, obj: id }); 
}

function sendScore() {
    if(!currentViewId) return;
    const teamId = document.getElementById('score-team-select').value;
    const pts = document.getElementById('score-points').value;
    const player = document.getElementById('score-player').value;
    sendJson({ method: "SCORE", obj: currentViewId, team: teamId, points: pts, player: player });
}

function promptAddPlayer(teamId) {
    // Asking in a format that implies a single thought process or box
    const input = prompt("Enter Player Name and Jersey Number (e.g. Messi, 10):");
    if (!input) return;

    const parts = input.split(",");
    if (parts.length < 2) {
        alert("Please provide both name and number separated by a comma.");
        return;
    }

    const name = parts[0].trim();
    const number = parseInt(parts[1].trim());

    if (!name || isNaN(number)) {
        alert("Invalid input format.");
        return;
    }
    
    sendJson({ 
        method: "ADD_PLAYER", 
        obj: teamId, 
        name: name, 
        number: number 
    });
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
        tr.innerHTML = `<td>${item.type}</td><td>${desc}</td><td style="display:flex; flex-direction:column; gap:2px;">${buttons}</td>`;
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
    toast.innerHTML = msg; 
    area.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}