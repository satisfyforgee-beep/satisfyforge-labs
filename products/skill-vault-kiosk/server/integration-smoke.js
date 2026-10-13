const {spawn}=require('child_process');
const path=require('path');
const crypto=require('crypto');
const {signHardwareEvent}=require('./hardware-input');
const port=8091, owner='owner-smoke-token', secret='hardware-smoke-secret';
const base=`http://127.0.0.1:${port}`;
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
async function json(path,opts={}){const r=await fetch(base+path,opts);const d=await r.json().catch(()=>({}));return {r,d};}
(async()=>{
  const child=spawn(process.execPath,[path.join(__dirname,'server.js')],{env:{...process.env,PORT:String(port),SKILL_VAULT_OWNER_TOKEN:owner,SKILL_VAULT_INPUT_SECRET:secret},stdio:['ignore','pipe','pipe']});
  let stderr=''; child.stderr.on('data',d=>stderr+=d);
  try{
    for(let i=0;i<30;i++){try{const x=await fetch(base+'/api/health');if(x.ok)break;}catch{}await sleep(100);}
    let q=await json('/api/health'); if(!q.r.ok||q.d.hardwareInputEnabled!==true||q.d.paymentsEnabled!==false) throw new Error('health gate failed');
    q=await json('/api/dashboard'); if(q.r.status!==401) throw new Error('owner auth gate failed');
    q=await json('/api/dashboard',{headers:{'x-owner-token':owner}}); if(!q.r.ok||q.d.actual.collectedCents!==0) throw new Error('owner dashboard failed');
    q=await json('/api/session/start',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({playerId:'hardware-smoke',mode:'paid'})}); if(q.r.status!==409||q.d.error!=='real_money_disabled') throw new Error('paid gate failed');
    q=await json('/api/session/start',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({playerId:'hardware-smoke',mode:'demo'})}); if(q.r.status!==201) throw new Error('demo start failed');
    const s=q.d.session; const delay=Math.max(0,s.startAt-Date.now()+80); await sleep(delay);
    const step=Math.floor((Date.now()-s.startAt)/s.stepMs); const tile=s.targets[Math.max(0,step)];
    const ev={sessionId:s.id,tile,ts:Date.now(),nonce:crypto.randomUUID()}; ev.signature=signHardwareEvent(secret,ev);
    q=await json('/api/hardware/hit',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(ev)}); if(!q.r.ok||q.d.accepted!==true||q.d.score!==1) throw new Error('hardware hit failed '+JSON.stringify(q.d));
    q=await json('/api/hardware/hit',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(ev)}); if(q.r.status!==401||q.d.error!=='hardware_event_replay') throw new Error('replay gate failed');
    const rc=await fetch(base+'/api/operator/reconciliation.csv',{headers:{'x-owner-token':owner}}); const text=await rc.text(); if(!rc.ok||!text.includes('actual_collected_cents,0,actual')) throw new Error('reconciliation failed');
    console.log('SKILL_VAULT_INTEGRATION_SMOKE_PASS');
  }finally{child.kill('SIGTERM');await sleep(100);if(stderr)process.stderr.write(stderr);}
})().catch(e=>{console.error(e);process.exit(1);});
