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

## 快速开始（待代码落地后补充）

```bash
# 安装依赖
python -m pip install -r requirements.txt

# 初始化数据库与领域配置
python -m pipeline init

# 跑一次今日流水线（不含发布）
python -m pipeline run --domain ai-tools --dry-run

# 启动审核界面
python -m web.app
```
