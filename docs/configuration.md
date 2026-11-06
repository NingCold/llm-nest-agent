# Agent 模型与本机配置

[Agent](../README.md) · [开发指南](development.md) · [节点说明](node-cli.md)

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

每个 AI 的模型、思考强度、温度和输出上限属于其档案。温度留空使用模型服务默认值，输出上限留空使用意识系统预算。非法模型和参数明确报错，不自动替换模型。已开始的任务保持冻结设置，新配置用于后续任务。节点总预算及每窗口自动额度见[节点说明](node-cli.md)。

当前源码每次调用按最终组装输入的保守估算加输出上限预留额度，必要推理预算包含在输出上限中；模型的 `context_window` 只约束请求容量，不作为每轮扣除量。云端、同机、自动接话与摘要使用同一规则。这是软件本地额度，不能当作供应商实际 Token 用量或账单。桌面进入 **我的账号 → 我管理的 AI → 在这台电脑上运行**，停止节点后展开 **每日调用额度**，可调整 **每日最多调用次数 / 每日 token 额度**；AI 设置中可调整每窗口每日自动额度。命令行节点对应 `daily_calls`、`daily_tokens` 和 `profile.auto_daily_tokens`。

上述桌面入口与预算规则对应当前客户端源码 `0.1.1-alpha.15`、Agent 源码 `0.1.1-alpha.14`，尚未发布；公开安装版仍为 `0.1.1-alpha.13`。

## 配置与恢复边界

命令行节点目录由 init 的参数指定，不依赖旧 llmn.toml。桌面管理的节点由客户端写入配置并注入 Key；不要手工覆盖它的 node.toml。模型 Key 和节点凭据不随意识资料迁移；恢复文件与节点数据请在仓库外安全备份。角色、模型、记忆与摘要的密文资源区分云端保存与当前节点 applied。详见[节点说明](node-cli.md)。

`crypto-status <directory> <AI id> [<对方账号 ID> <对方设备 ID>]` 查看已有加密身份，可同时检查指定设备是否已受信任；状态查询不会创建加密身份。`crypto-init` 中断后可重试，继续使用同一身份和已有历史密钥备份，不会重置它们；需要换设备时使用私有恢复文件恢复，当前不提供身份重置。

状态中的 `identityReady` 表示身份与历史密钥备份已准备，`recoverySaved` 表示已记录恢复文件保存或恢复准备；提供对方账号和设备时，`peerTrusted` 表示该设备是否已通过本机信任检查。查询状态不会替代保存恢复文件或核对双方指纹。
