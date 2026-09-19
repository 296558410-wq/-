'use strict';
const $ = (id) => document.getElementById(id);
const esc = (x) => String(x ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const num = (x, d = 2) => (x === null || x === undefined || x === '') ? '鈥? : (+x).toFixed(d);
const money = (x) => (x === null || x === undefined) ? '鏈煡' : '$' + (+x).toFixed(2);
const DOT = { ok: '馃煝', warn: '馃煛', bad: '馃敶', empty: '鈿? };
const DEC_CN = { WAIT: '绛夊緟', TRADE: '鍙戠幇浜ゆ槗鏈轰細', REJECT: '鎷掔粷', BLOCK: '鏆傚仠' };
const DIR_CN = { LONG: '鍋氬', SHORT: '鍋氱┖' };
let LAST = null, EVT = null, LAST_OK = 0, FAILS = 0;

function chip(t, c) { return `<span class="chip ${c || ''}">${t}</span>`; }
function pill(t, c) { return `<span class="pill ${c || ''}">${t}</span>`; }
function row(k, v) { return `<div class="kv"><span class="k">${k}</span><span class="v">${v}</span></div>`; }
function ageText(s) { return s == null ? '鏈煡' : (s < 90 ? s + ' 绉掑墠' : (s < 5400 ? Math.round(s / 60) + ' 鍒嗛挓鍓? : Math.round(s / 3600) + ' 灏忔椂鍓?)); }

/* ---------- 椤堕儴锛歏2 褰撳墠鐘舵€?---------- */
function renderTop(o, s) {
  const items = o.data_items || [];
  const ages = items.map(i => i.age_s).filter(x => x != null);
  const newest = ages.length ? Math.min(...ages) : null;
  const dataCls = items.some(i => i.cls === 'bad') ? 'bad' : (items.some(i => i.cls === 'warn') ? 'warn' : (items.some(i => i.cls === 'ok') ? 'ok' : 'empty'));
  const dec = o.last_decision || {};
  const ac = s.account || {};
  const pos = o.position_known ? ((o.positions || []).length ? (o.positions || []).length + ' 涓? : '鏃?) : '鏃犳硶纭';
  $('topTag').innerHTML = pill(o.run_mode || '鈥?, 'gold');
  $('top').innerHTML =
    `<div class="kv"><span class="k">绯荤粺鐘舵€?/span><span class="v">${DOT[o.system_cls] || ''} <b>${esc(o.system_status)}</b></span></div>` +
    row('甯傚満', '榛勯噾 XAUUSD') +
    row('鏁版嵁', `${DOT[dataCls] || ''} ${dataCls === 'ok' ? '姝ｅ父' : dataCls === 'warn' ? '杈冩棫/閮ㄥ垎寮傚父' : dataCls === 'bad' ? '寮傚父' : '鏆傛棤鏁版嵁'}`) +
    row('鏁版嵁鏈€鏂?, ageText(newest)) +
    row('褰撳墠鍒ゆ柇', `<b>${esc(DEC_CN[dec.decision] || dec.decision || '鏈煡')}</b>`) +
    row('褰撳墠鎸佷粨', esc(pos)) +
    row('璐︽埛浣欓', money(ac.balance)) + row('褰撳墠鏉冪泭', money(ac.equity)) +
    row('鏈€鍚庢洿鏂?, esc(new Date().toLocaleString('zh-CN', { hour12: false })));
}

/* ---------- 鏁版嵁鐘舵€?---------- */
function renderData(o) {
  const items = o.data_items || [];
  $('dataTag').innerHTML = pill(items.length + ' 椤?, '');
  $('data').innerHTML = items.map(i =>
    `<div class="kv"><span class="k">${esc(i.name)}</span><span class="v">${DOT[i.cls] || ''} ${esc(i.status)}` +
    `<span class="muted" style="margin-left:8px">${ageText(i.age_s)}</span></span></div>` +
    `<div class="muted" style="font-size:11px;margin:-2px 0 6px 0">鏉ユ簮锛?{esc(i.source || '鏈煡')}${i.data_ts ? ' 路 鏁版嵁鏃堕棿 ' + esc(String(i.data_ts).slice(0, 19)) : ''}</div>`
  ).join('');
}

/* ---------- 褰撳墠浜ゆ槗鍒ゆ柇 + 涓轰粈涔堟病鏈変氦鏄?---------- */
function renderDecision(o, s) {
  const dec = o.last_decision || {};
  const d = dec.decision;
  const items = o.data_items || [];
  $('decTag').innerHTML = pill(DEC_CN[d] || d || '鏈煡', d === 'TRADE' ? 'ok' : (d === 'WAIT' ? 'warn' : 'bad'));
  let head;
  if (d === 'WAIT') head = `<div style="font-size:18px"><b>褰撳墠锛氱瓑寰?/b></div><div class="muted">鏆傛椂娌℃湁婊¤冻鍏ㄩ儴鏉′欢鐨勪氦鏄撴満浼氥€?/div>`;
  else if (d === 'TRADE') head = `<div style="font-size:18px"><b>褰撳墠锛氬彂鐜颁氦鏄撴満浼?/b></div>`;
  else head = `<div style="font-size:18px"><b>褰撳墠锛?{esc(DEC_CN[d] || d || '鏈煡')}</b></div>`;
  const checks = items.map(i => `${i.cls === 'ok' ? '鉁? : (i.cls === 'bad' ? '鉁? : '鈥?)} ${esc(i.name)}锛?{esc(i.status)}`).join('<br>');
  const why = d === 'WAIT' ? `<div class="sec-t">涓轰粈涔堟病鏈変氦鏄擄紵</div><div style="line-height:1.8">${checks}<br><b>鈫?绯荤粺閫夋嫨锛氱瓑寰?/b></div>` : '';
  const reason = dec.reason ? `<div class="sec-t">鍘熷洜</div><div class="muted">${esc(dec.reason)}</div>` : '';
  $('decision').innerHTML = head + reason + why;
}

/* ---------- 褰撳墠鎸佷粨 ---------- */
function renderPosition(o, s) {
  if (!o.position_known) {
    $('posTag').innerHTML = pill('鏃犳硶纭', 'warn');
    $('position').innerHTML = `<div style="font-size:18px"><b>褰撳墠鎸佷粨锛氭棤娉曠‘璁?/b></div><div class="muted">Broker 鏆傛椂鏃犳硶璇诲彇銆傜郴缁熶笉浼氱敤鈥?鈥濇帺鐩栨湭鐭ョ姸鎬併€?/div>`;
    return;
  }
  const ps = o.positions || [];
  $('posTag').innerHTML = pill(ps.length ? ps.length + ' 涓? : '鏃犳寔浠?, ps.length ? 'gold' : 'ok');
  $('position').innerHTML = ps.length ? ps.map(p =>
    row('鏂瑰悜', esc(DIR_CN[p.side] || p.side || '鈥?)) + row('鎵嬫暟', num(p.qty)) + row('鍏ュ満', num(p.open_price)) +
    row('姝㈡崯', num(p.sl)) + row('姝㈢泩', num(p.tp)) + row('娴姩鐩堜簭', num(p.profit))).join('<hr class="sep">')
    : `<div class="muted">褰撳墠娌℃湁鎸佷粨銆?/div>`;
}

/* ---------- 璐︽埛璧勯噾 ---------- */
function renderAccount(o, s) {
  const a = s.account || {}, b = s.broker_account || {}, mi = s.mode_info || {};
  $('acctTag').innerHTML = b.ok ? pill(`Broker ${b.demo ? 'Demo' : '瀹炵洏'}`, b.demo ? 'ok' : 'bad') : pill('Broker 鏈繛鎺?, 'warn');
  const v2 = `<div class="sec-t">杩愯璐︽埛锛?{esc(mi.execution_mode || '鈥?)}锛?/div>` +
    row('浣欓', money(a.balance)) + row('鏉冪泭', money(a.equity)) + row('宸插疄鐜扮泩浜?, a.realized_pnl == null ? '鏈煡' : (a.realized_pnl >= 0 ? '+' : '') + '$' + num(a.realized_pnl)) +
    row('鎸佷粨/宸插钩', `${a.positions ?? '鏈煡'} / ${a.closed ?? '鏈煡'}`);
  const br = b.ok
    ? `<div class="sec-t">Broker 路 ${esc(b.label || b.account || '')}</div>` + row('浣欓', money(b.balance)) + row('鏉冪泭', money(b.equity)) +
      row('鍙敤淇濊瘉閲?, money(b.margin_free)) + row('鎸佷粨', b.positions ?? '鏈煡') + row('鏉犳潌', b.leverage ? '1:' + b.leverage : '鏈煡')
    : `<div class="sec-t">Broker</div><div class="muted">鏈繛鎺ワ細${esc(b.error || 'unavailable')}锛堟樉绀衡€滄湭鐭モ€濓紝涓嶄唬琛?0锛?/div>`;
  $('account').innerHTML = v2 + br;
}

/* ---------- 绯荤粺鍋ュ悍 ---------- */
function renderHealth(o, s) {
  const rh = s.run_health || {}, mi = s.mode_info || {}, rs = s.run_state || {};
  const comps = [
    ['璋冨害鍣?, rh.last_success ? 'ok' : 'warn', rh.last_success ? '姝ｅ父' : '鏈煡'],
    ['鏁版嵁璺敱', mi.router_enabled ? 'ok' : 'warn', mi.router_enabled ? '姝ｅ父' : '鍏抽棴'],
    ['鎶€鏈暟鎹?, (o.data_items || []).find(x => x.name === '鎶€鏈暟鎹?)?.cls || 'warn', (o.data_items || []).find(x => x.name === '鎶€鏈暟鎹?)?.status || '鏈煡'],
    ['瀹忚鏁版嵁', (o.data_items || []).find(x => x.name === '瀹忚鏁版嵁')?.cls || 'warn', (o.data_items || []).find(x => x.name === '瀹忚鏁版嵁')?.status || '鏈煡'],
    ['鏁版嵁鏂伴矞搴?, (o.data_items || []).find(x => x.name === '榛勯噾浠锋牸')?.cls || 'warn', (o.data_items || []).find(x => x.name === '榛勯噾浠锋牸')?.status || '鏈煡'],
    ['浠锋牸绌洪棿', mi.price_space_enabled ? 'ok' : 'empty', mi.price_space_enabled ? '鍚敤' : '鏈惎鐢?],
    ['Replay', rh.replay_status === 'MISMATCH' ? 'bad' : 'ok', rh.replay_status === 'MISMATCH' ? '涓嶄竴鑷? : '涓€鑷?],
    ['璐︽湰 Ledger', rs.status === 'BLOCKED' ? 'bad' : 'ok', rs.status === 'BLOCKED' ? '寮傚父' : '姝ｅ父'],
    ['Broker', s.broker_account && s.broker_account.ok ? 'ok' : 'warn', s.broker_account && s.broker_account.ok ? '姝ｅ父' : '鏈繛鎺?],
  ];
  const worst = comps.some(c => c[1] === 'bad') ? 'bad' : (comps.some(c => c[1] === 'warn') ? 'warn' : 'ok');
  $('healthTag').innerHTML = pill(worst === 'ok' ? '姝ｅ父' : worst === 'warn' ? '閮ㄥ垎寮傚父' : '涓ラ噸寮傚父', worst);
  $('health').innerHTML = `<details><summary style="cursor:pointer">灞曞紑鏌ョ湅鍚勯儴鍒?/summary>` +
    comps.map(c => row(esc(c[0]), `${DOT[c[1]] || ''} ${esc(c[2])}`)).join('') + `</details>`;
}

/* ---------- 闃舵 / 妯″紡 / Forward Gate ---------- */
function renderStage(o, s) {
  const rem = o.stage_remaining_s;
  const remTxt = (rem == null) ? '鈥? : (Math.floor(rem / 3600) + ' 灏忔椂 ' + String(Math.floor(rem % 3600 / 60)).padStart(2, '0') + ' 鍒?);
  $('stageTag').innerHTML = pill(o.stage || '鈥?, 'gold');
  $('stage').innerHTML =
    row('褰撳墠闃舵', `<b>${esc(o.stage || '鈥?)}</b>`) +
    row('杩愯妯″紡', esc(o.run_mode || '鈥?)) +
    row('鐪熷疄涓嬪崟', `<b>${esc(o.real_orders || '鍚?)}</b>`) +
    row('闃舵缁撴潫', esc(String(o.stage_end || '鈥?).replace('T', ' ').slice(0, 19))) +
    row('璺濈缁撴潫', remTxt) +
    row('姝ｅ紡鍓嶅悜楠岃瘉', `<b>${esc(o.forward_gate?.label || '鏈厑璁?)}</b>`) +
    `<div class="muted" style="font-size:11px">鍘熷洜锛?{esc(o.forward_gate?.reason || '')}</div>`;
}

/* ---------- V1 瀹夊叏 ---------- */
function renderV1(o) {
  const v = o.v1_isolation || {};
  $('v1Tag').innerHTML = pill(v.status === '姝ｅ父' ? '姝ｅ父' : '鏃犳硶纭', v.status === '姝ｅ父' ? 'ok' : 'warn');
  $('v1').innerHTML = row('V1', esc(v.status || '鏃犳硶纭')) + row('V2', '鐙珛杩愯') +
    `<div class="muted" style="font-size:11px">${esc(v.detail || '')}</div>`;
}

/* ---------- 鏈€杩戦棶棰?---------- */
function renderProblems(o) {
  const ps = o.recent_problems || [];
  $('probTag').innerHTML = pill(ps.length ? ps.length + ' 鏉? : '鏃?, ps.length ? 'warn' : 'ok');
  $('problems').innerHTML = ps.length ? ps.map(p =>
    `<div class="kv"><span class="k">${esc(String(p.ts || '').replace('T', ' ').slice(0, 16))}</span>` +
    `<span class="v" style="text-align:right">${esc(p.problem)}<br><span class="muted" style="font-size:11px">${esc(p.detail)}</span></span></div>`).join('')
    : `<div class="muted">鏈€杩戞病鏈夊彂鐜伴棶棰樸€?/div>`;
}

/* ---------- 鎶€鏈鎯?---------- */
function renderTech(s) {
  const man = s.manifest || {}, rs = s.run_state || {}, mi = s.mode_info || {}, rh = s.run_health || {};
  const b = s.broker_account || {};
  $('tech').innerHTML =
    row('RUN_ID', esc(s.run_id || '鈥?)) +
    row('浠ｇ爜鎻愪氦 commit', esc((man.code_commit || '鈥?).slice(0, 12))) +
    row('閰嶇疆鍝堝笇 config_hash', esc((man.config_hash || '鈥?).slice(0, 16))) +
    row('绛栫暐鐗堟湰', esc(man.strategy_version || '鈥?)) +
    row('鏍囩殑 instrument', esc(mi.instrument || '鈥?)) + row('鍙傝€冨競鍦?, esc(mi.reference_market || '鈥?)) +
    row('鏁版嵁婧?, esc(mi.data_source || '鈥?)) + row('Router', mi.router_enabled ? '鍚敤' : '鍏抽棴') +
    row('Price Space', mi.price_space_enabled ? '鍚敤' : '鏈惎鐢?) +
    row('鏈€鍚庡喅绛?decision_id', esc((rs.last_decision || {}).decision_id || '鈥?)) +
    row('Replay', esc(rh.replay_status || '鈥?)) + row('Ledger', esc(rs.status || '鈥?)) +
    row('Broker 瑙勬牸(瀹炴祴 digits/tick)', esc((b.spec ? `${b.spec.digits}/${b.spec.tick_size}` : '鏈鍙?))) +
    row('璋冨害鍣?, esc(rh.scheduler || '鈥?));
}

/* ---------- 鏃堕挓 / 鍒锋柊鐘舵€?---------- */
function tickClock() { $('clock').textContent = new Date().toISOString().slice(11, 19) + ' UTC'; }
function refreshOK() { LAST_OK = Date.now(); FAILS = 0; }
function refreshFail() { FAILS++; }

function renderRefreshState() {
  const s = LAST_OK ? Math.round((Date.now() - LAST_OK) / 1000) : null;
  if (FAILS >= 3) $('refreshState').innerHTML = `<span style="color:#fb7185">馃敶 鏁版嵁杩炴帴寮傚父锛堣繛缁け璐?${FAILS} 娆★級</span>`;
  else if (FAILS > 0) $('refreshState').innerHTML = `<span style="color:#fbbf24">鈿狅笍 鏁版嵁鏇存柊澶辫触锛屾渶鍚庝竴娆℃垚鍔燂細${ageText(s)}</span>`;
  else $('refreshState').textContent = `鑷姩鍒锋柊姝ｅ父 路 鏈€鍚庢垚鍔熸洿鏂帮細${ageText(s)}`;
}

/* ---------- 涓绘覆鏌?---------- */
function render(s) {
  LAST = s;
  const o = s.observability || { system_status: '鏈煡', data_items: [], run_mode: '鏈煡', forward_gate: { label: '鏈煡' }, position_known: false, last_decision: {} };
  renderTop(o, s); renderData(o); renderDecision(o, s); renderPosition(o, s); renderAccount(o, s);
  renderHealth(o, s); renderStage(o, s); renderV1(o); renderProblems(o); renderTech(s);
  $('foot').textContent = `绯荤粺鏈€鍚庢洿鏂?${new Date().toLocaleString('zh-CN', { hour12: false })} 路 Hermes V2 鎺у埗闈㈡澘锛堝彧璇?路 鐙珛浜?V1锛塦;
}

function start() {
  setInterval(tickClock, 1000); tickClock();
  setInterval(renderRefreshState, 1000);
  fetch('/api/snapshot', { cache: 'no-store' }).then(r => r.json()).then(s => { render(s); refreshOK(); }).catch(refreshFail);
  try {
    EVT = new EventSource('/api/stream');
    EVT.addEventListener('snap', e => { $('live').className = 'live'; $('liveTxt').textContent = '瀹炴椂鏇存柊涓?; try { render(JSON.parse(e.data)); refreshOK(); } catch (_) { refreshFail(); } });
    EVT.addEventListener('err', () => refreshFail());
    EVT.onerror = () => { $('live').className = 'live off'; $('liveTxt').textContent = '杞妯″紡'; };
  } catch (_) { }
  setInterval(async () => {
    if (EVT && EVT.readyState === 1) return;
    try { render(await (await fetch('/api/snapshot', { cache: 'no-store' })).json()); refreshOK(); } catch (_) { refreshFail(); }
  }, 3000);
}
start();
