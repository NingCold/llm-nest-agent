# LLM-Nest Agent

独立运行的官方 AI 节点，负责模型接入、角色、记忆、窗口摘要、执行预算与加解密。节点主动连接云端，模型 Key 留在运行节点的设备，不需要客户端或服务端源码。

产品用于邀请制内网 Alpha 日常试用。**只聊天不需要运行节点**；使用[客户端](https://github.com/NingCold/llm-nest)连接已有 AI 即可。想运行自己的 AI 时，选择：

- **桌面托管**：在客户端“我的账号 → 我管理的 AI → 在这台电脑上运行”配置随包 Agent，适合日常使用。
- **独立节点**：在自己的电脑或服务器管理进程，按下方配置和配对；无需开放入站端口。

## 下载与独立节点起步

公开下载 **0.1.1-alpha.13**：[Windows x64](https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.1-alpha.13/llmn-agent-0.1.1-alpha.13-x86_64-pc-windows-msvc.exe) · [Linux x64](https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.1-alpha.13/llmn-agent-0.1.1-alpha.13-x86_64-unknown-linux-gnu)（Ubuntu 24.04 构建基线）。使用[SHA256SUMS.txt](https://github.com/NingCold/llm-nest-agent/releases/download/v0.1.1-alpha.13/SHA256SUMS.txt)核对下载，配套声明见[发布页](https://github.com/NingCold/llm-nest-agent/releases/tag/v0.1.1-alpha.13)。当前源码为 **0.1.1-alpha.14**，尚未发布。

### Windows PowerShell

以下假定程序保存在当前用户的“下载”目录；如下载位置不同，修改 `$agentExe`。节点目录必须尚不存在。

```powershell
$agentExe = "$HOME\Downloads\llmn-agent-0.1.1-alpha.13-x86_64-pc-windows-msvc.exe"
$nodeDirectory = "$HOME\.llmn-agent"
& $agentExe --version
& $agentExe init $nodeDirectory
```

编辑 `$nodeDirectory\node.toml`，把 `server` 改为试用站地址，配置供应商与模型；通过环境变量提供模型 Key。初始化模板引用 `API_KEY_CHATECNU`，更换供应商时同步修改引用。运行进程必须继承该环境变量，Key 不写入 CLI 参数或配置正文。然后：

```powershell
& $agentExe check $nodeDirectory
& $agentExe pair $nodeDirectory
# 在客户端“我的账号 → 我管理的 AI”选择 AI，输入配对码并授权。
# 等待 pair 完成，保持节点停止；按下方“加密准备”完成身份、恢复与信任设置。
& $agentExe run $nodeDirectory
```

### Linux shell

在下载目录运行；`node_directory` 同样须为新目录。初始化后按上方说明编辑配置，并在当前 shell 环境中准备配置引用的 Key，再继续 `check` 和 `pair`。

```sh
chmod u+x ./llmn-agent-0.1.1-alpha.13-x86_64-unknown-linux-gnu
agent_exe="$PWD/llmn-agent-0.1.1-alpha.13-x86_64-unknown-linux-gnu"
node_directory="$HOME/.llmn-agent"
"$agent_exe" init "$node_directory"
# 先编辑 node.toml 并准备模型 Key 环境变量。
"$agent_exe" check "$node_directory"
"$agent_exe" pair "$node_directory"
# 在客户端授权，等待 pair 完成；节点停止时完成身份、恢复与信任设置。
"$agent_exe" run "$node_directory"
```

### 加密准备

内网试用站要求新内容加密。**配对只授予节点运行资格**，还须按以下时机完成准备：

1. **节点停止时**：准备 AI 加密身份（换设备则从恢复文件恢复）、保存恢复文件，独立核对并建立双方设备信任。所有 `crypto-*` 命令都须独占节点目录，不能与 `run` 或 `pair` 同时使用。
2. **执行上方 `run` 后**：在客户端保存角色与模型，等待显示节点已应用，再开启窗口加密并发送消息。

[加密设备与资料](docs/node-cli.md#加密设备与资料)给出完整 CLI、公开版与源码版的差异及界面步骤。

节点目录包含连接凭据、SQLite 和加密材料，应保持私有并单独备份；不要提交或分发该目录。

### 可选：从源码构建

在本仓根目录执行，工具链见[开发指南](docs/development.md)：

```sh
cargo build -p agent-node --bin llmn-agent --locked
```

Windows 程序为 `.\target\debug\llmn-agent.exe`，Linux 为 `./target/debug/llmn-agent`。用其绝对路径替换上方 `$agentExe` / `agent_exe`，其余步骤相同。

## 开发与参考

[配置](docs/configuration.md) · [完整节点命令](docs/node-cli.md) · [模块与开发](docs/development.md) · [验证](docs/validation/README.md) · [设计](docs/design/README.md)

产品与桌面客户端见 [llm-nest](https://github.com/NingCold/llm-nest)，云端、协议与连接器见 [llm-nest-server](https://github.com/NingCold/llm-nest-server)。跨仓 Rust 依赖固定到同一个服务端 Git 提交并由锁文件记录；Agent 独立发版，使用协议 v4 / sealedV1。

项目代码采用 [Apache-2.0](LICENSE)，第三方组件保留各自许可。
