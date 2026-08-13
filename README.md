# moersity.github.io

个人主页与自动发布的推理系统技术日报。

## 日报自动化

- GitHub Actions 每天北京时间 08:30 启动，并在 0–15 分钟内按日期确定性等待后发布。
- 工作流调用 OpenAI Responses API 的网页搜索，生成带一手来源的结构化日报。
- 生成物写入 `blog/posts/`，归档数据位于 `blog/data/`，同时更新博客首页与 RSS。

仓库需要配置 Actions secret `OPENAI_API_KEY`。可选的 Actions variable `OPENAI_MODEL` 默认是 `gpt-5.6-luna`。

本地用已有 JSON 重建页面：

```sh
python3 scripts/generate_daily_report.py --date 2026-08-13 --input blog/data/2026-08-13.json
```
