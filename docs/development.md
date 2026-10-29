# Agent 开发

安装 Rust 1.99.1（rustfmt、clippy）和 Python 3.12。Linux 使用 C/C++ 工具链、pkg-config 和 OpenSSL 开发库；Windows 使用 MSVC 工具链。本仓不需要 Node、WebView 或 PostgreSQL。

```sh
cargo build -p agent-node --bin llmn-agent --locked
cargo run -p agent-node -- catalog
python scripts/check-boundaries.py
```

五个工作区包位于 `node/` 与 `crates/`。social/connector 从服务端固定 Git revision 读取，锁文件维护已验证依赖版本，不使用其他仓库的源码路径。新仓尚未公开时，维护者可在测试命令环境临时配置 Git URL 镜像；镜像地址不进入 Cargo.toml、锁文件或 CI。

运行配置用独立临时节点，见[配置](configuration.md)。catalog 与 --version 不读配置、凭据、不联网或创建数据；check 严格校验候选配置。

[检查与验证范围](validation/README.md) · [修改约定](../AGENTS.md)

## 发布产物

Agent 版本由本仓 Cargo.toml 独立维护。发布流程支持已有版本 tag；手动运行填写 release_tag 时构建该 tag，经版本和提交核验后生成双平台程序、统一 manifest、SHA256SUMS.txt 和草稿 Release。只有维护者公开草稿后，固定 tag URL 才可供客户端正式消费。不填写 tag 时仅生成临时验收产物。流程不替维护者创建 tag 或自动公开版本，见[验证说明](validation/README.md)。
