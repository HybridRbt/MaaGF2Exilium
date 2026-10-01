# Codex Cloud 接续

2026-10-01：用户下一步选择在游戏电脑开本地会话，当前接续入口改为 [WINDOWS_HANDOFF.md](WINDOWS_HANDOFF.md)。本文保留云端开发方式；最新证据与待验证项见 PROJECT_STATE.md。

官方当前入口：新任务 Work in → Cloud → Select environment → Create environment，选择 HybridRbt/MaaGF2Exilium，完成依赖准备与验证后Publish，再从已发布环境开始任务。不能把本地会话是否迁移成功与源码已推送混为一谈。

准备依赖：python -m pip install -r requirements-dev.txt
验证：python -m unittest discover -s tests -v；python check_resource.py。

日常流水线/图片开发无须完整GUI、游戏账户或Windows。构建完整安装包时才按上游开发流程初始化MaaCommonAssets子模块、配置OCR模型并下载平台依赖。不默认运行全部旧requirements.txt（其maafw5.4.1与当前打包版本不一致）。

云端首条任务建议：

> 在HybridRbt/MaaGF2Exilium中检出codex/pc-dialog-fixes，先读AGENTS.md及docs/PROJECT_STATE.md。继续验证极限峰值缺员开关及预演人形介绍关闭路径，运行requirements-dev.txt对应测试和check_resource.py。缺员提示和版本截图均已提供，缺员确认已实机成功。继续验证 r3 战斗等待与领奖、多角色预演，模拟结果不等于实机成功。云端不要连接、停止或执行游戏战斗。更新个人fork的草稿PR，不自动合并或发上游PR。

官方依据：https://learn.chatgpt.com/docs/environments/cloud-environments 。当前客户端可见性与用户GitHub连接权限仍需在创建环境时确认。
