const WS_URL = 'ws://localhost:12345';
let ws = null;
let data = {
    teams: [],
    games: [],
    cups: []
};
let gameStats = {}; // Store stats for each game: { gameId: { Home: {...}, Away: {...}, Time: "...", Status: "..." } }
let currentStatsRequestGameId = null; // Track which game we're currently requesting stats for
let statsRequestQueue = []; // Queue of game IDs waiting for stats
let tables = {
    teams: null,
    games: null,
    cups: null
};
let currentModalObjId = null; // Store current object ID for modal actions

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function updateStatus(connected) {
    const status = document.getElementById('status');
    if (connected) {
        status.textContent = '✓ Connected';
        status.className = 'status connected';
    } else {
        status.textContent = '✗ Disconnected';
        status.className = 'status disconnected';
    }
}

function connect() {
    try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log('Connected to server');
            updateStatus(true);
            sendCommand({ method: 'USER', username: 'WebUser' });
            refreshList();
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleMessage(message);
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateStatus(false);
        };

        ws.onclose = () => {
            console.log('Disconnected from server');
            updateStatus(false);
            setTimeout(connect, 3000); // Reconnect after 3 seconds
        };
    } catch (e) {
        console.error('Connection error:', e);
        updateStatus(false);
    }
}

function sendCommand(cmd) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(cmd));
    } else {
        showNotification('Not connected to server', 'error');
    }
}

let lastActionGameId = null; // Track which game ID was used for the last action command

function handleMessage(message) {
    if (message.status === 'notification') {
        handleNotification(message.data);
    } else if (message.status === 'success') {
        if (message.meta && message.meta.action === 'created') {
            refreshList();
        }
        if (message.value && Array.isArray(message.value)) {
            updateData(message.value);
            refreshTables();
        } else if (message.value && typeof message.value === 'object') {
            // Check if this is a stats response (has Home and Away)
            if (message.value.Home && message.value.Away) {
                // This is a stats response
                if (currentStatsRequestGameId) {
                    // This is for the table - store stats and continue fetching
                    const gameId = currentStatsRequestGameId;
                    gameStats[gameId] = message.value;
                    currentStatsRequestGameId = null;
                    fetchNextGameStats(); // Fetch next game
                    refreshGamesTable(); // Refresh table with new stats
                }

                // Also update modal if it's open and showing this game
                if (currentModalObjId) {
                    displayModalData(message.value);
                }
            } else {
                // Handle standings responses
                displayModalData(message.value);
            }
        } else if (typeof message.value === 'string' && lastActionGameId) {
            // This is a string response from START/PAUSE/RESUME/END command
            // Fetch stats for the game that was just acted upon
            const gameId = lastActionGameId;
            lastActionGameId = null;

            // Clear cached stats and fetch new ones
            delete gameStats[gameId];
            if (currentStatsRequestGameId !== gameId) {
                statsRequestQueue.unshift(gameId); // Add to front of queue
                if (currentStatsRequestGameId === null) {
                    fetchNextGameStats();
                }
            }
            // Refresh table immediately to show "Loading..." while fetching
            refreshGamesTable();
        }
    } else if (message.status === 'fail') {
        showNotification('Error: ' + message.reason, 'error');
        if (currentStatsRequestGameId) {
            // If stats request failed, continue to next
            currentStatsRequestGameId = null;
            fetchNextGameStats();
        }
        lastActionGameId = null; // Clear on error
    }
}

function getGameStatus(stats) {
    // Use the Status field from stats if available
    if (stats && stats.Status) {
        return stats.Status;
    }
    // Fallback for backward compatibility
    if (!stats || !stats.Time) {
        return 'Scheduled';
    }
    if (stats.Time === 'Full Time') {
        return 'Ended';
    }
    if (stats.Time === '00:00.0' || stats.Time === '00:00') {
        return 'Scheduled';
    }
    return 'In Progress';
}

function handleNotification(notification) {
    const type = notification.type;
    showNotification(`Notification: ${type}`, 'info');

    if (type.endsWith('_created') || type.endsWith('_deleted')) {
        refreshList();
    } else if (type === 'score' || type === 'game_started' || type === 'game_paused' || type === 'game_resumed' || type === 'game_ended') {
        // For game events, refresh stats for the affected game
        if (notification.game_id) {
            // Clear cached stats and refetch
            delete gameStats[notification.game_id];
            if (currentStatsRequestGameId !== notification.game_id) {
                statsRequestQueue.unshift(notification.game_id); // Add to front of queue
                if (currentStatsRequestGameId === null) {
                    fetchNextGameStats();
                }
            }
            // Refresh table immediately to show "Loading..." while fetching
            refreshGamesTable();
        }
        // Don't call refreshList() here as it might interfere with stats fetching
        // The list will be refreshed when needed
    } else {
        // For other events, refresh list
        refreshList();
    }
}

function refreshList() {
    sendCommand({ method: 'LIST' });
}

function updateData(items) {
    data.teams = items.filter(item => item.type === 'team');
    data.games = items.filter(item => item.type === 'game');
    data.cups = items.filter(item => item.type === 'cup');

    // Update dropdowns
    updateTeamDropdowns();
}

function updateTeamDropdowns() {
    const homeSelect = document.getElementById('gameHomeTeam');
    const awaySelect = document.getElementById('gameAwayTeam');
    const cupSelect = document.getElementById('cupTeams');

    [homeSelect, awaySelect, cupSelect].forEach(select => {
        select.innerHTML = '<option value="">Select a team...</option>';
        data.teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team.id;
            option.textContent = team.description;
            select.appendChild(option);
        });
    });
}

function refreshTables() {
    refreshTeamsTable();
    refreshGamesTable();
    refreshCupsTable();
}

function refreshTeamsTable() {
    const container = document.getElementById('teamsTable');
    if (data.teams.length === 0) {
        container.innerHTML = '<p>No teams yet.</p>';
        return;
    }

    let html = '<table id="teamsDataTable" class="display"><thead><tr><th>ID</th><th>Description</th><th>Actions</th></tr></thead><tbody>';
    data.teams.forEach(team => {
        html += `<tr>
                    <td>${team.id.substring(0, 8)}...</td>
                    <td>${team.description}</td>
                    <td><button class="btn-danger btn-sm" onclick="deleteItem('${team.id}')">Delete</button></td>
                </tr>`;
    });
    html += '</tbody></table>';

    container.innerHTML = html;

    if (tables.teams) {
        tables.teams.destroy();
    }
    tables.teams = $('#teamsDataTable').DataTable({
        pageLength: 10,
        order: [[1, 'asc']]
    });
}

function fetchNextGameStats() {
    if (statsRequestQueue.length === 0 || currentStatsRequestGameId !== null) {
        return; // Queue empty or request in progress
    }

    const gameId = statsRequestQueue.shift();
    currentStatsRequestGameId = gameId;

    sendCommand({
        method: 'STATS',
        obj: gameId
    });

    // Timeout in case response never comes
    setTimeout(() => {
        if (currentStatsRequestGameId === gameId) {
            currentStatsRequestGameId = null;
            fetchNextGameStats();
        }
    }, 2000);
}

function fetchAllGameStats() {
    // Clear queue and add all games that need stats
    statsRequestQueue = data.games
        .filter(game => !gameStats[game.id])
        .map(game => game.id);

    // Start fetching
    fetchNextGameStats();
}

function refreshGamesTable() {
    const container = document.getElementById('gamesTable');
    if (data.games.length === 0) {
        container.innerHTML = '<p>No games yet.</p>';
        return;
    }

    // Fetch stats for all games if we don't have them
    let needsStats = false;
    data.games.forEach(game => {
        if (!gameStats[game.id]) {
            needsStats = true;
        }
    });

    if (needsStats) {
        fetchAllGameStats();
    }

    let html = '<table id="gamesDataTable" class="display"><thead><tr><th>Description</th><th>Score</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
    data.games.forEach(game => {
        const stats = gameStats[game.id];
        const score = stats ? `${stats.Home.Pts} - ${stats.Away.Pts}` : '-';
        const status = stats ? getGameStatus(stats) : 'Loading...';
        // Map status to CSS class
        let statusClass = 'status-scheduled';
        if (status === 'Ended') {
            statusClass = 'status-ended';
        } else if (status === 'Running') {
            statusClass = 'status-running';
        } else if (status === 'Paused') {
            statusClass = 'status-paused';
        } else if (status === 'Scheduled') {
            statusClass = 'status-scheduled';
        }

        html += `<tr>
                    <td>${game.description}</td>
                    <td><strong>${score}</strong></td>
                    <td><span class="${statusClass}">${status}</span></td>
                    <td>
                        <button class="btn-sm btn-success" onclick="showGameDetails('${game.id}')">Details</button>
                        <button class="btn-danger btn-sm" onclick="deleteItem('${game.id}')">Delete</button>
                    </td>
                </tr>`;
    });
    html += '</tbody></table>';

    container.innerHTML = html;

    if (tables.games) {
        tables.games.destroy();
    }
    tables.games = $('#gamesDataTable').DataTable({
        pageLength: 10,
        order: [[2, 'asc']] // Sort by status
    });
}

function refreshCupsTable() {
    const container = document.getElementById('cupsTable');
    if (data.cups.length === 0) {
        container.innerHTML = '<p>No cups yet.</p>';
        return;
    }

    let html = '<table id="cupsDataTable" class="display"><thead><tr><th>ID</th><th>Description</th><th>Actions</th></tr></thead><tbody>';
    data.cups.forEach(cup => {
        html += `<tr>
                    <td>${cup.id.substring(0, 8)}...</td>
                    <td>${cup.description}</td>
                    <td>
                        <button class="btn-sm btn-success" onclick="showCupStandings('${cup.id}')">Standings</button>
                        <button class="btn-danger btn-sm" onclick="deleteItem('${cup.id}')">Delete</button>
                    </td>
                </tr>`;
    });
    html += '</tbody></table>';

    container.innerHTML = html;

    if (tables.cups) {
        tables.cups.destroy();
    }
    tables.cups = $('#cupsDataTable').DataTable({
        pageLength: 10,
        order: [[1, 'asc']]
    });
}

function createTeam() {
    const name = document.getElementById('teamName').value.trim();
    const year = document.getElementById('teamYear').value;
    const country = document.getElementById('teamCountry').value.trim();

    if (!name) {
        showNotification('Team name is required', 'error');
        return;
    }

    sendCommand({
        method: 'CREATE_TEAM',
        name: name,
        year: year || null,
        country: country || null
    });

    document.getElementById('teamName').value = '';
    document.getElementById('teamYear').value = '';
    document.getElementById('teamCountry').value = '';
}

function createGame() {
    const home = document.getElementById('gameHomeTeam').value;
    const away = document.getElementById('gameAwayTeam').value;
    const datetime = document.getElementById('gameDateTime').value;

    if (!home || !away) {
        showNotification('Please select both teams', 'error');
        return;
    }

    if (home === away) {
        showNotification('Home and away teams must be different', 'error');
        return;
    }

    let dtStr = null;
    if (datetime) {
        // Convert datetime-local to format expected by server (YYYY-MM-DD HH:MM)
        const dt = new Date(datetime);
        dtStr = dt.toISOString().slice(0, 16).replace('T', ' ');
    }

    sendCommand({
        method: 'CREATE_GAME',
        home: home,
        away: away,
        datetime: dtStr
    });

    document.getElementById('gameHomeTeam').value = '';
    document.getElementById('gameAwayTeam').value = '';
    document.getElementById('gameDateTime').value = '';
}

function createCup() {
    const cupType = document.getElementById('cupType').value;
    const interval = document.getElementById('cupInterval').value;
    const teamsSelect = document.getElementById('cupTeams');
    const teams = Array.from(teamsSelect.selectedOptions).map(opt => opt.value);

    if (teams.length < 2) {
        showNotification('Please select at least 2 teams', 'error');
        return;
    }

    sendCommand({
        method: 'CREATE_CUP',
        cup_type: cupType,
        interval: interval || 1,
        teams: teams
    });

    teamsSelect.selectedIndex = -1;
}

function deleteItem(id) {
    if (confirm('Are you sure you want to delete this item?')) {
        sendCommand({
            method: 'DELETE',
            id: id
        });
    }
}

function showGameDetails(gameId) {
    currentModalObjId = gameId;
    sendCommand({
        method: 'STATS',
        obj: gameId
    });

    const modal = document.getElementById('gameModal');
    document.getElementById('modalTitle').textContent = 'Game Details & Controls';
    document.getElementById('modalBody').innerHTML = '<p>Loading...</p>';
    modal.style.display = 'block';
}

function showCupStandings(cupId) {
    currentModalObjId = cupId;
    sendCommand({
        method: 'STANDINGS',
        obj: cupId
    });

    const modal = document.getElementById('gameModal');
    document.getElementById('modalTitle').textContent = 'Cup Standings';
    document.getElementById('modalBody').innerHTML = '<p>Loading...</p>';
    modal.style.display = 'block';
}

function displayModalData(data) {
    const modalBody = document.getElementById('modalBody');
    let html = '';

    // If it's game stats, format nicely
    if (data.Home && data.Away) {
        html += '<div style="margin-bottom: 20px;">';
        html += `<h3>${data.Home.Name} vs ${data.Away.Name}</h3>`;
        html += `<p><strong>Score:</strong> ${data.Home.Name} ${data.Home.Pts} - ${data.Away.Pts} ${data.Away.Name}</p>`;
        html += `<p><strong>Time:</strong> ${data.Time}</p>`;
        if (data.Timeline && data.Timeline.length > 0) {
            html += '<h4>Timeline:</h4><ul>';
            data.Timeline.forEach(event => {
                html += `<li>${event[0]}: ${event[1]} ${event[2] ? '(' + event[2] + ')' : ''} +${event[3]} points</li>`;
            });
            html += '</ul>';
        }
        html += '</div>';

        // Game controls
        html += '<div class="game-controls" style="margin-top: 20px; margin-bottom: 20px;">';
        html += '<button class="btn-success btn-sm" onclick="gameAction(\'START\')">Start</button>';
        html += '<button class="btn-warning btn-sm" onclick="gameAction(\'PAUSE\')">Pause</button>';
        html += '<button class="btn-success btn-sm" onclick="gameAction(\'RESUME\')">Resume</button>';
        html += '<button class="btn-danger btn-sm" onclick="gameAction(\'END\')">End</button>';
        html += '</div>';

        // Score controls
        html += '<div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px;">';
        html += '<h4>Add Score</h4>';
        html += '<div class="form-row">';
        html += '<div class="form-group"><label>Team</label>';
        html += `<select id="scoreTeam"><option value="${data.Home.Name}">${data.Home.Name}</option><option value="${data.Away.Name}">${data.Away.Name}</option></select>`;
        html += '</div>';
        html += '<div class="form-group"><label>Points</label>';
        html += '<input type="number" id="scorePoints" value="1" min="1">';
        html += '</div>';
        html += '<div class="form-group" style="grid-column: 1 / -1;"><label>Player (optional)</label>';
        html += '<input type="text" id="scorePlayer" placeholder="Player name">';
        html += '</div>';
        html += '</div>';
        html += '<button onclick="addScore()">Add Score</button>';
        html += '</div>';

        // Store team IDs for score
        html += `<script>window.gameHomeTeamName = "${data.Home.Name}"; window.gameAwayTeamName = "${data.Away.Name}";</script>`;
    } else {
        // For standings or other data, show as JSON
        html = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }

    modalBody.innerHTML = html;
}

function gameAction(action) {
    if (!currentModalObjId) return;

    // Track which game we're acting upon
    lastActionGameId = currentModalObjId;

    sendCommand({
        method: action,
        obj: currentModalObjId
    });

    // Refresh stats after action (for modal)
    setTimeout(() => {
        sendCommand({
            method: 'STATS',
            obj: currentModalObjId
        });
    }, 500);
}

function addScore() {
    if (!currentModalObjId) return;

    const teamSelect = document.getElementById('scoreTeam');
    const points = parseInt(document.getElementById('scorePoints').value) || 1;
    const player = document.getElementById('scorePlayer').value.trim() || null;
    const teamName = teamSelect.value;

    // Find team ID from team name (team description format: "Team: <name>")
    const team = data.teams.find(t => {
        // Extract team name from description (format: "Team: <name>")
        const descName = t.description.replace('Team: ', '').trim();
        return descName === teamName;
    });

    if (!team) {
        showNotification('Team not found', 'error');
        return;
    }

    sendCommand({
        method: 'SCORE',
        obj: currentModalObjId,
        team: team.id,
        points: points,
        player: player
    });

    // Clear form
    document.getElementById('scorePoints').value = '1';
    document.getElementById('scorePlayer').value = '';

    // Refresh stats after scoring
    setTimeout(() => {
        sendCommand({
            method: 'STATS',
            obj: currentModalObjId
        });
    }, 500);
}

function closeGameModal() {
    document.getElementById('gameModal').style.display = 'none';
    currentModalObjId = null;
}

window.onclick = function (event) {
    const modal = document.getElementById('gameModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Initialize connection when page loads
connect();