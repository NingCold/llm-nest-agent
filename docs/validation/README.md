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

发布程序另用 `scripts/package-agent.py` 核对 --version 并生成含 SHA-256、版本、平台的清单；release workflow 只构建程序和 manifest，通过 Actions artifact 交付，不自动公开 Release。客户端/服务端组合联调由服务端仓组织，读取明确提交和产物摘要，独立账号与模拟模型；当前本地拆仓结果由主仓进度说明记录。
