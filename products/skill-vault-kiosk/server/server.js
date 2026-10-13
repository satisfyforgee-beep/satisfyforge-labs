const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {authorizePaidSession} = require('./payment-adapter');
const {verifyHardwareEvent} = require('./hardware-input');
const {buildReconciliationCsv} = require('./reconciliation');

const ROOT = path.resolve(__dirname, '..');
const DATA = path.join(__dirname, 'data', 'state.json');
const CONFIG_PATH = path.join(__dirname, 'config.json');
const config = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
const port = Number(process.env.PORT || 8080);
const AUDIT = path.join(__dirname, 'data', 'audit.jsonl');
const ownerToken = process.env.SKILL_VAULT_OWNER_TOKEN || crypto.randomBytes(18).toString('hex');
const hardwareInputSecret = process.env.SKILL_VAULT_INPUT_SECRET || '';
const startedAt = Date.now();

function emptyState(){
  return {
    balances: { demo: 0 },
    sessions: {},
    redemptions: [],
    counters: { demoPlays: 0, paidPlays: 0, collectedCents: 0, awardedTickets: 0, redeemedTickets: 0 }
  };
}
function loadState(){
  try { return {...emptyState(), ...JSON.parse(fs.readFileSync(DATA, 'utf8'))}; }
  catch { return emptyState(); }
}
let state = loadState();
function saveState(){
  const tmp = DATA + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
  fs.renameSync(tmp, DATA);
}
function audit(type, details={}){
  const row={ts:new Date().toISOString(),type,...details};
  fs.appendFileSync(AUDIT,JSON.stringify(row)+'\n');
}
function json(res, status, payload){
  res.writeHead(status, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
  res.end(JSON.stringify(payload));
}
function body(req){
  return new Promise((resolve,reject)=>{
    let raw='';
    req.on('data',c=>{raw+=c; if(raw.length>100000) reject(new Error('body too large'));});
    req.on('end',()=>{try{resolve(raw?JSON.parse(raw):{});}catch(e){reject(e);}});
    req.on('error',reject);
  });
}
function safePlayerId(value){
  const v=String(value||'demo').replace(/[^a-zA-Z0-9_-]/g,'').slice(0,48);
  return v || 'demo';
}
function prizeById(id){ return config.prizes.find(p=>p.id===id); }
function makeTargets(){
  const out=[];
  let last=-1;
  for(let i=0;i<config.steps;i++){
    let n=crypto.randomInt(0,config.gridSize);
    if(n===last) n=(n+1)%config.gridSize;
    out.push(n); last=n;
  }
  return out;
}
function sessionPublic(s){
  return {id:s.id,startAt:s.startAt,stepMs:config.stepMs,steps:config.steps,gridSize:config.gridSize,targets:s.targets,mode:s.mode,playPriceCents:config.playPriceCents};
}
function currentStep(s, now=Date.now()){
  return Math.floor((now-s.startAt)/config.stepMs);
}
function validateHit(s,tile,now=Date.now()){
  if(s.finished) return {ok:false,reason:'session_finished'};
  const step=currentStep(s,now);
  if(step<0 || step>=config.steps) return {ok:false,reason:'outside_active_window'};
  if(s.hitSteps.includes(step)) return {ok:false,reason:'step_already_scored'};
  if(!Number.isInteger(tile) || tile<0 || tile>=config.gridSize) return {ok:false,reason:'invalid_tile'};
  if(s.targets[step]!==tile) return {ok:false,reason:'wrong_tile',step};
  const elapsed=now-(s.startAt+step*config.stepMs);
  if(elapsed<0 || elapsed>config.stepMs+config.hitGraceMs) return {ok:false,reason:'timing_outside_window'};
  return {ok:true,step};
}
function ownerAuthorized(req){ return req.headers['x-owner-token']===ownerToken; }
function applyVerifiedHit(s,tile,source='touch'){
  const result=validateHit(s,tile);
  if(!result.ok) return {accepted:false,score:s.score,reason:result.reason,step:result.step};
  s.hitSteps.push(result.step); s.score+=1; saveState();
  audit('hit_accepted',{sessionId:s.id,step:result.step,score:s.score,source});
  return {accepted:true,score:s.score,tickets:s.score*config.ticketsPerHit,step:result.step};
}
function dashboard(){
  const modeledRevenueCents=(state.counters.demoPlays+state.counters.paidPlays)*config.playPriceCents;
  const actualRevenueCents=state.counters.collectedCents;
  const ownerModeled=Math.round(modeledRevenueCents*config.ownerSharePct/100);
  const venueModeled=Math.round(modeledRevenueCents*config.venueSharePct/100);
  return {
    paymentsEnabled:config.paymentsEnabled,
    counters:state.counters,
    balances:state.balances,
    modeled:{grossRevenueCents:modeledRevenueCents,ownerShareCents:ownerModeled,venueShareCents:venueModeled},
    actual:{collectedCents:actualRevenueCents},
    prizes:config.prizes.map(p=>({...p}))
  };
}

async function api(req,res,url){
  if(req.method==='GET' && url.pathname==='/api/health'){
    return json(res,200,{status:'ok',serverTime:new Date().toISOString(),uptimeSeconds:Math.floor((Date.now()-startedAt)/1000),paymentsEnabled:config.paymentsEnabled,hardwareInputEnabled:Boolean(hardwareInputSecret),ledgerWritable:true});
  }
  if(req.method==='GET' && url.pathname==='/api/config'){
    return json(res,200,{paymentsEnabled:config.paymentsEnabled,playPriceCents:config.playPriceCents,ticketsPerHit:config.ticketsPerHit,stepMs:config.stepMs,steps:config.steps,gridSize:config.gridSize,prizes:config.prizes});
  }
  if(req.method==='GET' && url.pathname==='/api/dashboard'){
    if(!ownerAuthorized(req)) return json(res,401,{error:'owner_auth_required'});
    return json(res,200,dashboard());
  }
  if(req.method==='GET' && url.pathname==='/api/operator/reconciliation.csv'){
    if(!ownerAuthorized(req)) return json(res,401,{error:'owner_auth_required'});
    const csv=buildReconciliationCsv({state,config});
    res.writeHead(200,{'content-type':'text/csv; charset=utf-8','cache-control':'no-store','content-disposition':'attachment; filename=skill-vault-reconciliation.csv'});
    return res.end(csv);
  }
  if(req.method==='GET' && url.pathname==='/api/operator/redemptions'){
    if(!ownerAuthorized(req)) return json(res,401,{error:'owner_auth_required'});
    return json(res,200,{redemptions:state.redemptions});
  }
  if(req.method==='POST' && url.pathname==='/api/operator/redemptions/complete'){
    if(!ownerAuthorized(req)) return json(res,401,{error:'owner_auth_required'});
    const b=await body(req); const r=state.redemptions.find(x=>x.id===String(b.redemptionId||''));
    if(!r) return json(res,404,{error:'redemption_not_found'});
    if(r.status==='COMPLETED') return json(res,200,{redemption:r,alreadyCompleted:true});
    if(r.status!=='PENDING_OPERATOR') return json(res,409,{error:'redemption_not_pending'});
    r.status='COMPLETED'; r.completedAt=Date.now(); saveState(); audit('redemption_completed',{redemptionId:r.id,playerId:r.playerId,prizeId:r.prizeId});
    return json(res,200,{redemption:r});
  }

  if(req.method==='POST' && url.pathname==='/api/session/start'){
    const b=await body(req); const mode=b.mode==='paid'?'paid':'demo'; const playerId=safePlayerId(b.playerId);
    let payment=null;
    if(mode==='paid'){
      if(!config.paymentsEnabled) return json(res,409,{error:'real_money_disabled'});
      try{
        payment=await authorizePaidSession({authorizationId:b.paymentAuthorizationId,idempotencyKey:b.idempotencyKey,amountCents:config.playPriceCents});
      }catch(e){return json(res,503,{error:e.code||'payment_authorization_failed'});}
    }
    const id=crypto.randomUUID();
    const s={id,playerId,mode,payment,createdAt:Date.now(),startAt:Date.now()+650,targets:makeTargets(),hitSteps:[],score:0,finished:false};
    state.sessions[id]=s; saveState(); audit('session_started',{sessionId:id,playerId,mode});
    return json(res,201,{session:sessionPublic(s),balance:state.balances[playerId]||0});
  }

  if(req.method==='POST' && url.pathname==='/api/session/hit'){
    const b=await body(req); const s=state.sessions[String(b.sessionId||'')];
    if(!s) return json(res,404,{error:'session_not_found'});
    return json(res,200,applyVerifiedHit(s,Number(b.tile),'touch'));
  }
  if(req.method==='POST' && url.pathname==='/api/hardware/hit'){
    const b=await body(req); const verified=verifyHardwareEvent(hardwareInputSecret,b);
    if(!verified.ok) return json(res,401,{error:verified.reason});
    const s=state.sessions[verified.sessionId];
    if(!s) return json(res,404,{error:'session_not_found'});
    return json(res,200,applyVerifiedHit(s,verified.tile,'hardware'));
  }

  if(req.method==='POST' && url.pathname==='/api/session/finish'){
    const b=await body(req); const s=state.sessions[String(b.sessionId||'')];
    if(!s) return json(res,404,{error:'session_not_found'});
    if(s.finished) return json(res,200,{alreadyFinished:true,score:s.score,tickets:s.awardedTickets||0,balance:state.balances[s.playerId]||0});
    if(Date.now()<s.startAt+config.steps*config.stepMs-250) return json(res,409,{error:'session_still_active'});
    s.finished=true; s.finishedAt=Date.now(); s.awardedTickets=s.score*config.ticketsPerHit;
    state.balances[s.playerId]=(state.balances[s.playerId]||0)+s.awardedTickets;
    state.counters.awardedTickets+=s.awardedTickets;
    if(s.mode==='demo') state.counters.demoPlays+=1; else {state.counters.paidPlays+=1; state.counters.collectedCents+=config.playPriceCents;}
    saveState(); audit('session_finished',{sessionId:s.id,mode:s.mode,score:s.score,tickets:s.awardedTickets});
    return json(res,200,{score:s.score,tickets:s.awardedTickets,balance:state.balances[s.playerId],mode:s.mode});
  }

  if(req.method==='POST' && url.pathname==='/api/redeem'){
    const b=await body(req); const playerId=safePlayerId(b.playerId); const prize=prizeById(String(b.prizeId||''));
    if(!prize) return json(res,404,{error:'prize_not_found'});
    const balance=state.balances[playerId]||0;
    if(balance<prize.tickets) return json(res,409,{error:'insufficient_tickets',balance,needed:prize.tickets});
    const used=state.redemptions.filter(r=>r.prizeId===prize.id && r.status!=='CANCELED').length;
    if(used>=prize.inventory) return json(res,409,{error:'out_of_stock'});
    state.balances[playerId]=balance-prize.tickets;
    state.counters.redeemedTickets+=prize.tickets;
    const redemption={id:crypto.randomUUID(),playerId,prizeId:prize.id,tickets:prize.tickets,status:'PENDING_OPERATOR',createdAt:Date.now()};
    state.redemptions.push(redemption); saveState(); audit('redemption_created',{redemptionId:redemption.id,playerId,prizeId:prize.id,tickets:prize.tickets});
    return json(res,201,{redemption,balance:state.balances[playerId]});
  }

  return json(res,404,{error:'not_found'});
}

function serve(req,res,url){
  let rel=url.pathname==='/'?'index.html':url.pathname.replace(/^\//,'');
  const file=path.resolve(ROOT,rel);
  if(!file.startsWith(ROOT)) {res.writeHead(403); return res.end('forbidden');}
  fs.stat(file,(err,st)=>{
    if(err||!st.isFile()){res.writeHead(404);return res.end('not found');}
    const ext=path.extname(file).toLowerCase();
    const types={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg'};
    res.writeHead(200,{'content-type':types[ext]||'application/octet-stream','cache-control':'no-store'});
    fs.createReadStream(file).pipe(res);
  });
}

const server=http.createServer(async(req,res)=>{
  const url=new URL(req.url,'http://localhost');
  try{
    if(url.pathname.startsWith('/api/')) await api(req,res,url); else serve(req,res,url);
  }catch(err){ console.error(err); json(res,500,{error:'server_error'}); }
});

if(require.main===module){server.listen(port,()=>{console.log(`Skill Vault server: http://localhost:${port} paymentsEnabled=${config.paymentsEnabled}`);console.log(`Owner dashboard token: ${ownerToken}`);});}
module.exports={validateHit,currentStep,makeTargets,emptyState,config,applyVerifiedHit,dashboard};
