#!/usr/bin/env python3
"""
dev-pipeline watchdog — 全自动开发流水线门控调度

核心规则:
  1. 门控去重: 待开发/ 的项目名如果在 开发中/ 或 开发完/ 已存在 → 跳过
  2. 门控开发: 仅当 开发中/ 和 开发完/ 都没有同名项目 → 才自动开发
  3. 严格步骤: 每一步记录 dev-log，不跳步，异常保留现场

工作流程:
  待开发/ 新方案 → [门控: 检查同名项目]
     ├─ 开发中/或开发完/ 已有 → ⏭️ 跳过（已做过）
     └─ 都没有                → 🚀 dev-collab-ultimate → 开发中/ → 开发完/
"""

import os, sys, json, hashlib, subprocess, time, logging, shutil
from pathlib import Path
from datetime import datetime

# === 配置 ===
REPO_ROOT = Path("/mnt/f/AI_Work/Agent/Hermes/Sandbox/dev-pipeline")
WATCH_DIR = REPO_ROOT / "待开发"
DEV_DIR = REPO_ROOT / "开发中"
DONE_DIR = REPO_ROOT / "开发完"
SANDBOX = Path("/mnt/f/AI_Work/Agent/Hermes/Sandbox")
WORKSPACE = SANDBOX / ".workspace"
STATE_FILE = Path.home() / ".hermes" / "scripts" / ".pipeline_state.json"
LOG_FILE = Path.home() / ".hermes" / "scripts" / "pipeline_watchdog.log"
API_TOKENS = Path.home() / ".hermes" / "scripts" / "api_tokens.sh"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")
    logging.info(msg)

# ─────────────────────────────────────────────
# Dev Log 系统 — 每项目结构化开发日志
# ─────────────────────────────────────────────

def dev_log_path(project_name):
    """项目开发日志路径，存于项目目录相邻位置"""
    log_dir = REPO_ROOT / ".dev-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{project_name}.json"

def init_dev_log(project_name, plan_path=None, plan_summary=""):
    """初始化项目开发日志"""
    log_path = dev_log_path(project_name)
    # 检查是否已有日志
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text())
            return existing
        except:
            pass
    
    log_entry = {
        "project": project_name,
        "plan": str(plan_path) if plan_path else "",
        "plan_summary": plan_summary[:200] if plan_summary else "",
        "status": "pending",               # pending → gate_passed → coding → testing → validating → done
        "step": 0,                          # 当前步骤编号
        "steps": [],                        # 步骤列表 [{step, phase, status, time, detail, error}]
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "last_error": None,
        "error_count": 0,
        "pipeline_gate": {                  # 门控决策记录
            "checked_at": None,
            "dev_dir_has_projects": False,
            "done_dir_has_projects": False,
            "gate_passed": False
        }
    }
    log_path.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False))
    return log_entry

def update_dev_log(project_name, updates):
    """更新项目开发日志"""
    log_path = dev_log_path(project_name)
    if not log_path.exists():
        return None
    try:
        entry = json.loads(log_path.read_text())
        # 递归更新
        for k, v in updates.items():
            if isinstance(v, dict) and k in entry and isinstance(entry[k], dict):
                entry[k].update(v)
            else:
                entry[k] = v
        log_path.write_text(json.dumps(entry, indent=2, ensure_ascii=False))
        return entry
    except Exception as e:
        log(f"⚠️ dev-log 更新失败 {project_name}: {e}")
        return None

def add_dev_log_step(project_name, step_name, status="pending", detail="", error=""):
    """向开发日志添加一个步骤记录"""
    log_path = dev_log_path(project_name)
    if not log_path.exists():
        return None
    try:
        entry = json.loads(log_path.read_text())
        step_num = entry["step"] + 1
        step_entry = {
            "step": step_num,
            "phase": step_name,
            "status": status,       # pending → in_progress → completed / failed
            "time": datetime.now().isoformat(),
            "detail": detail,
            "error": error
        }
        entry["steps"].append(step_entry)
        entry["step"] = step_num
        if status == "completed":
            entry["status"] = step_name  # 更新整体状态为当前阶段名
        elif status == "failed":
            entry["status"] = f"failed@{step_name}"
            entry["last_error"] = error
            entry["error_count"] = entry.get("error_count", 0) + 1
        log_path.write_text(json.dumps(entry, indent=2, ensure_ascii=False))
        return step_entry
    except Exception as e:
        log(f"⚠️ dev-log step 添加失败 {project_name}: {e}")
        return None

def print_dev_log(project_name):
    """打印开发日志摘要"""
    log_path = dev_log_path(project_name)
    if not log_path.exists():
        log(f"📋 无开发日志: {project_name}")
        return
    try:
        entry = json.loads(log_path.read_text())
        log(f"📋 === 开发日志: {project_name} ===")
        log(f"   状态: {entry['status']} | 步骤: {entry['step']}")
        log(f"   开始: {entry['started_at']}")
        if entry['completed_at']:
            log(f"   完成: {entry['completed_at']}")
        if entry['last_error']:
            log(f"   ❌ 上次错误: {entry['last_error']}")
        log(f"   错误次数: {entry['error_count']}")
        log(f"   步骤列表:")
        for s in entry.get("steps", []):
            icon = "✅" if s["status"] == "completed" else ("❌" if "failed" in s["status"] else "⏳")
            err_info = f" | ERROR: {s['error'][:80]}" if s.get("error") else ""
            log(f"     [{s['step']}] {icon} {s['phase']} ({s['status']}){err_info}")
        if "pipeline_gate" in entry and entry["pipeline_gate"]["checked_at"]:
            g = entry["pipeline_gate"]
            log(f"   门控: 通过={g['gate_passed']} | 开发中须={g['dev_dir_has_projects']} | 开发完须={g['done_dir_has_projects']}")
    except Exception as e:
        log(f"⚠️ 读取 dev-log 失败: {e}")

# ─────────────────────────────────────────────
# 门控系统 — 防止流水线堆栈
# ─────────────────────────────────────────────

def count_projects(directory):
    """统计目录下有多少项目（子目录），排除 .md 文件项目"""
    if not directory.exists():
        return 0
    count = 0
    for item in directory.iterdir():
        if item.is_dir():
            # 排除隐藏目录
            if not item.name.startswith("."):
                count += 1
    return count

def list_projects(directory):
    """列出目录中的项目名"""
    if not directory.exists():
        return []
    projects = []
    for item in sorted(directory.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            projects.append(item.name)
    return projects

def check_project_exists(project_name):
    """
    按项目名去重: 检查项目是否已存在于 开发中/ 或 开发完/
    
    返回: (exists: bool, where: str|None)
      - exists=True, where="开发中" → 正在开发
      - exists=True, where="开发完" → 已完成
      - exists=False, where=None    → 新项目，可以开发
    """
    if (DEV_DIR / project_name).exists():
        return True, "开发中"
    if (DONE_DIR / project_name).exists():
        return True, "开发完"
    return False, None


# ─────────────────────────────────────────────
# 核心操作
# ─────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"scanned": {}, "projects": {}, "gate_log": []}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def scan_plans():
    """扫描待开发/ 目录，返回 {相对路径: md5} 映射"""
    plans = {}
    if not WATCH_DIR.exists():
        return plans
    for plan_dir in sorted(WATCH_DIR.iterdir()):
        if not plan_dir.is_dir():
            continue
        for md_file in plan_dir.glob("*.md"):
            rel = str(md_file.relative_to(WATCH_DIR))
            content = md_file.read_bytes()
            plans[rel] = hashlib.md5(content).hexdigest()
    return plans

def detect_changes(state):
    """对比快照，返回新增/修改的文件列表"""
    current = scan_plans()
    old = state.get("scanned", {})
    new_or_modified = []
    for rel, md5 in current.items():
        if rel not in old or old[rel] != md5:
            new_or_modified.append(rel)
    return new_or_modified, current

def trigger_development(plan_rel_path, bypass_gate=False):
    """
    检测到新方案 → 触发全自动开发
    
    步骤:
      0. 门控检查（除非 bypass）
      1. 解析方案文件
      2. 初始化 dev-log
      3. 创建 workspace
      4. 记录到流水线状态
    """
    plan_path = WATCH_DIR / plan_rel_path
    project_name = plan_path.parent.name  # YYYY-MM-DD-项目名
    log(f"🚀 检测到新方案: {project_name}/{plan_path.name}")
    
    # ── 步骤 0: 门控去重检查 ──
    exists, where = check_project_exists(project_name)
    
    if exists and not bypass_gate:
        log(f"⏭️ [门控] {project_name} 已在 {where} 中，跳过")
        return None, "exists", where
    
    log(f"✅ [门控] {project_name} 是新项目，可以开发")
    
    plan_content = plan_path.read_text()
    plan_summary = plan_content[:500]
    
    # ── 步骤 1: 初始化 dev-log ──
    dev_log = init_dev_log(project_name, plan_path, plan_summary)
    dev_log = update_dev_log(project_name, {
        "pipeline_gate": {
            "checked_at": datetime.now().isoformat(),
            "project_exists_in": where,
            "gate_passed": True
        }
    })
    add_dev_log_step(project_name, "门控通过", status="completed", 
                     detail=f"方案: {plan_path.name}, 流水线空闲")
    
    # ── 步骤 2: 在开发中/ 创建项目目录（占位）──
    dev_project_dir = DEV_DIR / project_name
    dev_project_dir.mkdir(parents=True, exist_ok=True)
    add_dev_log_step(project_name, "创建开发目录", status="completed",
                     detail=f"开发中/{project_name}/")
    
    # ── 步骤 3: 复制方案到开发中/ 作为参考 ──
    shutil.copy2(str(plan_path), str(dev_project_dir / "README.md"))
    add_dev_log_step(project_name, "复制方案参考", status="completed",
                     detail="方案 → 开发中/README.md")
    
    # ── 步骤 4: 写 dev-log 到项目目录 ──
    dev_log_entry = json.loads(dev_log_path(project_name).read_text())
    (dev_project_dir / ".dev-log.json").write_text(
        json.dumps(dev_log_entry, indent=2, ensure_ascii=False)
    )
    add_dev_log_step(project_name, "写入开发日志", status="completed",
                     detail=f".dev-log.json → 开发中/{project_name}/")
    
    # ── 步骤 5: 提交占位 commit ──
    commit_msg = f"auto: start dev {project_name} - {plan_path.name}"
    subprocess.run(["git", "-C", str(REPO_ROOT), "add", "-A"], capture_output=True)
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "commit", "-m", commit_msg],
        capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "push", "origin"],
        capture_output=True, timeout=30
    )
    add_dev_log_step(project_name, "提交占位commit", status="completed",
                     detail=f"git commit: {commit_msg}")
    
    log(f"✅ 门控通过 → {project_name} 已进入流水线")
    log(f"   📋 dev-log: {dev_log_path(project_name)}")
    log(f"   📂 项目目录: {dev_project_dir}")
    log(f"   ⏭️  下一步: 启动 dev-collab-ultimate 完成编码+测试+验证")
    
    # 标记整体状态
    update_dev_log(project_name, {"status": "gate_passed"})
    
    return project_name, "ok", ""

def print_pipeline_status():
    """打印流水线完整状态"""
    log("=" * 60)
    log("📊 流水线状态报告")
    log("=" * 60)
    
    # 待开发/
    plans = scan_plans()
    log(f"\n📋 待开发/ ({len(plans)} 个方案)")
    for rel in sorted(plans.keys()):
        log(f"   📄 {rel}")
    
    # 开发中/
    dev_projects = list_projects(DEV_DIR)
    log(f"\n🔧 开发中/ ({len(dev_projects)} 个项目)")
    for p in dev_projects:
        status = "未知"
        log_path = dev_log_path(p)
        if log_path.exists():
            try:
                entry = json.loads(log_path.read_text())
                status = entry.get("status", "未知")
                step = entry.get("step", 0)
                err = entry.get("last_error", "")
                err_str = f" ❌ {err[:60]}" if err else ""
                log(f"   📦 {p} [步骤{step}] 状态: {status}{err_str}")
            except:
                pass
        else:
            log(f"   📦 {p}")
    
    # 开发完/
    done_projects = list_projects(DONE_DIR)
    log(f"\n✅ 开发完/ ({len(done_projects)} 个项目)")
    for p in done_projects:
        log(f"   📦 {p}")
    
    # 门控状态（按项目去重展示）
    dev_projects = list_projects(DEV_DIR)
    done_projects = list_projects(DONE_DIR)
    log(f"\n🔒 门控: 按项目名去重 — 新项目不在开发中/开发完 即可自动开发")
    log(f"   开发中/ 项目: {dev_projects if dev_projects else '（空）'}")
    log(f"   开发完/ 项目: {done_projects if done_projects else '（空）'}")
    
    log("=" * 60)

# ─────────────────────────────────────────────
# 命令处理
# ─────────────────────────────────────────────

def main():
    log("=" * 50)
    log("🔍 Pipeline Watchdog 启动")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if mode == "scan":
        # ── 扫描模式：按项目名去重，新项目才开发 ──
        state = load_state()
        changes, current = detect_changes(state)
        
        if not changes:
            log("⏭️ 无新方案")
        else:
            log(f"📋 发现 {len(changes)} 个新/修改的方案")
            
            new_count = 0
            skip_count = 0
            
            for rel in sorted(changes):
                plan_path = WATCH_DIR / rel
                project_name = plan_path.parent.name
                
                # ⚡ 门控: 检查此项目是否已存在于开发中/开发完
                exists, where = check_project_exists(project_name)
                
                if exists:
                    log(f"⏭️ [门控] {project_name} 已在 {where}，跳过")
                    skip_count += 1
                else:
                    log(f"✅ [门控] {project_name} 是新项目，启动开发")
                    project_name, result, extra = trigger_development(rel)
                    if result == "ok":
                        log(f"   ✅ {project_name} 已进入开发流水线")
                        new_count += 1
            
            # 记录扫描快照
            state["scanned"] = current
            log(f"📊 本次扫描: {new_count} 个新项目启动, {skip_count} 个已存在跳过")
        
        # 记录门控日志到 state
        state["gate_log"] = state.get("gate_log", [])
        gate_entry = {
            "time": datetime.now().isoformat(),
            "dev_count": len(list_projects(DEV_DIR)),
            "done_count": len(list_projects(DONE_DIR)),
            "dev_projects": list_projects(DEV_DIR),
            "done_projects": list_projects(DONE_DIR)
        }
        state["gate_log"].append(gate_entry)
        if len(state["gate_log"]) > 20:
            state["gate_log"] = state["gate_log"][-20:]
        state["last_scan"] = datetime.now().isoformat()
        save_state(state)
    
    elif mode == "force":
        # ── 强制模式：跳过门控检查，直接开发 ──
        # 仅用于手动干预
        log("⚠️ 强制模式 — 跳过门控检查")
        state = load_state()
        changes, current = detect_changes(state)
        if changes:
            for rel in changes:
                trigger_development(rel, bypass_gate=True)
        else:
            log("⏭️ 无新方案")
        state["scanned"] = current
        state["last_scan"] = datetime.now().isoformat()
        save_state(state)
    
    elif mode == "status":
        # ── 状态模式 ──
        print_pipeline_status()
    
    elif mode == "log":
        # ── 查看项目开发日志 ──
        project = sys.argv[2] if len(sys.argv) > 2 else None
        if project:
            print_dev_log(project)
        else:
            # 列出所有 dev-log
            log_dir = REPO_ROOT / ".dev-logs"
            if log_dir.exists():
                for lf in sorted(log_dir.glob("*.json")):
                    print_dev_log(lf.stem)
            else:
                log("📋 无开发日志")
    
    elif mode == "gate":
        # ── 按项目名去重检查 ──
        project = sys.argv[2] if len(sys.argv) > 2 else None
        if project:
            exists, where = check_project_exists(project)
            if exists:
                print(f"⏭️ {project} 已存在于 {where}")
            else:
                print(f"✅ {project} 是新项目，可以开发")
        else:
            # 项目名模式: 列出所有开发中/开发完项目
            dev = list_projects(DEV_DIR)
            done = list_projects(DONE_DIR)
            print("开发中/:")
            for p in dev: print(f"  📦 {p}")
            print("开发完/:")
            for p in done: print(f"  📦 {p}")
            print("\n用法: pipeline_watchdog.py gate <项目名> — 检查单个项目")
    
    elif mode == "sync":
        sync_to_remote()
    
    elif mode == "move-done":
        project = sys.argv[2] if len(sys.argv) > 2 else None
        if project:
            src = DEV_DIR / project
            dst = DONE_DIR / project
            if src.exists():
                # 记录完成日志
                add_dev_log_step(project, "归档到开发完", status="completed",
                                detail=f"开发中/ → 开发完/")
                update_dev_log(project, {
                    "status": "done",
                    "completed_at": datetime.now().isoformat()
                })
                
                shutil.copytree(src, dst, dirs_exist_ok=True)
                shutil.rmtree(src)
                log(f"✅ {project} 已归档到 开发完/")
                sync_to_remote()
            else:
                log(f"❌ 项目 {project} 不存在于 开发中/")
        else:
            log("❌ 请指定项目: move-done YYYY-MM-DD-项目名")

def sync_to_remote():
    """同步 开发中/ 开发完/ 到远程仓库"""
    log("📤 同步到远程仓库...")
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "add", "-A"],
        capture_output=True, text=True, timeout=30
    )
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--cached", "--quiet"],
        capture_output=True, timeout=10
    )
    if result.returncode != 0:
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "commit", "-m",
             f"auto: daily sync {datetime.now():%Y-%m-%d %H:%M}"],
            capture_output=True, timeout=30
        )
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "push", "origin"],
            capture_output=True, timeout=30
        )
        log("✅ 同步完成")
    else:
        log("⏭️ 无变更，跳过同步")

if __name__ == "__main__":
    main()
