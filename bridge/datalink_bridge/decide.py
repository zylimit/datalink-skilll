"""派工决定。纯函数，不发请求。

命中即返回，顺序如下：
1. 这个 version 已经处理过 → 不做。
2. 现在不可派，而且以前派过 → 只记「待收回」，不撤任务。
3. 现在不可派，没派过 → 不做。
4. 这个 site_key 没有配置行 → 不派，记「缺督导」。
5. 这个 site_key 多于一行配置 → 不派，记「配置重复」。
6. 派过，version 变了，任务已有反馈 → 不改任务，记「已有反馈，未改」。
7. 派过，version 变了，还没有反馈 → 更新计划行，并带上站点的 OCC 日期和时间。
8. 还没派过 → 写计划行，派 OCC。
"""

KIND_WRITE_PLAN = "写计划行"
KIND_DISPATCH = "派 OCC"
KIND_UPDATE_PLAN = "更新计划行"
KIND_UPDATE_TASK = "更新任务上的 OCC 时间"

NOTE_FEEDBACK = "已有反馈，未改"
NOTE_NO_SUPERVISOR = "缺督导"
NOTE_RECALL = "待收回"
NOTE_DUP_CONFIG = "配置重复"


def decide(site: dict, configs: list, prior: dict | None) -> dict:
    if prior is not None and prior["version"] == site["version"]:
        return _result([], [])

    ready = site["ready"]
    if ready is not True and ready is not False:
        raise TypeError("ready 必须是 bool")
    if ready is False:
        if prior is not None and _is_true(prior, "dispatched"):
            return _result([], [NOTE_RECALL])
        return _result([], [])

    matched = [row for row in configs if row["site_key"] == site["site_key"]]
    if len(matched) == 0:
        return _result([], [NOTE_NO_SUPERVISOR])
    if len(matched) > 1:
        return _result([], [NOTE_DUP_CONFIG])

    if prior is not None and _is_true(prior, "dispatched"):
        if _is_true(prior, "has_feedback"):
            return _result([], [NOTE_FEEDBACK])
        return _result(
            [
                {"kind": KIND_UPDATE_PLAN},
                _occ_update(site),
            ],
            [],
        )

    return _result(
        [
            {"kind": KIND_WRITE_PLAN},
            {"kind": KIND_DISPATCH},
        ],
        [],
    )


def _is_true(prior: dict, name: str) -> bool:
    value = prior[name]
    if value is True:
        return True
    if value is False:
        return False
    raise TypeError("%s 必须是 bool" % name)


def _occ_update(site: dict) -> dict:
    occ = site["occ"]
    if not isinstance(occ, dict):
        raise TypeError("站点 occ 必须是对象")
    return {
        "kind": KIND_UPDATE_TASK,
        "date": occ["date"],
        "time": occ["time"],
    }


def _result(actions: list, notes: list) -> dict:
    return {"actions": list(actions), "notes": list(notes)}
