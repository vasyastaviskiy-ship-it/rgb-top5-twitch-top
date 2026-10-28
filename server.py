import asyncio, os, time
from aiohttp import web
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent, GiftEvent, LikeEvent

USER=os.environ.get("TIKTOK_USERNAME","twitch_top").lstrip("@")
PORT=int(os.environ.get("PORT","10000"))
state={"status":"starting","message":"Ожидание","top":[],"last_gift":None}
scores={}
likes_scores={}
likes_state={"top":[],"last_like":None}
client=TikTokLiveClient(unique_id="@"+USER)

@client.on(ConnectEvent)
async def connected(event):
    state.update(status="connected",message="TikTok подключен")
    print("CONNECTED @"+USER,flush=True)

@client.on(DisconnectEvent)
async def disconnected(event):
    state.update(status="disconnected",message="Эфир отключен")

@client.on(GiftEvent)
async def gift(event):
    g=getattr(event,"gift",None)
    if g is None or getattr(event,"streaking",False): return
    price=int(getattr(g,"diamond_count",0) or getattr(getattr(g,"info",None),"diamond_count",0) or 0)
    if price<=0: return
    count=max(1,int(getattr(event,"repeat_count",1) or 1))
    u=getattr(event,"user",None)
    uid=str(getattr(u,"unique_id","") or getattr(u,"nickname","Зритель"))
    name=str(getattr(u,"nickname","") or uid)
    item=scores.setdefault(uid,{"name":name,"coins":0})
    item["name"]=name
    item["coins"]+=price*count
    state["top"]=sorted(scores.values(),key=lambda x:-x["coins"])[:5]
    state["last_gift"]={"name":name,"gift":str(getattr(g,"name","Подарок")),"coins":price*count}
    print("GIFT",name,price*count,flush=True)

@client.on(LikeEvent)
async def like(event):
    u=getattr(event,"user",None)
    uid=str(getattr(u,"unique_id","") or getattr(u,"nickname","Зритель"))
    name=str(getattr(u,"nickname","") or uid)
    # LikeEvent.count is the increment for this event, not the livestream total.
    count=int(getattr(event,"count",0) or getattr(event,"like_count",0) or 0)
    print("LIKE_EVENT",name,"count=",count,flush=True)
    if count <= 0: return
    count=min(count,10000)
    item=likes_scores.setdefault(uid,{"name":name,"coins":0})
    item["name"]=name
    item["coins"]+=count
    likes_state["top"]=sorted(likes_scores.values(),key=lambda x:-x["coins"])[:5]
    likes_state["last_like"]={"name":name,"count":count}
    print("LIKE_TOP",likes_state["top"],flush=True)

async def loop():
    await asyncio.sleep(2)
    while True:
        try:
            state.update(status="connecting",message="Подключение к TikTok...")
            await client.start(fetch_gift_info=True)
        except asyncio.CancelledError: raise
        except Exception as e:
            if type(e).__name__ == "AlreadyConnectedError":
                # The existing TikTok connection is alive; do not call start again.
                state.update(status="connected",message="TikTok подключен")
                print("TikTok connection already active; keeping it",flush=True)
                await asyncio.Event().wait()
            state.update(status="error",message=(type(e).__name__+": "+str(e))[:180])
            print("TikTok error",repr(e),flush=True)
        await asyncio.sleep(15)

async def startup(app): app["worker"]=asyncio.create_task(loop())
async def cleanup(app):
    app["worker"].cancel()
    await asyncio.gather(app["worker"],return_exceptions=True)

HTML=r"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>
*{box-sizing:border-box}html,body{margin:0;background:transparent;color:white;font-family:Arial,sans-serif;overflow:hidden}body{padding:26px}.shell{width:460px;padding:4px;border-radius:25px;background:linear-gradient(120deg,#00eeff,#ba23ff,#ff2892,#04ffc3,#00eeff);background-size:400% 400%;animation:rgb 7s linear infinite;box-shadow:0 0 26px #b825ff99,0 0 44px #00ecff65}.inside{background:linear-gradient(130deg,#0b0f2abd,#17133299);border-radius:21px;padding:23px 19px 20px;backdrop-filter:blur(3px)}header{display:flex;justify-content:space-between;align-items:center}.eyebrow{font-weight:900;font-size:11px;letter-spacing:3px;color:#63f1ff}.title{font-weight:1000;font-size:32px;margin-top:8px;text-shadow:0 0 25px #c439ff}.title span{color:#4df1ff}.live{font-size:11px;border:1px solid #f25c9e;border-radius:30px;padding:7px;color:#ff9dc4}.line{height:2px;background:linear-gradient(90deg,#00f0ff,#f152ff,#ff3e95);box-shadow:0 0 18px #00fff0;margin:16px 0}.rank{margin:9px 0;padding:12px;display:flex;gap:12px;align-items:center;background:#17203e9e;border:1px solid #ffffff35;border-radius:14px;position:relative;overflow:hidden;min-height:63px;animation:enter .3s ease}.rank:before{content:"";position:absolute;inset:0 auto 0 0;width:4px;background:var(--c);box-shadow:0 0 15px var(--c)}.pos{width:37px;text-align:center;font-size:23px;font-weight:900;color:var(--c);text-shadow:0 0 15px var(--c)}.who{flex:1;min-width:0}.name{font-size:16px;font-weight:900;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.sub{font-size:10px;color:#aabbd8;margin-top:4px}.num{text-align:right;font-size:18px;font-weight:900;color:#e2feff}.num small{display:block;font-size:10px;color:#98a9d0;letter-spacing:1px;margin-top:4px}.foot{display:flex;justify-content:space-between;font-size:11px;color:#aac4db;margin-top:15px;gap:10px}.foot b{color:#79faff}#recent{overflow:hidden;white-space:nowrap;text-overflow:ellipsis;max-width:270px}@keyframes rgb{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}@keyframes enter{from{transform:translateX(-12px);opacity:.2}to{transform:translateX(0);opacity:1}}
.inside{background:linear-gradient(135deg,rgba(4,7,24,.93),rgba(10,7,29,.91))!important}.rank{background:rgba(4,9,26,.91)!important;border:1px solid rgba(160,228,255,.55)!important;min-height:75px!important;padding:15px 13px!important;box-shadow:inset 0 0 13px rgba(0,225,255,.10),0 3px 10px rgba(0,0,0,.5)}.name{font-size:21px!important;color:#fff!important;font-weight:1000!important;text-shadow:0 2px 2px #000,0 0 9px #000,0 0 3px #000!important}.num{font-size:23px!important;color:#fff!important;text-shadow:0 2px 3px #000,0 0 8px #000!important}.sub,.num small{color:#e2e8ff!important;font-size:11px!important;text-shadow:0 2px 3px #000}.pos{font-size:27px!important}.title{text-shadow:0 3px 4px #000,0 0 18px #9438ff!important}.eyebrow,.foot{color:#f4f7ff!important;text-shadow:0 1px 4px #000}header{gap:10px}/* Transparent TikTok overlays, visible on gameplay */
html,body{background:transparent!important}
.shell{background:transparent!important;box-shadow:none!important;padding:4px!important;border:2px solid rgba(85,244,255,.82)!important;filter:drop-shadow(0 0 9px rgba(122,62,255,.8));animation:none!important}
.inside{background:transparent!important;backdrop-filter:none!important}
.rank{background:rgba(0,0,0,.10)!important;border:1px solid rgba(130,225,255,.75)!important;box-shadow:0 0 9px rgba(70,230,255,.36)!important}
.name,.num,.title{paint-order:stroke fill;-webkit-text-stroke:1px rgba(0,0,0,.9);text-shadow:1px 2px 1px #000,0 0 9px #000!important}
.name{font-size:22px!important}.num{font-size:23px!important}
.eyebrow,.sub,.foot,.num small{color:white!important;text-shadow:0 0 6px black,1px 1px 2px black!important}
</style></head><body><div class="shell"><div class="inside"><header><div><div class="eyebrow">TWITCH_TOP · RGB GAMING</div><div class="title">TOP <span>5</span> GIFTERS</div></div><div class="live">● LIVE</div></header><div class="line"></div><div id="list"></div><div class="foot"><span id="recent">Ждём подарков…</span><b id="status">● ПОДКЛЮЧЕНИЕ</b></div></div></div><script>
const colors=['#ffd76a','#bde8ff','#ffa868','#9e8dff','#62ffe1'],medals=['👑','②','③','④','⑤'];
const demo=new URLSearchParams(location.search).has('demo');
function render(top){let list=document.getElementById('list');list.innerHTML='';for(let i=0;i<5;i++){let u=top[i]||{name:'Свободное место',coins:0};let el=document.createElement('div');el.className='rank';el.style.setProperty('--c',colors[i]);let p=document.createElement('div');p.className='pos';p.textContent=medals[i];let who=document.createElement('div');who.className='who';let name=document.createElement('div');name.className='name';name.textContent=u.name;let sub=document.createElement('div');sub.className='sub';sub.textContent=i===0?'ЛИДЕР ЭФИРА':'ПОДАРКИ ЗА ЭФИР';who.append(name,sub);let num=document.createElement('div');num.className='num';num.textContent=Number(u.coins||0).toLocaleString('ru-RU');let small=document.createElement('small');small.textContent='💎 МОНЕТ';num.append(small);el.append(p,who,num);list.append(el)}}
if(demo){render([{name:'DiamondKing',coins:12450},{name:'NeonQueen',coins:8420},{name:'MinecraftPro',coins:5100},{name:'Alex',coins:2500},{name:'Steve',coins:960}]);document.getElementById('status').textContent='● ДЕМО';}
else{render([]);let lastTop='[]';async function poll(){try{const r=await fetch('/api/state',{cache:'no-store'});let s=await r.json();const nextTop=JSON.stringify(s.top||[]);if(nextTop!==lastTop){render(s.top||[]);lastTop=nextTop;}document.getElementById('status').textContent=s.status==='connected'?'● TIKTOK LIVE':'● '+(s.status||'WAIT').toUpperCase();if(s.last_gift)document.getElementById('recent').textContent=s.last_gift.name+' · '+s.last_gift.gift+' 💎 '+s.last_gift.coins;}catch(e){document.getElementById('status').textContent='● ОШИБКА СВЯЗИ'}}poll();setInterval(poll,2000);}
</script></body></html>"""

LIKES_HTML=(HTML.replace("TOP <span>5</span> GIFTERS","TOP <span>5</span> LIKES")
 .replace("💎 МОНЕТ","❤️ ЛАЙКОВ")
 .replace("ПОДАРКИ ЗА ЭФИР","ЛАЙКИ ЗА ЭФИР")
 .replace("Ждём подарков…","Ждём лайков…")
 .replace("'/api/state'","'/api/likes-state'")
 .replace("s.last_gift.name+' · '+s.last_gift.gift+' 💎 '+s.last_gift.coins","s.last_like.name+' · ❤️ '+s.last_like.count")
 .replace("if(s.last_gift)","if(s.last_like)")
 .replace("DiamondKing","LikeMaster")
 .replace("NeonQueen","HeartQueen"))

CLEAN_CSS = """<style>
html,body{background:transparent!important;color:#fff!important}
body{padding:12px!important}
.shell{width:460px!important;background:transparent!important;border:0!important;box-shadow:none!important;filter:none!important;padding:0!important;animation:none!important;border-radius:0!important}
.inside{background:transparent!important;backdrop-filter:none!important;padding:8px!important;border-radius:0!important}
.eyebrow{color:#fff!important;font-size:12px!important;letter-spacing:1px!important}
.title{font-size:28px!important;color:white!important;text-shadow:0 2px 3px #000!important}
.title span{color:white!important}
.line{height:1px!important;background:rgba(255,255,255,.8)!important;box-shadow:none!important;margin:10px 0!important}
.live{border:1px solid #fff!important;color:#fff!important}
.rank{background:transparent!important;border:0!important;border-bottom:1px solid rgba(255,255,255,.45)!important;border-radius:0!important;box-shadow:none!important;animation:none!important;min-height:58px!important;padding:9px!important;margin:4px 0!important}
.rank:before{display:none!important}
.pos{font-size:22px!important;color:white!important;text-shadow:0 2px 3px #000!important}
.name{font-size:21px!important;color:white!important;font-weight:800!important;text-shadow:0 2px 3px black,1px 1px 2px black!important}
.num{font-size:22px!important;color:white!important;text-shadow:0 2px 3px black!important}
.num small,.sub,.foot{color:white!important;text-shadow:0 2px 3px black!important}
</style>"""
# CSS appended after the existing page CSS so clean style wins; remove emoji leader color via CSS.
def clean(html):
    return html.replace("</head>",CLEAN_CSS+"</head>")
CLEAN_LIKES_HTML=clean(LIKES_HTML)
CLEAN_GIFTS_HTML=clean(HTML)

MINECRAFT_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
html,body{background:transparent!important;overflow:hidden!important}
body{padding:18px!important}
.shell{width:480px!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;filter:none!important;animation:none!important;padding:0!important}
.inside{padding:15px!important;border-radius:0!important;background:transparent!important;backdrop-filter:none!important}
.eyebrow{font-family:monospace!important;color:#aeff97!important;font-size:12px!important;letter-spacing:1px!important;text-shadow:2px 2px #162b10!important}
.title{font-family:'Press Start 2P',monospace!important;color:#fff!important;font-size:19px!important;line-height:1.6!important;text-shadow:3px 3px #202020!important}
.title span{color:#79fc61!important}
.live{border:3px solid #ffd36a!important;border-radius:0!important;background:#3d2919d9!important;color:#fff8d4!important;box-shadow:3px 3px #241806!important}
.line{height:5px!important;background:repeating-linear-gradient(90deg,#529839 0px,#529839 18px,#80582c 18px,#80582c 35px)!important;box-shadow:none!important;margin:13px 0!important}
.rank{background:rgba(24,26,19,.69)!important;border:3px solid #7d9469!important;border-radius:0!important;box-shadow:inset 3px 3px #b6c4a1,inset -3px -3px #394831,3px 3px #0009!important;animation:none!important;min-height:69px!important;padding:10px!important;margin:7px 0!important}
.rank:before{display:none!important}
.rank:first-child{border-color:#e6bf5e!important;box-shadow:inset 3px 3px #fff0a1,inset -3px -3px #8b6624,3px 3px #000a!important}
.pos{font-family:monospace!important;font-size:22px!important;color:#ffd968!important;text-shadow:2px 2px #17130a!important}
.name{font-family:monospace!important;font-size:19px!important;font-weight:900!important;color:white!important;text-shadow:2px 2px #000!important}
.num{font-family:monospace!important;font-size:20px!important;font-weight:900!important;color:#93ff9a!important;text-shadow:2px 2px #000!important}
.num small,.sub{font-family:monospace!important;color:#e8fbe2!important;text-shadow:1px 1px #000!important}
.foot{font-family:monospace!important;color:white!important;text-shadow:2px 2px #000!important}
</style>"""
def minecraft_style(html):
    return html.replace("</head>",MINECRAFT_CSS+"</head>")
MINECRAFT_LIKES_HTML=minecraft_style(LIKES_HTML)
MINECRAFT_GIFTS_HTML=minecraft_style(HTML)
async def minecraft_likes(request): return web.Response(text=MINECRAFT_LIKES_HTML,content_type="text/html")
async def minecraft_gifts(request): return web.Response(text=MINECRAFT_GIFTS_HTML,content_type="text/html")

async def clean_likes_page(request): return web.Response(text=CLEAN_LIKES_HTML,content_type="text/html")
async def clean_gifts_page(request): return web.Response(text=CLEAN_GIFTS_HTML,content_type="text/html")

LIKES_GAMING_HTML = "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>RGB TOP 5 LIKES · twitch_top</title><style>\n*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:transparent;color:#fff;font-family:Inter,'Segoe UI',Arial,sans-serif;overflow:hidden}body{display:flex;align-items:flex-start;justify-content:flex-start;padding:28px}.wrap{width:475px;position:relative;filter:drop-shadow(0 12px 25px #0008)}.shell{position:relative;padding:4px;border-radius:26px;background:linear-gradient(115deg,#00f7ff,#a000ff,#ff238f,#03ffa6,#00f7ff);background-size:380% 380%;animation:hue 8s linear infinite;isolation:isolate}.shell:before{content:\"\";position:absolute;inset:-8px;border-radius:30px;z-index:-1;background:inherit;filter:blur(18px);opacity:.8}.inside{background:linear-gradient(145deg,rgba(12,13,32,.98),rgba(16,8,38,.97));border-radius:23px;padding:22px 21px 21px;overflow:hidden;position:relative}.inside:after{content:\"\";position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 25px,#ffffff06 26px);pointer-events:none}.line{height:3px;width:100%;background:linear-gradient(90deg,transparent,#5cfbff,#ec4cff,transparent);margin:13px 0 17px;box-shadow:0 0 17px #29e7ff}.topline{display:flex;align-items:center;justify-content:space-between;gap:8px}.eyebrow{font-weight:800;letter-spacing:3px;color:#6beeff;font-size:11px}.title{font-size:34px;letter-spacing:1px;font-weight:1000;line-height:1.13;text-shadow:0 0 24px #ab49ff}.title b{background:linear-gradient(90deg,#69f3ff,#d775ff,#ff69c7);color:transparent;background-clip:text}.live{padding:6px 9px;background:#ff187526;border:1px solid #ff348c7a;color:#ff81b7;font-size:11px;font-weight:900;letter-spacing:1px;border-radius:25px}.live:before{content:\"\";display:inline-block;width:7px;height:7px;background:#ff4a9b;border-radius:50%;margin-right:6px;box-shadow:0 0 9px #ff249c;animation:blink 1.3s ease-in-out infinite}.subtitle{font-size:11px;color:#9db6d0;letter-spacing:2px;margin-top:5px}.rank{position:relative;display:flex;align-items:center;gap:12px;min-height:68px;margin:9px 0;border-radius:15px;border:1px solid #ffffff17;background:linear-gradient(90deg,#263050c9,#171b35dd);overflow:hidden;padding:10px 13px;transition:transform .35s,box-shadow .35s}.rank:before{position:absolute;content:\"\";width:3px;inset:0 auto 0 0;background:var(--accent);box-shadow:0 0 18px var(--accent)}.rank:first-child{min-height:90px;background:linear-gradient(90deg,#4c3550,#2b2444);border-color:#f8d97b6a;box-shadow:inset 0 0 19px #ffc05218,0 0 25px #ffc52a15}.rank:nth-child(2){border-color:#b1ddff47}.rank:nth-child(3){border-color:#ffa97640}.medal{display:flex;align-items:center;justify-content:center;flex-shrink:0;width:43px;height:43px;border-radius:12px;color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 48%,transparent);background:color-mix(in srgb,var(--accent) 11%,transparent);font-size:22px;font-weight:1000;text-shadow:0 0 15px var(--accent)}.rank:first-child .medal{width:55px;height:55px;font-size:29px}.details{min-width:0;flex:1}.name{font-size:17px;font-weight:900;max-width:232px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap}.rank:first-child .name{font-size:20px}.minor{font-size:10px;color:#98a5bd;letter-spacing:1.3px;margin-top:3px}.points{text-align:right;flex-shrink:0}.amount{font-weight:1000;font-size:22px;color:#fff;text-shadow:0 0 16px var(--accent)}.rank:first-child .amount{font-size:28px}.coins{font-size:10px;letter-spacing:1.3px;color:#a7aecd;margin-top:3px}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:17px;font-size:12px;color:#a7b3d9}.brand{font-weight:900;color:#b684ff;letter-spacing:1px}.status{display:flex;align-items:center;gap:6px;max-width:270px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap}.dot{width:8px;height:8px;border-radius:100%;background:#ffad3b;box-shadow:0 0 10px currentColor;flex-shrink:0}.dot.online{background:#4affb7}.dot.offline{background:#ff577f}.lower{font-size:10px;color:#8191ac;letter-spacing:1px;margin-top:10px;text-align:center} @keyframes hue{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}@keyframes blink{50%{opacity:.35}}@keyframes enter{from{opacity:0;transform:translateX(35px) scale(.95)}to{opacity:1;transform:translateX(0) scale(1)}}.rank.bump{animation:enter .55s cubic-bezier(.2,1.4,.4,1)}.glow{position:absolute;width:130px;height:130px;right:-40px;top:-50px;background:#bc34ff22;filter:blur(32px);pointer-events:none}\nbody{padding:36px!important;overflow:hidden!important}html,body{scrollbar-width:none!important}html::-webkit-scrollbar,body::-webkit-scrollbar{display:none!important}.wrap{margin-bottom:80px!important}.shell{background:linear-gradient(115deg,#ff34a6,#732dff,#00eaff,#ff34a6)!important;background-size:380% 380%!important;animation:hue 5s linear infinite!important}</style></head><body><div class=\"wrap\"><div class=\"shell\"><div class=\"inside\"><div class=\"glow\"></div><div class=\"topline\"><div><div class=\"eyebrow\">✦ TWITCH_TOP • COMMUNITY</div><div class=\"title\">TOP <b>5 LIKES</b></div></div><div class=\"live\">LIVE</div></div><div class=\"subtitle\">RGB LEGENDS • ЛИДЕРЫ ПО ЛАЙКАМ</div><div class=\"line\"></div><div id=\"list\"></div><div class=\"footer\"><span class=\"brand\">✧ @twitch_top</span><span class=\"status\"><i id=\"dot\" class=\"dot\"></i><span id=\"status\">Ожидание...</span></span></div><div class=\"lower\">✦ THANK YOU FOR YOUR SUPPORT ✦</div></div></div></div><script>\nconst demo=new URLSearchParams(location.search).has('demo');const demoUsers=[{name:'DiamondKing',coins:15620},{name:'NightWolf',coins:8140},{name:'AlexCraft',coins:4250},{name:'LunaPlay',coins:2180},{name:'Steve_777',coins:990}];const cols=['#ff4fb5','#86eaff','#ce79ff','#ff98cf','#62ffe0'];let old='';\nfunction render(users){const arr=Array.from({length:5},(_,i)=>users[i]||{name:'Свободное место',coins:0});let signature=JSON.stringify(arr);if(signature===old)return;old=signature;const list=document.getElementById('list');list.replaceChildren();arr.forEach((user,i)=>{const rank=document.createElement('div');rank.className='rank bump';rank.style.setProperty('--accent',cols[i]);const medal=document.createElement('div');medal.className='medal';medal.textContent=i===0?'♛':String(i+1).padStart(2,'0');const details=document.createElement('div');details.className='details';const name=document.createElement('div');name.className='name';name.textContent=user.name||user.username||'Зритель';const minor=document.createElement('div');minor.className='minor';minor.textContent=i===0?'♥ HEART CHAMPION':i===1?'♥ TOP FAN':i===2?'♥ SUPPORTER':'♥ SUPPORTER';details.append(name,minor);const points=document.createElement('div');points.className='points';const amount=document.createElement('div');amount.className='amount';amount.textContent=Number(user.coins||0).toLocaleString('ru-RU');const coins=document.createElement('div');coins.className='coins';coins.textContent='♥ ЛАЙКОВ';points.append(amount,coins);rank.append(medal,details,points);list.append(rank)})}\nfunction status(msg,online){document.getElementById('status').textContent=msg;document.getElementById('dot').className='dot '+(online===true?'online':online===false?'offline':'')}\nasync function poll(){if(demo){render(demoUsers);status('ДЕМО • тестовые данные',null);return}try{const r=await fetch('/api/likes-state',{cache:'no-store'});if(!r.ok)throw Error('Сервер недоступен');const data=await r.json();render(data.top||[]);status(({connected:'TIKTOK ПОДКЛЮЧЕН',connecting:'ПОДКЛЮЧЕНИЕ...',starting:'ЗАПУСК...',disconnected:'НЕТ СОЕДИНЕНИЯ',error:'ОШИБКА СОЕДИНЕНИЯ'})[data.status]||'ОЖИДАНИЕ',data.status==='connected'?true:data.status==='error'||data.status==='disconnected'?false:null)}catch(err){render([]);status('НЕТ СОЕДИНЕНИЯ С СЕРВЕРОМ',false)}}poll();setInterval(poll,1500);\n</script></body></html>"
async def likes_page(request): return web.Response(text=LIKES_GAMING_HTML,content_type="text/html")
async def likes_api(request):
    r=web.json_response({"status":state["status"],"top":likes_state["top"],"last_like":likes_state["last_like"]})
    r.headers["Cache-Control"]="no-store"
    return r


# Keep the original RGB visual CSS and discard conflicting transparent variants.
# Gift leaderboard has its own isolated RGB style; other routes are unchanged.
_ORIGINAL_CSS = HTML.split("<style>", 1)[1].split("\n.inside{background:linear-gradient(135deg", 1)[0]
_CURRENT_CSS = HTML.split("<style>", 1)[1].split("</style>", 1)[0]
_RGB_GAMING_CSS = """
html,body{background:transparent!important;overflow:hidden!important;scrollbar-width:none!important}
html::-webkit-scrollbar,body::-webkit-scrollbar{display:none!important}
body{padding:32px!important}
.shell{position:relative!important;width:460px!important;padding:5px!important;border:0!important;border-radius:25px!important;overflow:visible!important;background:linear-gradient(105deg,#00f5ff,#8c27ff,#ff1b93,#11ffb5,#00f5ff)!important;background-size:450% 450%!important;animation:rgbGamingMove 3s linear infinite!important;box-shadow:0 0 12px 3px #00eaffcc,0 0 23px 5px #a028ff99,0 0 32px 6px #ff289177!important;filter:none!important}
.shell:before,.shell:after{display:none!important}
.inside{background:#101329!important;backdrop-filter:none!important;border-radius:20px!important;padding:22px 19px 20px!important}
.rank{background:#202845!important;border:1px solid #7889b44a!important;min-height:73px!important}
.rank:first-child{background:#34283b!important}
.name{font-size:21px!important;font-weight:900!important;color:white!important;text-shadow:0 2px 4px black!important}
.num{font-size:23px!important;color:white!important;text-shadow:0 2px 4px black!important}
@keyframes rgbGamingMove{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
"""
_FULL_HEIGHT_CSS = """
/* Leave sufficient canvas space for all five rows and the neon glow. */
html,body{height:auto!important;min-height:780px!important;overflow:visible!important}
body{padding:36px 36px 100px!important}
.shell{margin-bottom:65px!important}
"""
_VISIBLE_NEON_CSS = """
/* Animate actual outer light, not only gradient position. */
@keyframes rgbGlowPulse {
  0%,100% {box-shadow:0 0 16px 5px #00f5ffee,0 0 38px 10px #00eaffaa,0 0 54px 14px #8c27ff88}
  33% {box-shadow:0 0 16px 5px #ff1b93ee,0 0 38px 10px #ff1b93aa,0 0 54px 14px #00f5ff88}
  66% {box-shadow:0 0 16px 5px #9b33ffee,0 0 38px 10px #8c27ffaa,0 0 54px 14px #11ffb588}
}
.shell{animation:rgbGamingMove 3s linear infinite,rgbGlowPulse 3s linear infinite!important}
"""
RESTORED_GIFTS_HTML = "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>RGB TOP 5 · twitch_top</title><style>\n*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:transparent;color:#fff;font-family:Inter,'Segoe UI',Arial,sans-serif;overflow:hidden}body{display:flex;align-items:flex-start;justify-content:flex-start;padding:28px}.wrap{width:475px;position:relative;filter:drop-shadow(0 12px 25px #0008)}.shell{position:relative;padding:4px;border-radius:26px;background:linear-gradient(115deg,#00f7ff,#a000ff,#ff238f,#03ffa6,#00f7ff);background-size:380% 380%;animation:hue 8s linear infinite;isolation:isolate}.shell:before{content:\"\";position:absolute;inset:-8px;border-radius:30px;z-index:-1;background:inherit;filter:blur(18px);opacity:.8}.inside{background:linear-gradient(145deg,rgba(12,13,32,.98),rgba(16,8,38,.97));border-radius:23px;padding:22px 21px 21px;overflow:hidden;position:relative}.inside:after{content:\"\";position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 25px,#ffffff06 26px);pointer-events:none}.line{height:3px;width:100%;background:linear-gradient(90deg,transparent,#5cfbff,#ec4cff,transparent);margin:13px 0 17px;box-shadow:0 0 17px #29e7ff}.topline{display:flex;align-items:center;justify-content:space-between;gap:8px}.eyebrow{font-weight:800;letter-spacing:3px;color:#6beeff;font-size:11px}.title{font-size:34px;letter-spacing:1px;font-weight:1000;line-height:1.13;text-shadow:0 0 24px #ab49ff}.title b{background:linear-gradient(90deg,#69f3ff,#d775ff,#ff69c7);color:transparent;background-clip:text}.live{padding:6px 9px;background:#ff187526;border:1px solid #ff348c7a;color:#ff81b7;font-size:11px;font-weight:900;letter-spacing:1px;border-radius:25px}.live:before{content:\"\";display:inline-block;width:7px;height:7px;background:#ff4a9b;border-radius:50%;margin-right:6px;box-shadow:0 0 9px #ff249c;animation:blink 1.3s ease-in-out infinite}.subtitle{font-size:11px;color:#9db6d0;letter-spacing:2px;margin-top:5px}.rank{position:relative;display:flex;align-items:center;gap:12px;min-height:68px;margin:9px 0;border-radius:15px;border:1px solid #ffffff17;background:linear-gradient(90deg,#263050c9,#171b35dd);overflow:hidden;padding:10px 13px;transition:transform .35s,box-shadow .35s}.rank:before{position:absolute;content:\"\";width:3px;inset:0 auto 0 0;background:var(--accent);box-shadow:0 0 18px var(--accent)}.rank:first-child{min-height:90px;background:linear-gradient(90deg,#4c3550,#2b2444);border-color:#f8d97b6a;box-shadow:inset 0 0 19px #ffc05218,0 0 25px #ffc52a15}.rank:nth-child(2){border-color:#b1ddff47}.rank:nth-child(3){border-color:#ffa97640}.medal{display:flex;align-items:center;justify-content:center;flex-shrink:0;width:43px;height:43px;border-radius:12px;color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 48%,transparent);background:color-mix(in srgb,var(--accent) 11%,transparent);font-size:22px;font-weight:1000;text-shadow:0 0 15px var(--accent)}.rank:first-child .medal{width:55px;height:55px;font-size:29px}.details{min-width:0;flex:1}.name{font-size:17px;font-weight:900;max-width:232px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap}.rank:first-child .name{font-size:20px}.minor{font-size:10px;color:#98a5bd;letter-spacing:1.3px;margin-top:3px}.points{text-align:right;flex-shrink:0}.amount{font-weight:1000;font-size:22px;color:#fff;text-shadow:0 0 16px var(--accent)}.rank:first-child .amount{font-size:28px}.coins{font-size:10px;letter-spacing:1.3px;color:#a7aecd;margin-top:3px}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:17px;font-size:12px;color:#a7b3d9}.brand{font-weight:900;color:#b684ff;letter-spacing:1px}.status{display:flex;align-items:center;gap:6px;max-width:270px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap}.dot{width:8px;height:8px;border-radius:100%;background:#ffad3b;box-shadow:0 0 10px currentColor;flex-shrink:0}.dot.online{background:#4affb7}.dot.offline{background:#ff577f}.lower{font-size:10px;color:#8191ac;letter-spacing:1px;margin-top:10px;text-align:center} @keyframes hue{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}@keyframes blink{50%{opacity:.35}}@keyframes enter{from{opacity:0;transform:translateX(35px) scale(.95)}to{opacity:1;transform:translateX(0) scale(1)}}.rank.bump{animation:enter .55s cubic-bezier(.2,1.4,.4,1)}.glow{position:absolute;width:130px;height:130px;right:-40px;top:-50px;background:#bc34ff22;filter:blur(32px);pointer-events:none}\nhtml,body{height:auto!important;min-height:900px!important;overflow-x:hidden!important;overflow-y:hidden!important;scrollbar-width:none!important}html::-webkit-scrollbar,body::-webkit-scrollbar{display:none!important}body{padding:36px!important}.wrap{margin-bottom:100px!important}.coin-burst{position:absolute;right:23px;top:5px;font-size:22px;font-weight:900;color:#ffdf72;text-shadow:0 0 14px #ffc324;pointer-events:none;z-index:5;animation:coinFloat 1.1s ease-out forwards}.coin-flash{animation:coinFlash .65s ease-out!important}@keyframes coinFloat{0%{opacity:0;transform:translateY(14px) scale(.7)}25%{opacity:1}100%{opacity:0;transform:translateY(-45px) scale(1.3)}}@keyframes coinFlash{0%{box-shadow:0 0 0 #ffd35b}40%{box-shadow:0 0 23px #ffd35bbb,inset 0 0 10px #ffc5424d}100%{box-shadow:0 0 0 #ffd35b}}</style></head><body><div class=\"wrap\"><div class=\"shell\"><div class=\"inside\"><div class=\"glow\"></div><div class=\"topline\"><div><div class=\"eyebrow\">✦ TWITCH_TOP • COMMUNITY</div><div class=\"title\">TOP <b>5 GIFTERS</b></div></div><div class=\"live\">LIVE</div></div><div class=\"subtitle\">RGB LEGENDS • ЛИДЕРЫ ПО ПОДАРКАМ</div><div class=\"line\"></div><div id=\"list\"></div><div class=\"footer\"><span class=\"brand\">✧ @twitch_top</span><span class=\"status\"><i id=\"dot\" class=\"dot\"></i><span id=\"status\">Ожидание...</span></span></div><div class=\"lower\">✦ THANK YOU FOR YOUR SUPPORT ✦</div></div></div></div><script>\nconst demo=new URLSearchParams(location.search).has('demo');const demoUsers=[{name:'DiamondKing',coins:15620},{name:'NightWolf',coins:8140},{name:'AlexCraft',coins:4250},{name:'LunaPlay',coins:2180},{name:'Steve_777',coins:990}];const cols=['#ffcf69','#a2dfff','#ffad7d','#bc8cff','#5affd4'];let old='';\nconst fmt=n=>Math.round(n).toLocaleString('ru-RU');\nfunction animateAmount(el,from,to){cancelAnimationFrame(el._raf);const started=performance.now(),duration=850;function step(t){const p=Math.min(1,(t-started)/duration),ease=1-Math.pow(1-p,3);el.textContent=fmt(from+(to-from)*ease);if(p<1)el._raf=requestAnimationFrame(step);else el.textContent=fmt(to)}el._raf=requestAnimationFrame(step)}\nfunction coinBurst(rank){const fx=document.createElement('div');fx.className='coin-burst';fx.textContent='🪙 +';rank.append(fx);setTimeout(()=>fx.remove(),1150);rank.classList.remove('coin-flash');void rank.offsetWidth;rank.classList.add('coin-flash')}\nfunction render(users){const arr=Array.from({length:5},(_,i)=>users[i]||{name:'Свободное место',coins:0});const list=document.getElementById('list');arr.forEach((user,i)=>{let rank=list.children[i];if(!rank){rank=document.createElement('div');rank.className='rank';rank.style.setProperty('--accent',cols[i]);rank.innerHTML='<div class=\"medal\"></div><div class=\"details\"><div class=\"name\"></div><div class=\"minor\"></div></div><div class=\"points\"><div class=\"amount\"></div><div class=\"coins\">◆ МОНЕТ</div></div>';list.append(rank)}rank.style.setProperty('--accent',cols[i]);const name=user.name||user.username||'Зритель',num=Math.max(0,Number(user.coins)||0);rank.querySelector('.medal').textContent=i===0?'♛':String(i+1).padStart(2,'0');rank.querySelector('.minor').textContent=['★ CHAMPION','◆ ELITE SUPPORTER','✦ TOP SUPPORTER','✧ SUPPORTER','✧ SUPPORTER'][i];const label=rank.querySelector('.name'),amount=rank.querySelector('.amount');if(label.textContent!==name){label.textContent=name;rank._coinValue=undefined}const prev=rank._coinValue;if(prev===undefined){amount.textContent=fmt(num)}else if(prev!==num){animateAmount(amount,prev,num);if(num>prev)coinBurst(rank)}rank._coinValue=num})}\n\nfunction status(msg,online){document.getElementById('status').textContent=msg;document.getElementById('dot').className='dot '+(online===true?'online':online===false?'offline':'')}\nasync function poll(){if(demo){render(demoUsers);status('ДЕМО • тестовые данные',null);return}try{const r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error('Сервер недоступен');const data=await r.json();render(data.top||[]);status(({connected:'TIKTOK ПОДКЛЮЧЕН',connecting:'ПОДКЛЮЧЕНИЕ...',starting:'ЗАПУСК...',disconnected:'НЕТ СОЕДИНЕНИЯ',error:'ОШИБКА СОЕДИНЕНИЯ'})[data.status]||'ОЖИДАНИЕ',data.status==='connected'?true:data.status==='error'||data.status==='disconnected'?false:null)}catch(err){render([]);status('НЕТ СОЕДИНЕНИЯ С СЕРВЕРОМ',false)}}poll();setInterval(poll,1500);\n</script></body></html>"

async def index(request): return web.Response(text=RESTORED_GIFTS_HTML,content_type="text/html")
async def status(request):
    r=web.json_response(state)
    r.headers["Cache-Control"]="no-store"
    return r
app=web.Application()
app.router.add_get("/",index)
app.router.add_get("/api/state",status)
app.router.add_get("/likes",likes_page)
app.router.add_get("/api/likes-state",likes_api)
app.router.add_get("/clean/likes",clean_likes_page)
app.router.add_get("/clean/gifts",clean_gifts_page)
app.router.add_get("/minecraft/likes",minecraft_likes)
app.router.add_get("/minecraft/gifts",minecraft_gifts)
app.on_startup.append(startup)
app.on_cleanup.append(cleanup)
if __name__=="__main__":
    web.run_app(app,host="0.0.0.0",port=PORT)
