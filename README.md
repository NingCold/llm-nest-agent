# LLM-Nest Agent

独立运行的官方 AI 节点，负责模型接入、角色、记忆、每 AI 窗口摘要、执行预算、恢复及加解密。节点主动连接云端，不需要客户端或服务端源码。

当前 Alpha 版本为 **0.1.1-alpha.13**：[Windows x64](https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.1-alpha.13/llmn-agent-0.1.1-alpha.13-x86_64-pc-windows-msvc.exe) · [Linux x64](https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.1-alpha.13/llmn-agent-0.1.1-alpha.13-x86_64-unknown-linux-gnu)。Linux 构建基线为 Ubuntu 24.04。下载时一并保留[发布页](https://github.com/NingCold/llm-nest-agent/releases/tag/v0.1.1-alpha.13)中的对应平台第三方声明、LICENSE 与 NOTICE，并用 [SHA256SUMS.txt](https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.1-alpha.13/SHA256SUMS.txt) 核对文件。

发布仍处于 Alpha；Linux 实机、真实客户端重启验读及独立安全审查等边界见[验证说明](docs/validation/README.md)。桌面用户可使用客户端安装包中附带的 Agent。

```powershell
cargo build -p agent-node --bin llmn-agent --locked
# 也可下载发布程序；以下假定可通过 llmn-agent 调用
llmn-agent --version
# llmn-agent 0.1.1-alpha.13
llmn-agent init C:\private\llmn-agent
llmn-agent check C:\private\llmn-agent
llmn-agent pair C:\private\llmn-agent
llmn-agent run C:\private\llmn-agent
```

初始化后先编辑节点目录中的 `node.toml`，填写服务器和模型供应商；模型 Key 仅用环境变量引用。在客户端“我的账号 → 我管理的 AI”完成配对。节点目录含凭据、SQLite 和加密材料，请保持私有并单独备份。

[配置](docs/configuration.md) · [完整节点命令](node/README.md) · [开发](docs/development.md) · [验证](docs/validation/README.md) · [设计](docs/design/README.md)

产品入口和桌面客户端见 [llm-nest](https://github.com/NingCold/llm-nest)，云端、协议及连接器见 [llm-nest-server](https://github.com/NingCold/llm-nest-server)。跨仓 Rust 依赖固定到同一个服务端 Git 提交并由本仓锁文件记录，不使用兄弟目录。Agent 独立发版，协议 v4、sealedV1 和数据目录不因拆仓改变。源码由本仓独立维护，固定版本产物和双平台 [agent-manifest.json](https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.1-alpha.13/agent-manifest.json) 由本仓发布。

项目代码采用 [Apache-2.0](LICENSE) 许可证；第三方组件保留各自的许可证和声明。
