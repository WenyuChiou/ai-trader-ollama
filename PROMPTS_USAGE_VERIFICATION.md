# Prompts 使用路径验证

## ✅ 确认：test_scenarios.py 和实际运行使用相同的 prompts

### 路径解析逻辑

1. **test_scenarios.py 运行路径**：
   - 文件位置：`backend/test_scenarios.py`
   - 运行目录：`backend/`（从 backend 目录运行）

2. **AgentFactory 创建**：
   - `run_multi_analyst_discussion` 使用：`AgentFactory(ROOT / "config" / "agents.yaml")`
   - `ROOT = Path(__file__).resolve().parents[2]` = `backend/` 目录
   - 所以 `config_path` = `backend/config/agents.yaml`

3. **factory.py 的 _load_prompts 方法**：
   ```python
   config_path = backend/config/agents.yaml
   root_prompts_dir = config_path.parent.parent.parent / "prompts"
   # = backend/config -> backend/config -> backend -> prompts
   # = 项目根目录 / prompts
   ```

4. **实际使用的 prompts 路径**：
   - ✅ **项目根目录的 `prompts/` 文件夹**
   - 这是 `test_scenarios.py` 和实际运行都使用的路径

### 验证结果

- ✅ `backend/config/agents.yaml` 存在
- ✅ `prompts/` 文件夹存在（项目根目录）
- ✅ `prompts/trader_agent.yml` 存在
- ✅ `factory.py` 优先使用项目根目录的 `prompts/` 文件夹

### 结论

**test_scenarios.py 和实际运行使用完全相同的 prompts 文件夹**：
- 都使用项目根目录的 `prompts/` 文件夹
- 都通过 `backend/config/agents.yaml` 中的 `../prompts/xxx.yml` 路径
- `factory.py` 统一解析到项目根目录的 `prompts/` 文件夹

### 统一后的优势

1. ✅ **一致性**：测试和实际运行使用相同的 prompts
2. ✅ **维护简单**：只需要维护一个 prompts 文件夹
3. ✅ **避免混淆**：不会因为路径不同导致版本不一致

