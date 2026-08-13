# moersity.github.io

个人主页与自动发布的推理系统技术日报。

## 日报自动化

- 本机 Codex 自动任务每天在北京时间 08:30–08:45 的确定性随机分钟运行。
- Codex 使用 ChatGPT Plus/Pro 订阅能力检索并撰写日报，不调用 OpenAI API。
- 自动任务在本机生成页面，通过已登录的 Git/GitHub 凭据提交并推送至 GitHub Pages。
- 生成物写入 `blog/posts/`，归档数据位于 `blog/data/`，同时更新博客首页与 RSS。

运行时 Mac 必须保持唤醒、联网，并确保 Codex 与 GitHub CLI 登录有效。仓库不需要 `OPENAI_API_KEY`。

本地用已有 JSON 重建页面：

```sh
python3 scripts/generate_daily_report.py --date 2026-08-13 --input blog/data/2026-08-13.json
```
