# CLAUDE.md

本文件是给 Claude Code 读的项目记忆文件，每次在项目目录启动 `claude` 会自动加载。
人类作者：Sophia。本项目最初由 Codex 协助生成，Claude Code 作为**备用审查 agent**使用。

---

## 项目一句话

发发布ai小助手：本地 AI 视频自动发布工具。把一个已经做好的 MP4，通过浏览器自动化上传到**抖音**和**视频号**，停在发布确认页由用户人工点击最终发布。

技术栈：Python 3 + Playwright（浏览器自动化）+ 原生 HTML 网页（任务填写界面）。
默认使用系统已装的 Google Chrome，无需额外下载 Chromium。

## 目录与模块职责

```
ai视频自动化/
├── ai_video_publisher/         # Python 主包
│   ├── __main__.py             # CLI 入口：login / check / upload-video / publish / serve
│   ├── config.py               # 本地数据目录、登录态路径、profile 路径
│   ├── task.py                 # 读取并校验 task.web.json
│   ├── browser.py              # Playwright 启动、登录态保存、用户暂停确认
│   ├── server.py               # 本地网页服务（serve 命令；/api/publish 网页一键触发）
│   ├── publish_flow.py         # 多平台发布编排：失败隔离、统一停在确认页
│   └── uploaders/
│       ├── base.py             # 平台 uploader 统一接口
│       ├── douyin.py           # 抖音登录/检查/上传
│       └── wechat_channels.py  # 视频号登录/检查/上传
├── web/index.html              # 任务填写网页
├── hyperframes/                # AI 视频制作产物（脚本/分镜/配音/成片）
│   └── finalvideo.mp4          # 默认要发布的视频
├── uploads/                    # 网页上传的视频存放处
├── examples/task.example.json  # 任务文件示例
├── task.web.json               # 网页生成的当前任务（运行时产物）
├── .publisher_data/            # 登录态/profile/日志（本地，不提交）
├── requirements.txt            # 只有 playwright>=1.46.0
├── PRD_ai_video_publisher.md   # 产品需求文档
└── README.md                   # 用户文档
```

数据目录约定（见 `config.py`）：
- `.publisher_data/states/{platform}-{account}.json` — Playwright 浏览器 state
- `.publisher_data/profiles/{platform}-{account}/` — 浏览器 profile
- `.publisher_data/logs/` — 日志

## 关键命令（人类视角）

```bash
# 启动网页（在项目根目录）
python3 -m ai_video_publisher serve --port 8765
# → http://127.0.0.1:8765

# 登录（首次）
python3 -m ai_video_publisher login douyin   --account creator
python3 -m ai_video_publisher login tencent  --account creator

# 检查登录态
python3 -m ai_video_publisher check douyin   --account creator
python3 -m ai_video_publisher check tencent  --author creator

# 执行发布任务（serve 模式下也可直接由网页「开始上传流程」按钮触发）
python3 -m ai_video_publisher publish task.web.json --account creator
```

## 发布流程行为（2026-10 更新）

- **网页 serve 模式**：点「开始上传流程」→ server 起子进程跑 publish → 页面轮询 `/api/publish/status` 展示日志与 5 步进度；停在确认页后用户手动发布，**关闭浏览器窗口即收尾**（30 分钟超时兜底，见 `browser.HOLD_TIMEOUT_SECONDS`）。
- **终端 publish**：两个平台先依次上传+填写，最后**统一**停在确认页，按一次 Enter 结束（不再每平台按一次）。
- **S2 已修**：平台间 try/except 隔离，结束输出 `[SUMMARY] douyin=ok,wechat_channels=fail` 这样的行；任一失败退出码非零。
- 上传器 `publish()` 内部**不再**调用 `pause_for_user`；停顿统一由 `browser.wait_for_user_confirm` 收尾（终端等 Enter / 非交互等窗口关闭，靠 `sys.stdin.isatty()` 区分）。

平台别名：`douyin`=抖音；`tencent`=`wechat_channels`=视频号。

## 硬约束（审查 / 修改时必须遵守）

1. **永远不要让代码自动点击最终发布按钮**。`publish_now` 默认 `false`，行为是停在确认页。
2. **不绕过扫码登录、不绕过验证码、不保存账号密码**。
3. `.publisher_data/` 里的内容（state、profile、cookie）属于敏感登录态，**不要输出到对话里、不要写入 git、不要放进任何报告**。
4. 修改后必须保持 `python3 -m ai_video_publisher --help` 能正常显示，所有子命令不报错。

## 审查重点（这个项目最容易出问题的地方）

按优先级从高到低：

1. **平台选择器脆弱性**（高危）
   - `douyin.py` / `wechat_channels.py` 里的 `input[type=file]`、标题输入框、正文输入框、标签输入框的选择器，平台一旦改版就失效。
   - 审查时确认：是否有显式 `wait_for_selector` + 合理超时；选择器是否过于依赖 nth-child / 结构位置；缺少有意义的报错信息。

2. **登录态过期处理**
   - state JSON 失效后，uploader 是抛清晰错误还是默默卡住？建议失败时引导用户重新 `login`。

3. **上传完成的等待**
   - 抖音/视频号上传是异步的，文件 input 提交后还要等平台处理完才能填信息。检查是否有等待"上传完成"指示元素的逻辑，超时设定是否合理。

4. **错误处理与重试**
   - 当前 README 待优化项里写了"增加失败重试提示"。审查时看 catch 是否吞异常、是否区分网络错误 / 选择器错误 / 登录失效。

5. **路径与编码**
   - 项目根目录名含中文（`ai视频自动化`）。检查所有 Path 拼接、subprocess 调用、视频文件路径传递是否对中文路径友好。

6. **publish 命令的多平台串行**
   - 平台循环在 `publish_flow.py` 里，已做 try/except 隔离 + `[SUMMARY]` 汇总。审查时确认隔离逻辑没被改坏。

7. **headless 模式**
   - 首次登录不应 headless（需扫码）。审查默认值和提示是否正确。

## 工作约定（给 Claude Code 的行为指令）

- **先理解再动手**：任何审查任务，第一步是复述你对相关模块的理解，确认读懂后再报告问题。
- **先报告再修改**：列出问题清单（按上面"审查重点"分档：严重/中等/轻微，每条带 文件:行号 + 问题 + 建议改法），等用户确认后再改。
- **不擅自扩大范围**：用户让你查 A，就查 A；想动 B 先问。
- **涉及平台选择器时**：明确告知"平台改版可能让此处失效"，不要打包票说"这样改就稳了"。
- **运行项目前先问**：发布命令会真的打开浏览器去平台上传，可能触发风控。不要自动跑 `publish` / `upload-video`，除非用户明确要求。

## 已知待优化项（来自 README，非 bug）

- 网页里直接触发登录
- 展示更细的上传进度
- 保存每次发布日志
- 增加失败重试提示
- 用户确认后再支持自动点击最终发布

---

参考资料：
- 用户文档：`README.md`
- 产品文档：`PRD_ai_video_publisher.md`
- 上游参考项目：https://github.com/dreammis/social-auto-upload （只参考思路，不复制源码）