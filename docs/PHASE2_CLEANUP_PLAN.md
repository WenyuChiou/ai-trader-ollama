# Phase 2 清理计划

## 🗑️ 需要清理的文件

### 1. 旧的根目录文件（已迁移到 backend/）
- ❌ `src/` - 已移到 `backend/src/`
- ❌ `config/` - 已移到 `backend/config/`
- ❌ `tests/` - 已移到 `backend/tests/`

### 2. 临时文档（检查清单、预览等）
- ❌ `GIT_PUSH_CHECKLIST.md` - 推送检查清单（临时）
- ❌ `PUSH_PREVIEW.md` - 推送预览（临时）
- ❌ `PUSH_README_UPDATE.md` - README 更新预览（临时）

### 3. 可以合并的重复文档
- ❌ `PHASE2_COMPLETE.md` - 内容已包含在 `docs/PHASE2_SUMMARY.md`
- ❌ `PHASE2_GITHUB_PUSH.md` - 内容已包含在 `docs/PHASE2_PUSH_SUCCESS.md`
- ❌ `PHASE1_READY.md` - 内容已包含在 `docs/PHASE1_SUMMARY.md`
- ❌ `docs/PHASE2_PROGRESS.md` - 临时进度，已包含在 SUMMARY
- ❌ `docs/PHASE2_GIT_COMMITS.md` - 已包含在 SUMMARY
- ❌ `docs/PHASE2_PUSH_SUCCESS.md` - 已包含在 SUMMARY
- ❌ `docs/README_UPDATE_PUSHED.md` - 临时推送确认

### 4. 保留的重要文档
- ✅ `docs/PHASE0_SUMMARY.md` - Phase 0 总结
- ✅ `docs/PHASE1_SUMMARY.md` - Phase 1 总结
- ✅ `docs/PHASE2_SUMMARY.md` - Phase 2 总结
- ✅ `BRANCH_STRATEGY.md` - 分支策略
- ✅ `MIGRATION_MASTER_PLAN.md` - 完整迁移计划
- ✅ `README.md` - 主文档

## 🎯 清理原则

1. **删除已迁移的旧目录**（src/, config/, tests/）
2. **删除临时文档**（推送前的检查清单、预览等）
3. **合并重复的文档**到 SUMMARY 中
4. **保留重要的总结文档**

