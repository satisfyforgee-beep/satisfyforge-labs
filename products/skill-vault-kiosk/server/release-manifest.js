const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const ROOT=path.resolve(__dirname,'..');
const files=['index.html','styles.css','app.js','server/server.js','server/config.json','server/payment-adapter.js','server/hardware-input.js','server/reconciliation.js'];
function sha(file){return crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,file))).digest('hex');}
const config=JSON.parse(fs.readFileSync(path.join(ROOT,'server/config.json'),'utf8'));
const manifest={schema:1,generatedAt:new Date().toISOString(),paymentsEnabled:config.paymentsEnabled,files:Object.fromEntries(files.map(f=>[f,sha(f)]))};
const text=JSON.stringify(manifest,null,2)+'\n';
if(process.argv.includes('--write')){
  const out=path.join(ROOT,'server','data','release-manifest.json'); fs.writeFileSync(out,text); console.log(out);
}else process.stdout.write(text);
