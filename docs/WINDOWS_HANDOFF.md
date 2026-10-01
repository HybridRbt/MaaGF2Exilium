# Windows 游戏电脑本地接续（2026-10-01）

## 获取当前工作

- 仓库：https://github.com/HybridRbt/MaaGF2Exilium
- 开发分支：`codex/pc-dialog-fixes`；草稿 PR：https://github.com/HybridRbt/MaaGF2Exilium/pull/1
- r3 代码提交：`a14a52452c030d3125c6051ca541df20ab20088c`。后续接续文档提交不改变该安装包内容。
- r3 复制安装器：https://github.com/HybridRbt/MaaGF2Exilium/actions/runs/36901860525/artifacts/11182535634
- 此代码的 check 和 install 工作流均成功。check 包含19项测试、三种资源组合加载及测试包构建。安装器属于测试 artifact，不是正式发布。

先读 `AGENTS.md`、`docs/PROJECT_STATE.md`、本文及 `docs/测试补丁安装.md`。从上述分支检出独立开发目录；不要把源码工作目录与游戏安装目录混用。已经位于独立 worktree 时无需再嵌套创建。

## 已知现场状态

用户版本为软件 v2.16.1、资源 v2.7.2、框架 v5.12.3，中文 PC 画面证据为1280×720。连接采用 FramePool，键盘和鼠标均 Seize。助手必须以管理员身份运行；用户确认补权限后点击恢复，启用新选项后极限峰值缺员确认成功进入战斗。无需再次询问这些已提供的信息。

用户要求原安装目录保持不变：复制完整文件夹，只在新副本打补丁，并把副本可执行文件快捷方式放到桌面。原路径记录为 `C:\MaaGF2ExiliumGUI-win-x86_64-v2.7.2`。日志记录的成功 r2 副本为 `C:\MaaGF2ExiliumGUI-win-x86_64-v2.7.2-补丁测试-20261001-121034-c4fbb6`，仅供定位参考，不能认为当前仍运行这一副本。r3 是否已安装尚未得到用户确认。

用户已开启「极限峰值：槽位未满仍开始作战」。该选项源码默认关闭，仅重定向极限峰值0级三个子群，不改变其他模式补人逻辑。

## 实测与待验证分开记录

已实机确认：副本安装成功、新选项显示、管理员权限修复无点击、缺员确认成功开启极限峰值战斗。

已实现但尚待实机验证：预演介绍关闭和连续多个角色预演；r3 战斗等待、主动打开周期报酬，以及快捷方式管理员标志。用户确认游戏将已完成预演移到列表尾部，代码每场结束后重新选择第一项，总尝试上限8。

r3 两处修复依据用户提供的 `log_20261001_123447.zip`：

1. 12:30:28 确认缺员作战节点 duration=20311ms/reco_timeout=20000ms；错误截图仍在自动战斗中。确认节点采用原作战开始节点的 timeout=2000000，继续等待胜利/失败及结算，未修改全局超时。
2. 12:29:25 已执行「进入常规峰值」，随后因没有自动报酬弹窗而退出；OCR 可见左下「周期报酬」。新增主动打开路径，ROI=[0,560,300,160] 基于该日志的1280×720截图，复用既有领取/关闭节点。无需根据红点猜测是否切页。

测试模拟视觉识别和外部战斗，不等于真实游戏验证。19项测试全部通过；当前不能宣称上述待验证项已成功。

用户最新表示有新问题，但尚未描述现象。本地会话应接收新的反馈，先读现场日志，再确定原因，不预设与旧问题相同。

## 本地会话首先做什么

1. 确认工具环境确实运行在 Windows 游戏电脑，能读取本地文件；本次上传工作在 Linux 云端完成，不能把聊天在电脑上打开视为已接入本地运行环境。
2. 只读查看助手进程路径、桌面补丁快捷方式的目标/工作目录/管理员标志，定位用户实际运行的副本。核对其 interface 版本、补丁备份/清单及关键节点，确定安装的是哪轮补丁，不根据文件夹后缀猜测。
3. 从实际副本读取 `debug/maafw.log`、`logs/log*.log`、`debug/on_error` 最新相关截图及 `dialog-patch/apply-output.log`。保存错误节点、时间、超时和前后节点，结合用户的新现象分析。不要修改原目录，不删除失败副本，不覆盖用户桌面上其他快捷方式。
4. 需要调整代码时在源码独立目录进行，适当验证后构建新的版本定向包。若需部署，沿用复制安装器，只在新副本修改；从已有补丁副本复制时，安装器会先在新副本回滚旧补丁再安装。详见安装说明。
5. 当前上传/接续请求不授权自动启动助手、停止现有脚本或执行游戏战斗。新的现场操作依据本地会话的当前用户指令；文件与日志的只读检查可先进行。

原始附件日志和截图未提交到公开仓库；仓库记录了技术证据与结论，保留已有匿名介绍模板。新会话优先读取游戏电脑当前日志，旧附件可从原聊天取得。不要上传账号资料、角色BOX或凭证。

## 开发与验证入口

- `assets/resource/base/pipeline/public/SimulatedCombat/极限峰值缺员作战.json`：独立缺员确认和战斗等待。
- 同目录 `peakValueAssessment.json`：常规峰值切页及周期报酬领取。
- `assets/resource/base/pipeline/public/活动/预演.json`、`assets/resource/base/pipeline/public/通用战斗.json`：多角色预演与介绍弹窗。
- `scripts/build_dialog_patch.py`、`scripts/dialog_patch/patch.py`、`scripts/dialog_patch/deploy-copy.ps1`：构建、校验/回滚、副本与桌面快捷方式。
- `tests/`：安装保护、预演循环、峰值运行路由等测试。

开发 Python 环境安装 `requirements-dev.txt`，然后执行：

```text
python -m unittest discover -s tests -v
python check_resource.py
git diff --check
python scripts/build_dialog_patch.py --output build/dialog-test
```

保持个人 fork 草稿 PR，不自动合并、发上游 PR 或正式发布。继续上传源码时使用 HybridRbt GitHub 账号；不要误用另一个已连接账号。

## 新本地会话首条消息

> 继续 HybridRbt/MaaGF2Exilium 的 codex/pc-dialog-fixes 分支开发（草稿PR #1）。现在在游戏电脑本地会话，请先读 AGENTS.md、docs/PROJECT_STATE.md 和 docs/WINDOWS_HANDOFF.md，确认本地环境并只读定位实际运行的补丁副本及最新日志。原安装目录不能修改；后续补丁只在新副本安装并创建桌面快捷方式。我会继续反馈新问题。管理员启动和缺员确认已实机通过，其他待验证项目按文档记录。
