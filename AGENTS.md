# MaaGF2Exilium fork 开发约定

- 工作仓库：HybridRbt/MaaGF2Exilium；上游：DarkLingYun/MaaGF2Exilium。先读 docs/PROJECT_STATE.md。独立改动使用 codex/ 分支与独立 worktree；已在 worktree 中不要再嵌套创建。
- 本仓库只维护助手代码、模板及匿名游戏证据，不导入二游助手的角色BOX、账号资源或凭证。用户提供的裁剪图只证明图中内容，不能推出整窗坐标或游戏分辨率。
- 当前目标是极限峰值0级缺员可选继续，以及预演试用介绍弹窗关闭。范围和授权见 docs/PROJECT_STATE.md。
- 缺员继续选项默认关闭、限定极限峰值；不能改变其他模式补人行为。弹窗必须先识别，再识别并点击按钮，避免无条件固定坐标点击。
- 用户现有脚本正在运行，不接管Windows、不停止脚本、不执行战斗。新的游戏操作需要当前用户授权；历史授权不能替代。
- 验证命令：python -m unittest discover -s tests -v；python check_resource.py；git diff --check。依赖见 requirements-dev.txt。资源可加载、离线图片匹配、实机通关是不同证据，分别报告。
- 只在个人fork开草稿PR；不自动合并，不向上游发PR或发布版本。待缺员弹窗与安装版本齐全、用户实机反馈后再调整并构建测试包。
- 云端接续读 docs/CLOUD_HANDOFF.md。Linux云端能改代码和检查资源；它不等于已连接Windows游戏。不要安装远端控制或战斗执行服务来绕过此边界。
