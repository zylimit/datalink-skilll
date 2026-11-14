# ARIANE 站点派工信号 约定 v1（site-feed/1）

状态：草案，2026-11-14。来源：Product-Spec v1.73 REQ-INT-001～006，Architecture-Design.md §17、ADR-6、ADR-7。
本文件是 ARIANE 与接收方（现在是 datalink-bridge）之间唯一的共享物。以本仓这份为准，接收方仓库放一份逐字相同的副本；改它必须同时改两边的样本和用例。
第 5、6 节用户 2026-11-14 已确认（Spec Q18、Q19「都按推荐」）。

## 1. 角色

- 发布方：ARIANE。判断哪个站可以派现场任务，状态变了发通知，提供只读接口。不知道接收方是谁。
- 接收方：收通知，来取状态，自己决定在自己的系统里做什么。不改 ARIANE 的数据。

## 2. 配置（各自服务器的环境变量，不进仓库、不进日志）

| 变量（ARIANE 侧） | 含义 | 不设时 |
|---|---|---|
| `ARIANE_FEED_URL` | 接收方收通知的地址，如 `http://127.0.0.1:8766/notify` | 整个功能关闭：不比对、不发通知、只读接口回 404 |
| `ARIANE_FEED_TOKEN` | 共享口令，两个方向都用 | 设了地址没设口令：ARIANE 启动时报错并保持功能关闭 |
| `ARIANE_FEED_INTERVAL` | 比对间隔秒数 | 30 |

接收方需要：ARIANE 的地址（如 `http://127.0.0.1:8765`）和同一个口令。

## 3. 通知（ARIANE → 接收方）

`POST {ARIANE_FEED_URL}`，头 `Authorization: Bearer <口令>`、`Content-Type: application/json`，超时 10 秒。

```json
{
  "schema": "ariane.site-feed/1",
  "event_id": "0b6f5c1e-8f0a-4c55-9a43-2f6f1f0c9d11",
  "seq": 42,
  "type": "site.ready",
  "site_key": "CHATILLON LA PALUD #1",
  "site_id": 17,
  "version": "9f2c41d07a1e",
  "occurred_at": "2026-11-18T09:02:11Z",
  "test": false
}
```

| 字段 | 说明 |
|---|---|
| `event_id` | 每条通知唯一；重发时不变。接收方按它去重 |
| `seq` | 全局递增整数，不倒退（快照恢复后也不倒退）；只用来发现缺号，不用来排序 |
| `type` | `site.ready` 这个站现在可以派任务了；`site.changed` 已经可派的站，计划变了；`site.withdrawn` 这个站不再可派；`ping` 测试 |
| `site_key` | 站点标识，见第 5 节 |
| `site_id` | ARIANE 内部编号，只供排查；删站后会被别的站复用，不能当键 |
| `version` | 这个站当前状态的版本号，与只读接口返回的 `version` 是同一个东西 |
| `occurred_at` | ARIANE 发现变化的时刻，UTC |
| `test` | `true` 时接收方只回 2xx，不取数、不做任何事。`type=ping` 时恒为 `true`，且 `site_key`、`site_id`、`version` 为 `null` |

**语义：通知只是「这个站变了，去取」。** 接收方不得依据通知里的 `type` 和 `version` 直接动手，必须调只读接口，以返回为准。所以通知重复、乱序、迟到都不影响结果。

**回应：** 2xx = 收到了（不代表事情办完）。其它状态码、连接失败、超时都算没送到。
**重发：** 没送到的按 30 秒、1 分钟、5 分钟、15 分钟、1 小时退避，之后每小时一次，满 24 小时仍失败标为失败并留在记录里；同一个站有更新的通知时，旧的不再重发。
**兜底：** 接收方每天至少调一次清单接口（第 4.2 节）全量核对，补上漏掉的。

## 4. 只读接口（接收方 → ARIANE）

头 `Authorization: Bearer <口令>`。口令不对回 401；功能关闭回 404。两个接口都不改 ARIANE 任何数据。

### 4.1 取一个站

`GET /api/feed/v1/sites/one?key=<URL 编码的 site_key>`

```json
{
  "schema": "ariane.site-feed/1",
  "site_key": "CHATILLON LA PALUD #1",
  "site_id": 17,
  "name": "CHATILLON LA PALUD",
  "seq_no": 1,
  "region": "UCI-EST",
  "subcontractors": ["HOVIA"],
  "status": "in_progress",
  "occ": {"date": "2026-12-01", "time": "09:00", "confirmed": true, "timezone": "Europe/Paris"},
  "ready": true,
  "version": "9f2c41d07a1e",
  "updated_at": "2026-11-18T09:02:11Z"
}
```

| 字段 | 说明 |
|---|---|
| `ready` | ARIANE 的结论：这个站现在可不可以派任务。规则只在 ARIANE 里算（站点进行中且 OCC 已确认），接收方不要自己推 |
| `version` | 由 `ready`、`occ.date`、`occ.time`、`subcontractors` 算出的短哈希；这几项都没变则不变。接收方记下「这个站的这个版本我处理过」 |
| `status` | `not_started` / `in_progress` / `done` |
| `occ.time` | 可能为 `null`（只定了日期） |
| `occ.date`、`occ.time` | 站点当地时间，不换算；时区名在 `occ.timezone` |
| `subcontractors` | 看板站名下的分包商标签，可能为空数组，也可能多个 |

站不存在：404，`{"detail": {"code": "site_not_found", "params": {"key": "..."}, "message": "..."}}`（与 ARIANE 现有错误形状一致）。站存在但不可派：200，`ready=false`。

### 4.2 取清单

`GET /api/feed/v1/sites` → `{"schema": "ariane.site-feed/1", "sites": [ <同 4.1 的对象>, ... ], "generated_at": "..."}`

返回所有 `ready=true` 的站，以及曾经发过 `site.ready`、现在已不可派的站（`ready=false`，让接收方知道该收回）。量级几十个站，不分页。

## 5. 站点标识

`site_key` = 看板上显示的站名加序号，形如 `CHATILLON LA PALUD #1`；没有序号的站就是站名本身。接收方系统里的站点文字要与它逐字一致（大小写、空格都算）。对不上的站，接收方不派任务，记下来报人工，不猜。

## 6. 身份验证

共享口令；两个程序同机部署，接收方只听本机地址。口令不写进日志、报错信息和自检输出。

## 7. 兼容规则

- 加字段不算破坏：两边都忽略不认识的字段。
- 改字段含义、删字段、改路径：升到 `v2`（路径 `/api/feed/v2/...`，`schema` 为 `ariane.site-feed/2`），两个版本并存到接收方切完。
- `type` 出现不认识的值：接收方当成 `site.changed` 处理（去取状态）。

## 8. 样本与用例

本目录 `site-feed-v1-samples/` 下的 JSON 是两边共用的测试数据（2026-11-14 手写，清单见其中 README.md）：四种通知各一条、取一个站五种情况、清单一条、三种错误各一条。ARIANE 的实现以样本为准，用例保证真实输出与样本的字段名、类型、可空性、枚举值一致（`version`、`event_id`、时间的值本身每次不同）；接收方用样本做假 ARIANE。错误码：口令不对 401 `feed_unauthorized`，功能没开 404 `feed_disabled`，站不存在 404 `site_not_found`。

## 9. 不在本约定里的

- 接收方在自己的系统里建什么表、派什么任务、派给谁。
- 督导反馈回 ARIANE（第二条线，另立约定）。
