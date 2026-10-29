# AGENTS.md — LLM-Nest Agent

## 范围与边界

本仓维护独立 `llmn-agent`。`node` 负责 SQLite、配置、配对、WSS/同机通信、执行和加密同步；`crates/ai-client` 负责模型目录及供应商协议；`crates/core` 负责纯上下文、预算和摘要提示；`crates/crypto` 包装官方 Matrix SDK；`crates/common` 保存模型内部类型。social 与 connector 来自服务端同一固定 Git 提交，不复制源码、不使用兄弟目录 path 或 submodule。

核心不得读取数据库、配置或网络；crypto 不依赖节点、供应商或连接器；不得恢复旧 Runtime、SocialFeature、工具 worker 或引入通用 Shell/文件执行。角色不能授予工具权限。

## 修改与验证

- 工作前读取 `git status --short`，保留用户修改；通过当前调用链确认行为。只修改负责该行为的模块。
- 边界校验保留；内部直接使用已成立类型与不变量，不叠加重复校验、静默兜底或假设性框架。
- 日常明确的实现可委派 GPT-6.1-Sol；主代理划分范围、审核、统一提交并核对文档。默认直接 main 开发；提交不等于推送或发布。
- 使用临时节点和模拟 provider；真实 API 需明确授权。不读取日常节点资料，不提交配置、Key、凭据、恢复文件、用户 SQLite 或测试数据。
- Key 只在本机配置中引用环境变量，不出现在 CLI 参数、目录响应、日志、DTO 或迁移包；不关闭 TLS 校验。
- 编译后确认无并行 Cargo/rustc，再用 `scripts/clean-build-artifacts.py` 先列完整清单再逐文件整理，空目录逐个删除，保留可复用缓存。禁止递归删除与 cargo clean；PowerShell Remove-Item 不用 -Force。清理前核对绝对路径、隐藏项、属性与范围，不跟随链接/junction；失败说明实际路径和错误，不换方式绕过策略。

## 必须维持的行为

- 模型、provider、协议、reasoning effort 和生成参数在配置边界严格校验，不静默换模型、丢必要输入或模拟回答。新配置只影响新运行，已开始任务保持冻结快照。图片能力依精确目录声明，不从模型名猜测；明确不支持时不调用，未知可尝试。
- 持久化成功后才替换内存或报告保存；节点目录用 OS 锁互斥，托管停止核对实例 UUID，不按任意 PID 终止。
- 云端调用前持久保存开始意图、取得并保存开始确认；开始后结果未知绝不自动重做。仅明确未开始的 conversation_busy/task_not_ready 允许撤销意图和预算预留。已保存原结果可在权限仍有效时重交。
- 同机执行单独落盘，不伪造云端开始确认，重连补传不再排模型任务。断网无法即时获知撤销，补传重新复核绑定、成员、来源与窗口状态；不扩大为完整离线社交。
- sealedV1 使用官方 Matrix SDK，核验设备和账号 master 双签；启用后的新文字、流式及结果必须密文，失败不得降级。密文资源 CAS 区分云端保存和当前绑定 applied，来源墓碑与遗忘优先。
- 重连先补齐按稳定 AI 的来源失效，再构造上下文；开始和提交复核实际使用来源、权限、绑定、窗口及节点材料版本。修改/撤回清除相关派生正文，成员变化不抹除仍有效资料；退群重入不复活旧引用。
- 每 AI/窗口独立保存记忆和摘要；摘要默认关闭、独立显式模型与预算，保留最近12条、每段最多32条。摘要调用先取得持久确认，重启不重做。遗忘清正文、保留墓碑，不声称能删除已发给模型或备份的内容。
- 合并输入、触发消息、回复原文和必要图片必须完整读取，不能静默裁剪；普通文件只保留元信息。控制帧被 select 接收后完整处理管理命令，不把已消费命令的异步保存放进可取消分支。
- 迁移包不含 Key、provider地址、凭据、任务、预算或来源游标；导入核对当前来源、权限和版本，同包重试不覆盖后来编辑或恢复遗忘。保持已有账号、密钥身份及数据格式。

## 检查

```sh
cargo fmt --all -- --check
cargo test --workspace --locked
cargo clippy --workspace --all-targets --locked
python scripts/check-boundaries.py
python scripts/test_clean_build_artifacts.py
```

参考 [开发](docs/development.md) 与 [验证](docs/validation/README.md)。CI、模拟 provider、真实模型和实机验收分别报告；不把拆仓构建通过称为生产或全面安全验收。发布仅检查本仓版本；产物包含程序、带 SHA-256 的 manifest、对应平台第三方声明及 LICENSE/NOTICE，不带任何节点目录。本仓代码采用 Apache-2.0，第三方组件保留各自条款；不要虚构签名、支持或安全验收承诺。
