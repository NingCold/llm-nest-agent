# 节点操作与命令

## 首次运行

以下使用[公开下载](../README.md#下载)的程序。节点目录须尚不存在；从源码构建则按[开发指南](development.md)，Windows 程序为 `target/debug/llmn-agent.exe`，Linux 为 `target/debug/llmn-agent`，用其绝对路径替换下面的程序变量。

### 1. 初始化

Windows PowerShell（按实际下载位置修改 `$agentExe`）：

```powershell
$agentExe = "$HOME\Downloads\llmn-agent-0.1.1-alpha.13-x86_64-pc-windows-msvc.exe"
$nodeDirectory = "$HOME\.llmn-agent"
& $agentExe --version
& $agentExe init $nodeDirectory
```

Linux shell，在下载目录运行：

```sh
chmod u+x ./llmn-agent-0.1.1-alpha.13-x86_64-unknown-linux-gnu
agent_exe="$PWD/llmn-agent-0.1.1-alpha.13-x86_64-unknown-linux-gnu"
node_directory="$HOME/.llmn-agent"
"$agent_exe" --version
"$agent_exe" init "$node_directory"
```

### 2. 配置模型并检查

编辑节点目录中的 `node.toml`，将 `server` 改为试用站地址，配置供应商与模型。Key 仅接受环境变量引用，初始化模板使用 `API_KEY_CHATECNU`；更换供应商时同步修改引用，并确保运行进程继承该环境变量，Key 不写入命令行或配置正文。配置格式见[模型配置](configuration.md)。

HTTPS/WSS 验证证书；私有 CA 在文件顶层设置 `ca_file = "C:/private/ca.pem"`，仅本机开发允许 HTTP。初始化目录仅当前用户可访问，其中的凭据、SQLite 与加密材料应单独备份，不可分享、提交或打包。

Windows：

```powershell
& $agentExe check $nodeDirectory
```

Linux：

```sh
"$agent_exe" check "$node_directory"
```

### 3. 配对并准备加密

Windows：

```powershell
& $agentExe pair $nodeDirectory
```

Linux：

```sh
"$agent_exe" pair "$node_directory"
```

在客户端“我的账号 → 我管理的 AI”选择 AI，输入一次性配对码并授权，等待命令完成。中断的待授权配对继续使用原码，过期自动申请新码；再次运行 `pair` 可绑定其他 AI，同一目录由一个 `run` 运行。

**此时保持节点停止，继续[加密设备与资料](#加密设备与资料)的身份、恢复文件和双方信任步骤，再启动并发送首条消息。** 内网试用站要求新内容加密。

## 档案与执行

以下开发命令在仓库根目录执行；下载程序可将 `cargo run -p agent-node --` 替换为程序路径。

`--version` 输出程序版本；`catalog` 输出内置模型目录 JSON（`protocolVersion: 1`、`agentVersion`、`providers`）。两者不读配置、Key 或节点目录，不联网或创建节点数据。`check <directory>` 无网络严格校验配置，不读取 Key 值。

`node.toml` 的 `providers` 使用 `ai-client` 的供应商与模型配置格式，模型名称和推理强度严格校验。`profile` 是新绑定 AI 的模板，修改模板不会覆盖已经保存的 AI。每个 AI 的角色与模型参数分别保存，更新时提供 JSON：

```json
{
  "revision": "2",
  "persona": "你是一位友善、诚实的 AI 联系人。",
  "selection": { "provider": "chatecnu", "model": "ecnu-max" },
  "temperature": null,
  "max_tokens": null,
  "auto_daily_tokens": 262144
}
```

```powershell
# 先停止使用该目录的 run；AI id 来自云端账号资料。
cargo run -p agent-node -- profile C:\private\llmn-agent <AI-ID> C:\private\profile.json
```

未启用加密时，修改后提升 `revision`，下一次启动与新任务使用保存后的设置。加密启用后通过管理页保存角色与模型，等待云端保存和节点应用；旧本机档案命令的修改不能替代密文同步。空温度和输出上限使用模型默认温度与意识系统预算。运行期间配置冻结，不在飞行请求中切换供应商。

云端任务通过每个绑定的 WSS 连接接入，所有 AI 共享 4 个社交模型调用槽，摘要独立使用 1 个槽；同一 AI 仍按顺序执行；单次调用最长 120 秒。每日次数和本次请求的估算 Token 额度先在 SQLite 预留，已开始后的失败不返还；墙钟回拨不重开旧日预算。云端任务在模型调用前先保存开始意图、获得云端确认，再保存确认。重启遇到不明确的开始只报告 uncertain，绝不重调模型；已保存 final 可原样重发。云端任务在节点断线时停止生成，源编辑、取消或撤权由服务端复核并阻止失效结果提交。

节点协议为 v4：材料包含真实窗口种类、名称、版本和当前成员，以及每条消息的实际发送者、回复目标和结构化提及。各次请求按目标 AI 与窗口独立构造，不把所有其他成员都当成一个私聊对方。云端按持久任务顺序串行同群发言，并将前序 AI 已提交回答提供给后续任务；节点只使用本次取得的冻结材料。

正常排队不算模型失败。云端任务列表只提供当前可开始的队首；若开始时明确收到 HTTP 409 `conversation_busy` 或 `task_not_ready`，节点在一个事务中撤销本次尚未开始的意图与预算预留，释放模型槽，等待通知或下一轮任务读取。此例外不适用于未知网络失败或任何已开始调用，原有不重复调用和预算不退还规则继续生效。

记忆与窗口摘要按 AI 分开保存在 `node.sqlite`。节点在线时，可从聊天或联系人详情维护显式记忆；AI 管理员还能为它在当前窗口选择专用模型，开启或手动整理摘要。摘要默认关闭，使用同一节点预算，最近 12 条原文保留，每段最多 32 条。群话题带入私聊时，节点读取获准引用的原文，并结合该 AI 自己的资料。完整操作见[使用指南](https://github.com/NingCold/llm-nest/blob/main/docs/usage.md#记忆摘要和群话题接续)。

编辑、遗忘和来源变化会停止依赖旧资料的回复。节点重连先补齐来源变化，再使用记忆和摘要；未完成摘要在重启后标为中断，不自动重复调用模型。更换运行设备时，按下方步骤导出资料包并在新节点导入；旧本地版本的数据见[迁移指南](https://github.com/NingCold/llm-nest-server/blob/main/docs/migration.md)。

普通文件只进入名称、类型和大小说明；图片经授权接口读取后作为原生图片材料，明确不支持图片的模型在调用前拒绝。当前没有工具执行；角色和模型参数可以由上述本机档案命令或在线管理入口调整。

图片下载前先按元信息选材：保留所有合并输入、触发消息和被回复原文的必要图片，再从最近历史向前选取，最多 16 张、16 MiB。超过剩余预算的普通历史消息整条略去，保留的消息不单独丢图；必要图片超限会明确失败。实际下载长度还要匹配元信息。准备材料与下载期间继续处理 WSS 心跳和取消。

## 执行预算

每轮按最终组装输入的保守估算加配置输出上限预留 `daily_tokens`。输入估算包括 UTF-8 字节、消息开销和图片估算，输出上限包含必要推理预算；`context_window` 用于检查请求容量，不按完整窗口预留。输入材料相同时，降低 `max_tokens` 会降低预留量，但仍须满足模型的必要推理要求。云端、同机聊天和摘要共用节点总额度，默认 `daily_tokens = 1048576`。这是软件内部的准入额度，不是供应商实际 Token 用量或账单。

群自动接话与一次性约定另外按每个 AI、窗口、UTC 日预留同一份“本次输入估算加输出上限”额度，`profile.auto_daily_tokens` 可省略（默认 262144），范围 1024–4000000；可在桌面 AI 设置或该 AI 的 JSON 档案中独立调整。普通私聊和明确点名不扣这份自动额度，仍受节点顶层 `daily_calls/daily_tokens` 约束。两份额度与开始意图在同一 SQLite 事务预留；仅明确未开始的队列 409 同时释放它们，开始后失败、取消和重启不返还。预算拒绝区分 `token_limit`（窗口自动额度）、`node_call_limit`、`node_token_limit` 和 `budget_clock_rollback`。

消息触发的 `inputIds` 均为必要材料，容量不足时明确失败。约定使用独立触发来源，把授权内容作为一次性约定提供给模型，可在聊天历史为空时执行；不会虚构真人消息，也不沿用共同群引用，当前窗口的有效记忆与摘要照常参与选材。

## 在线管理与桌面托管

在线配置管理通过 v4 `Hello.capabilities = ["profileManagement"]` 声明。云端仅转发角色、节点已经配置的模型选项及生成参数，响应不包含模型地址、Key 或环境变量名。管理员的写入由节点校验完整模型选择与参数，按预期版本原子保存；相同 requestId 重试只读取当前档案，回执仅存指纹。保存后的新任务使用新档案，已开始任务保持冻结设置。供应商和 Key 仍只能在节点本机配置。

桌面使用 `pair-json <directory>` 获取 JSON 行：`{type:"pairing",pairingId,userCode,expiresAt}`，授权并持久保存后输出 `{type:"paired",aiId,bindingVersion}`；凭据不输出。`check <directory>` 无网络校验模板及模型参数，输出 `{type:"checked",models:[...]}`，不读取 Key 值。

桌面托管使用 `run-managed <directory>`。取得目录锁、校验并准备完成后，输出 `{type:"ready",instanceId}`；调用方收到这行确认后再查询状态。`status <directory>` 输出 `{type:"status",running,instanceId,aiIds}`，未运行时 instanceId 为 null，aiIds 只读查询已配对账号。`stop <directory>` 请求停止当前托管实例，随后可用 status 确认退出；普通命令行 run 不接受这种停止。关闭桌面不影响独立托管进程，系统休眠或关机会使本机 AI 离线。

桌面节点以受限目录中的 `desktop-config.json` 为持久配置来源，配对和启动时会据此重建 `node.toml`，仅修改后者会被覆盖。当前源码中，进入 **我的账号 → 我管理的 AI → 在这台电脑上运行**，停止节点后展开 **每日调用额度**，可调整 **每日最多调用次数 / 每日 token 额度**；每个 AI 的设置可调整每窗口每日自动额度。

## 加密设备与资料

私聊和群聊可开启加密。节点验证发送者身份后读取消息和附件，并将角色、模型、记忆和各窗口摘要作为密文同步；云端保存后，由当前节点另行确认应用。恢复文件和模型 Key 留在自己的设备。

使用 `crypto-init <directory> <AI id>` 首次建立身份；已有云端身份时使用 `crypto-recover` 恢复。当前源码中，初始化中断后重试会继续使用同一身份与已有历史密钥备份；`crypto-status <directory> <AI id> [<对方账号 ID> <对方设备 ID>]` 查看已有状态，可同时检查指定设备是否受信任，不会创建身份。公开 alpha.13 的 `crypto-init` 遇到已有云端身份会拒绝，`crypto-status` 只支持节点目录和 AI ID，输出 `ready` 与设备指纹，并可能初始化本机 SDK 会话；它不提供源码版的身份准备、恢复保存及指定设备信任状态字段。两版均支持 `crypto-export-recovery`、`crypto-recover` 和 `crypto-trust`，参数顺序相同。`crypto-trust` 需独立核对账号 master、设备 Ed25519 和 Curve25519 指纹。`crypto-export-recovery` 保存私有恢复文件，换节点用 `crypto-recover` 恢复；仅登录或重新配对不能获得历史解密能力，当前不提供身份重置。向新管理员分享历史前，先确认当前管理员身份与设备信任，再用 `crypto-authorize-admin` 明确授权。恢复文件不提交、分享或交给服务管理员。参数与传输契约见[加密契约](https://github.com/NingCold/llm-nest-server/blob/main/docs/design/crypto-contract.md)，联调状态见[当前安排](https://github.com/NingCold/llm-nest/blob/main/docs/project/current.md)。

客户端 `0.1.1-alpha.15` 与 Agent `0.1.1-alpha.14` 已验收的设置流程：在 **我的账号 → 我管理的 AI → 在这台电脑上运行** 配对后进入 **完成加密 AI 设置**：准备首次身份或从恢复文件恢复，保存 AI 恢复文件，确认双方信任，保存角色与模型，然后启动 Agent。该入口及预算改进的验收记录见[2026-11-01 记录](validation/records.md#2026-11-01-源码与桌面验收)；公开安装版仍为 `0.1.1-alpha.13`。

当前源码 `crypto-status` 的 `identityReady` 表示身份及历史密钥备份已准备，`recoverySaved` 表示已记录恢复文件保存或恢复准备；传入对方账号与设备后，`peerTrusted` 表示该设备是否通过本机信任检查。查看状态不会代为初始化或信任设备。

公开安装版可使用随包 `agent/llmn-agent.exe`，独立节点使用下载或构建的程序，按以下步骤准备加密身份。内网试用站要求新内容加密，配对完成后须先完成这些准备：

1. 等待配对完成；桌面用户停止本机 Agent，独立 CLI 用户先结束 `run`。以下所有 `crypto-*` 命令都需要独占节点目录，包括 `crypto-status`；运行或配对期间不能执行。
2. 首次使用时，对已配对的节点目录执行 `crypto-init`；换设备时改用 `crypto-recover <directory> <AI id> <recovery.json>` 恢复。保存输出的 AI 设备 ID、Ed25519、Curve25519 和账号主指纹（`master.keys` 中的公钥值）。再用 `crypto-export-recovery` 将恢复文件保存到节点目录之外、仅当前用户可访问的私有目录；Windows 文件继承目标目录权限，先准备好受限目录。
3. 真人客户端打开 **我的账号 → 可信设备与恢复 → 本机设备 → 查看完整设备指纹**，将这里的真人账号主指纹、Ed25519 和 Curve25519 交给节点的 `crypto-trust`。反方向在真人页面查询 AI 账号，用第 2 步节点本机输出的三项指纹核对并信任。不要用服务器查询结果本身充当独立核对来源。
4. 完成以上准备后启动节点：桌面点击启动；独立节点 Windows 执行 `& $agentExe run $nodeDirectory`，Linux 执行 `"$agent_exe" run "$node_directory"`。在客户端保存加密角色与模型，等待显示节点已应用。
5. 打开双方私聊，在聊天详情选择 **开启端到端加密**，再发送消息。此操作不会自动转换旧历史。

以下命令对应第 2–3 步，路径和 ID 均为占位值。独立节点沿用首次运行的程序和节点目录变量；桌面用户先将这两个变量设为安装程序路径和桌面节点目录。Linux 用 `"$agent_exe"` 和 `"$node_directory"` 执行同名命令：

```powershell
& $agentExe crypto-init $nodeDirectory "<AI-ID>"
# 换设备时不要执行 crypto-init，改为：
# & $agentExe crypto-recover $nodeDirectory "<AI-ID>" "C:\private\llmn-recovery\ai-recovery.json"
& $agentExe crypto-status $nodeDirectory "<AI-ID>"
# 仅当前源码版可追加 "<真人账号ID>" "<真人设备ID>" 检查指定设备信任。
& $agentExe crypto-export-recovery $nodeDirectory "<AI-ID>" "C:\private\llmn-recovery\ai-recovery.json"
& $agentExe crypto-trust $nodeDirectory "<AI-ID>" "<真人账号ID>" "<真人设备ID>" "<真人Ed25519>" "<真人Curve25519>" "<真人账号主指纹>"
```

桌面节点目录位于数据目录的 `desktop-agents/<服务器地址的 SHA256>/<真人账号 ID>`，默认数据目录为用户目录下的 `.llmn`，设置 `LLMN_DATA_DIR` 时使用该位置。恢复文件不要放进仓库或发到聊天中，并另行安全备份。

旧节点资料使用 `crypto-migration-preview <directory> <AI id>` 预览，再用 `crypto-migrate <directory> <AI id> <digest>` 转为云端密文资料。先备份、停止节点并完成身份和恢复准备；转换不会调用模型重写摘要，已有云端资料与遗忘记录优先。完整步骤见[迁移说明](https://github.com/NingCold/llm-nest-server/blob/main/docs/migration.md#现有云端记录转为加密)。迁移历史会保留原作者，并明确标为由迁移者转换的旧记录。

## 同机文字私聊

`run-managed` 还提供只供桌面原生层使用的同机通道：Windows 使用命名管道，Unix 使用本机 socket，不监听公网或局域网端口。通道地址和认证 token 留在受限节点目录；模型 Key 和节点凭据不交给网页。普通 `run` 仍只运行原有云端任务，不开放这个通道。

先在线登录桌面真人账号，在已由本机节点运行、且自己管理的 AI 私聊中选择“开启同机私聊”。云端核对当前成员、管理员、节点绑定和窗口状态后，节点缓存最近最多 64 条可用文字历史及授权。准备成功后，同一登录会话即使与云端断开，也可读取已缓存记录、保存新文字并让本机模型回复；模型服务本身仍须可用。首次准备必须联网，没有缓存时不会凭空开始离线聊天。已知绑定版本不符时拒绝使用旧缓存执行。

真人消息先在 `node.sqlite` 落盘，再返回发送确认。模型开始前保存执行材料和预算，定期保存片段；同一窗口的云端任务和本机回复共用串行控制，所有调用共用节点次数、token 预算与社交并发槽。停止或重启保留中断片段，已开始的调用不会自动重做。联网后后台补传已有结果，云端接纳历史不会再次启动模型；网络失败保留待同步，权限、来源或云端历史冲突则保留本机记录并明确提示冲突。

同机私聊沿用云端相同的消息和加密格式，支持文字、密文附件、回复目标及已经准备好的群话题来源。先在线准备来源和附件，再断网接续；补传重新核对当前权限，只保存原结果。未启用窗口仍使用明文路径。不提供局域网连接或完整离线社交。桌面重启先联网核对登录会话，Windows 可选择保持登录；登录并解锁本机资料后，可恢复该账号已保存的同机窗口，不提供离线重新登录。

## AI 资料迁移

AI 资料迁移使用独立 JSON 包，不复制节点目录：

```text
llmn-agent export-ai <directory> <AI id> <new-package.json>
llmn-agent preview-import-ai <directory> <AI id> <package.json> <expected-profile-revision>
llmn-agent import-ai <directory> <AI id> <package.json> <expected-profile-revision>
```

先备份并停止源节点；导出使用只读 SQLite 快照和目录锁，目标文件必须不存在。包只含角色、模型选择及参数、显式记忆、每窗摘要配置和摘要，不含模型 Key、provider 地址、节点凭据、执行任务、预算或来源游标。未完成摘要作为中断资料导出，不恢复调用。

目标先配置自己的 `node.toml` 模型并重新配对，再预览和导入。模型及参数按目标目录严格校验，不能静默换模型。`expected-profile-revision` 是目标当前档案版本；导入只适用于尚无意识资料的 AI，成功后返回新档案版本。同包重试不重写已有资料，不会恢复已经遗忘的记忆；其它包与已有导入冲突。

导入检查 AI 当前窗口成员身份和全部来源版本；无效来源的正文清空并标失效，旧失效/遗忘资料不会重新启用。自动摘要始终关闭，需要管理员重新确认。旧本地资料必须先经迁移脚本按云端映射转换账号、窗口、消息、修订和消息位置；此 CLI 不自行猜测映射。完整旧库备份仍应保留。

预览会与云端同步来源失效并更新节点同步游标，不导入包内资料；已有来源失效可能因此被清理。可省略预览的版本参数，从输出 `expectedProfileRevision` 取得导入所需版本。导入摘要在资料界面保留导入来源标记。
