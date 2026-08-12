#!/usr/bin/env python3
"""
push_to_github.py — 用 GitHub REST API 逐文件上传仓库内容

背景：本环境 git 走 HTTPS 时 TLS/认证异常，但 GitHub REST API 稳定可用。
此脚本遍历项目文件，用 Contents API 逐个 PUT 到远端仓库对应路径。
需要：环境变量 GH_TOKEN（fine-grained PAT，需 Contents: Read and write 权限）
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error

REPO = "shenyyds999-code/CleanReading_OS"
BRANCH = "main"
API = f"https://api.github.com/repos/{REPO}/contents/"

TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    print("❌ 需要设置环境变量 GH_TOKEN")
    sys.exit(1)

ROOT = os.path.dirname(os.path.abspath(__file__))
# 需要上传的根目录 = scripts 的上一级（webview-builder 项目根）
SRC = os.path.abspath(os.path.join(ROOT, ".."))

# 参照 .gitignore，跳过不应上传的路径
SKIP_DIRS = {".git", "node_modules", "venv", "__pycache__", "build", "dist", "out", ".gradle"}
SKIP_EXT = {".pyc", ".log", ".apk", ".exe", ".msi", ".dmg", ".AppImage"}
SKIP_FILES = {".env", "Thumbs.db", ".DS_Store"}
SKIP_NAME = {".env", ".env.local", ".env.production"}


def should_skip(rel):
    parts = rel.split(os.sep)
    if any(p in SKIP_DIRS for p in parts):
        return True
    if any(p in SKIP_FILES for p in parts):
        return True
    if any(p in SKIP_NAME for p in parts):
        return True
    base = os.path.basename(rel)
    if base.startswith(".env"):
        return True
    ext = os.path.splitext(base)[1].lower()
    return ext in SKIP_EXT


def walk():
    files = []
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, SRC)
            if should_skip(rel):
                print(f"  跳过: {rel}")
                continue
            files.append((rel, full))
    files.sort(key=lambda x: x[0])
    return files


def api(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        try:
            return json.loads(body)
        except Exception:
            return {"message": f"HTTP {e.code}: {body[:200]}"}


def main():
    print(f"🚀 上传 {SRC} → {REPO} ({BRANCH})")
    files = walk()
    print(f"共 {len(files)} 个文件待上传\n")

    ok, fail = 0, 0
    for rel, full in files:
        # 先查是否已存在（拿 sha 用于更新）
        existing = api("GET", API + rel.replace(os.sep, "/"))
        sha = existing.get("sha") if isinstance(existing, dict) and existing.get("type") == "file" else None

        with open(full, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode()

        payload = {
            "message": f"Add {rel} [auto-upload]",
            "content": content_b64,
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha

        res = api("PUT", API + rel.replace(os.sep, "/"), payload)
        if res.get("content"):
            print(f"  ✓ {rel} {'(更新)' if sha else '(新建)'}")
            ok += 1
        else:
            print(f"  ✗ {rel}: {res.get('message')}")
            fail += 1

    print(f"\n完成: 成功 {ok}, 失败 {fail}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
