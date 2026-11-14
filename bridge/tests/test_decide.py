# risk: high
"""派工决定。decide 模块还不存在，源文件也不在，现在跑必须失败。

datalink_bridge.decide.decide(site, configs, prior) 按位置传三个参数，不发请求。
- site：样本里的站点 dict（约定第 4.1 节）
- configs：配置行 list。一行是 dict，有 site_key、supervisor。
  空列表表示没有配置行。同一个 site_key 两行表示配置重复。
- prior：None 表示账本没有这个站。否则是 dict：
  version（已处理过的版本）、dispatched（是否派过）、has_feedback（任务是否已有反馈）

返回 dict 或对象，有 actions 和 notes。
notes 是字符串列表。
actions 里每个元素有 kind，取值只使用：
- 写计划行
- 派 OCC
- 更新计划行
- 更新任务上的 OCC 时间
- 撤任务
「更新任务上的 OCC 时间」带 date 和 time，可以平铺，也可以放在 occ 里。
date 等于站点 occ.date，不换算。
站点 occ.time 有值时，time 等于该值。
站点 occ.time 为 null 时，time 为 None 或不带这个字段（只带日期）。

本文件另外读 bridge/datalink_bridge/decide.py 的源码，禁止 import
datalink_api 或 ariane_client。文件不在时这条断言失败，保留。
"""
import ast
import json
import sys
import unittest
from collections.abc import Mapping
from pathlib import Path

_BRIDGE = Path(__file__).resolve().parents[1]
_REPO = _BRIDGE.parent
if str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

SAMPLES = _REPO / "docs" / "ariane-bridge" / "site-feed-v1-samples"

ACT_WRITE_PLAN = "写计划行"
ACT_DISPATCH = "派 OCC"
ACT_UPDATE_PLAN = "更新计划行"
ACT_UPDATE_TASK = "更新任务上的 OCC 时间"
ACT_WITHDRAW = "撤任务"

NOTE_FEEDBACK = "已有反馈，未改"
NOTE_NO_SUPERVISOR = "缺督导"
NOTE_RECALL = "待收回"
NOTE_DUP_CONFIG = "配置重复"

_BANNED = {"datalink_api", "ariane_client"}


def _load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def _field(obj, name):
    if isinstance(obj, Mapping):
        if name not in obj:
            raise AssertionError("缺少字段 %s" % name)
        return obj[name]
    if not hasattr(obj, name):
        raise AssertionError("缺少字段 %s" % name)
    return getattr(obj, name)


def _has_field(obj, name):
    if isinstance(obj, Mapping):
        return name in obj
    return hasattr(obj, name)


def _maybe(obj, name):
    if isinstance(obj, Mapping):
        return obj[name] if name in obj else None
    if hasattr(obj, name):
        return getattr(obj, name)
    return None


def _actions(result):
    if isinstance(result, Mapping):
        return list(result["actions"])
    return list(result.actions)


def _notes(result):
    if isinstance(result, Mapping):
        return list(result["notes"])
    return list(result.notes)


def _kinds(result):
    return [_field(action, "kind") for action in _actions(result)]


def _date_time(action):
    if _has_field(action, "occ"):
        occ = _field(action, "occ")
        return _field(occ, "date"), _maybe(occ, "time")
    return _field(action, "date"), _maybe(action, "time")


def _config(site, supervisor):
    return {"site_key": site["site_key"], "supervisor": supervisor}


def _prior(version, dispatched, has_feedback):
    return {
        "version": version,
        "dispatched": dispatched,
        "has_feedback": has_feedback,
    }


def _imported_names(tree):
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.append(node.module)
            for alias in node.names:
                found.append(alias.name)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                fname = func.id
            elif isinstance(func, ast.Attribute):
                fname = func.attr
            else:
                fname = ""
            if fname in {"import_module", "__import__"} and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.append(arg.value)
    return found


class TestDecide(unittest.TestCase):
    def test_ready_one_config_unseen_version_writes_plan_and_dispatches(self):
        from datalink_bridge.decide import decide

        site = _load("site-ready.json")
        result = decide(site, [_config(site, "督导甲")], None)
        self.assertCountEqual(_kinds(result), [ACT_WRITE_PLAN, ACT_DISPATCH])

    def test_same_version_already_handled_has_no_actions(self):
        from datalink_bridge.decide import decide

        site = _load("site-ready.json")
        prior = _prior(site["version"], dispatched=True, has_feedback=False)
        result = decide(site, [_config(site, "督导甲")], prior)
        self.assertEqual(_actions(result), [])

    def test_version_changed_without_feedback_updates_plan_and_occ_time(self):
        from datalink_bridge.decide import decide

        for name in ("site-ready.json", "site-ready-no-time.json"):
            with self.subTest(sample=name):
                site = _load(name)
                prior = _prior("handled-earlier", dispatched=True, has_feedback=False)
                result = decide(site, [_config(site, "督导甲")], prior)
                self.assertCountEqual(
                    _kinds(result), [ACT_UPDATE_PLAN, ACT_UPDATE_TASK]
                )
                task = next(
                    action
                    for action in _actions(result)
                    if _field(action, "kind") == ACT_UPDATE_TASK
                )
                date, time = _date_time(task)
                self.assertEqual(date, site["occ"]["date"])
                if site["occ"]["time"] is None:
                    self.assertIsNone(time)
                else:
                    self.assertEqual(time, site["occ"]["time"])

    def test_version_changed_with_feedback_does_not_update_task(self):
        from datalink_bridge.decide import decide

        site = _load("site-ready.json")
        prior = _prior("handled-earlier", dispatched=True, has_feedback=True)
        result = decide(site, [_config(site, "督导甲")], prior)
        kinds = _kinds(result)
        self.assertNotIn(ACT_UPDATE_TASK, kinds)
        self.assertNotIn(ACT_DISPATCH, kinds)
        self.assertNotIn(ACT_WITHDRAW, kinds)
        self.assertEqual(_notes(result), [NOTE_FEEDBACK])

    def test_missing_config_does_not_dispatch(self):
        from datalink_bridge.decide import decide

        site = _load("site-ready.json")
        result = decide(site, [], None)
        self.assertNotIn(ACT_DISPATCH, _kinds(result))
        self.assertEqual(_notes(result), [NOTE_NO_SUPERVISOR])

    def test_not_ready_after_dispatch_notes_recall_without_withdraw(self):
        from datalink_bridge.decide import decide

        site = _load("site-withdrawn.json")
        self.assertIs(site["ready"], False)
        prior = _prior("handled-earlier", dispatched=True, has_feedback=False)
        result = decide(site, [_config(site, "督导甲")], prior)
        kinds = _kinds(result)
        self.assertNotIn(ACT_WITHDRAW, kinds)
        self.assertNotIn(ACT_DISPATCH, kinds)
        self.assertEqual(_notes(result), [NOTE_RECALL])

    def test_duplicate_config_does_not_dispatch(self):
        from datalink_bridge.decide import decide

        site = _load("site-ready.json")
        configs = [_config(site, "督导甲"), _config(site, "督导乙")]
        result = decide(site, configs, None)
        self.assertNotIn(ACT_DISPATCH, _kinds(result))
        self.assertEqual(_notes(result), [NOTE_DUP_CONFIG])

    def test_decide_source_does_not_import_clients(self):
        path = _BRIDGE / "datalink_bridge" / "decide.py"
        self.assertTrue(path.is_file(), "bridge/datalink_bridge/decide.py 不存在")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name in _imported_names(tree):
            parts = set(name.split("."))
            self.assertTrue(_BANNED.isdisjoint(parts), "decide.py 不许 import %s" % name)
