# site-feed/1 样本

两边共用的测试数据，2026-11-14 手写，ARIANE 的实现以它为准。站名、分包商、区域、版本号都是编的，只代表形状。

| 文件 | 是什么 |
|---|---|
| notify-site-ready / changed / withdrawn / ping.json | 四种通知各一条（约定第 3 节） |
| site-ready.json | 取一个站：可派，有日期有时间 |
| site-ready-no-time.json | 可派，没单独设过时间，`occ.time` 是默认的 08:30 |
| site-ready-multi-subcon.json | 可派，两个分包商 |
| site-not-ready.json | 站存在但不可派（OCC 未确认），没有序号的站 |
| site-withdrawn.json | 以前可派、现在不可派（改回未开始） |
| sites-list.json | 清单接口（约定第 4.2 节） |
| error-401.json | 口令不对，HTTP 401 |
| error-404-disabled.json | 功能没开，HTTP 404 |
| error-404-site.json | 站不存在，HTTP 404 |
| error-409-ambiguous.json | 两个站的名字和序号完全相同，HTTP 409 |

「与样本一致」指字段名、类型、可空性、枚举值一致；`version`、`event_id`、时间这些值本身每次不同。
