# -*- coding: utf-8 -*-
"""
setup_cloud.py ── 雲端版一鍵設定（用GitHub API,免gh CLI）
================================================================
拿到董事長的PAT後，一次做完：
  1. 建 GitHub repo（不好猜的名字，public以支援免費Pages）
  2. 設 remote（token存本機git設定）+ push main
  3. 開 GitHub Pages（source=main分支根目錄）
  4. 印出手機網址

用法：
  python setup_cloud.py <PAT> [repo名]
  # repo名可省略,預設 hontu-sa-board
  # PAT不會被寫進任何檔案上傳,只寫進本機 .git/config 的remote URL
"""
import sys, io, json, subprocess, time, urllib.request, urllib.error
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if len(sys.argv) < 2:
    raise SystemExit("用法: python setup_cloud.py <PAT> [repo名]")

PAT   = sys.argv[1].strip()
REPO  = sys.argv[2].strip() if len(sys.argv) > 2 else "hontu-sa-board"
OWNER = "by860207"
SITE  = Path(r"C:\Users\User\Desktop\股票\鴻圖\SA看板網站")

def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {PAT}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "hontu-setup")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")
    except Exception as e:
        return -1, {"error": str(e)}

def git(args):
    r = subprocess.run(["git"] + args, cwd=SITE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(f"  $ git {' '.join(args)}\n   {(r.stdout+r.stderr).strip()[:300]}")
    return r.returncode

print("=" * 56)
print(f"  雲端版設定  owner={OWNER} repo={REPO}")
print("=" * 56)

# 0. 驗證PAT + 帳號
st, me = api("GET", "https://api.github.com/user")
if st != 200:
    raise SystemExit(f"✗ PAT驗證失敗({st}): {me}")
print(f"  ✓ PAT有效，登入為 {me.get('login')}")

# 1. 建repo(已存在就略過)
st, res = api("POST", "https://api.github.com/user/repos",
              {"name": REPO, "private": False, "auto_init": False,
               "description": "鴻圖SA訊號看板(自動更新)"})
if st == 201:
    print(f"  ✓ repo已建立: {res.get('full_name')}")
elif st == 422:
    print(f"  · repo已存在，沿用")
else:
    print(f"  ⚠️ 建repo回應({st}): {res}")

# 2. remote + push (token內嵌URL,只存本機)
remote_url = f"https://{OWNER}:{PAT}@github.com/{OWNER}/{REPO}.git"
subprocess.run(["git", "remote", "remove", "origin"], cwd=SITE,
               capture_output=True)
git(["remote", "add", "origin", remote_url])
# 確保有東西可push
if not (SITE / "index.html").exists():
    (SITE / "index.html").write_text("<h1>看板生成中…</h1>", encoding="utf-8")
(SITE / ".nojekyll").write_text("", encoding="utf-8")
git(["add", "-A"])
git(["commit", "-m", "雲端版初始化"])
git(["branch", "-M", "main"])
rc = git(["push", "-u", "origin", "main"])
if rc != 0:
    raise SystemExit("✗ push失敗，檢查PAT權限(需Contents:write)")
print("  ✓ 已push")

# 3. 開Pages
time.sleep(2)
st, res = api("POST", f"https://api.github.com/repos/{OWNER}/{REPO}/pages",
              {"source": {"branch": "main", "path": "/"}})
if st in (201, 409):
    print("  ✓ GitHub Pages 已開啟" + ("(原本就開著)" if st == 409 else ""))
else:
    print(f"  ⚠️ 開Pages回應({st}): {res}  (可到repo Settings→Pages手動開main分支)")

url = f"https://{OWNER}.github.io/{REPO}/"
print("\n" + "=" * 56)
print(f"  ★ 雲端版網址(手機加書籤): {url}")
print("  (首次部署等1-3分鐘生效;之後排程自動更新)")
print("  token已存本機 .git/config,不外傳。撤銷:GitHub→Settings→PAT")
print("=" * 56)
