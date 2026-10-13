const $ = s => document.querySelector(s);
const grid = $('#grid');
const defaults = {price:2,baseTickets:20,ticketCostPer100:0.55,ops:0.20};
let cfg = {...defaults,...JSON.parse(localStorage.getItem('sfSkillVault')||'{}')};
let running=false,score=0,tickets=0,timeLeft=20,active=-1,timer=null,spawnTimer=null;
const prizes=[
  {name:'Snack / drink credit',tickets:120,cost:0.70},
  {name:'$5 venue merchandise credit',tickets:450,cost:2.50},
  {name:'Premium small prize',tickets:900,cost:5.25},
  {name:'Choose-your-prize shelf item',tickets:1800,cost:10.00}
];
function money(v){return '$'+Number(v).toFixed(2)}
function renderEconomics(){
  $('#playPrice').textContent=money(cfg.price); $('#profitPlayPrice').textContent=money(cfg.price); $('#baseTickets').textContent=cfg.baseTickets;
  const guaranteedCost=cfg.baseTickets/100*cfg.ticketCostPer100;
  const modeledBonus=30/100*cfg.ticketCostPer100;
  const avg=guaranteedCost+modeledBonus;
  $('#avgPrizeCost').textContent=money(avg); $('#opsCost').textContent=money(cfg.ops); $('#grossMargin').textContent=money(Math.max(0,cfg.price-avg-cfg.ops));
}
function renderPrizes(){ $('#prizes').innerHTML=prizes.map(p=>`<div class="prize"><div><strong>${p.name}</strong><small class="fineprint">Est. cost ${money(p.cost)}</small></div><b>${p.tickets} tickets</b></div>`).join('') }
function buildGrid(){grid.innerHTML='';for(let i=0;i<16;i++){let b=document.createElement('button');b.className='tile';b.setAttribute('aria-label','reaction tile');b.onclick=()=>hit(i,b);grid.appendChild(b)}}
function setActive(){if(!running)return;[...grid.children].forEach(x=>x.classList.remove('active','wrong'));let next=Math.floor(Math.random()*16);if(next===active)next=(next+1)%16;active=next;grid.children[active].classList.add('active')}
function hit(i,b){if(!running)return;if(i===active){score++;tickets=cfg.baseTickets+score*2;$('#score').textContent=score;$('#tickets').textContent=tickets;setActive()}else{b.classList.add('wrong');score=Math.max(0,score-1);tickets=cfg.baseTickets+score*2;$('#score').textContent=score;$('#tickets').textContent=tickets;setTimeout(()=>b.classList.remove('wrong'),120)}}
function start(){if(running)return;running=true;score=0;tickets=cfg.baseTickets;timeLeft=20;$('#score').textContent=0;$('#tickets').textContent=tickets;$('#time').textContent='20.0';$('#startBtn').disabled=true;setActive();let startAt=performance.now();timer=setInterval(()=>{timeLeft=Math.max(0,20-(performance.now()-startAt)/1000);$('#time').textContent=timeLeft.toFixed(1);if(timeLeft<=0)finish()},50);spawnTimer=setInterval(setActive,850)}
function finish(){running=false;clearInterval(timer);clearInterval(spawnTimer);[...grid.children].forEach(x=>x.classList.remove('active','wrong'));$('#startBtn').disabled=false;active=-1}
function reset(){finish();score=0;tickets=0;$('#score').textContent=0;$('#tickets').textContent=0;$('#time').textContent='20.0'}
$('#startBtn').onclick=start;$('#resetBtn').onclick=reset;
$('#ownerBtn').onclick=()=>{$('#ownerPanel').classList.remove('hidden');$('#cfgPrice').value=cfg.price;$('#cfgBase').value=cfg.baseTickets;$('#cfgTicketCost').value=cfg.ticketCostPer100;$('#cfgOps').value=cfg.ops;$('#ownerPanel').scrollIntoView({behavior:'smooth'})};
$('#closeOwner').onclick=()=>$('#ownerPanel').classList.add('hidden');
$('#saveOwner').onclick=()=>{cfg={price:Math.max(0,Number($('#cfgPrice').value)||0),baseTickets:Math.max(1,Math.floor(Number($('#cfgBase').value)||1)),ticketCostPer100:Math.max(0,Number($('#cfgTicketCost').value)||0),ops:Math.max(0,Number($('#cfgOps').value)||0)};localStorage.setItem('sfSkillVault',JSON.stringify(cfg));renderEconomics();$('#ownerPanel').classList.add('hidden')};
buildGrid();renderPrizes();renderEconomics();
