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
    count=int(getattr(event,"count",0) or 0)
    if count <= 0: return
    count=min(count,10000)
    item=likes_scores.setdefault(uid,{"name":name,"coins":0})
    item["name"]=name
    item["coins"]+=count
    likes_state["top"]=sorted(likes_scores.values(),key=lambda x:-x["coins"])[:5]
    likes_state["last_like"]={"name":name,"count":count}

async def loop():
    await asyncio.sleep(2)
    while True:
        try:
            state.update(status="connecting",message="Подключение к TikTok...")
            await client.start(fetch_gift_info=True)
        except asyncio.CancelledError: raise
        except Exception as e:
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

async def likes_page(request): return web.Response(text=LIKES_HTML,content_type="text/html")
async def likes_api(request):
    r=web.json_response({"status":state["status"],"top":likes_state["top"],"last_like":likes_state["last_like"]})
    r.headers["Cache-Control"]="no-store"
    return r


RESTORED_GIFTS_HTML=HTML.replace('</head>','<style>.shell{border-radius:25px!important;background:linear-gradient(115deg,#00edff,#742dff,#ff299d,#00f5cd,#00edff)!important;background-size:400% 400%!important;animation:rgb 7s linear infinite!important;box-shadow:0 0 20px #00eaff8f,0 0 40px #fa20c78e!important;border:0!important;filter:none!important;padding:4px!important}.inside{background:linear-gradient(130deg,rgba(7,12,37,.83),rgba(29,10,49,.79))!important;border-radius:21px!important}.rank{border:1px solid #b8e9ff88!important;border-radius:14px!important;background:rgba(19,25,55,.86)!important;box-shadow:0 0 12px #792cff50,inset 0 0 10px #00eaff22!important}.rank:first-child{border:1px solid #ffe18b!important;box-shadow:0 0 13px #ffd36c77!important}.rank:before{display:block!important}.name,.num{color:white!important;text-shadow:0 2px 3px #000!important}.line{background:linear-gradient(90deg,#00edff,#ff3ace,#7d4cff)!important;box-shadow:0 0 12px #fc37db!important}</style></head>')
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
