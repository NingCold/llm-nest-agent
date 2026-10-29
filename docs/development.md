# Agent 开发

安装 Rust 1.99.1（rustfmt、clippy）和 Python 3.12。Linux 使用 C/C++ 工具链、pkg-config 和 OpenSSL 开发库，发布构建基线为 Ubuntu 24.04；Windows 使用 MSVC 工具链。本仓不需要 Node、WebView 或 PostgreSQL。

```sh
cargo build -p agent-node --bin llmn-agent --locked
cargo run -p agent-node -- catalog
python scripts/check-boundaries.py
```

五个工作区包位于 `node/` 与 `crates/`。social/connector 从服务端固定 Git revision 读取，锁文件维护已验证依赖版本，不使用其他仓库的源码路径。三仓均已公开，依赖从正式 GitHub 地址读取；当前 social/connector 固定在同一提交 [`f47f9b4a99ba8602b7992b53d22bacf08534a64c`](https://github.com/NingCold/llm-nest-server/commit/f47f9b4a99ba8602b7992b53d22bacf08534a64c)。

运行配置用独立临时节点，见[配置](configuration.md)。catalog 与 --version 不读配置、凭据、不联网或创建数据；check 严格校验候选配置。

[检查与验证范围](validation/README.md) · [修改约定](../AGENTS.md)

## 发布产物

当前已公开版本为 [0.1.1-alpha.13](https://github.com/NingCold/llm-nest-agent/releases/tag/v0.1.1-alpha.13)，Agent 版本由本仓 Cargo.toml 独立维护。发布流程支持已有版本 tag；手动运行填写 release_tag 时构建该 tag，经版本和提交核验后生成双平台程序、统一 manifest、SHA256SUMS.txt 和草稿 Release。只有维护者公开草稿后，固定 tag URL 才可供客户端正式消费。不填写 tag 时仅生成临时验收产物。流程不替维护者创建 tag 或自动公开版本，见[验证说明](validation/README.md)。

Windows MSVC 的 `llmn-agent` 由 `node/build.rs` 显式保留 2 MiB 主线程栈，以容纳 Matrix SDK 调试构建中的 Olm 接收链。仅该二进制使用 `/STACK:2097152`，初始提交量仍为链接器默认 4096 字节；不设置全局 Rust 栈环境变量，不改变其他平台或后台任务的栈配置。

## 第三方声明

发布使用固定的 cargo-about 0.9.3，按目标平台与锁文件生成完整许可正文和源码定位；配置与纯文本模板在 `scripts/licenses/`。开发依赖排除，构建依赖及传递依赖保留。正式生成不能使用 `--offline`，以免上游 crate 省略 LICENSE 时只得到缺版权信息的标准文本。任何无法判定的许可均使生成失败，不能跳过该包。

```sh
cargo-about generate --manifest-path node/Cargo.toml --target x86_64-pc-windows-msvc --locked --fail --config scripts/licenses/about.toml --output-file agent-notices.txt scripts/licenses/third-party-notices.hbs
python scripts/package-agent.py --binary path/to/llmn-agent.exe --output agent-artifacts --version <exact-version> --target x86_64-pc-windows-msvc --notices agent-notices.txt
```

Linux 使用对应 target。打包同时带上根 LICENSE、NOTICE，以及 `THIRD_PARTY_NOTICES-<version>-<target>.txt`；manifest 的 `artifacts[target].notices` 保存其 file、sha256，正式合并后还提供固定 tag 的 HTTPS url。客户端必须核验并随附该声明；临时本地验收可显式提供本地声明文件，不作为长期下载地址。MPL 组件的原始 Source Code Form 按声明中的确切版本 crate archive 获取，本项目源代码按对应 Release tag 获取，不用浮动 main 替代。
