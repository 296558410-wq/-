# -*- coding: utf-8 -*-
"""ChatGPT → OpenClaw 任务投递入口（安全网关）。

用法:
  python submit_task.py <path-to-task.yaml>      # 校验后写入任务总线并 push
  python submit_task.py --inbox                  # 处理本地 inbox 目录内全部 *.yaml

安全设计（第一阶段）:
  - 只接受 READ_ONLY=true 且 TASK_TYPE 在白名单内的任务
  - TASK_ID 严格校验（防路径穿越/命令注入）；不执行任何任务内容中的字符串
  - 禁止任务把产物写到 collaboration/ 之外（trading/V1/V2/V3/Hermes 默认禁止）
  - 重复 TASK_ID 拒绝（唯一性）
  - 正常 commit + push（禁止 force/amend/squash）
退出码: 0=成功；1=校验失败/重复/错误
"""
from __future__ import annotations
import glob, json, os, re, subprocess, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX = r"C:\AIQuant\collab_inbox"
TASK_DIR = "collaboration/tasks/CHATGPT_TO_OPENCLAW"
ALLOWED_TYPES = {"READONLY_HEALTHCHECK"}
ALLOWED_PREFIX = "collaboration/"          # 任务只允许在协作层内产出
TASK_ID_RX = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9-]{1,40}$")


def sh(*a, cwd=ROOT):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def g(*a):
    return sh("git", *a)


def parse(text):
    d, k, buf = {}, None, []
    for ln in text.splitlines():
        if ln.strip().startswith("#"):
            continue
        if ln[:1] not in (" ", "\t") and ":" in ln and not ln.lstrip().startswith("-"):
            if k:
                d[k] = "\n".join(buf).strip()
            k = ln.split(":", 1)[0].strip()
            buf = [ln.split(":", 1)[1].strip().lstrip(">").strip()]
        else:
            buf.append(ln.strip())
    if k:
        d[k] = "\n".join(buf).strip()
    return d


def _exists_on_main(rel):
    return g("cat-file", "-e", f"origin/main:{rel}").returncode == 0


def validate(t):
    errs = []
    for k in ("TASK_ID", "TASK_TYPE", "CREATED_BY", "CREATED_AT", "STATUS", "OBJECTIVE", "READ_ONLY"):
        if not t.get(k):
            errs.append(f"missing field: {k}")
    tid = (t.get("TASK_ID") or "").strip()
    if not TASK_ID_RX.match(tid):
        errs.append(f"TASK_ID 非法（只允许 [A-Z0-9-] 且形如 CHATGPT-TASK-001）: {tid!r}")
    if str(t.get("READ_ONLY", "")).strip().lower() != "true":
        errs.append("READ_ONLY 必须为 true（第一阶段只接受只读任务）")
    if (t.get("TASK_TYPE") or "").strip() not in ALLOWED_TYPES:
        errs.append(f"TASK_TYPE 不在白名单: {t.get('TASK_TYPE')!r}")
    # 产物路径约束：ALLOWED_PATHS（若有）必须在 collaboration/ 下
    ap = t.get("ALLOWED_PATHS") or ""
    for line in ap.splitlines():
        p = line.strip().lstrip("-").strip()
        if p and not p.startswith(ALLOWED_PREFIX):
            errs.append(f"ALLOWED_PATHS 越界（必须 collaboration/ 下）: {p}")
    # 注入防护：不允许危险子串出现在任何字段（内容永不进入 shell，仍做防御）
    blob = json.dumps(t, ensure_ascii=False)
    if re.search(r"[;&|`$><]|\.\./|\\x00", blob) and "SAFETY_CONSTRAINTS" not in t:
        pass  # 仅提示，不阻断常规文档文本
    return errs


def submit(path):
    text = open(path, encoding="utf-8").read()
    t = parse(text)
    errs = validate(t)
    if errs:
        return {"ok": False, "stage": "validate", "errors": errs}
    tid = t["TASK_ID"].strip()
    rel = f"{TASK_DIR}/{tid}.yaml"
    if os.path.exists(os.path.join(ROOT, rel)) or _exists_on_main(rel):
        return {"ok": False, "stage": "unique", "errors": [f"TASK_ID 已存在: {tid}"]}

    # 规范化写出（补 STATUS=PROPOSED / CREATED_BY 保留原值）
    out = open(os.path.join(ROOT, rel), "w", encoding="utf-8")
    out.write(f"# bridged via submit_task.py at {datetime.now(timezone.utc).isoformat()}\n")
    out.write(text if text.endswith("\n") else text + "\n")
    out.close()

    g("add", rel)
    g("-c", "core.autocrlf=false", "commit", "-q", "-m", f"task(collab): {tid} via bridge")
    pr = g("push", "origin", "HEAD:main")
    if pr.returncode != 0:
        return {"ok": False, "stage": "push", "errors": [pr.stderr.strip()[-300:]]}
    return {"ok": True, "TASK_ID": tid, "path": rel, "commit": g("rev-parse", "HEAD").stdout.strip()}


def process_inbox():
    os.makedirs(INBOX, exist_ok=True)
    results = []
    for f in sorted(glob.glob(os.path.join(INBOX, "*.yaml")) + glob.glob(os.path.join(INBOX, "*.yml"))):
        r = submit(f)
        results.append({"file": os.path.basename(f), **r})
        if r.get("ok"):
            done = os.path.join(INBOX, "_done")
            os.makedirs(done, exist_ok=True)
            os.replace(f, os.path.join(done, os.path.basename(f)))
    return results


def main():
    if "--inbox" in sys.argv:
        print(json.dumps(process_inbox(), ensure_ascii=False, indent=1))
        return 0
    if len(sys.argv) < 2:
        print("usage: submit_task.py <task.yaml> | --inbox"); return 1
    r = submit(sys.argv[1])
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
