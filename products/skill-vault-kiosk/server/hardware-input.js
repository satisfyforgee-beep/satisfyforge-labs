const crypto=require('crypto');

const MAX_SKEW_MS=5000;
const seenNonces=new Map();

function purge(now=Date.now()){
  for(const [nonce,ts] of seenNonces){ if(now-ts>MAX_SKEW_MS*2) seenNonces.delete(nonce); }
}
function payloadString({sessionId,tile,ts,nonce}){
  return `${sessionId}|${tile}|${ts}|${nonce}`;
}
function signHardwareEvent(secret,event){
  return crypto.createHmac('sha256',secret).update(payloadString(event)).digest('hex');
}
function verifyHardwareEvent(secret,event,now=Date.now()){
  if(!secret) return {ok:false,reason:'hardware_input_disabled'};
  const sessionId=String(event.sessionId||'');
  const nonce=String(event.nonce||'');
  const signature=String(event.signature||'');
  const tile=Number(event.tile);
  const ts=Number(event.ts);
  if(!sessionId||!nonce||nonce.length>96||!Number.isInteger(tile)||!Number.isFinite(ts)||!/^[a-f0-9]{64}$/i.test(signature)) return {ok:false,reason:'invalid_hardware_event'};
  if(Math.abs(now-ts)>MAX_SKEW_MS) return {ok:false,reason:'hardware_event_stale'};
  purge(now);
  if(seenNonces.has(nonce)) return {ok:false,reason:'hardware_event_replay'};
  const expected=signHardwareEvent(secret,{sessionId,tile,ts,nonce});
  const a=Buffer.from(signature,'hex'), b=Buffer.from(expected,'hex');
  if(a.length!==b.length||!crypto.timingSafeEqual(a,b)) return {ok:false,reason:'hardware_signature_invalid'};
  seenNonces.set(nonce,now);
  return {ok:true,sessionId,tile};
}
module.exports={MAX_SKEW_MS,signHardwareEvent,verifyHardwareEvent};
