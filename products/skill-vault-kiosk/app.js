const $=s=>document.querySelector(s);
const grid=$('#grid');
const defaults={price:2,ticketsPerHit:2,ticketCostPer100:0.55,ops:0.20};
let cfg={...defaults,...JSON.parse(localStorage.getItem('sfSkillVault')||'{}')};
let prizes=[
  {id:'sticker-pack',name:'Sticker / collectible pack',tickets:120,wholesaleCents:70},
  {id:'small-plush',name:'Small plush or desk toy',tickets:450,wholesaleCents:250},
  {id:'premium-merch',name:'Premium shelf merchandise',tickets:900,wholesaleCents:525},
  {id:'shelf-choice',name:'Choose-your-prize shelf item',tickets:1800,wholesaleCents:1000}
];
let ownerToken=sessionStorage.getItem('sfSkillVaultOwnerToken')||'';
let serverOnline=false,session=null,running=false,score=0,tickets=0,balance=0,timeLeft=20,active=-1,tickTimer=null,finishTimer=null;
function money(v){return '$'+Number(v).toFixed(2)}
function updateScore(){
  tickets=score*cfg.ticketsPerHit;
  $('#score').textContent=score; $('#tickets').textContent=tickets; $('#balance').textContent=balance;
}
function renderEconomics(){
  $('#playPrice').textContent=money(cfg.price); $('#profitPlayPrice').textContent=money(cfg.price); $('#ticketsPerHit').textContent=cfg.ticketsPerHit;
  const modeledScore=15, avg=(modeledScore*cfg.ticketsPerHit)/100*cfg.ticketCostPer100;
  $('#avgPrizeCost').textContent=money(avg); $('#opsCost').textContent=money(cfg.ops); $('#grossMargin').textContent=money(Math.max(0,cfg.price-avg-cfg.ops));
}
function renderPrizes(){
  $('#prizes').innerHTML=prizes.map(p=>`<div class="prize"><div><strong>${p.name}</strong><small class="fineprint">Est. wholesale ${money((p.wholesaleCents||0)/100)}</small></div><b>${p.tickets} tickets</b></div>`).join('');
}
function buildGrid(){
  grid.innerHTML='';
  for(let i=0;i<16;i++){
    const b=document.createElement('button'); b.className='tile'; b.setAttribute('aria-label','reaction tile'); b.onclick=()=>hit(i,b); grid.appendChild(b);
  }
}
function showTarget(tile){
  [...grid.children].forEach(x=>x.classList.remove('active','wrong'));
  active=Number.isInteger(tile)?tile:-1;
  if(active>=0&&grid.children[active]) grid.children[active].classList.add('active');
}
async function post(url,payload){
  const r=await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)});
  const data=await r.json().catch(()=>({}));
  if(!r.ok) throw Object.assign(new Error(data.error||`HTTP ${r.status}`),{status:r.status,data});
  return data;
}
async function bootstrap(){
  try{
    const r=await fetch('/api/config',{cache:'no-store'}); if(!r.ok) throw new Error('offline'); const data=await r.json();
    serverOnline=true; cfg.price=data.playPriceCents/100; cfg.ticketsPerHit=data.ticketsPerHit; prizes=data.prizes||prizes;
    $('#serverStatus').textContent=data.paymentsEnabled?'Verified server online — payment adapter enabled':'Verified server online — real payments hard-disabled';
    renderEconomics(); renderPrizes();
  }catch{
    serverOnline=false; $('#serverStatus').textContent='Static demo mode — score is not server-verified';
  }
}
function fallbackStart(){
  running=true; score=0; tickets=0; timeLeft=20; updateScore(); $('#startBtn').disabled=true;
  let started=performance.now();
  function pick(){if(!running)return;let n=Math.floor(Math.random()*16);if(n===active)n=(n+1)%16;showTarget(n)}
  pick();
  tickTimer=setInterval(()=>{timeLeft=Math.max(0,20-(performance.now()-started)/1000);$('#time').textContent=timeLeft.toFixed(1);if(timeLeft<=0)finishLocal();else if(Math.floor(timeLeft*10)%9===0)pick()},100);
}
function finishLocal(){running=false;clearInterval(tickTimer);showTarget(-1);$('#startBtn').disabled=false;}
async function serverStart(){
  const data=await post('/api/session/start',{playerId:'demo',mode:'demo'}); session=data.session; balance=data.balance||0; score=0; tickets=0; running=true; updateScore(); $('#startBtn').disabled=true;
  const endAt=session.startAt+session.stepMs*session.steps;
  tickTimer=setInterval(()=>{
    const now=Date.now(); const step=Math.floor((now-session.startAt)/session.stepMs); timeLeft=Math.max(0,(endAt-now)/1000); $('#time').textContent=timeLeft.toFixed(1);
    if(step>=0&&step<session.steps) showTarget(session.targets[step]); else showTarget(-1);
    if(now>=endAt){clearInterval(tickTimer);showTarget(-1);finishTimer=setTimeout(serverFinish,350);}
  },50);
}
async function start(){
  if(running)return;
  try{ if(serverOnline) await serverStart(); else fallbackStart(); }
  catch(e){serverOnline=false;$('#serverStatus').textContent='Verification server unavailable — static demo fallback';fallbackStart();}
}
async function hit(i,b){
  if(!running)return;
  if(!serverOnline||!session){
    if(i===active){score++;updateScore();}else{b.classList.add('wrong');score=Math.max(0,score-1);updateScore();setTimeout(()=>b.classList.remove('wrong'),120)}
    return;
  }
  try{
    const data=await post('/api/session/hit',{sessionId:session.id,tile:i});
    if(data.accepted){score=data.score;updateScore();}
    else if(i!==active){b.classList.add('wrong');setTimeout(()=>b.classList.remove('wrong'),120);}
  }catch{ $('#serverStatus').textContent='Hit verification error — session preserved'; }
}
async function serverFinish(){
  if(!session)return;
  try{
    const data=await post('/api/session/finish',{sessionId:session.id}); score=data.score; tickets=data.tickets; balance=data.balance; updateScore();
    $('#serverStatus').textContent=`Verified result: ${score} hits → ${tickets} tickets`;
  }catch(e){
    if(e.status===409){finishTimer=setTimeout(serverFinish,500);return;}
    $('#serverStatus').textContent='Could not finalize verified session';
  }
  running=false;session=null;$('#startBtn').disabled=false;loadDashboard();
}
function reset(){
  if(running)return;score=0;tickets=0;timeLeft=20;showTarget(-1);$('#time').textContent='20.0';updateScore();
}
async function loadDashboard(){
  if(!serverOnline)return;
  try{
    const r=await fetch('/api/dashboard',{cache:'no-store',headers:{'x-owner-token':ownerToken}}); if(!r.ok) throw new Error('owner auth required'); const d=await r.json();
    $('#dashPayments').textContent=d.paymentsEnabled?'ON':'OFF'; $('#dashPlays').textContent=d.counters.demoPlays||0; $('#dashTickets').textContent=d.counters.awardedTickets||0;
    $('#dashCollected').textContent=money((d.actual.collectedCents||0)/100); $('#dashOwnerShare').textContent=money((d.modeled.ownerShareCents||0)/100); $('#dashVenueShare').textContent=money((d.modeled.venueShareCents||0)/100);
  }catch{}
}
$('#startBtn').onclick=start; $('#resetBtn').onclick=reset;
$('#ownerBtn').onclick=()=>{
  if(serverOnline&&!ownerToken){
    const entered=prompt('Owner token (shown in the local Skill Vault server terminal):');
    if(entered){ownerToken=entered.trim();sessionStorage.setItem('sfSkillVaultOwnerToken',ownerToken);}
  }
  $('#ownerPanel').classList.remove('hidden'); $('#cfgPrice').value=cfg.price; $('#cfgTicketsPerHit').value=cfg.ticketsPerHit; $('#cfgTicketCost').value=cfg.ticketCostPer100; $('#cfgOps').value=cfg.ops;
  loadDashboard(); $('#ownerPanel').scrollIntoView({behavior:'smooth'});
};
$('#closeOwner').onclick=()=>$('#ownerPanel').classList.add('hidden');
$('#saveOwner').onclick=()=>{
  cfg={price:Math.max(0,Number($('#cfgPrice').value)||0),ticketsPerHit:Math.max(1,Math.min(10,Math.floor(Number($('#cfgTicketsPerHit').value)||1))),ticketCostPer100:Math.max(0,Number($('#cfgTicketCost').value)||0),ops:Math.max(0,Number($('#cfgOps').value)||0)};
  localStorage.setItem('sfSkillVault',JSON.stringify(cfg)); renderEconomics(); $('#ownerPanel').classList.add('hidden');
};
buildGrid();renderPrizes();renderEconomics();updateScore();bootstrap();
