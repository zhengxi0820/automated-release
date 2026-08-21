# XHS 热点内容流水线（XHS Hotspot Pipeline）

每日自动跑通「热点采集 → 探讨意义判断 → 人工审核 → 成文 → 手机润色 → 图文卡片 → 发布包」的小红书内容流水线。

- 第一版：本地 Windows 运行，手动发布
- 多领域共存：流水线逻辑与领域配置分层，`domains/` 下每目录一个领域，可并行运行
- 文档先行：见 `docs/`（需求、架构、接口）
- 回归测试：`tests/`（固定 fixture，防行为漂移）

## 文档导航

- [需求文档](docs/需求文档.md)
- [架构文档](docs/架构文档.md)
- [接口文档](docs/接口文档.md)
- [AIHOT API 参考](docs/AIHOT_API参考.md)（数据源接口字段说明）
- [AIHOT Skill 说明](docs/AIHOT_Skill说明.md)（官方 Skill 规则，含安全边界）

## 快速开始

```bash
# 安装依赖
python -m pip install -r requirements.txt

# 配置凭据：复制 .env.example 为 .env，填写 DEEPSEEK_API_KEY / PUSHPLUS_TOKEN

# 初始化数据库与领域注册
python scripts/init_db.py

# 跑一次今日流水线：collect → assess（生成候选池，等待人工挑题）
python scripts/run_daily.py --domain ai-tools --until assess

# 全流程演示（自动选 1 条，走到成文）：--until draft --auto-select 1
# 成图与发布包：--until package（需要本机 Chrome）

# 启动审核界面（手机访问 http://<局域网IP>:8000）
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
```

## 测试

```bash
python -m pytest tests/ -q
```
