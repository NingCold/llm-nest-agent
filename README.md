# LLM-Nest Agent

独立运行的官方 AI 节点，负责模型接入、角色、记忆、每 AI 窗口摘要、执行预算、恢复及加解密。节点主动连接云端，不需要客户端或服务端源码。

```powershell
cargo build -p agent-node --bin llmn-agent --locked
# 也可使用对应平台的已发布程序
llmn-agent init C:\private\llmn-agent
llmn-agent check C:\private\llmn-agent
llmn-agent pair C:\private\llmn-agent
llmn-agent run C:\private\llmn-agent
```

初始化后先编辑节点目录中的 `node.toml`，填写服务器和模型供应商；模型 Key 仅用环境变量引用。在客户端“我的账号 → 我管理的 AI”完成配对。节点目录含凭据、SQLite 和加密材料，请保持私有并单独备份。

[配置](docs/configuration.md) · [完整节点命令](node/README.md) · [开发](docs/development.md) · [验证](docs/validation/README.md) · [设计](docs/design/README.md)

产品入口和桌面客户端见 [llm-nest](https://github.com/NingCold/llm-nest)，云端、协议及连接器见 [llm-nest-server](https://github.com/NingCold/llm-nest-server)。跨仓 Rust 依赖固定到同一个服务端 Git 提交并由本仓锁文件记录，不使用兄弟目录。Agent 独立发版，协议 v4、sealedV1 和数据目录不因拆仓改变。当前本地拆分尚未创建远端或发布产物；已有平台及安全验收缺口不会由编译通过消除。
