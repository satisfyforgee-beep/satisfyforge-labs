const http=require('http');
const port=Number(process.env.PORT||8080);
const timeoutMs=Number(process.env.SKILL_VAULT_WATCHDOG_TIMEOUT_MS||2500);
const req=http.get({hostname:'127.0.0.1',port,path:'/api/health',timeout:timeoutMs},res=>{
  let raw=''; res.on('data',c=>raw+=c); res.on('end',()=>{
    if(res.statusCode!==200){console.error(`UNHEALTHY HTTP ${res.statusCode}`);process.exit(2);}
    try{
      const d=JSON.parse(raw);
      if(d.status!=='ok'||d.paymentsEnabled!==false){console.error('UNHEALTHY_RESPONSE',raw);process.exit(3);}
      console.log(`SKILL_VAULT_HEALTH_OK uptime=${d.uptimeSeconds}s hardware=${d.hardwareInputEnabled}`);
    }catch(e){console.error('INVALID_HEALTH_RESPONSE');process.exit(4);}
  });
});
req.on('timeout',()=>{req.destroy(new Error('timeout'));});
req.on('error',e=>{console.error('HEALTHCHECK_FAILED',e.message);process.exit(1);});
