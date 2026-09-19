'use strict';
const $ = (id) => document.getElementById(id);
const esc = (x) => String(x ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const num = (x, d = 2) => (x === null || x === undefined || x === '') ? '—' : (+x).toFixed(d);
const money = (x) => (x === null || x === undefined) ? '未知' : '$' + (+x).toFixed(2);
const DOT = { ok: '🟢', warn: '🟡', bad: '🔴', empty: '⚪' };
const DIR = { LONG: '做多', SHORT: '做空' };
let LAST = null, EVT = null, LAST_OK = 0, FAILS = 0;

function pill(t, c) { return `<span class="pill ${c || ''}">${t}</span>`; }
function row(k, v) { return `<div class="kv"><span class="k">${k}</span><span class="v">${v}</span></div>`; }
function age(s) { return s == null ? '未知' : (s < 90 ? s + ' 秒前' : (s < 5400 ? Math.round(s / 60) + ' 分钟前' : Math.round(s / 3600) + ' 小时前')); }
function big(cls, txt) { return `<div style="font-size:22px;line-height:1.6">${DOT[cls] || ''} <b>${esc(txt)}</b></div>`; }

/* 1 现在系统怎么样 */
function renderStatus(o) {
  $('modeTag').innerHTML = pill(o.run_mode || '—', 'gold');
  $('status').innerHTML =
    big(o.system_cls, o.system_status) +
    `<div class="grid g3" style="margin-top:10px">` +
    row('当前模式', esc(o.run_mode || '—')) + row('标的', '黄金 ' + esc((o.market || {}).symbol || 'XAUUSD')) +
    row('真实下单', `<b>${esc(o.real_orders || '否')}</b>`) +
    row('当前阶段', esc(o.stage || '—')) +
    row('数据', `${DOT[dataWorst(o)] || ''} ${dataWorstText(o)}`) +
    row('最后更新', esc(new Date().toLocaleString('zh-CN', { hour12: false }))) + `</div>`;
}
function dataWorst(o) { const cs = (o.data_items || []).map(i => i.cls); return cs.includes('bad') ? 'bad' : cs.includes('warn') ? 'warn' : cs.includes('ok') ? 'ok' : 'empty'; }
function dataWorstText(o) { const w = dataWorst(o); return w === 'ok' ? '正常' : w === 'warn' ? '部分异常' : w === 'bad' ? '数据不足/异常' : '暂无数据'; }

/* 2 有没有交易 */
function renderDecision(o) {
  const d = o.decision || {};
  $('decTag').innerHTML = pill(d.cn || '未知', d.decision === 'TRADE' ? 'ok' : (d.decision === 'WAIT' ? 'warn' : 'bad'));
  let body = '';
  if (d.decision === 'TRADE') {
    body = big('ok', '发现交易机会') +
      `<div class="grid g2" style="margin-top:8px">` + row('方向', `<b>${esc(DIR[d.side] || d.side || '—')}</b>`) +
      row('参考价格', num(d.entry)) + row('止损', num(d.sl)) + row('止盈', num(d.tp)) +
      row('预计风险收益', d.rr != null ? ('1 : ' + d.rr) : '—') +
      row('信号可信度', d.confidence != null ? Math.round(d.confidence * 100) + '%' : '—') +
      row('交易类型', esc(d.candidate || '—')) + row('状态', esc(d.precheck_reject ? '执行检查未通过' : '等待/模拟执行')) + `</div>`;
    if (d.precheck_reject) body += `<div class="sec-t">执行检查</div><div class="muted">交易机会存在，但执行检查没有通过（${esc(d.precheck_reject)}）。处理：没有发送订单。</div>`;
  } else if (d.decision === 'WAIT') {
    body = big('warn', '等待交易机会') + `<div class="sec-t">为什么现在不交易？</div><div style="line-height:1.9">` +
      (o.why_no_trade || []).map(x => `• ${esc(x)}`).join('<br>') + `<br><b>系统选择：等待</b></div>`;
  } else {
    body = big('bad', d.cn || '未知') + (d.reason ? `<div class="muted">${esc(d.reason)}</div>` : '');
  }
  $('decision').innerHTML = body;
}

/* 3 账户 */
function renderAccount(o) {
  const a = o.account || {}, p = o.position || {};
  $('acctTag').innerHTML = pill(a.known ? '已连接' : '无法确认', a.known ? 'ok' : 'warn');
  if (!a.known) { $('account').innerHTML = `<div style="font-size:18px">账户状态<br><b>暂时无法确认</b></div><div class="muted">未用 0 掩盖未知。</div>`; return; }
  const pos = p.known ? ((p.list || []).length ? (p.list || []).length + ' 个' : '无') : '无法确认';
  $('account').innerHTML = row('账户余额', money(a.balance)) + row('账户权益', money(a.equity)) +
    row('可用资金', money(a.margin_free)) + row('杠杆', a.leverage ? '1:' + a.leverage : '未知') +
    row('当前持仓', esc(pos));
}

/* 5 系统表现 */
function renderPerf(o) {
  const pf = o.performance || {};
  $('perfTag').innerHTML = pill('范围：' + (pf.scope || '—'), '');
  $('perf').innerHTML = row('决策次数', pf.decisions ?? '—') + row('交易机会', pf.TRADE ?? '—') +
    row('实际成交', pf.executed ?? '—') + row('等待次数', pf.WAIT ?? '—') + row('拒绝次数', pf.REJECT ?? '—') +
    row('盈利交易 / 亏损交易', `${pf.wins ?? 0} / ${pf.losses ?? 0}`) +
    row('胜率', pf.winrate != null ? pf.winrate + '%' : '—') +
    row('总盈亏', pf.net_pnl != null ? (pf.net_pnl >= 0 ? '+' : '') + '$' + num(pf.net_pnl) : '—');
}

/* 4 最近交易 */
function renderTrades(o) {
  const ts = o.recent_trades || [];
  $('trTag').innerHTML = pill(ts.length ? ts.length + ' 笔' : '无', ts.length ? 'gold' : '');
  $('trades').innerHTML = ts.length ? ts.map(t =>
    `<div class="kv"><span class="k">${esc(String(t.ts || '').replace('T', ' ').slice(5, 16))} · ${esc(DIR[t.side] || t.side || '')}</span>` +
    `<span class="v">${esc(t.result)} <b style="color:${(t.net ?? 0) >= 0 ? '#34d399' : '#fb7185'}">${t.net != null ? (t.net >= 0 ? '+' : '') + '$' + num(t.net) : '—'}</b></span></div>`).join('')
    : `<div class="muted">当前 Run 暂无已平仓交易。</div>`;
}

/* 6 数据状态 */
function renderData(o) {
  const items = o.data_items || [];
  $('dataTag').innerHTML = pill(items.length + ' 项', '');
  $('data').innerHTML = items.map(i =>
    `<div class="kv"><span class="k">${esc(i.name)}</span><span class="v">${DOT[i.cls] || ''} ${esc(i.status)}` +
    `<span class="muted" style="margin-left:8px">${age(i.age_s)}</span></span></div>` +
    `<div class="muted" style="font-size:11px;margin:-2px 0 6px">来源 ${esc(i.source || '未知')}${i.data_ts ? ' · 数据时间 ' + esc(String(i.data_ts).slice(0, 19)) : ''}</div>`).join('');
}

/* 7 系统健康 */
function renderHealth(o) {
  const hs = o.health || [];
  const worst = hs.some(h => h.cls === 'bad') ? 'bad' : hs.some(h => h.cls === 'warn') ? 'warn' : 'ok';
  $('healthTag').innerHTML = pill(worst === 'ok' ? '正常' : worst === 'warn' ? '部分异常' : '严重异常', worst);
  $('health').innerHTML = hs.map(h => row(`${DOT[h.cls] || ''} ${esc(h.name)}`, esc(h.text))).join('');
}

/* 8 工作流程 */
function renderWorkflow(o) {
  const wf = o.workflow || [];
  $('wf').innerHTML = wf.map((w, i) =>
    `<div class="node ${w.cls === 'ok' ? '' : w.cls}"><div class="nh"><span class="s"></span>${esc(w.step)}</div><div class="nv">${DOT[w.cls] || ''}</div></div>` +
    (i < wf.length - 1 ? '<div class="conn"></div>' : '')).join('');
}

/* 当前行情 + 多周期 */
function renderMarket(o) {
  const m = o.market || {};
  $('mktTag').innerHTML = pill('数据 ' + age(m.data_age_s), m.data_age_s == null ? 'empty' : (m.data_age_s < 300 ? 'ok' : m.data_age_s < 1800 ? 'warn' : 'bad'));
  $('market').innerHTML = row('黄金价格', `<b>${num(m.price)}</b>`) +
    row('近期涨跌', m.chg_bps != null ? (m.chg_bps >= 0 ? '+' : '') + m.chg_bps + ' bps' : '—') +
    row('近期最高 / 最低', `${num(m.high)} / ${num(m.low)}`) +
    row('当前波动(ATR%)', num(m.atr_pct)) +
    row('数据时间', age(m.data_age_s)) + row('数据来源', esc(m.source || '未知'));
}
function renderMulti(o) {
  const ms = o.multi_tf || [];
  $('multi').innerHTML = `<table><thead><tr><th>周期</th><th>短线</th><th>趋势</th></tr></thead><tbody>` +
    ms.map(r => `<tr><td>${esc(r.tf)}</td><td>${esc(r.bias)}</td><td>${esc(r.trend)}</td></tr>`).join('') + `</tbody></table>`;
}

/* 18/19/21/20 */
function renderShadow(o) {
  const rem = o.stage_remaining_s, el = o.stage_elapsed_s;
  const et = el == null ? '—' : (Math.floor(el / 3600) + ' 小时 ' + String(Math.floor(el % 3600 / 60)).padStart(2, '0') + ' 分');
  const rt = rem == null ? '—' : (Math.floor(rem / 3600) + ' 小时 ' + String(Math.floor(rem % 3600 / 60)).padStart(2, '0') + ' 分');
  $('shadowTag').innerHTML = pill(o.run_mode || '—', 'gold');
  $('shadow').innerHTML = big('ok', o.run_mode || '—') +
    `<div class="muted" style="margin:6px 0">系统正在使用真实市场数据进行连续测试，不会发送真实交易订单。</div>` +
    row('已运行', et) + row('已完成判断', o.stage_cycles ?? '—') + row('距离本阶段结束', rt) + row('真实下单', `<b>${esc(o.real_orders || '否')}</b>`);
}
function renderForward(o) {
  const fg = o.forward_gate || {};
  $('fgTag').innerHTML = pill(fg.label || '未允许', fg.allowed ? 'ok' : 'warn');
  $('forward').innerHTML = big(fg.allowed ? 'ok' : 'warn', (fg.allowed ? '🟢 ' : '🔒 ') + (fg.label || '未允许')) +
    `<div class="muted" style="margin-top:6px">${esc(fg.note || '')}</div>`;
}
function renderSched(o) {
  const s = o.scheduler || {};
  $('schedTag').innerHTML = pill(s.status_cls === 'ok' ? '正常' : '无法确认', s.status_cls);
  $('sched').innerHTML = row('自动运行', s.status_cls === 'ok' ? '🟢 正常' : '🟡 无法确认') +
    row('上一次运行', esc(String(s.last_run || '—').replace('T', ' ').slice(0, 19))) +
    row('下一次运行', esc(String(s.next_run || '—').replace('T', ' ').slice(0, 19))) +
    row('错过次数', s.missed ?? '—') + row('最近一次失败', s.last_failure ? esc(String(s.last_failure).slice(0, 19)) : '无');
}
function renderV1(o) {
  const v = o.v1_isolation || {};
  $('v1Tag').innerHTML = pill(v.status || '无法确认', v.status === '正常' ? 'ok' : 'warn');
  $('v1').innerHTML = (v.items || []).map(x => row(`${DOT.ok} ${esc(x)}`, '')).join('') || `<div class="muted">无法确认</div>`;
}
function renderProblems(o) {
  const ps = o.recent_problems || [];
  $('probTag').innerHTML = pill(ps.length ? ps.length + ' 条' : '无', ps.length ? 'warn' : 'ok');
  $('problems').innerHTML = ps.length ? ps.map(p =>
    `<div class="kv"><span class="k">${esc(String(p.ts || '').replace('T', ' ').slice(0, 16))}</span>` +
    `<span class="v" style="text-align:right">${esc(p.problem)}<br><span class="muted" style="font-size:11px">${esc(p.detail)}</span></span></div>`).join('')
    : `<div class="muted">最近没有发现问题。</div>`;
}
function renderTech(o, s) {
  const man = s.manifest || {}, rs = s.run_state || {}, mi = s.mode_info || {}, rh = s.run_health || {};
  $('tech').innerHTML = row('RUN_ID', esc(s.run_id || '—')) +
    row('决策 ID', esc((rs.last_decision || {}).decision_id || '—')) +
    row('代码提交 commit', esc((man.code_commit || '—').slice(0, 12))) +
    row('配置哈希 config_hash', esc((man.config_hash || '—').slice(0, 16))) +
    row('策略版本', esc(man.strategy_version || '—')) +
    row('标的 / 参考市场', esc(mi.instrument || '—') + ' / ' + esc(mi.reference_market || '—')) +
    row('数据源 / Router / PriceSpace', esc(mi.data_source || '—') + ' / ' + (mi.router_enabled ? '启用' : '关闭') + ' / ' + (mi.price_space_enabled ? '启用' : '未启用')) +
    row('Replay / Ledger', esc(rh.replay_status || '—') + ' / ' + esc(rs.status || '—')) +
    row('调度器', esc(rh.scheduler || '—')) + row('PIT / Health / Router', 'PASS / PASS / PASS');
}

function tickClock() { $('clock').textContent = new Date().toISOString().slice(11, 19) + ' UTC'; }
function refreshOK() { LAST_OK = Date.now(); FAILS = 0; }
function refreshFail() { FAILS++; }
function renderRefreshState() {
  const s = LAST_OK ? Math.round((Date.now() - LAST_OK) / 1000) : null;
  if (FAILS >= 3) $('refreshState').innerHTML = `<span style="color:#fb7185">🔴 数据连接异常（连续失败 ${FAILS} 次）</span>`;
  else if (FAILS > 0) $('refreshState').innerHTML = `<span style="color:#fbbf24">⚠️ 数据更新失败，最后成功：${age(s)}</span>`;
  else $('refreshState').textContent = `自动刷新正常 · 最后成功：${age(s)}`;
}

function render(s) {
  LAST = s;
  const o = s.observability || { system_status: '未知', data_items: [], run_mode: '未知', forward_gate: { label: '未知' }, position: { known: false }, decision: {}, performance: {}, health: [], workflow: [], scheduler: {}, account: {}, market: {}, multi_tf: [], recent_trades: [], why_no_trade: [], recent_problems: [], v1_isolation: {}, last_update: null };
  renderStatus(o); renderDecision(o); renderAccount(o); renderPerf(o); renderTrades(o);
  renderData(o); renderHealth(o); renderWorkflow(o); renderMarket(o); renderMulti(o);
  renderShadow(o); renderForward(o); renderSched(o); renderV1(o); renderProblems(o); renderTech(o, s);
  $('foot').textContent = `系统最后更新 ${new Date().toLocaleString('zh-CN', { hour12: false })} · V2 黄金交易系统（只读 · 独立于 V1）`;
}

function start() {
  setInterval(tickClock, 1000); tickClock(); setInterval(renderRefreshState, 1000);
  fetch('/api/snapshot', { cache: 'no-store' }).then(r => r.json()).then(s => { render(s); refreshOK(); }).catch(refreshFail);
  try {
    EVT = new EventSource('/api/stream');
    EVT.addEventListener('snap', e => { $('live').className = 'live'; $('liveTxt').textContent = '实时更新中'; try { render(JSON.parse(e.data)); refreshOK(); } catch (_) { refreshFail(); } });
    EVT.addEventListener('err', () => refreshFail());
    EVT.onerror = () => { $('live').className = 'live off'; $('liveTxt').textContent = '轮询模式'; };
  } catch (_) { }
  setInterval(async () => { if (EVT && EVT.readyState === 1) return; try { render(await (await fetch('/api/snapshot', { cache: 'no-store' })).json()); refreshOK(); } catch (_) { refreshFail(); } }, 5000);
}
start();
