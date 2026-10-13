const assert=require('assert');
const {validateHit,currentStep,makeTargets,config}=require('./server');

const targets=makeTargets();
assert.equal(targets.length,config.steps);
assert(targets.every(n=>Number.isInteger(n)&&n>=0&&n<config.gridSize));
for(let i=1;i<targets.length;i++) assert.notEqual(targets[i],targets[i-1]);

const now=1_000_000;
const s={id:'x',startAt:now,targets:Array(config.steps).fill(3),hitSteps:[],score:0,finished:false};
assert.equal(currentStep(s,now),0);
assert.equal(currentStep(s,now+config.stepMs),1);
let r=validateHit(s,3,now+10);
assert.equal(r.ok,true); s.hitSteps.push(r.step); s.score++;
r=validateHit(s,3,now+20);
assert.equal(r.ok,false); assert.equal(r.reason,'step_already_scored');
r=validateHit({...s,hitSteps:[]},2,now+10);
assert.equal(r.ok,false); assert.equal(r.reason,'wrong_tile');
r=validateHit({...s,finished:true,hitSteps:[]},3,now+10);
assert.equal(r.ok,false); assert.equal(r.reason,'session_finished');

assert.equal(config.paymentsEnabled,false);
assert(config.prizes.every(p=>p.wholesaleCents<=1000));
assert(config.prizes.every(p=>p.tickets>0&&p.inventory>=0));
assert.equal(config.ownerSharePct+config.venueSharePct,100);
console.log('SKILL_VAULT_SERVER_TESTS_PASS');

const {signHardwareEvent,verifyHardwareEvent}=require('./hardware-input');
const {buildReconciliationCsv}=require('./reconciliation');
const secret='test-secret';
const event={sessionId:'s1',tile:4,ts:2_000_000,nonce:'nonce-1'};
event.signature=signHardwareEvent(secret,event);
let hv=verifyHardwareEvent(secret,event,event.ts);
assert.equal(hv.ok,true);
hv=verifyHardwareEvent(secret,event,event.ts);
assert.equal(hv.ok,false); assert.equal(hv.reason,'hardware_event_replay');
const csv=buildReconciliationCsv({state:{counters:{demoPlays:2,paidPlays:0,collectedCents:0,awardedTickets:12,redeemedTickets:0}},config});
assert(csv.includes('actual_collected_cents,0,actual'));
assert(csv.includes('modeled_gross_cents,400,planning only'));
assert.equal(config.paymentsEnabled,false);
console.log('SKILL_VAULT_SECURITY_ACCOUNTING_TESTS_PASS');
