# 给 Cursor：开发 datalink-bridge（一个落盘的程序，不是技能）

> 写这份说明的人（ARIANE 的主 Agent）连不上内网、调不了 DataLink 开放 API，只能看你贴回的输出。所以每一步都要把命令和完整输出贴回来。
> 工作目录：`~/code/datalink-skill`。配套文件：`docs/ariane-bridge/site-feed-v1.md`（接口约定）、`docs/ariane-bridge/site-feed-v1-samples/`（约定样本，13 个 JSON 加一份清单）、本文件。

## 0. 先纠正一件事

到现在为止，这个仓里只有技能文档（`.claude/skills/datalink/`），没有一行程序。**这次要交付的是一个能被别的系统调用、能自己常驻运行的程序，代码必须落盘在 `bridge/` 目录、提交进 git。**

- 不要把这次的逻辑写进 `SKILL.md` 或 `references/`。那两份只当 DataLink 的操作与 API 参考来读。
- 不要用浏览器点页面来完成派任务。派任务走开放 API，由程序做。页面只在需要建表单、建流程、核对结果时用，照技能里已确认的步骤。
- 按本仓 `.claude/CLAUDE.md` 的流程走：先在仓库根写 `DEV-PLAN.md`（照下面第 5 节的里程碑），编码派 implementer，每个里程碑做完提交一次，`progress.md` 记完成与决策。
- 判断自己有没有跑偏的标准：每个里程碑结束时 `git log --stat` 里要有 `bridge/` 下的 `.py` 文件，并且有一条能跑的命令证明它工作。只有文档变化 = 没完成。

## 1. 要做的东西

ARIANE（站点跟踪系统，部署在内网 feilan-node 的 8765 端口）会在「某个站可以派现场任务了」时通知你的程序。你的程序收到后去 ARIANE 取这个站的计划，然后在 DataLink 应用「现场督导施工管理」（France FBB，appId 19093046）里写施工计划、给这个站的督导派 OCC 任务。

边界（用户定的，不要越过）：

- ARIANE 不知道 DataLink 的存在，你也不要让它知道：不改 ARIANE 的代码、不读它的数据库、不调它约定以外的接口。
- 哪个站可以派，由 ARIANE 说了算（约定里的 `ready`）。你的程序不自己判断「OCC 前一周」之类的规则。
- 哪个站派给哪个督导，读 DataLink 的「站点督导配置」表。
- 本期只派 OCC 任务。Retassage、Dismantle 任务和督导反馈回 ARIANE 都不做。

## 2. 先读这三样，读完再动手

1. `docs/ariane-bridge/site-feed-v1.md`：通知长什么样、只读接口返回什么、重复和乱序怎么处理。全文都要读。
2. `.claude/skills/datalink/references/api.md`：AK/SK 签名、表单数据的查询与增改、「任务派发」（`POST /datalinkprobackend/aksk/workflow/task/dispatch`，异步，一次最多 100 个，结果用返回的 `linkTaskId` 另查，要工作空间管理员权限，只能派给已启用工作流的表单）。用到哪个接口就读那一节的完整参数，不凭摘要。
3. `.claude/skills/datalink/references/confirmed-operations.md` 的「现场督导施工管理」和「工作流设计」：五张表现在的字段，以及工作流启用的条件。

## 3. 目录与职责（照这个建，名字不要改）

```
bridge/
├── README.md                 # 怎么配置、怎么跑、怎么自检
├── datalink_bridge/
│   ├── __init__.py
│   ├── config.py             # 只从环境变量读：ARIANE 地址与口令、DataLink 地址与 AK/SK、表单 id、监听端口
│   ├── contract.py           # 约定里的数据形状与校验（通知、站点对象）
│   ├── ariane_client.py      # 调 ARIANE 两个只读接口，别的不调
│   ├── datalink_api.py       # 签名、发请求、翻页、重试；只做传输，不含业务判断
│   ├── mapping.py            # 读「站点督导配置」：site_key -> 督导、分包商
│   ├── decide.py             # 纯函数：站点对象 + 督导配置 + 账本 -> 要做的动作清单（不发任何请求）
│   ├── apply.py              # 把动作清单变成 DataLink 调用，记结果
│   ├── ledger.py             # 本地 SQLite 账本：处理过的 event_id、每个站处理到哪个 version、DataLink 实例编号、派发任务号与结果
│   ├── server.py             # 常驻服务：收通知的 HTTP 入口 + 每天一次全量核对
│   └── cli.py                # 命令行入口，见第 4 节
├── fakes/
│   ├── fake_ariane.py        # 照约定样本回数据的假 ARIANE，供你在没有 ARIANE 时开发
│   └── samples/              # 约定样本：从 docs/ariane-bridge/site-feed-v1-samples/ 原样复制到 samples/ariane/；你在内网录回来的 DataLink 真实返回（脱敏后）放 samples/datalink/
└── tests/                    # 不联网就能跑的用例
```

硬性要求：

- 只用标准库（`http.server`、`urllib`、`sqlite3`、`hmac`、`json`、`argparse`、`unittest`），不装任何第三方包。开发和 M0～M3 用你这台机器上现有的 Python（3.12 及以上都行，比如本机的 3.14）；但程序最终要跑在内网服务器 feilan-node 的 `/opt/gde/python/python-3.12.10/bin/python3.12` 上，所以不要用 3.12 没有的语法和标准库功能。那条路径只在服务器上有，到 M4 部署前在服务器上核对一次，本机没有是正常的（2026-11-14 更正：上一版把这句写成了开工条件，是写说明的人的错）。
- `decide.py` 不许 import `datalink_api`、`ariane_client`，不许发请求。它是这个程序里唯一写业务规则的地方，要能用样本在外网测全。
- AK/SK 和口令只从环境变量读，不进仓库、不进日志、不进任何输出。`~/datalink-aksk.csv` 不要读进程序，也不要打印。
- 所有会写 DataLink 的命令默认是试运行（只打印要做什么），加 `--apply` 才真写。
- 只动应用「现场督导施工管理」。「铜缆拆除防盗管理」「项目交付进度管理」不打开、不读、不写（仓库 Pinned 里的规矩）。
- 监听只绑 `127.0.0.1`。

## 4. 命令（都要有，都要能贴回输出）

| 命令 | 做什么 | 写不写 DataLink |
|---|---|---|
| `python -m datalink_bridge.cli doctor` | 查配置齐不齐、ARIANE 两个接口通不通、DataLink 签名通不通、三张表读不读得到；口令和密钥只显示「已设置 / 未设置」 | 不写 |
| `... record-samples` | 把 DataLink 真实返回脱敏后存进 `fakes/samples/datalink/`（人名、工号、电话换成占位） | 不写 |
| `... plan --site "<site_key>"` | 取这个站的状态，打印动作清单 | 不写 |
| `... sync --site "<site_key>" [--apply]` | 执行动作清单；不带 `--apply` 等同 `plan` | 带 `--apply` 才写 |
| `... reconcile [--apply]` | 取 ARIANE 全量清单，逐站 `sync` | 同上 |
| `... serve` | 常驻：收通知即对该站 `sync --apply`，每天定时 `reconcile --apply` | 写 |
| `... ledger [--site ...]` | 打印账本，供排查 | 不写 |

## 5. 里程碑（一个一个做，做完一个贴回再做下一个）

**M0 骨架，不联网。** 建目录、`contract.py`、`fake_ariane.py`、`ledger.py`、`decide.py` 的第一版和用例。
`decide.py` 至少覆盖这些情况，每种一条用例：
- 站可派、督导配置里有这个站、账本里没处理过 → 写计划行 + 派 OCC 任务。
- 同一个 `version` 已处理过 → 什么都不做。
- `version` 变了、任务还没有反馈 → 更新计划行与任务上的 OCC 时间。
- `version` 变了、任务已有反馈 → 不动任务，记一条「已有反馈，未改」。
- 督导配置里没有这个站 → 不派，记「缺督导」，下次核对再试。
- `ready=false` 且以前派过 → 记「待收回」，本期不自动撤任务，只报人工。
- `site_key` 在督导配置里有多行 → 不派，记「配置重复」。
证据：`python -m unittest discover bridge/tests` 的完整输出；`git log --stat -1`。

**M1 DataLink 只读（内网）。** `datalink_api.py` 的签名与查询，`mapping.py`，`doctor`，`record-samples`。
证据：`doctor` 的输出；录回来的样本文件清单（确认已脱敏）；读到的「站点督导配置」行数。

**M2 用假 ARIANE 跑通试运行（内网）。** `ariane_client.py` 对着 `fake_ariane.py`，`plan` 和不带 `--apply` 的 `sync`。
证据：对三个样本站各跑一次 `plan` 的输出。

**M3 真写、真派，一个测试站（内网）。** 先停下来，和用户确认下面第 6 节的三件事，再做。`apply.py`、派发结果查询、账本。
证据：`sync --site "<测试站>" --apply` 的输出；再跑一次同一条命令（应该什么都不做）；`ledger --site` 的输出；派发结果查询的返回（脱敏）。

**M4 常驻服务与真 ARIANE 联调（内网）。** `server.py`，收 `ping` 只回 2xx，收真通知走 `sync`，每天 `reconcile`。
证据：ARIANE 那边自检命令的输出（届时由 ARIANE 的离线包提供）；你这边收到通知的日志；一个真实站点走通后的 `ledger`。

## 6. 这三件事你不要自己定，到 M3 之前停下来问用户

1. **OCC 任务挂在哪张表、流程怎么走。** 派发接口只能派给已启用工作流的表单，现在五张表都只保存、没发布、没启用流程。是给「OCC 反馈」表建流程并派发，还是另建一张任务表？这会改 DataLink 应用的结构。
2. **表单发布。** 技能里「真正发布」还没教过，属于参考外的步骤，按技能规矩先停。
3. **用哪个站做测试、派给谁。** 测试任务会真的出现在某个人的待办里。

## 7. 出错时的规矩

- 派发接口返回已受理但结果查不到：这是「结果未知」，不是失败。不要重派，记进账本，继续查；查到为止或报人工。
- DataLink 返回 HTTP 200 但 body 里 `code` 不是成功：按失败处理，把 `code` 和文案原样记下。
- ARIANE 接口回 404（功能没开）或 401（口令不对）：停，不重试轰炸，`doctor` 里要能一眼看出来。
- 任何一步对不上预期：停下回报原始输出，不换办法硬试。

## 8. 每次回报的格式

```
里程碑：M?
做了什么：（一两句）
落盘的文件：（git log --stat -1 的输出）
跑过的命令与完整输出：（逐条）
没做 / 没验证的：（必须列，没有就写「无」）
需要用户定的：（没有就写「无」）
```
