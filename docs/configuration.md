# Agent 模型与本机配置

[Agent](../README.md) · [开发指南](development.md) · [节点说明](../node/README.md)

浏览器和桌面连接云端服务，模型由独立 Agent 调用。桌面在“我的账号 → 我管理的 AI”配置本机节点；远程节点在运行设备维护自己的配置。服务器地址、模型 Key 和节点凭据留在运行设备，角色、模型选择、温度和输出上限按 AI 账号管理。

## 独立命令行节点

```powershell
llmn-agent init C:\private\llmn-agent
# 编辑 node.toml：服务器、可选私有 CA、供应商与模型。
llmn-agent check C:\private\llmn-agent
llmn-agent pair C:\private\llmn-agent
llmn-agent run C:\private\llmn-agent
```

`node.toml` 的 `providers` 使用 [ai-client](../crates/ai-client/README.md) 的配置格式。Key 仅接受环境变量引用，初始化模板使用 `API_KEY_CHATECNU`；不要把真实 Key 写进示例或提交到仓库。HTTPS 与 WSS 验证证书，私有 CA 使用 `ca_file`，仅本机开发允许 HTTP。

每个 AI 的模型、思考强度、温度和输出上限属于其档案。温度留空使用模型服务默认值，输出上限留空使用意识系统预算。非法模型和参数明确报错，不自动替换模型。已开始的任务保持冻结设置，新配置用于后续任务。节点总预算及每窗口自动额度见[节点说明](../node/README.md)。

## 配置与恢复边界

命令行节点目录由 init 的参数指定，不依赖旧 llmn.toml。桌面管理的节点由客户端写入配置并注入 Key；不要手工覆盖它的 node.toml。模型 Key 和节点凭据不随意识资料迁移；恢复文件与节点数据请在仓库外安全备份。角色、模型、记忆与摘要的密文资源区分云端保存与当前节点 applied。详见[节点说明](../node/README.md)。
