'use strict';
const $ = (id) => document.getElementById(id);
const esc = (x) => String(x ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const num = (x, d = 2) => (x === null || x === undefined || x === '') ? '—' : (+x).toFixed(d);
const int = (x) => (x === null || x === undefined) ? '—' : Math.round(x);
const C = { up:'#34d399', down:'#fb7185', warn:'#fbbf24', info:'#4f8cff', vio:'#a78bfa', gold:'#f5c451', dim:'#8599bd', dim2:'#57668b', grid:'rgba(125,156,224,.12)' };
let LAST = null, EVT = null, PREV_MID = null;
const chip=(t,c)=>`<span class="chip ${c||''}">${t}</span>`, pill=(t,c)=>`<span class="pill ${c||''}">${t}</span>`;
function fit(cv,h){const dpr=devicePixelRatio||1,w=cv.parentElement.clientWidth||400;cv.width=w*dpr;cv.height=h*dpr;cv.style.height=h+'px';const x=cv.getContext('2d');x.setTransform(dpr,0,0,dpr,0,0);return{x,w,h};}

function renderHero(s){
  const q=s.quote||{}, ses=s.session||{}, a=s.account||{};
  const mid=q.mid;
  $('tkMid').textContent = mid!=null?num(mid):'—';
  const px=$('tkMid');
  if(PREV_MID!=null && mid!=null){ px.className='px mono '+(mid>PREV_MID?'up':mid<PREV_MID?'down':''); setTimeout(()=>px.className='px mono',400); }
  if(mid!=null) PREV_MID=mid;
  $('tkSpread').textContent = q.spread_usd!=null?('spread '+num(q.spread_usd)+' ('+ (mid? (q.spread_usd/mid*1e4).toFixed(2):'—') +'bps)'):'';
  $('tkBA').textContent = `bid ${num(q.bid)} / ask ${num(q.ask)}  ·  age ${q.age_s??'—'}s  ·  ${q.source||''}`;
  $('live').className='live '+((q.age_s??999)<90?'':'off');
  $('liveTxt').textContent=(q.age_s??999)<90?'LIVE · 实时推送':'行情偏旧';
  $('sesTxt').textContent = `${ses.weekday||''} · ${ses.reason||''}`;
  // chips: identity + account + session
  const id = a.ok ? `V1 · MT5 ${a.demo?'DEMO':'??'} · ${a.login} @ ${(a.server||'').split('-')[0]}` : 'V1 · MT5 DEMO';
  $('stateChips').innerHTML = chip(esc(id), 'gold') +
    chip(`session <b>${esc(ses.open?'OPEN':(ses.armed?'PRE-OPEN':'CLOSED'))}</b>`, ses.open?'ok':(ses.armed?'warn':'')) +
    chip(`invariants <b>${(s.invariants||{}).pass===false?'FAIL':'PASS'}</b>`, (s.invariants||{}).pass===false?'bad':'ok') +
    ((s.alerts||[]).length?chip(`⚠ ${s.alerts.length} alert`,'warn'):'');
  // ring = session state
  const frac = ses.open?1:(ses.armed?0.6:0.12), col = ses.open?C.up:(ses.armed?C.warn:C.dim2);
  drawRing(frac,col); $('ringVal').textContent = ses.open?'OPEN':(ses.armed?'PRE':'SHUT');
}

function renderKpis(s){
  const a=s.account||{}, st=(s.positions||{}).stats||{}, cnt=s.counters||{};
  const eq = a.ok?a.equity:null, bal=a.ok?a.balance:null;
  const r=st.realized_usd, rc=(r??0)>0?'g':(r??0)<0?'r':'';
  const tiles=[
    ['账户净值 Equity', eq!=null?`$${num(eq)}`:'—', a.ok?`balance $${num(bal)}`:esc(a.error||'账户不可用'), 'o'],
    ['已实现 PnL', r!=null?`${r>=0?'+':''}$${num(r)}`:'—', 'demo 自平仓累计', rc],
    ['胜率 / PF', st.closed?`${(st.win_rate*100).toFixed(0)}% / ${num(st.profit_factor)}`:'—', `${st.wins||0}W / ${st.losses||0}L`, 'g'],
    ['持仓 / 已平', `${(s.positions||{}).open?'':''}${(s.positions||{}).open.length} / ${st.closed||0}`, 'open / closed', 'v'],
    ['决策数', int(cnt.decisions), `${int(cnt.plans_registered)} plans`, ''],
    ['成交 trades', `${int(cnt.trades_opened)} / ${int(cnt.trades_closed)}`, 'opened / closed', ''],
    ['在册计划', (s.plans||[]).filter(p=>p.type==='registered').length, 'pending/registered', 'y'],
    ['连续 WAIT', int((s.waits||{}).consecutive), 'consecutive waits', ''],
  ];
  $('kpis').innerHTML=tiles.map(([k,v,d,cls])=>`<div class="kpi ${cls}"><div class="glow"></div><div class="k">${k}</div><div class="v mono">${v}</div><div class="d">${d}</div></div>`).join('');
}

function drawCandle(s){
  const cv=$('candle'); if(!cv) return; const {x,w,h}=fit(cv,300);
  x.clearRect(0,0,w,h);
  const bars=(s.bars||[]).filter(b=>b.o!=null);
  for(let i=0;i<=4;i++){const y=16+i*(h-40)/4;x.strokeStyle=C.grid;x.beginPath();x.moveTo(8,y);x.lineTo(w-8,y);x.stroke();}
  if(bars.length<3){x.fillStyle=C.dim;x.font='12px Inter,sans-serif';x.textAlign='center';x.fillText('无足够 tick 重建 K 线', w/2,h/2);$('candleTag').textContent='—';return;}
  const L=Math.min(...bars.map(b=>b.l)), H=Math.max(...bars.map(b=>b.h)), rng=(H-L)||1;
  const pad=6, W=(w-16)/bars.length, Y=v=>16+(1-(v-L)/rng)*(h-40), X=i=>8+i*W;
  // MA20
  const closes=bars.map(b=>b.c);
  x.beginPath();let started=false;
  for(let i=19;i<closes.length;i++){const ma=closes.slice(i-19,i+1).reduce((a,b)=>a+b,0)/20;const px=X(i)+W/2,py=Y(ma);started?x.lineTo(px,py):x.moveTo(px,py);started=true;}
  x.strokeStyle=C.gold;x.lineWidth=1.4;x.stroke();
  // candles
  bars.forEach((b,i)=>{const up=b.c>=b.o,col=up?C.up:C.down,bx=X(i)+W*0.18,bw=W*0.64;
    x.strokeStyle=col;x.fillStyle=col;x.lineWidth=1;
    x.beginPath();x.moveTo(X(i)+W/2,Y(b.h));x.lineTo(X(i)+W/2,Y(b.l));x.stroke();
    const y1=Y(Math.max(b.o,b.c)),y2=Y(Math.min(b.o,b.c));
    x.fillRect(bx,y1,bw,Math.max(1,y2-y1));});
  // last price
  const last=bars[bars.length-1].c, ly=Y(last);
  x.strokeStyle='rgba(79,140,255,.7)';x.setLineDash([4,4]);x.beginPath();x.moveTo(8,ly);x.lineTo(w-8,ly);x.stroke();x.setLineDash([]);
  x.fillStyle=C.info;x.font='10.5px Inter,sans-serif';x.textAlign='left';x.fillText(num(last),10,ly-4);
  x.fillStyle=C.dim;x.fillText(num(H),10,12);x.fillText(num(L),10,h-6);
  $('candleTag').textContent = `${bars.length} bars · MA20`;
  $('candleLegend').innerHTML=`<span><i style="background:${C.up}"></i>up</span><span><i style="background:${C.down}"></i>down</span><span><i style="background:${C.gold}"></i>MA20</span><span>M15 from MT5 ticks (read-only)</span>`;
}

function renderWorkflow(s){
  const wf=s.workflow||{}; const steps=wf.steps||[];
  $('wfTag').textContent = wf.cycle||'';
  $('wf').innerHTML = steps.map(st=>{const cl=(st.status||'').toLowerCase();
    return `<div class="step ${cl==='done'?'done':cl==='running'?'running':cl==='pending'?'pending':'idle'}">
      <div class="sn"><span class="sd"></span>${esc(st.step)}</div><div class="sr" title="${esc(st.result)}">${esc(st.result)}</div></div>`;}).join('');
}

function renderTf(s){
  const rows=s.tf||[]; $('tfTag').textContent=`${rows.length} TF`;
  $('tfTbl').querySelector('thead').innerHTML=`<tr><th>TF</th><th>close</th><th>RSI</th><th>MA20</th><th>cat</th><th>er</th><th>pos%</th><th>exp</th></tr>`;
  $('tfTbl').querySelector('tbody').innerHTML=rows.map(r=>`<tr>
    <td>${esc(r.tf)}</td><td class="mono">${num(r.close)}</td>
    <td class="mono" style="color:${r.rsi<35?C.up:r.rsi>65?C.down:''}">${num(r.rsi,1)}</td>
    <td class="mono">${num(r.ma20)}</td><td>${esc(r.cat||'')}</td><td class="mono">${num(r.er)}</td>
    <td class="mono">${num(r.pos,0)}</td><td>${esc(r.exp||'')}</td></tr>`).join('')||`<tr><td colspan="8"><div class="muted">—</div></td></tr>`;
}

function renderPositions(s){
  const p=s.positions||{}, st=p.stats||{}, open=p.open||[];
  $('posTag').textContent=`${open.length} open · ${st.closed||0} closed`;
  let html='';
  if(open.length){
    html += open.map(o=>`<div class="pos"><div style="display:flex;justify-content:space-between">
      <b>${esc(o.side)} ${esc(o.position_id)}</b>${o.live_pt!=null?`<span class="mono" style="color:${o.live_pt>=0?C.up:C.down}">${o.live_pt>=0?'+':''}${num(o.live_pt)}pt</span>`:''}</div>
      <div class="muted" style="text-align:left;padding:6px 0 0">entry ${num(o.entry)} · SL ${num(o.stop)} · ticket ${esc(o.ticket??'—')}</div></div>`).join('');
  } else html += '<div class="muted">无持仓（FLAT）</div>';
  html += `<div class="acc" style="margin-top:10px">
    <div class="acct"><div class="k">REALIZED (demo)</div><div class="v mono" style="color:${st.realized_usd>=0?C.up:C.down}">${st.realized_usd>=0?'+':''}$${num(st.realized_usd)}</div></div>
    <div class="acct"><div class="k">WIN RATE</div><div class="v mono">${st.closed?(st.win_rate*100).toFixed(0):'—'}%</div></div>
    <div class="acct"><div class="k">AVG WIN / LOSS</div><div class="v mono" style="font-size:14px">+${num(st.avg_win)} / ${num(st.avg_loss)}</div></div>
    <div class="acct"><div class="k">PROFIT FACTOR</div><div class="v mono">${num(st.profit_factor)}</div></div>
  </div>`;
  $('pos').innerHTML=html;
}

function renderPlans(s){
  const pl=(s.plans||[]).filter(p=>p.type==='registered'||p.type==='cancelled').slice(0,8);
  $('plTag').textContent=`${pl.length}`;
  $('plans').innerHTML=pl.length?pl.map(p=>{const reg=p.type==='registered';
    const z=p.zone?`${num(p.zone.low)}–${num(p.zone.high)}`:'';
    return `<div class="fitem"><div class="ic ${reg?'reg':'cancel'}">${reg?'◈':'✕'}</div>
    <div class="b"><div class="l1"><span>${esc(p.direction||p.type)}</span>${pill(esc((p.plan_id||'').slice(-9)))}${p.R!=null?pill('R '+num(p.R,2)):''}${p.EV!=null?pill('EV '+(p.EV>=0?'+':'')+num(p.EV,3)):''}</div>
    <div class="l2">zone ${z} · SL ${num(p.SL)} · ${esc(p.reason||'')}</div></div>
    <div class="t">${esc((p.ts||'').slice(5,16))}</div></div>`;}).join(''):'<div class="muted">无</div>';
}

function renderDecisions(s){
  const d=s.decisions||[]; $('decTag').textContent=`${d.length}`;
  $('decFeed') // noop
  $('decisions').innerHTML=d.length?d.map(o=>{const cls=o.decision||'WAIT';
    return `<div class="fitem"><div class="ic ${esc(cls)}">${(o.decision||'').slice(0,1)}</div>
    <div class="b"><div class="l1"><span>${esc(o.decision)}</span>${o.confidence!=null?pill('conf '+num(o.confidence,2)):''}</div>
    <div class="l2" title="${esc(o.bias)}">${esc((o.bias||'').slice(0,120))}</div></div>
    <div class="t">${esc((o.cycle||'').slice(5,16))}</div></div>`;}).join(''):'<div class="muted">无</div>';
}

function renderSummary(s){
  const t=s.summary||[]; $('sumTag').textContent=`${t.length} 行`;
  $('summary').textContent = t.join('\n') || '—';
}

function renderSys(s){
  const inv=s.invariants||{}, ig=s.integrity||{}, dq=s.data_quality||{}, a=s.account||{};
  const lh=ig.ledger_head||{};
  $('sysTag').innerHTML=(inv.pass===false)?pill('INVARIANTS FAIL','bad'):pill('OK','ok');
  $('sys').innerHTML=
    `<div class="kv"><span class="k">账户 login</span><span class="v mono">${a.ok?esc(a.login):'—'}</span></div>`+
    `<div class="kv"><span class="k">server / demo</span><span class="v">${a.ok?esc(a.server):'—'} · ${a.ok?(a.demo?'DEMO':'??'):'—'}</span></div>`+
    `<div class="kv"><span class="k">balance / equity</span><span class="v mono">${a.ok?'$'+num(a.balance)+' / $'+num(a.equity):'—'}</span></div>`+
    `<div class="kv"><span class="k">margin / free / level</span><span class="v mono">${a.ok?`${num(a.margin)} / ${num(a.margin_free)} / ${num(a.margin_level)}`:'—'}</span></div>`+
    `<div class="kv"><span class="k">leverage / currency</span><span class="v mono">${a.ok?`1:${a.leverage} ${a.currency}`:'—'}</span></div>`+
    `<div class="kv"><span class="k">ledger head</span><span class="v mono">${esc((lh.hash||'—').slice(0,12))} · len ${esc(lh.len??'—')}</span></div>`+
    `<div class="kv"><span class="k">data quality</span><span class="v">live_days ${esc(dq.live_days??'—')} · ticks ${esc(dq.live_ticks??'—')} · gaps ${(dq.gaps||[]).length}</span></div>`+
    `<div class="kv"><span class="k">pkg age</span><span class="v">${s.pkg_age_s??'—'}s · cycle ${esc(s.cycle||'')}</span></div>`;
}

function renderWaits(s){
  const w=s.waits||{}, top=w.top||[];
  $('waitTag').textContent=`consec ${int(w.consecutive)}`;
  $('waits').innerHTML = (top.length?top.map(([k,v])=>`<div class="kv"><span class="k" style="max-width:74%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(k)}">${esc(k)}</span><span class="v">${v}×</span></div>`).join(''):'<div class="muted">无</div>')
    + `<div class="sec-t">最近 WAIT</div><div class="muted" style="text-align:left">${esc(w.last_reason||'—')}</div>`;
}

function drawRing(frac,col){const cv=$('ring');if(!cv)return;const dpr=devicePixelRatio||1,S=62;cv.width=S*dpr;cv.height=S*dpr;const x=cv.getContext('2d');x.setTransform(dpr,0,0,dpr,0,0);x.clearRect(0,0,S,S);x.lineWidth=5;x.strokeStyle='rgba(125,156,224,.16)';x.beginPath();x.arc(31,31,25,0,7);x.stroke();x.strokeStyle=col;x.lineCap='round';x.shadowColor=col;x.shadowBlur=8;x.beginPath();x.arc(31,31,25,-Math.PI/2,-Math.PI/2+Math.max(.04,frac)*Math.PI*2);x.stroke();x.shadowBlur=0;}
function tickClock(){const d=new Date();$('clock').textContent=d.toISOString().slice(11,19)+' UTC';}

function render(s){LAST=s;renderHero(s);renderKpis(s);drawCandle(s);renderWorkflow(s);renderTf(s);renderPositions(s);renderPlans(s);renderDecisions(s);renderSummary(s);renderSys(s);renderWaits(s);
  $('foot').textContent=`更新 ${new Date().toLocaleTimeString()} · cycle ${s.cycle||'—'} · V1 控制面板 (read-only · 不碰 V1/8787)`;}

function start(){
  addEventListener('resize',()=>{if(LAST){drawCandle(LAST);}});
  setInterval(tickClock,1000);tickClock();
  if(/[?&]noss\b/.test(location.search)){fetch('/api/snapshot',{cache:'no-store'}).then(r=>r.json()).then(render).catch(()=>{});return;}
  try{EVT=new EventSource('/api/stream');EVT.addEventListener('snap',e=>{$('live').className='live';try{render(JSON.parse(e.data));}catch(_){} });EVT.onerror=()=>{$('liveTxt').textContent='轮询模式';};}catch(_){}
  setInterval(async()=>{if(EVT&&EVT.readyState===1)return;try{render(await(await fetch('/api/snapshot',{cache:'no-store'})).json());}catch(_){}},3000);
  fetch('/api/snapshot',{cache:'no-store'}).then(r=>r.json()).then(render).catch(()=>{});
}
start();
