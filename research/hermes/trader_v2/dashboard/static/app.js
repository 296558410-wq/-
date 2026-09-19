'use strict';
/* V2 控制面板 — 前端渲染（只读）。数据来自 /api/snapshot 与 /api/stream。 */
const $ = (id) => document.getElementById(id);
const esc = (x) => String(x ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const num = (x, d = 2) => (x === null || x === undefined || x === '' || isNaN(+x)) ? '—' : (+x).toFixed(d);
const money = (x, d = 2) => (x === null || x === undefined || isNaN(+x)) ? '—' : '$' + (+x).toFixed(d);
const sgn = (x, d = 2) => (x === null || x === undefined || isNaN(+x)) ? '—' : ((+x >= 0 ? '+' : '') + (+x).toFixed(d));
const DOT = { ok: '🟢', warn: '🟡', bad: '🔴', empty: '⚪' };
const DIR = { LONG: '做多', SHORT: '做空' };
const DEC_CN = { WAIT: '等待', TRADE: '发现交易机会', REJECT: '拒绝' };
let LAST = null, EVT = null, LAST_OK = 0, FAILS = 0;

function row(k, v) { return `<div class="kv"><span class="k">${k}</span><span class="v">${v}</span></div>`; }
function ageText(s) { return s == null ? '—' : (s < 90 ? Math.round(s) + ' 秒前' : (s < 5400 ? Math.round(s / 60) + ' 分钟前' : Math.round(s / 3600) + ' 小时前')); }
function hms(sec) { if (sec == null) return '—'; sec = Math.max(0, Math.round(sec)); const h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = sec % 60; return (h ? h + 'h ' : '') + String(m).padStart(2, '0') + 'm ' + String(s).padStart(2, '0') + 's'; }
function worstCls(items) { const c = (items || []).map(i => i.cls); return c.includes('bad') ? 'bad' : c.includes('warn') ? 'warn' : c.includes('ok') ? 'ok' : 'empty'; }
function clsCn(c) { return { ok: '正常', warn: '部分异常', bad: '异常', empty: '暂无数据' }[c] || '—'; }

/* ============ 顶部时钟 / 连接状态 ============ */
function tickClock() { $('clock').textContent = new Date().toISOString().slice(11, 19) + ' UTC'; }
function refreshState() {
  const s = LAST_OK ? Math.round((Date.now() - LAST_OK) / 1000) : null;
  if (FAILS >= 3) return '🔴 连接异常';
  if (FAILS > 0) return '⚠️ 更新失败；最后成功 ' + ageText(s);
  return '自动刷新正常 · ' + ageText(s);
}

/* ============ 系统状态（hero + KPI） ============ */
function renderStatus(o, s) {
  $('modeBadge').textContent = o.run_mode || '—';
  const dot = $('sysDot'); dot.className = 'bigdot ' + (o.system_cls || '');
  $('sysText').textContent = o.system_status || '未知';
  const run = (s.active || {}).run_id || '—';
  const mode = (s.mode_info || {});
  $('sysSub').textContent = `${o.run_mode || '—'} · ${o.instrument || 'XAUUSD'} · 数据源 ${mode.data_source || '—'} · ${o.stage || ''}`;
  // meta
  const el = o.stage_elapsed_s, rem = o.stage_remaining_s;
  $('heroMeta').innerHTML =
    `<div class="hm"><span class="k">运行模式</span><span class="v">${esc(o.run_mode || '—')}</span></div>` +
    `<div class="hm"><span class="k">真实下单</span><span class="v" style="color:${/否/.test(o.real_orders || '') ? 'var(--dim)' : 'var(--gold)'}">${esc(o.real_orders || '否')}</span></div>` +
    `<div class="hm"><span class="k">当前 Run</span><span class="v mono" style="font-size:11px">${esc(run)}</span></div>` +
    `<div class="hm"><span class="k">已运行</span><span class="v">${el == null ? '—' : hms(el)}</span></div>` +
    `<div class="hm"><span class="k">阶段结束</span><span class="v">${esc(String(o.stage_end || '—').replace('T', ' ').slice(0, 16))}</span></div>` +
    `<div class="hm"><span class="k">最后更新</span><span class="v">${esc(String(o.last_update || '—').replace('T', ' ').slice(11, 19))}</span></div>` +
    `<div class="hm" style="grid-column:1/-1"><span class="k">阶段进度</span><div class="prog"><i style="width:${Math.round(((s.active || {}).elapsed_frac || 0) * 100)}%"></i></div></div>`;
  const nw = s.next_window || {};
  $('heroNext').textContent = hms(nw.countdown_s);
  // KPIs
  const acc = o.account || {}, p = o.position || {};
  const pnl = (p.items || []).reduce((a, x) => a + (+x.profit || 0), 0);
  const dworst = worstCls(o.data_items);
  const mkt = o.market || {};
  const K = [
    { k: '系统状态', v: o.system_status || '未知', d: o.stage || '', c: o.system_cls || '' },
    { k: '运行模式', v: o.run_mode || '—', d: '真实下单：' + esc(o.real_orders || '否'), c: 'gold' },
    { k: '当前持仓', v: (p.count ?? 0) + ' <small>个</small>', d: '浮盈 ' + `<span class="${pnl >= 0 ? 'up' : 'down'}">${sgn(pnl, 2)}</span>`, c: 'vio' },
    { k: '账户权益', v: money(acc.equity), d: '余额 ' + money(acc.balance), c: 'cy' },
    { k: '数据健康', v: clsCn(dworst), d: '主源：' + esc(mkt.source || '—') + ' · ' + ageText(mkt.data_age_s), c: dworst },
    { k: '下一周期', v: hms(nw.countdown_s), d: esc(String(nw.next || '—').replace('T', ' ').slice(11, 16)) + ' UTC', c: '' },
  ];
  $('kpis').innerHTML = K.map(x => `<div class="kpi ${x.c}"><div class="k">${x.k}</div><div class="v">${x.v}</div><div class="d">${x.d}</div></div>`).join('');
}

/* ============ 交易决策 ============ */
function renderDecision(o) {
  const d = o.decision || {};
  const cls = d.decision === 'TRADE' ? 'ok' : (d.decision === 'WAIT' ? 'warn' : 'bad');
  $('decTag').innerHTML = `<span class="pill ${cls}">${esc(d.cn || DEC_CN[d.decision] || '未知')}</span>`;
  let b = '';
  if (d.decision === 'TRADE') {
    b = `<div class="gridkv">` +
      row('方向', `<b style="color:${d.side === 'LONG' ? 'var(--up)' : (d.side === 'SHORT' ? 'var(--down)' : 'var(--dim)')}">${esc(DIR[d.side] || d.side || '—')}</b>`) +
      row('候选机会', esc(d.candidate || '—')) +
      row('参考入场', num(d.entry)) + row('止损', num(d.sl)) +
      row('止盈', num(d.tp)) + row('风险收益比', d.rr != null ? '1 : ' + d.rr : '—') +
      row('信号可信度', d.confidence != null ? Math.round(d.confidence * 100) + '%' : '—') +
      row('执行结果', d.precheck_reject ? `<span style="color:var(--warn)">${esc(d.precheck_reject)}</span>` : '<span style="color:var(--up)">已发送/执行</span>') +
      `</div>`;
    if (d.precheck_reject) b += `<div class="sec-t">执行检查</div><div class="muted" style="text-align:left">交易机会存在，但执行检查未通过（${esc(d.precheck_reject)}）→ 本次未成交。</div>`;
    if (d.reason) b += `<div class="sec-t">决策依据</div><div class="muted" style="text-align:left">${esc(d.reason)}</div>`;
  } else if (d.decision === 'WAIT') {
    const why = (o.why_no_trade || []);
    b = `<div style="font-size:15px;font-weight:700;color:var(--warn);margin-bottom:6px">${esc(d.reason || '等待交易机会')}</div>`;
    if (d.candidate) b += `<div class="muted" style="text-align:left">观察机会：${esc(d.candidate)}${d.reason_category ? ' · ' + esc(d.reason_category) : ''}</div>`;
    b += `<div class="sec-t">为什么现在不交易</div><div style="line-height:1.95;font-size:12.5px">` +
      why.map(x => `• ${esc(x)}`).join('<br>') + `<br><b>系统选择：等待</b></div>`;
  } else {
    b = `<div style="font-size:15px;font-weight:700;color:var(--down)">${esc(d.cn || d.decision || '未知')}</div>` + (d.reason ? `<div class="muted" style="text-align:left">${esc(d.reason)}</div>` : '');
  }
  if ((o.proxies || []).length) {
    b += `<div class="sec-t">数据代理说明</div>` + o.proxies.map(p =>
      `<div class="muted" style="text-align:left;font-size:11px">• ${esc(p.var)} → 显示为「${esc(p.shown_as)}」｜来源 ${esc(p.source || '—')}｜${esc(p.reason || '')}</div>`).join('');
  }
  $('decision').innerHTML = b;
}

/* ============ 账户与持仓 ============ */
function renderAccount(o) {
  const a = o.account || {}, p = o.position || {};
  $('acctTag').innerHTML = `<span class="pill ${a.known ? 'ok' : 'warn'}">${a.known ? '已连接' : '无法确认'}</span>`;
  if (!a.known) { $('account').innerHTML = `<div class="muted">账户状态暂时无法确认（未用 0 掩盖未知）。</div>`; return; }
  let h = `<div class="accts">` +
    `<div class="acct"><div class="k">账户余额</div><div class="v">${money(a.balance)}</div><div class="d">${esc(a.account || a.login || 'FXTM Demo')}</div></div>` +
    `<div class="acct"><div class="k">账户权益</div><div class="v">${money(a.equity)}</div><div class="d">可用保证金 ${money(a.margin_free)} · 杠杆 ${a.leverage ? '1:' + a.leverage : '—'}</div></div>` +
    `</div>`;
  const items = p.items || [];
  h += `<div class="sec-t">当前持仓 ${p.known ? '(' + (p.count ?? items.length) + ')' : ''}</div>`;
  if (!p.known) h += `<div class="muted">无法读取持仓。</div>`;
  else if (!items.length) h += `<div class="muted">无持仓。</div>`;
  else {
    h += `<div class="scroll"><table><thead><tr><th>票号</th><th>方向</th><th>手数</th><th>开仓价</th><th>止损</th><th>止盈</th><th>浮盈</th></tr></thead><tbody>` +
      items.map(x => `<tr><td class="mono">${esc(x.ticket)}</td>` +
        `<td style="color:${x.side === 'LONG' ? 'var(--up)' : 'var(--down)'};font-weight:700">${esc(DIR[x.side] || x.side || '—')}</td>` +
        `<td class="mono">${num(x.volume, 2)}</td><td class="mono">${num(x.entry)}</td><td class="mono">${num(x.sl)}</td><td class="mono">${num(x.tp)}</td>` +
        `<td class="mono" style="color:${(+x.profit || 0) >= 0 ? 'var(--up)' : 'var(--down)'}">${sgn(x.profit)}</td></tr>`).join('') +
      `</tbody></table></div>`;
  }
  $('account').innerHTML = h;
}

/* ============ 系统健康 ============ */
function renderHealth(o) {
  const hs = o.health || [];
  const w = hs.some(h => h.cls === 'bad') ? 'bad' : (hs.some(h => h.cls === 'warn') ? 'warn' : 'ok');
  $('healthTag').innerHTML = `<span class="pill ${w}">${clsCn(w)}</span>`;
  $('health').innerHTML = `<div class="hlist">` + hs.map(h =>
    `<div class="hitem"><span class="hdot ${h.cls}"></span><span class="ht">${esc(h.name)}</span><span class="hv">${esc(h.text)}</span></div>`).join('') + `</div>`;
}

/* ============ 数据状态 ============ */
function renderData(o) {
  const items = o.data_items || [];
  const w = worstCls(items);
  $('dataTag').innerHTML = `<span class="pill ${w}">${clsCn(w)}</span>`;
  let h = `<div class="dl">` + items.map(i =>
    `<div class="drow"><span class="ddot ${i.cls}"></span><span class="nm">${esc(i.name)}</span>` +
    `<span class="src">${esc(i.source || '')}${i.age_s != null ? ' · ' + ageText(i.age_s) : ''}</span>` +
    `<span class="st ${i.cls}">${esc(i.status)}</span></div>`).join('') + `</div>`;
  $('data').innerHTML = h;
}

/* ============ 运行闭环总览 ============ */
function renderLoop(s) {
  const o = s.observability || {}, p = s.pipeline || {}, d = o.decision || {};
  const m = o.market || {}, a1 = s.agent1 || {}, a2 = s.agent2 || {}, acc = o.account || {}, pos = o.position || {};
  const mi = s.mode_info || {};
  const src = m.source || '—';
  const srcOk = /mt5/i.test(String(src));
  const a1Ok = !!((p.agent1 || {}).ok) && a1.age_s != null;
  const a2Ok = !!((p.agent2 || {}).ok);
  const dec = d.decision;
  const decCls = dec === 'TRADE' ? 'ok' : (dec === 'REJECT' ? 'bad' : (dec === 'WAIT' ? 'warn' : 'mute'));
  const ledger = p.ledger || {}, execn = p.execution || {};
  const modeCn = mi.execution_mode === 'BROKER_DEMO' ? '模拟盘真实下单' : (mi.execution_mode === 'PAPER' ? 'Paper 模拟' : (mi.execution_mode || '—'));
  const nodes = [
    { t: 'MT5 行情', v: num(m.price), s: esc(src) + ' · ' + ageText(m.data_age_s), c: srcOk ? 'ok' : 'warn' },
    { t: 'Agent1 技术', v: esc((a1.regime || {}).regime || '—'), s: a1.age_s != null ? ageText(a1.age_s) : '—', c: a1Ok ? 'ok' : 'bad' },
    { t: 'Agent2 宏观', v: esc(a2.gold_macro_state || '—'), s: a2.age_s != null ? ageText(a2.age_s) : '—', c: a2Ok ? 'ok' : 'bad' },
    { t: 'Hermes 决策', v: esc(d.cn || dec || '—'), s: esc(d.reason_category || d.reason_code || ''), c: decCls },
    { t: '执行', v: esc(modeCn), s: '成交 ' + (execn.executed ?? 0) + ' · 拒 ' + (execn.rejected ?? 0), c: 'ok' },
    { t: '账本 Ledger', v: (ledger.n ?? 0) + ' 事件', s: ledger.ok ? 'verify ✓' : 'verify ?', c: ledger.ok ? 'ok' : 'warn' },
    { t: '对账 Replay', v: ledger.replay === true ? 'MATCH' : (ledger.replay === false ? 'MISMATCH' : '—'), s: '账户 == 回放', c: ledger.replay === false ? 'bad' : 'ok' },
    { t: '账户', v: money(acc.equity), s: '持仓 ' + (pos.count ?? 0) + ' · ' + esc(o.real_orders || '否'), c: acc.known ? 'ok' : 'warn' },
  ];
  $('loop').innerHTML = nodes.map((n, i) =>
    `<div class="lnode ${n.c}"><div class="lhd"><span class="ldot"></span>${esc(n.t)}</div><div class="lv">${n.v}</div><div class="ls">${n.s}</div></div>` +
    (i < nodes.length - 1 ? '<div class="lconn">→</div>' : '')).join('');
  const nw = s.next_window || {};
  $('loopTag').innerHTML = '<span class="pill info">15 分钟循环</span>';
  $('loopFoot').innerHTML =
    `<span class="lp"><i></i>节奏：Windows 任务 · 每 15 分钟一轮（当前阶段 ${esc(o.stage || '—')}）</span>` +
    `<span class="lp"><i></i>下一轮 <b>${esc(String(nw.next || '—').replace('T', ' ').slice(11, 16))} UTC</b>（${hms(nw.countdown_s)}）</span>` +
    `<span class="lp"><i></i>数据源 <b>${esc(src)}</b> · 执行 <b>${esc(modeCn)}</b></span>` +
    `<span class="lp loopback"><i></i>↺ 闭环：MT5 → Agent1/Agent2 → Hermes → 执行 → 账本 → 对账 → 回到 MT5</span>`;
}

/* ============ 行情 ============ */
function renderMarket(o) {
  const m = o.market || {};
  const ch = m.chg_bps;
  $('mktTag').innerHTML = `<span class="pill ${worstCls(o.data_items) === 'ok' ? 'ok' : 'warn'}">${esc(m.source || '—')}</span>`;
  let h = `<div class="gridkv">` +
    row('最新价', `<b class="mono" style="font-size:15px">${num(m.price)}</b>`) +
    row('点差', `<span class="mono">${num(m.spread, 2)}</span>`) +
    row('日内高 / 低', `<span class="mono">${num(m.high)} / ${num(m.low)}</span>`) +
    row('涨跌', `<span class="mono" style="color:${ch >= 0 ? 'var(--up)' : 'var(--down)'}">${ch == null ? '—' : sgn(ch, 1) + ' bp'}</span>`) +
    row('ATR(15m)', `<span class="mono">${m.atr_pct == null ? '—' : num(m.atr_pct, 3) + '%'}</span>`) +
    row('数据时效', ageText(m.data_age_s)) +
    `</div>`;
  const ms = o.multi_tf || [];
  if (ms.length) {
    h += `<div class="sec-t">多周期倾向</div><table><thead><tr><th>周期</th><th>短线</th><th>趋势</th></tr></thead><tbody>` +
      ms.map(r => `<tr><td>${esc(r.tf)}</td><td>${esc(r.bias)}</td><td>${esc(r.trend)}</td></tr>`).join('') + `</tbody></table>`;
  }
  $('market').innerHTML = h;
}

/* ============ 运行调度 ============ */
function renderSched(o) {
  const s = o.scheduler || {};
  const ok = s.status_cls === 'ok';
  $('schedTag').innerHTML = `<span class="pill ${ok ? 'ok' : 'warn'}">${ok ? '正常' : '注意'}</span>`;
  const nw = (LAST && LAST.next_window) || {};
  $('sched').innerHTML = `<div class="gridkv">` +
    row('自动运行', ok ? '<span style="color:var(--up)">正常</span>' : '<span style="color:var(--warn)">注意</span>') +
    row('调度方式', 'Windows 任务 · 15m') +
    row('上次运行', esc(String(s.last_run || '—').replace('T', ' ').slice(0, 19))) +
    row('下次运行', esc(String(nw.next || '—').replace('T', ' ').slice(0, 19))) +
    row('错过轮次', String(s.missed ?? 0)) +
    row('上次失败', s.last_failure ? esc(String(s.last_failure).replace('T', ' ').slice(0, 19)) : '无') +
    `</div>`;
}

/* ============ 最近交易 ============ */
function renderTrades(o) {
  const ts = o.recent_trades || [];
  $('trTag').innerHTML = `<span class="pill ${ts.length ? 'info' : ''}">${ts.length ? ts.length + ' 笔' : '无'}</span>`;
  if (!ts.length) { $('trades').innerHTML = `<div class="muted">暂无已平仓交易。</div>`; return; }
  $('trades').innerHTML = `<div class="scroll"><table><thead><tr><th>时间</th><th>方向</th><th>出场</th><th>结果</th><th>净盈亏</th></tr></thead><tbody>` +
    ts.map(t => `<tr><td>${esc(String(t.ts || '').replace('T', ' ').slice(5, 16))}</td>` +
      `<td>${esc(DIR[t.side] || t.side || '—')}</td><td class="mono">${num(t.exit)}</td>` +
      `<td>${esc(t.result)}</td><td class="mono" style="color:${(+t.net || 0) >= 0 ? 'var(--up)' : 'var(--down)'}">${sgn(t.net)}</td></tr>`).join('') +
    `</tbody></table></div>`;
}

/* ============ 高级：净值曲线 ============ */
function drawEquity(s) {
  const c = $('eqChart'); if (!c || !c.getContext) return;
  const pts = s.equity_curve || [];
  const ctx = c.getContext('2d'); const W = c.width = c.clientWidth || 560, H = c.height;
  ctx.clearRect(0, 0, W, H);
  if (pts.length < 2) { ctx.fillStyle = '#61708a'; ctx.font = '12px sans-serif'; ctx.fillText('数据点不足', 12, 20); $('eqLegend').innerHTML = ''; return; }
  const eq = pts.map(p => +p.equity), bl = pts.map(p => +p.balance);
  const all = eq.concat(bl).filter(v => !isNaN(v));
  const mn = Math.min(...all), mx = Math.max(...all), pad = (mx - mn) * 0.15 || 1;
  const y = v => H - 16 - ((v - (mn - pad)) / ((mx + pad) - (mn - pad))) * (H - 32);
  const x = i => 10 + i * (W - 20) / (pts.length - 1);
  const line = (arr, color) => { ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = 2; arr.forEach((v, i) => i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v))); ctx.stroke(); };
  ctx.strokeStyle = 'rgba(125,156,224,.12)'; ctx.lineWidth = 1;
  for (let g = 0; g <= 3; g++) { const yy = 16 + g * (H - 32) / 3; ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(W, yy); ctx.stroke(); }
  line(bl, '#4f8cff'); line(eq, '#22d3ee');
  $('eqLegend').innerHTML = `<span><i style="background:#22d3ee"></i>权益 ${money(eq[eq.length - 1])}</span><span><i style="background:#4f8cff"></i>余额 ${money(bl[bl.length - 1])}</span><span class="muted">区间 ${money(mn)} – ${money(mx)}</span>`;
  $('eqTag').textContent = pts.length + ' 点';
}

/* ============ 高级：决策构成 donut ============ */
function drawDonut(s) {
  const c = $('donut'); if (!c || !c.getContext) return;
  const p = (s.observability || {}).performance || {};
  const segs = [{ n: '交易机会', v: p.TRADE || 0, c: '#22c55e' }, { n: '等待', v: p.WAIT || 0, c: '#f59e0b' }, { n: '拒绝', v: p.REJECT || 0, c: '#ef4444' }];
  const total = segs.reduce((a, x) => a + x.v, 0);
  const ctx = c.getContext('2d'); const W = c.width, H = c.height, cx = W / 2, cy = H / 2, R = Math.min(W, H) / 2 - 6, r = R * 0.6;
  ctx.clearRect(0, 0, W, H);
  if (!total) { ctx.fillStyle = '#61708a'; ctx.font = '12px sans-serif'; ctx.fillText('暂无决策', cx - 28, cy); $('donutLegend').innerHTML = ''; return; }
  let a0 = -Math.PI / 2;
  segs.forEach(sg => { if (!sg.v) return; const a1 = a0 + sg.v / total * Math.PI * 2; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, R, a0, a1); ctx.closePath(); ctx.fillStyle = sg.c; ctx.fill(); a0 = a1; });
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fillStyle = '#101826'; ctx.fill();
  ctx.fillStyle = '#fff'; ctx.font = 'bold 20px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(total, cx, cy + 2); ctx.font = '10px sans-serif'; ctx.fillStyle = '#61708a'; ctx.fillText('决策数', cx, cy + 18);
  $('donutLegend').innerHTML = segs.map(sg => `<div class="kv" style="border:none;padding:3px 0"><span class="k"><i style="display:inline-block;width:9px;height:9px;border-radius:3px;background:${sg.c};margin-right:6px"></i>${sg.n}</span><span class="v">${sg.v} · ${total ? Math.round(sg.v / total * 100) : 0}%</span></div>`).join('');
  $('donutTag').textContent = '本周 Run';
}

/* ============ 高级：sizing ============ */
function renderSizing(s) {
  const rows = s.sizing || [];
  $('sizingTbl').innerHTML = `<thead><tr><th>时间</th><th>方向</th><th>入场</th><th>止损</th><th>点数</th><th>原始手</th><th>取整手</th><th>max</th><th>状态</th></tr></thead><tbody>` +
    rows.map(r => `<tr><td>${esc(String(r.window || '').replace('T', ' ').slice(5, 16))}</td><td>${esc(DIR[r.side] || r.side || '—')}</td>` +
      `<td class="mono">${num(r.entry)}</td><td class="mono">${num(r.sl)}</td><td class="mono">${num(r.dist, 1)}</td>` +
      `<td class="mono">${num(r.raw_lot, 4)}</td><td class="mono">${num(r.floored_lot, 2)}</td><td class="mono">${num(r.max_lot, 2)}</td>` +
      `<td>${esc(r.sizing_status || (r.reject_reason || '—'))}</td></tr>`).join('') + `</tbody>`;
}

/* ============ 高级：账本 ============ */
function renderLedger(s) {
  const ev = (s.ledger_tail || []).slice().reverse();
  $('ledTag').innerHTML = `<span class="pill">${ev.length} 条</span>`;
  $('ledTbl').innerHTML = `<thead><tr><th>seq</th><th>类型</th><th>状态</th><th>方向</th><th>手</th><th>价</th><th>净</th><th>时间</th></tr></thead><tbody>` +
    ev.map(e => `<tr><td class="mono">${e.seq}</td><td>${esc(e.type)}</td><td>${esc(e.status || e.retcode || '')}</td><td>${esc(e.side || '')}</td>` +
      `<td class="mono">${e.qty == null ? '' : num(e.qty, 2)}</td><td class="mono">${e.price == null ? '' : num(e.price)}</td><td class="mono">${e.net == null ? '' : sgn(e.net)}</td>` +
      `<td>${esc(String(e.ts || '').replace('T', ' ').slice(11, 19))}</td></tr>`).join('') + `</tbody>`;
}

/* ============ 高级：Agent1 ============ */
function renderA1(s) {
  const a = s.agent1 || {};
  $('a1Tag').innerHTML = a.age_s != null ? `<span class="pill">${ageText(a.age_s)}</span>` : '';
  let h = row('市场状态', esc((a.regime || {}).regime || '—') + ' · 波动 ' + esc((a.regime || {}).vol_state_15m || '—'));
  const rows = a.rows || [];
  if (rows.length) h += `<div class="sec-t">多周期</div><table><thead><tr><th>周期</th><th>收盘</th><th>RSI</th><th>SMA20</th><th>SMA50</th><th>结构</th></tr></thead><tbody>` +
    rows.map(r => `<tr><td>${esc(r.tf)}</td><td class="mono">${num(r.close)}</td><td class="mono">${num(r.rsi, 1)}</td><td class="mono">${num(r.sma20)}</td><td class="mono">${num(r.sma50)}</td><td>${esc(r.state)}</td></tr>`).join('') + `</tbody></table>`;
  const cds = a.candidates || [];
  if (cds.length) h += `<div class="sec-t">候选机会</div>` + cds.map(c => `<div class="muted" style="text-align:left;font-size:11.5px">• ${esc(c.id)} · ${esc(c.dir_hint || '')} · ${esc(c.type || '')}</div>`).join('');
  $('a1').innerHTML = h;
}

/* ============ 高级：Agent2 ============ */
function renderA2(s) {
  const a = s.agent2 || {};
  $('a2Tag').innerHTML = a.age_s != null ? `<span class="pill">${ageText(a.age_s)}</span>` : '';
  let h = `<div class="gridkv">` +
    row('黄金宏观', esc(a.gold_macro_state || '—')) + row('美元', num(a.usd, 3) + (a.usd_chg != null ? ' (' + sgn(a.usd_chg, 2) + ')' : '')) +
    row('UST10Y(代理)', num(a.ust10y, 2)) + row('实际利率', num(a.real_rate, 2)) +
    row('证据数', String(a.n_evidence ?? '—')) + row('宏观缺口', String((a.data_gaps || []).length)) +
    `</div>`;
  const geo = ((a.geo || {}).events || []).slice(0, 5);
  if (geo.length) h += `<div class="sec-t">地缘/事件</div>` + geo.map(e => `<div class="muted" style="text-align:left;font-size:11.5px">• ${esc(String(e.title || '').slice(0, 60))} <span style="color:var(--dim2)">[${esc(e.source || '')}]</span></div>`).join('');
  $('a2').innerHTML = h;
}

/* ============ 高级：全部 Run ============ */
function renderRuns(s) {
  const rs = s.runs || [];
  $('runsTag').innerHTML = `<span class="pill">${rs.length} 个</span>`;
  $('runsTbl').innerHTML = `<thead><tr><th>Run</th><th>状态</th><th>轮</th><th>TRADE</th><th>成交</th><th>开始</th></tr></thead><tbody>` +
    rs.map(r => `<tr><td class="mono" style="font-size:10.5px">${esc(r.run_id)}</td><td>${esc(r.status || '')}</td>` +
      `<td class="mono">${(r.counters || {}).cycles ?? ''}</td><td class="mono">${(r.counters || {}).TRADE ?? ''}</td>` +
      `<td class="mono">${(r.counters || {}).exec_executed ?? ''}</td><td>${esc(String(r.start || '').replace('T', ' ').slice(5, 16))}</td></tr>`).join('') + `</tbody>`;
}

/* ============ 高级：问题 / V1 ============ */
function renderProblems(o) {
  const ps = o.recent_problems || [];
  $('probTag').innerHTML = `<span class="pill ${ps.length ? 'warn' : 'ok'}">${ps.length ? ps.length + ' 条' : '无'}</span>`;
  $('problems').innerHTML = ps.length ? ps.map(p => `<div class="muted" style="text-align:left;font-size:11.5px">• ${esc(p.ts || '')} · ${esc(p.problem)} · ${esc(p.detail)}</div>`).join('')
    : `<div class="muted">近期无异常。</div>`;
}
function renderV1(o) {
  const v = o.v1_isolation || {};
  $('v1Tag').innerHTML = `<span class="pill ok">${esc(v.status || '—')}</span>`;
  $('v1').innerHTML = (v.items || []).map(x => `<div class="hitem"><span class="hdot ok"></span><span class="ht">${esc(x)}</span></div>`).join('');
}

/* ============ 决策层：Agent1 / Agent2 / Hermes ============ */
function fmtT(ts) { return ts ? String(ts).replace('T', ' ').slice(11, 19) : '—'; }
function agentBox(title, cycle, age, rows) {
  const meta = (cycle ? esc(String(cycle).slice(5, 16)) : '') + (age != null ? (cycle ? ' · ' : '') + ageText(age) : '');
  return `<div class="ab-hd"><span class="ab-t">${esc(title)}</span><span class="ab-c muted">${meta}</span></div>` +
    `<div class="ab-body">` + rows.map(r => `<div class="kv"><span class="k">${r[0]}</span><span class="v">${r[1]}</span></div>`).join('') + `</div>`;
}
function renderDecisionLayer(s) {
  const a1 = s.agent1 || {}, a2 = s.agent2 || {}, o = s.observability || {}, d = o.decision || {};
  const rg = a1.regime || {}, rows = a1.rows || [], cds = a1.candidates || [];
  const q = (a1.quote || {}).gold_spot || {};
  const r15 = rows.filter(r => r.tf === '15m')[0] || {};
  $('dlA1').innerHTML = agentBox('Agent1 · 技术 / 市场', a1.cycle, a1.age_s, [
    ['市场状态', esc(rg.regime || '—') + ' · 波动 ' + esc(rg.vol_state_15m || '—')],
    ['15m', (r15.rsi != null ? 'RSI ' + num(r15.rsi, 1) : '—') + ' · ' + esc(r15.state || '—')],
    ['候选机会', cds.length + ' 个' + (cds.length ? '：' + esc(cds.map(c => c.id || '').join(', ').slice(0, 44)) : '')],
    ['现价源', esc(q.source || '—') + (q.price != null ? ' · ' + num(q.price) : '')],
  ]);
  const geo = ((a2.geo || {}).events) || [];
  $('dlA2').innerHTML = agentBox('Agent2 · 宏观 / 地缘', a2.cycle, a2.age_s, [
    ['黄金宏观', esc(a2.gold_macro_state || '—')],
    ['美元 / UST10Y', num(a2.usd, 3) + ' / ' + num(a2.ust10y, 2)],
    ['实际利率', num(a2.real_rate, 2)],
    ['证据 / 缺口', String(a2.n_evidence ?? '—') + ' / ' + String((a2.data_gaps || []).length)],
    ['地缘事件', geo.length + ' 条' + (geo[0] ? '：' + esc(String(geo[0].title || '').slice(0, 26)) : '')],
  ]);
  $('dlH').innerHTML = agentBox('Hermes · 决策', null, null, [
    ['最新决策', `<b>${esc(d.cn || d.decision || '—')}</b>`],
    ['原因类别', esc(d.reason_category || d.reason_code || '—')],
    ['观察机会', esc(d.candidate || '—')],
    ['执行结果', d.precheck_reject ? `<span style="color:var(--warn)">${esc(d.precheck_reject)}</span>` : (d.decision === 'TRADE' ? '<span style="color:var(--up)">已执行</span>' : '—')],
  ]);
  const team = (s.team || []).slice().reverse().slice(0, 12);
  $('dlTag').innerHTML = `<span class="pill">近 ${team.length} 轮</span>`;
  $('dlTbl').innerHTML = '<thead><tr><th>窗口</th><th>Agent1</th><th>Agent2</th><th>Hermes</th><th>原因</th><th>replay</th></tr></thead><tbody>' +
    team.map(t => {
      const dec = t.decision || '—';
      const c = dec === 'TRADE' ? 'var(--up)' : (dec === 'REJECT' ? 'var(--down)' : 'var(--warn)');
      return `<tr><td class="mono">${esc(String(t.decision_window || '').slice(5, 16))}</td>` +
        `<td>${fmtT(t.agent1_generated_utc)} <span class="muted" style="font-size:10px">${esc(t.agent1_freshness || '')}</span></td>` +
        `<td>${fmtT(t.agent2_snapshot_ts)}</td>` +
        `<td style="color:${c};font-weight:700">${esc(DEC_CN[dec] || dec)}</td>` +
        `<td>${esc(t.reason_category || t.reason_code || '')}</td>` +
        `<td>${t.replay_match === true ? '✓' : (t.replay_match === false ? '✗' : '')}</td></tr>`;
    }).join('') + '</tbody>';
}

/* ============ 主渲染 ============ */
function render(s) {
  LAST = s;
  const o = s.observability || {};
  renderStatus(o, s); renderDecision(o); renderDecisionLayer(s); renderAccount(o); renderHealth(o); renderData(o);
  renderLoop(s); renderMarket(o); renderSched(o); renderTrades(o);
  try { drawEquity(s); drawDonut(s); renderSizing(s); renderLedger(s); renderA1(s); renderA2(s); renderRuns(s); renderProblems(o); renderV1(o); } catch (e) { /* keep main view alive */ }
  $('foot').textContent = `系统最后更新 ${new Date().toLocaleString('zh-CN', { hour12: false })} · 只读 · 独立于 V1（8787） · V2 控制面板`;
}

/* ============ 启动 ============ */
function start() {
  setInterval(tickClock, 1000); tickClock();
  setInterval(() => { const t = refreshState(); $('refreshState') && ($('refreshState').textContent = t); }, 1000);
  fetch('/api/snapshot', { cache: 'no-store' }).then(r => r.json()).then(s => { render(s); LAST_OK = Date.now(); FAILS = 0; }).catch(() => FAILS++);
  try {
    EVT = new EventSource('/api/stream');
    EVT.addEventListener('snap', e => { $('live').className = 'live'; $('liveTxt').textContent = '实时更新'; try { render(JSON.parse(e.data)); LAST_OK = Date.now(); FAILS = 0; } catch (_) { FAILS++; } });
    EVT.onerror = () => { $('live').className = 'live off'; $('liveTxt').textContent = '轮询模式'; };
  } catch (_) { }
  setInterval(async () => { if (EVT && EVT.readyState === 1) return; try { render(await (await fetch('/api/snapshot', { cache: 'no-store' })).json()); LAST_OK = Date.now(); FAILS = 0; } catch (_) { FAILS++; } }, 5000);
}
start();
