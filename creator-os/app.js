const KEY='satisfyforge.creator-os.v1';
const seed={
  queue:[],
  metrics:[],
  experiments:[
    {name:'Home Service Lead Rescue',model:'Service',buyer:'Local home-service owner',price:299,spend:0,revenue:0},
    {name:'Strange True Story Shorts Creator Kit',model:'Digital product',buyer:'Short-form creator',price:7.99,spend:0,revenue:0},
    {name:'Creator OS',model:'Software / subscription',buyer:'Creator or small business',price:0,spend:0,revenue:0}
  ],
  stack:[
    {name:'Direct Publisher',replaces:'Buffer / Metricool scheduling layer',status:'Built / authorization-dependent',detail:'Owned queue, state, duplicate protection and direct official-platform adapters live under publisher/.'},
    {name:'Mail Bridge',replaces:'Paid business-mail workflow tools',status:'Core tested / live OAuth pending',detail:'Gmail API semantics, sender allowlist and idempotency. Secrets never belong in the public repository.'},
    {name:'Creator Package Builder',replaces:'Hook / caption helper subscriptions',status:'Working locally',detail:'Turns one original premise into hooks, title, caption, structure and repurpose notes.'},
    {name:'Analytics + Experiment Tracker',replaces:'Basic creator dashboards',status:'Working locally',detail:'Tracks attention, clicks, revenue and $0-first business experiments.'},
    {name:'Owned Cloud Browser',replaces:'Metered browser automation where supported',status:'Verified for public-site jobs',detail:'Playwright / Chromium runner in GitHub Actions with Control Center integration.'},
    {name:'Video Assembly Engine',replaces:'Recurring basic video assembly subscriptions',status:'Next build',detail:'Planned local/CI pipeline for owned narration, captions, cuts, sizing and QA using lawful inputs.'}
  ]
};
let data=load();
let lastGenerated='';

function clone(v){return JSON.parse(JSON.stringify(v));}
function load(){try{return JSON.parse(localStorage.getItem(KEY))||clone(seed)}catch{return clone(seed)}}
function persist(){localStorage.setItem(KEY,JSON.stringify(data));renderAll();}
const $=id=>document.getElementById(id);
const money=n=>'$'+Number(n||0).toFixed(2);
const num=n=>new Intl.NumberFormat('en-US').format(Number(n||0));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function showTab(id){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('#nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));$(id).classList.add('active');window.scrollTo(0,0)}
$('nav').addEventListener('click',e=>{if(e.target.dataset.tab)showTab(e.target.dataset.tab)});
document.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>showTab(b.dataset.go)));

function renderDashboard(){
  const views=data.metrics.reduce((a,b)=>a+Number(b.views||0),0);
  const engagements=data.metrics.reduce((a,b)=>a+['likes','shares','saves','comments'].reduce((s,k)=>s+Number(b[k]||0),0),0);
  const metricRevenue=data.metrics.reduce((a,b)=>a+Number(b.revenue||0),0);
  const expRevenue=data.experiments.reduce((a,b)=>a+Number(b.revenue||0),0);
  $('kViews').textContent=num(views);$('kEng').textContent=num(engagements);$('kRevenue').textContent=money(metricRevenue+expRevenue);$('kReady').textContent=data.queue.filter(x=>['ready','scheduled'].includes(x.status)).length;
  const best=[...data.metrics].sort((a,b)=>Number(b.views)-Number(a.views)).slice(0,5);
  $('bestContent').innerHTML=best.length?best.map((p,i)=>`<div class="stackrow"><div class="topline"><strong>${esc(p.title)}</strong><span>${num(p.views)} views</span></div><div class="metricbar"><i style="width:${Math.min(100,(Number(p.views)/(Number(best[0].views)||1))*100)}%"></i></div></div>`).join(''):'<p>No performance data logged yet.</p>';
  $('scaleSignals').innerHTML=data.experiments.map(x=>{const profit=Number(x.revenue)-Number(x.spend);const sig=profit>0?'scale':Number(x.revenue)>0?'watch':'test';return `<div class="stackrow"><div class="topline"><strong>${esc(x.name)}</strong><span class="signal ${sig}">${sig}</span></div><small>${money(profit)} profit</small></div>`}).join('');
  const actions=[];
  if(data.queue.some(x=>x.status==='ready')) actions.push('A queue item is ready. Verify media, platform ownership and duplicate history before scheduling it.');
  if(data.experiments.some(x=>Number(x.revenue)>Number(x.spend))) actions.push('At least one experiment is profitable. Improve distribution and conversion before starting another unrelated offer.');
  if(!data.metrics.length) actions.push('Log real post performance so the system can rank content by evidence instead of guesses.');
  if(!data.queue.length) actions.push('Create one original content package and move it into the publishing queue.');
  $('nextActions').innerHTML=actions.map(x=>`<p>• ${esc(x)}</p>`).join('')||'<p>No urgent action detected.</p>';
}

function generate(){
  const topic=$('topic').value.trim(); if(!topic){alert('Enter a topic first.');return;}
  const goal=$('goal').value,tone=$('tone').value,detail=$('details').value.trim();
  const hooks={
    Curiosity:[`The part of ${topic} most people never hear about.`,`This gets stranger the closer you look.`,`Watch the detail that changes the whole story.`],
    'Fast payoff':[`Here is the payoff first — now watch how ${topic} got there.`,`No long intro: this is the part worth seeing.`,`The result is the hook. The story explains why.`],
    Story:[`It started normally. Then ${topic} changed everything.`,`This story sounds made up until you see what happened next.`,`The turning point came faster than anyone expected.`],
    Educational:[`Three things worth knowing about ${topic}.`,`The fastest useful explanation of ${topic}.`,`Before you scroll, here is what actually matters about ${topic}.`],
    Challenge:[`Can ${topic} hold attention for 20 seconds? Here is the test.`,`One rule: earn the payoff before the viewer swipes.`,`Guess the ending before the reveal.`]
  };
  const cta=goal==='Sales'?'If the offer genuinely fits, point to the verified product or inquiry path.':goal==='Clicks'?'Give viewers one clear reason to open the verified link.':goal==='Shares'?'Ask for a share only when the story gives someone a reason to send it.':goal==='Followers'?'Promise a specific next installment instead of a generic follow request.':'End with a question or loop that naturally continues the idea.';
  const h=hooks[tone]||hooks.Curiosity;
  lastGenerated=`ORIGINAL CONTENT PACKAGE\n\nTOPIC\n${topic}\n\nGOAL\n${goal}\n\nHOOK OPTIONS\n1. ${h[0]}\n2. ${h[1]}\n3. ${h[2]}\n\nTITLE\n${topic} — ${tone} cut\n\nSHORT-FORM STRUCTURE\n0–2s: strongest verified fact / visual\n2–7s: establish tension or transformation\n7–15s: escalate with a new detail\n15–25s: deliver the payoff\nFinal beat: visual or verbal loop where natural\n\nCAPTION\n${h[0]}${detail?' '+detail:''}\n\nCTA\n${cta}\n\nPLATFORM ADAPTATION\nTikTok: fastest first frame; minimal setup.\nYouTube Shorts: searchable title; payoff must stand alone.\nInstagram Reels: strong save/share value and clean caption.\nFacebook: one extra context sentence can help cold viewers.\nX: compress to one sharp observation plus the clip.\n\nRULES\nUse original execution. Do not copy another creator's footage, script, branding or protected assets. Verify factual claims before publishing.`;
  $('generated').textContent=lastGenerated;
}
$('generateBtn').addEventListener('click',generate);
$('queueGeneratedBtn').addEventListener('click',()=>{if(!lastGenerated)generate();if(!lastGenerated)return;data.queue.push({id:Date.now(),title:$('topic').value.trim().slice(0,90),platform:'youtube',status:'drafting',publish_at:'',video_url:'',caption:'',revenue:0});persist();showTab('queue')});

function renderQueue(){
  $('queueRows').innerHTML=data.queue.map(x=>`<tr><td><input value="${esc(x.title)}" onchange="editQueue(${x.id},'title',this.value)"></td><td><select onchange="editQueue(${x.id},'platform',this.value)">${['instagram','facebook','youtube','tiktok'].map(p=>`<option value="${p}" ${x.platform===p?'selected':''}>${p}</option>`).join('')}</select></td><td><select onchange="editQueue(${x.id},'status',this.value)">${['idea','drafting','ready','scheduled','published'].map(s=>`<option ${x.status===s?'selected':''}>${s}</option>`).join('')}</select></td><td><input placeholder="ISO-8601" value="${esc(x.publish_at||'')}" onchange="editQueue(${x.id},'publish_at',this.value)"></td><td><input placeholder="https://...mp4" value="${esc(x.video_url||'')}" onchange="editQueue(${x.id},'video_url',this.value)"></td><td><input type="number" step="0.01" value="${Number(x.revenue||0)}" onchange="editQueue(${x.id},'revenue',this.value)"></td><td><button onclick="removeQueue(${x.id})">Delete</button></td></tr>`).join('');
}
window.editQueue=(id,k,v)=>{const x=data.queue.find(q=>q.id===id);if(!x)return;x[k]=k==='revenue'?Number(v):v;persist()};
window.removeQueue=id=>{data.queue=data.queue.filter(q=>q.id!==id);persist()};
$('addQueueBtn').addEventListener('click',()=>{data.queue.push({id:Date.now(),title:'New content item',platform:'youtube',status:'idea',publish_at:'',video_url:'',caption:'',revenue:0});persist()});

function publisherObject(){
  const items=data.queue.filter(x=>['ready','scheduled'].includes(x.status)).map(x=>{
    const platforms={instagram:{enabled:false,caption:''},facebook:{enabled:false,title:'',caption:''},youtube:{enabled:false,title:'',description:'',privacy:'public',category_id:'27'},tiktok:{enabled:false,caption:'',privacy:'PUBLIC_TO_EVERYONE',is_aigc:false}};
    const p=x.platform;
    if(platforms[p]){platforms[p].enabled=true;if(p==='youtube'){platforms[p].title=x.title;platforms[p].description=x.caption||''}else if(p==='facebook'){platforms[p].title=x.title;platforms[p].caption=x.caption||''}else{platforms[p].caption=x.caption||''}}
    return {id:`creator-os-${x.id}`,publish_at:x.publish_at,video_url:x.video_url,platforms};
  });
  return {items};
}
$('exportPublisherBtn').addEventListener('click',()=>download('satisfyforge-publisher-queue.json',publisherObject()));

function renderMetrics(){
  $('metricRows').innerHTML=data.metrics.map((x,i)=>`<tr><td><input value="${esc(x.title)}" onchange="editMetric(${i},'title',this.value)"></td>${['views','likes','shares','saves','comments','clicks','revenue'].map(k=>`<td><input type="number" step="${k==='revenue'?'0.01':'1'}" value="${Number(x[k]||0)}" onchange="editMetric(${i},'${k}',this.value)"></td>`).join('')}</tr>`).join('');
  const v=data.metrics.reduce((a,b)=>a+Number(b.views||0),0),e=data.metrics.reduce((a,b)=>a+['likes','shares','saves','comments'].reduce((s,k)=>s+Number(b[k]||0),0),0),c=data.metrics.reduce((a,b)=>a+Number(b.clicks||0),0),r=data.metrics.reduce((a,b)=>a+Number(b.revenue||0),0);
  $('engRate').textContent=(v?e/v*100:0).toFixed(2)+'%';$('clickRate').textContent=(v?c/v*100:0).toFixed(2)+'%';$('rpm').textContent=money(v?r/v*1000:0);
}
window.editMetric=(i,k,v)=>{data.metrics[i][k]=k==='title'?v:Number(v);persist()};
$('addMetricBtn').addEventListener('click',()=>{data.metrics.push({title:'New post',views:0,likes:0,shares:0,saves:0,comments:0,clicks:0,revenue:0});persist()});

function renderExperiments(){
  $('experimentRows').innerHTML=data.experiments.map((x,i)=>{const profit=Number(x.revenue)-Number(x.spend),sig=profit>0?'scale':Number(x.revenue)>0?'watch':'test';return `<tr><td>${esc(x.name)}</td><td>${esc(x.model)}</td><td>${esc(x.buyer)}</td><td>${money(x.price)}</td><td><input type="number" step="0.01" value="${Number(x.spend||0)}" onchange="editExp(${i},'spend',this.value)"></td><td><input type="number" step="0.01" value="${Number(x.revenue||0)}" onchange="editExp(${i},'revenue',this.value)"></td><td>${money(profit)}</td><td><span class="signal ${sig}">${sig}</span></td></tr>`}).join('');
}
window.editExp=(i,k,v)=>{data.experiments[i][k]=Number(v);persist()};
$('addExperimentBtn').addEventListener('click',()=>{const name=prompt('Experiment name?');if(!name)return;const model=prompt('Business model?','Service')||'Other';const buyer=prompt('Specific buyer?','')||'Unspecified';const price=Number(prompt('Target price?','0')||0);data.experiments.push({name,model,buyer,price,spend:0,revenue:0});persist()});

function renderStack(){$('stackCards').innerHTML=data.stack.map(x=>`<article class="toolcard"><h2>${esc(x.name)}</h2><p><strong>Replaces:</strong> ${esc(x.replaces)}</p><p>${esc(x.detail)}</p><span class="status">${esc(x.status)}</span></article>`).join('')}
function download(name,obj){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
$('exportAllBtn').addEventListener('click',()=>download('satisfyforge-creator-os-backup.json',data));
$('importFile').addEventListener('change',e=>{const f=e.target.files?.[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const incoming=JSON.parse(r.result);if(!incoming||!Array.isArray(incoming.queue)||!Array.isArray(incoming.metrics)||!Array.isArray(incoming.experiments))throw new Error('shape');data=incoming;if(!Array.isArray(data.stack))data.stack=clone(seed.stack);persist();alert('Creator OS data restored.')}catch{alert('That file is not a valid Creator OS backup.')}};r.readAsText(f)});
function renderAll(){renderDashboard();renderQueue();renderMetrics();renderExperiments();renderStack()}
renderAll();
