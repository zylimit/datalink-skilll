# DEV-PLAN：datalink-bridge

程序落在 `bridge/`。技能文档只当 DataLink 参考，不写这次的逻辑。每个里程碑结束要有 `bridge/` 下的代码提交，外加一条能跑的命令。只有文档变化不算完成。

开发和 M0～M3 用本机 Python 3.14。语法停在 3.12 能跑的范围内。不装第三方包。

## M0 骨架，不联网

目录照 `docs/ariane-bridge/CURSOR-PROMPT-datalink-bridge.md` 第 3 节。这一里程碑做出并测过：`contract.py`、`fakes/fake_ariane.py`、`ledger.py`、`decide.py`、`bridge/tests/`。约定样本从 `docs/ariane-bridge/site-feed-v1-samples/` 原样复制到 `bridge/fakes/samples/ariane/`。

`decide.py` 不发请求。七种情况各一条用例：可派且配置唯一且没处理过；同一 version 已处理；version 变了且没有反馈；version 变了且已有反馈；缺督导；曾经派过但现在 ready=false；配置多行。

过关：`python -m unittest discover bridge/tests`；`git log --stat -1` 里有 `bridge/` 下的 `.py`。

## M1 DataLink 只读

`datalink_api.py`、`mapping.py`、`doctor`、`record-samples`。不写 DataLink。

## M2 假 ARIANE 试运行

`ariane_client.py` 对 `fake_ariane.py`。`plan` 和不带 `--apply` 的 `sync`。

## M3 真写真派

先停。OCC 挂哪张表、表单发布、测试站和接收人，这三件等用户定。然后才做 `apply.py`。

## M4 常驻

`server.py`。只绑 `127.0.0.1`。收 `ping` 只回 2xx。真通知走 `sync --apply`。每天 `reconcile --apply`。
