# Agent 验证

在独立 checkout 的仓库根目录运行，使用临时节点与模拟 provider，不读取日常数据；真实模型调用需另行授权。

## 本仓检查

```sh
cargo fmt --all -- --check
python scripts/check-boundaries.py
python scripts/test_license_config.py
python scripts/test_package_agent.py
python scripts/test_merge_agent_artifacts.py
cargo build --workspace --locked
cargo test --workspace --locked
cargo clippy --workspace --all-targets --locked
python scripts/test_clean_build_artifacts.py
```

测试覆盖模型协议及图片转换、必要上下文、预算、开始确认与 uncertain 恢复、密文资源、来源失效、同机与托管进程生命周期。

## 发布检查

发布程序使用 `scripts/package-agent.py` 核对 --version，并由 `scripts/merge-agent-artifacts.py` 合并同版两平台的 manifest、验证实际程序 SHA-256、生成 SHA256SUMS.txt。release workflow 的普通手动运行不填 release_tag 时只生成14天临时 Actions 验收产物，没有正式下载 URL，也不会创建 Release。

推送版本 tag 或手动输入已有 `release_tag` 时，流程先核对 tag 与源码版本，再用同一提交构建 Windows、Linux 两个平台。合并任务上传 `agent-release-assets`；创建草稿前再次检查 tag 是否仍指向实际构建提交。其 HTTPS 下载地址固定到该版本 tag，不使用 latest；仅最后的可选 job 获得 contents:write，并创建或更新草稿 Release，不创建 tag，不覆盖已公开 Release。维护者核对验收和许可证后手动公开，正式 URL 才可下载；客户端发布应引用公开后可长期下载的双平台清单，不能引用14天 Actions artifact。

第三方许可材料由 cargo-about 0.9.3 按 Windows/Linux 目标的锁定依赖生成，发布包要求同时提供程序、第三方声明、LICENSE 与 NOTICE。`test_package_agent.py` / `test_merge_agent_artifacts.py` 校验声明原文、摘要、固定地址及篡改拒绝。

## 验收记录与待验证范围

[验证记录](records.md)按版本记录运行环境和结果。[Agent 0.1.2](https://github.com/NingCold/llm-nest-agent/releases/tag/v0.1.2) 提供通过双平台检查的 Windows、Linux 程序及其固定清单；加密聊天、换节点和恢复验读已在隔离数据库与模拟模型上通过。日常试用仍需验证 Linux 实机、从桌面导入 AI 恢复文件及受邀者独立使用，见[产品安排](https://github.com/NingCold/llm-nest/blob/main/docs/project/current.md)。
