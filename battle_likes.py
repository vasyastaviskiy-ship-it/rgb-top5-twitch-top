import os,asyncio
from aiohttp import web
from TikTokLive import TikTokLiveClient
from TikTokLive.events import LikeEvent,ConnectEvent
scores={}
state={"connected":False,"top":[]}
app=web.Application()
client=TikTokLiveClient(unique_id="@"+os.getenv("TIKTOK_USERNAME","twitch_top").lstrip("@"))
@client.on(ConnectEvent)
async def connected(event):
    state["connected"]=True
@client.on(LikeEvent)
async def liked(event):
    user=getattr(event,"user",None)
    key=str(getattr(user,"unique_id","") or getattr(user,"nickname","Viewer"))
    name=str(getattr(user,"nickname","") or key)
    n=int(getattr(event,"count",0) or 0)
    if n<=0:return
    row=scores.setdefault(key,{"name":name,"likes":0})
    row["name"]=name
    row["likes"]+=n
    state["top"]=sorted(scores.values(),key=lambda v:-v["likes"])[:5]
async def connect_loop():
    while True:
        try:
            state["connected"]=False
            await client.start()
        except asyncio.CancelledError: raise
        except Exception as e:
            print("TikTok connection issue:",repr(e),flush=True)
        await asyncio.sleep(20)
async def startup(app):app["job"]=asyncio.create_task(connect_loop())
async def cleanup(app):
    app["job"].cancel()
    await asyncio.gather(app["job"],return_exceptions=True)
HTML="""<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>
*{box-sizing:border-box}html,body{background:transparent;margin:0;color:white;font-family:Arial,sans-serif;overflow:hidden}
body{padding:18px}.panel{width:460px;padding:16px;border:0;background:transparent}
.kicker{font-size:12px;font-weight:900;letter-spacing:3px;color:#64f9ff;text-shadow:0 2px 4px black}
h1{font-weight:1000;font-size:29px;margin:8px 0 12px;text-shadow:0 3px 4px #000}
h1 em{font-style:normal;color:#ff77c7}.track{height:7px;border-radius:6px;background:linear-gradient(90deg,#00f3ff 0 48%,white 48% 52%,#ff259b 52%);margin-bottom:15px}
.item{display:flex;align-items:center;gap:12px;border:2px solid #fff6;background:linear-gradient(110deg,#034957dc,#25163fdc,#811d63d2);margin-bottom:9px;padding:12px;border-radius:14px;box-shadow:0 3px 0 #0006}
.item:first-child{border-color:#ffdf82;background:linear-gradient(110deg,#075a66ed,#5e245bed)}
.rank{width:40px;font-size:23px;font-weight:1000;color:#ffe483;text-shadow:0 2px 3px black}
.name{flex:1;min-width:0;font-size:20px;font-weight:900;text-shadow:0 2px 3px black;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.score{font-weight:1000;font-size:21px;text-align:right;text-shadow:0 2px 3px black}.score small{font-size:10px;display:block;color:#fff}
footer{font-size:12px;color:#fff;text-shadow:0 2px 3px black;margin-top:13px}
</style><div class="panel"><div class="kicker">@TWITCH_TOP • LIVE BATTLE</div><h1>❤️ TOP 5 <em>LIKES</em></h1><div class="track"></div><main id="rows"></main><footer id="status">Ожидание подключения</footer></div>
<script>
const demo=new URLSearchParams(location.search).has('demo');
const examples=[{name:'DiamondKing',likes:15400},{name:'HeartQueen',likes:9100},{name:'Steve',likes:4600},{name:'Alex',likes:2400},{name:'Player',likes:800}];
const main=document.getElementById('rows');let previous='';
function draw(top){main.replaceChildren();for(let i=0;i<5;i++){let u=top[i]||{name:'Ожидание зрителя',likes:0};let row=document.createElement('div');row.className='item';let a=document.createElement('span');a.className='rank';a.textContent=['👑','2','3','4','5'][i];let b=document.createElement('span');b.className='name';b.textContent=u.name;let c=document.createElement('span');c.className='score';c.textContent=Number(u.likes||0).toLocaleString('ru-RU');let sm=document.createElement('small');sm.textContent='❤️ ЛАЙКОВ';c.append(sm);row.append(a,b,c);main.append(row)}}
if(demo){draw(examples);document.getElementById('status').textContent='ДЕМО — тестовые данные';}
else{draw([]);async function poll(){try{let r=await fetch('/state',{cache:'no-store'});let s=await r.json();let json=JSON.stringify(s.top);if(json!==previous){draw(s.top);previous=json;}document.getElementById('status').textContent=s.connected?'● TikTok подключен':'● Ожидание эфира';}catch(e){document.getElementById('status').textContent='Ошибка соединения';}}poll();setInterval(poll,2000);}
</script></html>"""
async def index(request):return web.Response(text=HTML,content_type="text/html")
async def api(request):return web.json_response(state,headers={"Cache-Control":"no-store"})
app.router.add_get("/",index)
app.router.add_get("/state",api)
app.on_startup.append(startup)
app.on_cleanup.append(cleanup)
if __name__=="__main__":web.run_app(app,host="0.0.0.0",port=int(os.getenv("PORT","10000")))
