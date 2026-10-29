# Agent 验证

在独立 checkout 执行：

```sh
cargo fmt --all -- --check
python scripts/check-boundaries.py
cargo test --workspace --locked
cargo clippy --workspace --all-targets --locked
python scripts/test_clean_build_artifacts.py
```

测试使用临时节点和模拟 provider，不读取日常数据或调用付费 API。重点覆盖模型协议及图片转换、必要上下文、预算、开始确认与 uncertain 恢复、密文资源、来源失效、同机与托管进程生命周期。构建及模拟测试通过不表示真实模型、桌面安装、Linux 实机、真实客户端重启验读或独立安全审查已完成。

发布程序另用 `scripts/package-agent.py` 核对 --version，并由 `scripts/merge-agent-artifacts.py` 合并同版两平台的 manifest、验证实际程序 SHA-256、生成 SHA256SUMS.txt。release workflow 的普通手动运行不填 release_tag 时只生成14天临时 Actions 验收产物，没有正式下载 URL，也不会创建 Release。

推送版本 tag 或手动输入已有 `release_tag` 时，流程 checkout 该 tag，核对 HEAD、tag 与本仓版本，再生成同时覆盖 Windows/Linux 的 agent-manifest.json。其 HTTPS 下载地址固定到该版本 tag，不使用 latest；仅最后的可选 job 获得 contents:write，并创建或更新草稿 Release，不创建 tag，不覆盖已公开 Release。维护者核对验收和许可证后手动公开，正式 URL 才可下载；客户端发布应引用公开后可长期下载的双平台清单，不能引用14天 Actions artifact。

客户端/服务端组合联调由服务端仓组织，读取明确提交和产物摘要，独立账号与模拟模型；当前本地拆仓结果由主仓进度说明记录。

2026-10-29 本地拆仓组合验收发现 Windows MSVC 默认 1 MiB 主线程栈不足以容纳 debug 构建的 Matrix SDK Olm 接收深链。`llmn-agent` 现仅在 Windows MSVC 显式保留 2 MiB 主线程栈，PE 验读为 reserve=2097152、commit=4096；不改变协议、任务顺序或持久恢复规则。平台参数见 [Microsoft /STACK](https://learn.microsoft.com/en-us/cpp/build/reference/stack-stack-allocations?view=msvc-170)。已有 SDK 身份的托管重启回归使用成功的密钥查询、上传及 sync 响应，确认处理后进入资料读取并正常停止。

同日服务端组织的 full 与 migration 两种隔离组合验收均通过：覆盖真实 Agent 加密消息/附件/引用、离线 Olm 和补传、资料应用与遗忘、摘要、交接及新节点恢复，以及历史转换与节点资料迁移；使用模拟模型和独立测试资料。Linux 实机、真实客户端重启验读与独立安全审查的原有缺口继续保留。
