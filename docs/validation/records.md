# Agent 验证记录

## 当前源码验证

2026-11-01，Agent 源码版本为 `0.1.1-alpha.14`，尚未发布；公开 Release 仍为 `0.1.1-alpha.13`。客户端 `0.1.1-alpha.15` 已在本机通过 NSIS 安装，随包 Agent `0.1.1-alpha.14` 的版本及 SHA-256 已核对；生产服务和 Web 未更新。协议仍为 v4 / sealedV1。

本轮预算预留改为最终组装输入的保守估算加配置输出上限（包含必要推理预算），云端、同机、自动接话及摘要共用规则。百万上下文回归核对预留不会随完整窗口膨胀，输出上限变化会相应改变预留；保留持久计数、开始后结果未知不重调、不返还额度及明确未开始队列冲突的事务释放规则。本地额度不代表供应商实际 Token 用量或账单。

加密状态查询不创建身份；`identityReady` 表示本机身份、交叉签名私钥和历史密钥备份已准备，`recoverySaved` 表示已记录恢复文件保存或恢复准备，指定对方账号与设备时 `peerTrusted` 检查该设备的信任状态。`crypto-init` 重试继续已有身份和备份，不轮换它们；`crypto-status` 可选参数为成对的对方账号 ID、设备 ID，当前不提供身份重置。

本轮 Windows stable MSVC 本机缓存检查通过：fmt、workspace test（209 个测试）、workspace all-targets clippy、依赖边界检查、清理脚本的 7 个隔离测试。Clippy 保留既有警告。测试使用临时节点与模拟 provider，不读取日常数据。

服务端组织的新 Agent 隔离 SDK 组合验收通过：完整加密路径使用模拟模型 21 次、真实模型 0 次；历史转换与资料迁移验收也通过，模型调用 0 次。覆盖加密消息及附件、资料同步、摘要、恢复与迁移，并核对初始化重试保留身份与备份、未初始化状态查询不创建身份及状态字段。这些隔离 SDK 结果与下方桌面安装验证分别记录，不代表生产部署或真实模型调用。


Windows 安装升级前后，83 个日常持久文件的 SHA-256 保持一致。独立桌面测试账号已通过实际界面完成创建 AI、配置与绑定、首次身份准备、恢复文件导出取消及成功导出、双方设备信任、停机时加密保存角色与模型、启动后节点应用、重新打开客户端、开启窗口加密与模拟模型回复。节点额度保存为每日最多 17 次、每日 Token 额度 123456，修改端点地址后仍保留。这是独立账号与模拟模型的界面验收，没有测试日常“小巢”的新模型，真实模型调用为 0。

本轮未推送、创建 tag 或部署服务端，公开下载仍为 alpha.13。Linux 实机、实际 AI 恢复文件导入界面和独立安全审查尚未完成；已验证首次身份准备与恢复文件导出，不把它们视为恢复导入界面通过。

## 当前公开版本

2026-10-29，[0.1.1-alpha.13](https://github.com/NingCold/llm-nest-agent/releases/tag/v0.1.1-alpha.13) 已公开，tag 源码为 `a78f729b`；随后 main 的 `fc9a587` 仅修复 CI Windows 工具解压路径。Windows/Linux Checks 均通过，[Artifacts 运行 40889208608](https://github.com/NingCold/llm-nest-agent/actions/runs/40889208608) 成功。已核对全部 8 个发布资产：两个平台程序及各自声明、manifest、SHA256SUMS、LICENSE、NOTICE；程序及声明的 SHA-256 与清单一致，LICENSE/NOTICE 与 tag 内原文字节一致，本机 Windows 程序的 `--version` 实际返回 `llmn-agent 0.1.1-alpha.13`。

Linux 构建基线为 Ubuntu 24.04。客户端 `alpha.13` 的 deb/AppImage 已校验内嵌 Agent 原始字节，本机 Windows 已安装同版客户端并核对 Agent 的版本与摘要。实际界面已连接云端，但本次未登录、解锁或重新运行日常节点。该版本仍为 Alpha；Linux 人工操作、真实客户端重启后的历史验读与独立安全审查继续保留。


## 2026-10-29 拆仓组合验收

2026-10-29 本地拆仓组合验收发现 Windows MSVC 默认 1 MiB 主线程栈不足以容纳 debug 构建的 Matrix SDK Olm 接收深链。`llmn-agent` 现仅在 Windows MSVC 显式保留 2 MiB 主线程栈，PE 验读为 reserve=2097152、commit=4096；不改变协议、任务顺序或持久恢复规则。平台参数见 [Microsoft /STACK](https://learn.microsoft.com/en-us/cpp/build/reference/stack-stack-allocations?view=msvc-170)。已有 SDK 身份的托管重启回归使用成功的密钥查询、上传及 sync 响应，确认处理后进入资料读取并正常停止。

同日服务端组织的 full 与 migration 两种隔离组合验收均通过：覆盖真实 Agent 加密消息/附件/引用、离线 Olm 和补传、资料应用与遗忘、摘要、交接及新节点恢复，以及历史转换与节点资料迁移；使用模拟模型和独立测试资料。Linux 实机、真实客户端重启验读与独立安全审查的原有缺口继续保留。
