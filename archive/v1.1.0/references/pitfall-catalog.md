# Pitfall Catalog — 已知坑全录

> 随流水线使用持续补充。每个坑按 `P-序号` 索引。

## P-01: 步进锁预写标记

**症状**: Tab3 不等 Tab1 完成就启动，步进锁形同虚设
**根因**: task.md 模板里预写了 `✅ step_3_done`，Tab3 的 grep 一启动就匹配到
**修复**: 模板只写"追加标记内容是 ✅ step_N_done"，不要预写标记本身
**验证**: `grep "✅" task.md` 不应返回任何行

---

## P-02: 归档路径不统一

**症状**: tab2 归档时报 `mv: cannot stat`，文件没搬走
**根因**: 归档时用短项目名，但目录是完整 `YYYY-MM-DD-项目名`
**修复**: 一律用目录全名，不要截断

---

## P-03: 归档后不清理开发中/

**症状**: 同一个项目同时在 `开发中/` 和 `开发完/` 出现
**根因**: tab2 归档 `Sandbox/` 后没删除 `开发中/` 下的项目
**修复**: `rm -rf "开发中/$项目名"` 在归档后执行

---

## P-04: grep 不锚定行开头（已修）

**症状**: 步进锁不生效，3 个 tab 并发跑
**根因**: `grep "✅ step_3_done"` 匹配到指令文字"追加一行: ✅ step_3_done"中的子串
**修复**: 必须 `grep "^✅ step_3_done"` 行开头锚定
**防回弹**: 模板指令也不应包含标记原文，用"标记内容是✅"而非"追加一行: ✅"

---

## P-05: pytest 找不到测试文件

**症状**: `pytest exit=5, collected 0 items`
**根因**: 代码在 `gomoku/src/` 下但 pytest 在根目录搜 `tests/`，`tests/` 在 `gomoku/` 里
**修复**: `find . -type d -name tests -path "*/$项目名/*"` 拿到路径再传
**回环比**: 每轮修复回环重新执行 find，因为路径可能变了

---

## P-06: 兜底 fallback 写假标记

**症状**: 下游提前启动，agent 失败也触发了下一步
**根因**: agent 脚本末尾有 fallback 逻辑（超时写假标记）
**修复**: 删除所有 fallback。agent 失败就不写标记，步进锁自然不动

---

## P-07: TOCTOU — 标记先于文件就绪

**症状**: tab2 读 `tests/` 说不存在，但明明已经创建了
**根因**: Tab1 写 `✅ step_3_done` 后文件系统还没 flush，tab2 立即读到了标记但 `tests/` 还没落盘
**修复**: tab2 检测到 `✅ step_3_done` 后重试 12×5s 等 `tests/` 出现再继续
**验证**: 在 WSL ext4 和 Windows drvfs 上都测试过，drvfs 延迟更明显

---

## P-08: 指令文字包含标记原文

**症状**: 指令文字本身被 grep 误匹配，锁提前释放
**根因**: 模板里的指令写的是"追加一行: ✅ step_3_done"，grep 搜 "✅ step_3_done" 时匹配到了指令行
**修复**: 指令改为"标记内容是✅"，字串不重叠。在 P-04 的基础上进一步隔离

---

## P-09: 修复回环内路径失效

**症状**: 第 2 轮修复时 pytest 还是 fail
**根因**: 修复回环第 1 轮 find 到的路径缓存在变量里，第 2 轮 Claude Code 改了文件结构后路径不对了
**修复**: 每轮重新 `find tests/` 计算路径，不要缓存

---

## P-10: DeepSeek 不支持 thinking 模式

**症状**: Claude Code 启动即崩溃，终端吐 `thinking mode not supported` 或 `400`
**根因**: DeepSeek API 不支持 Anthropic 的 extended thinking，Claude Code 默认开启
**修复**: `export ANTHROPIC_DANGEROUSLY_NO_THINKING=1` 在启动脚本中
**检查**: `echo $ANTHROPIC_DANGEROUSLY_NO_THINKING` 应输出 `1`

---

## P-11: 双目录搜索污染（2026-07-26 新增）

**症状**: pytest 跑了 2 倍以上 case，或报了旧代码的 ModuleNotFoundError
**根因**: `find tests/` 同时搜到 `Sandbox/`（当前项目）和 `开发中/` 下其他已归档项目的旧 `tests/`
**修复**: 步 3→步 4 之间先清理 `find Sandbox/ -type d \( -name __pycache__ -o -name .pytest_cache \) -exec rm -rf {} + 2>/dev/null`
**验证**: 清理后 pytest 只跑当前项目的 case 数

---

## P-12: Tab 启动失败 / 窗口卡住

**症状**: powershell Start-Process 不返回，或窗口启动了但 shell 未就绪
**根因**: Windows 资源紧张 / WT session 初始化慢 / 命令发送过早
**修复**: 
  - 先 `sleep 3` 再往 tab 写命令
  - 如果 60 秒内没看到 ✅ step_N_done，人工查
  - 不要多发命令——每个 tab 只发一次
**预防**: 启动前检查 `free -m` 剩余内存 > 1G

---

## P-13: 测试文件在项目根目录而非 tests/ 子目录（2026-07-26 新增）

**症状**: tab2 报 "等待测试文件超时"，但实际上项目已有 `test_*.py`
**根因**: tab2-ultimate.sh 只用 `find ... -type d -name "tests"` 搜索目录，不搜索根目录的 `test_*.py`
**修复**: 在 tab2-ultimate.sh 的测试搜索逻辑中添加降级策略——找不到 `tests/` 目录时搜索 `test_*.py` 文件
**验证**: `find /path/to/project -maxdepth 2 -name "test_*.py"` 应返回测试文件
**注意**: claude_task 和 opencode_task 中应明确指定测试文件存放位置（`tests/` 或根目录）

---

## 新增坑的提交流程

1. 在 pipeline-troubleshooting skill 的排查表加一行
2. 在这个 pitfall-catalog.md 加新 P-序号
3. 修复方法写入 active 的 SKILL.md 流程或脚本
4. 同步到 dev-collab-ultimate-v6 快照
