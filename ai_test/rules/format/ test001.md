创建的 Skill：feishu-import-xmind
~/.cursor/skills/feishu-import-xmind/
├── SKILL.md                        # Skill 主文件（触发条件+使用说明）
├── env.template                    # .env 配置模板
└── scripts/
    └── feishuImportXmind.ts        # 导入脚本
自动触发场景
当你在任何项目中提到以下关键词时，Cursor AI 会自动读取并应用这个 Skill：

"导入飞书"、"上传用例到飞书"
"同步用例到产研空间"
"飞书用例集"、"飞书脑图导入"
与 qa-testcase-workflow 的串联
已在 qa-testcase-workflow 中新增 Step 4（飞书项目导入），完整工作流变为：

Step 1 → 需求分析
Step 2 → 逻辑闭环验证
Step 3 → 用例设计 → 输出 JSON + XMind + Markdown
Step 4（新增） → 将 JSON 一键导入飞书项目用例管理
以后在任何新项目中，只需配好 .env、安装依赖，就能直接复用这个能力了。

到时候生成用例是不是一键生成飞书用例了？

还不是完全一键，目前是两步走：

生成用例 → qa-testcase-workflow Skill 分析需求，输出 JSON 文件
导入飞书 → 你手动说一句"导入飞书"，触发 feishu-import-xmind Skill 执行脚本
如果你想做到真正一键，可以在 qa-testcase-workflow 的 Step 3 末尾加上自动导入逻辑——用例 JSON 生成完毕后，自动执行飞书导入脚本，不需要你再说第二句话。

要不要我改成一键？改完后流程就是：

你提供需求文档 → AI 分析需求 → 生成 JSON + XMind + Markdown → 自动导入飞书 → 返回用例集链接

只需要确认一点：是否每次生成用例都要导入飞书？ 还是保留为可选（比如有时候你只想本地看看，不想上传）？