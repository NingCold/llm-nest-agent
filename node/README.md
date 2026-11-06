# node · 独立节点

`agent-node` 构建 `llmn-agent`，负责节点目录、SQLite、配置、配对、云端 WSS、同机通信、模型执行和加密资料同步。桌面与独立 CLI 使用同一个程序；模型 Key 留在运行节点的设备。

- **在桌面运行自己的 AI**：在客户端“我的账号 → 我管理的 AI → 在这台电脑上运行”配置托管节点，无需手动执行 CLI。
- **独立设备或自行管理进程**：按[配置指南](../docs/configuration.md)初始化私有节点目录，再配对并运行。
- **恢复、迁移与集成**：[节点操作与完整命令](../docs/node-cli.md)说明加密身份、恢复文件、资料迁移、托管 JSON 输出和同机通道。

## 开发入口

[main.rs](src/main.rs)组织 CLI、启动与运行；`store` 保存配置和 SQLite，`management` 处理模型目录及档案管理，`consciousness` 管理意识资料，`crypto` 处理加密同步，`direct` / `direct_runtime` 处理同机通信，`transfer` 处理资料迁移。

在仓库根目录运行：

```sh
cargo build -p agent-node --bin llmn-agent --locked
cargo test -p agent-node --locked
```

测试使用临时节点与模拟 provider。运行、执行和资料边界见[设计](../docs/design/README.md)，跨模块检查与实测范围见[验证](../docs/validation/README.md)。
