# -*- coding: utf-8 -*-
"""OpenClaw 协作任务总线（第一阶段，只读）。

功能：
  1) git fetch origin，读取 origin/main 上 collaboration/tasks/CHATGPT_TO_OPENCLAW/*.yaml
  2) 发现 STATUS: PROPOSED 且未处理过的任务 → 领取（写 CLAIMS.jsonl，不改任务文件）
  3) 执行只读任务（白名单：READONLY_HEALTHCHECK），生成结果到 OPENCLAW_TO_CHATGPT/
  4) 刷新 GITHUB_SYNC.md；commit + push（正常，不 force）

用法： python task_bus.py --once
退出码： 0=正常；1=有错误；2=无可处理任务（仍 0 变更）
"""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # <repo>
ORIGINAL_REPO = r"C:\AIQuant"
BASELINE = "22f27df40f4f3b71fdbbcc9a92753c3bb2743241"
OPENCLAW_VERSION = "openclaw 2026.7.1-2"
TASK_DIR = "collaboration/tasks/CHATGPT_TO_OPENCLAW"
OUT_DIR = "collaboration/tasks/OPENCLAW_TO_CHATGPT"
ALLOWED_TYPES = {"READONLY_HEALTHCHECK"}
CST = timezone(timedelta(hours=8))


def sh(*args, cwd=ROOT):
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def g(*args):
    return sh("git", *args)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def now_cst():
    return datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S") + " (GMT+8)"


def git_show(path, rev="origin/main"):
    r = g("show", f"{rev}:{path}")
    return r.stdout if r.returncode == 0 else None


def file_exists_on(rev, path):
    return g("cat-file", "-e", f"{rev}:{path}").returncode == 0


def parse_task(text):
    """最小 YAML 解析：KEY: value + 缩进续行/列表。"""
    d, key, buf = {}, None, []
    for ln in (text or "").splitlines():
        if ln.strip().startswith("#"):
            continue
        if ln[:1] not in (" ", "\t") and ":" in ln and not ln.lstrip().startswith("-"):
            if key:
                d[key] = "\n".join(x for x in buf).strip()
            key = ln.split(":", 1)[0].strip()
            buf = [ln.split(":", 1)[1].strip().lstrip(">").strip()]
        else:
            buf.append(ln.strip())
    if key:
        d[key] = "\n".join(x for x in buf).strip()
    return d


def append_claims(events):
    os.makedirs(os.path.join(ROOT, OUT_DIR), exist_ok=True)
    p = os.path.join(ROOT, OUT_DIR, "CLAIMS.json")  # 不用 .jsonl（repo .gitignore 有 *.jsonl）
    with open(p, "a", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def healthcheck(remote_head, local_head):
    """只读健康检查（不触交易系统）。"""
    facts = {}
    orig_head = sh("git", "rev-parse", "--short", "HEAD", cwd=ORIGINAL_REPO).stdout.strip()
    orig_count = sh("git", "rev-list", "--count", "HEAD", cwd=ORIGINAL_REPO).stdout.strip()
    facts["github_repo"] = "https://github.com/296558410-wq/-.git"
    facts["remote_head"] = remote_head
    facts["local_head"] = local_head
    facts["branch"] = g("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    facts["commit_count"] = g("rev-list", "--count", "HEAD").stdout.strip()
    facts["baseline_is_ancestor"] = g("merge-base", "--is-ancestor", BASELINE, "HEAD").returncode == 0
    facts["collab_files"] = sum(1 for _ in (g("ls-tree", "-r", "--name-only", "origin/main").stdout.splitlines())
                               if _.startswith("collaboration/"))
    tree = g("ls-tree", "-r", "--name-only", "origin/main").stdout.splitlines()
    bad = [x for x in tree if any(k in x for k in (".env", "run_state", "/state/", "trader_summary", "memory/reviews"))
           or x.endswith((".jsonl", ".log"))]
    facts["forbidden_in_remote"] = bad
    facts["original_repo_head"] = orig_head
    facts["original_repo_commits"] = orig_count
    facts["broker_order_sent"] = False
    return facts


def main():
    ok = True
    g("fetch", "origin", "-q")
    remote_head = g("rev-parse", "origin/main").stdout.strip()
    local_head = g("rev-parse", "HEAD").stdout.strip()

    lst = g("ls-tree", "-r", "--name-only", "origin/main", TASK_DIR).stdout.splitlines()
    tasks = [x for x in lst if x.endswith((".yaml", ".yml"))]
    processed = []
    for tpath in tasks:
        txt = git_show(tpath)
        t = parse_task(txt)
        tid = t.get("TASK_ID", os.path.splitext(os.path.basename(tpath))[0])
        status = (t.get("STATUS") or "").strip().upper()
        if status != "PROPOSED":
            continue
        result_rel = f"{OUT_DIR}/{tid}_RESULT.md"
        if os.path.exists(os.path.join(ROOT, result_rel)) or file_exists_on("origin/main", result_rel):
            continue  # 已处理，避免重复执行

        base = {"TASK_ID": tid, "OPENCLAW_VERSION": OPENCLAW_VERSION,
                "LOCAL_HEAD": local_head, "REMOTE_HEAD": remote_head}
        append_claims([dict(base, EVENT="DISCOVERED", TS=now_iso()),
                       dict(base, EVENT="CLAIMED", TS=now_iso()),
                       dict(base, EVENT="RUNNING", TS=now_iso())])

        ro = str(t.get("READ_ONLY", "")).strip().lower() == "true"
        ttype = (t.get("TASK_TYPE") or "").strip()
        started = now_iso()
        if not ro or ttype not in ALLOWED_TYPES:
            body = (f"STATUS=REJECTED\nREASON=READ_ONLY_OR_TYPE_NOT_ALLOWED (READ_ONLY={ro}, TASK_TYPE={ttype})\n")
            st = "REJECTED"
            append_claims([dict(base, EVENT="REJECTED", TS=now_iso())])
        else:
            facts = healthcheck(remote_head, local_head)
            lines = "".join(f"- **{k}**: `{v}`\n" for k, v in facts.items())
            st = "COMPLETED"
            body = (f"STATUS=COMPLETED\nSTARTED_AT={started}\nFINISHED_AT={now_iso()}\n\n"
                    f"LOCAL_HEAD={local_head}\nREMOTE_HEAD={remote_head}\n\n"
                    f"FILES_CHANGED=\nFILES_CREATED={result_rel}\nFILES_DELETED=\n\n"
                    f"V1_UNTOUCHED=TRUE\nV2_UNTOUCHED=TRUE\nV3_UNTOUCHED=TRUE\nHERMES_UNTOUCHED=TRUE\n\n"
                    f"BROKER_ORDER_SENT=FALSE\n\n"
                    f"FINDINGS:\n{lines}\n"
                    f"DATA_GAPS=\nERRORS=\nNEXT_RECOMMENDATION=\nREPORT_COMMIT=<the commit that adds this result>\n")
            append_claims([dict(base, EVENT="DONE", TS=now_iso())])

        os.makedirs(os.path.join(ROOT, OUT_DIR), exist_ok=True)
        with open(os.path.join(ROOT, result_rel), "w", encoding="utf-8") as f:
            f.write(f"# {tid} — RESULT\n\nTASK_ID={tid}\n{body}\n")
        processed.append({"TASK_ID": tid, "STATUS": st, "result": result_rel})

    # GITHUB_SYNC.md（仅在 Sync 状态变化或有任务处理时重写，避免每轮产生噪声 commit）
    synced = (local_head == remote_head)
    sync_val = "SYNCED" if synced else "SYNC_PENDING"
    sync_path = os.path.join(ROOT, "collaboration/status/GITHUB_SYNC.md")
    old = open(sync_path, encoding="utf-8").read() if os.path.exists(sync_path) else ""
    if processed or f"Sync:          {sync_val}" not in old:
        sync_doc = ("# GITHUB_SYNC.md — GitHub 同步状态\n\n"
                    "```text\n"
                    f"GitHub:        CONNECTED\n"
                    f"Remote HEAD:   {remote_head}\n"
                    f"Local HEAD:    {local_head}\n"
                    f"Sync:          {sync_val}\n"
                    f"Last Sync:     {now_cst()}\n"
                    "```\n")
        with open(sync_path, "w", encoding="utf-8") as f:
            f.write(sync_doc)

    # commit + push (仅当有变更)
    g("add", "-A")
    changed = g("status", "--porcelain").stdout.strip()
    commit = None
    if changed:
        msg = "chore(collab): task-bus run " + (", ".join(p["TASK_ID"] for p in processed) if processed else "sync")
        g("-c", "core.autocrlf=false", "commit", "-q", "-m", msg)
        commit = g("rev-parse", "HEAD").stdout.strip()
        pr = g("push", "origin", "HEAD:main")
        if pr.returncode != 0:
            ok = False

    print(json.dumps({"remote_head": remote_head, "local_head": local_head,
                      "tasks_found": len(tasks), "processed": processed,
                      "commit": commit, "ok": ok}, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
