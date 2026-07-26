# Recovery Guide — 故障恢复手册

## 通用恢复流程

```
1. 判断故障类型 → 对照 pitfall-catalog.md 找症状
2. 确定当前停在哪一步 → 看 dev-log 或 task.md 的 ✅ 标记
3. 选择恢复方式 → 手动推进 / 重置步进锁 / 重跑 tab
4. 验证恢复成功 → 检查 ✅ 标记和文件完整性
5. 更新 brain 记录
```

---

## R-01: Tab 卡住不返回

**症状**: 某个 tab 启动后 60 秒没写出 ✅ step_N_done

**排查**:
```bash
# 看 WT 窗口还在不在
powershell.exe "Get-Process | Where-Object { \$_.ProcessName -like '*wt*' }"

# 看 dev-log 最后状态
cat /home/zhang/.hermes/scripts/.pipeline_state.json
```

**恢复**:
1. 如果 WT 窗口还在 → 切过去看报错，修正后手动写 ✅
2. 如果 WT 窗口没了 → 重启该 tab
3. 如果资源不足 → `free -m` 确认内存，关掉不必要的程序

---

## R-02: 步进锁死锁

**症状**: step 3 标记已写，step 4 没启动，也没有报错

**排查**:
```bash
grep "^✅" task.md  # 看哪个 step 卡住
# 确认 grep 用的是 ^ 锚定
```

**恢复**:
```bash
# 如果 step 3 完成了但下游没触发 → 手动写 step 3 再次触发
# 或者检查 grep 指令是否用了 ^ 锚定
```

---

## R-03: pytest 全部失败

**症状**: pytest exit != 0，修复回环 3 轮全用完了

**排查**:
```bash
# 看是不是双目录污染（P-11）
find . -type d \( -name __pycache__ -o -name .pytest_cache \) | head -10
# 清理
find Sandbox/ -type d \( -name __pycache__ -o -name .pytest_cache \) -exec rm -rf {} + 2>/dev/null
```

**恢复**:
1. 清理缓存后重跑 pytest
2. 如果还是失败 → 检查是否是 tests/ 路径不对（P-05）
3. 人工介入修复最关键的失败 case，然后手动写 ✅ step_4_done

---

## R-04: 项目归档了一半

**症状**: `开发完/` 有项目文件但 `开发中/` 还没清理，或者反过来

**恢复**:
```bash
# 确认项目实际状态
ls -la "开发中/$项目名" 2>/dev/null && echo "仍在开发中/"
ls -la "开发完/$项目名" 2>/dev/null && echo "已归档"

# 手动清理
rm -rf "开发中/$项目名"
# 或 mv 回去
mv "开发完/$项目名" "开发中/$项目名"
```

---

## R-05: Hermes 断连后状态丢失

**症状**: 对话 /new 后不记得项目跑到哪一步了

**恢复**:
1. `gbrain query "dev-pipeline 项目名"` — 从 brain 查最后记录
2. 查本地 dev-log: `cat .pipeline_state.json`
3. 查 task.md 的 ✅ 标记
4. 三对照确定当前 step，继续推进

**预防**: 每次 step 完成都会写 brain 记录（见"brain 持久化"部分）

---

## R-06: 模型切换导致兼容问题

**症状**: Claude Code 启动时崩溃或 API 返回 400

**排查**:
```bash
echo $ANTHROPIC_BASE_URL          # 确认是 DeepSeek 端点
echo $ANTHROPIC_DANGEROUSLY_NO_THINKING  # 应为 1
```

**恢复**:
```bash
export ANTHROPIC_DANGEROUSLY_NO_THINKING=1
```

**预防**: 启动脚本里已写死 `export ANTHROPIC_DANGEROUSLY_NO_THINKING=1`

---

## 恢复后的处理

恢复完成后，跑一次验证确保流水线状态一致：
```bash
# 1. 确认 ✅ 标记正确
grep "^✅" task.md

# 2. 确认项目只在一个目录下
ls -d "开发中/$项目名" "开发完/$项目名" 2>/dev/null

# 3. 写 brain 恢复记录
gbrain query "复述: 项目 $项目名 恢复完成，当前在步 $N"
```
