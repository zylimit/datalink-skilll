# risk: high
"""约定解析。模块还不存在，现在跑必须失败。

样本目录：docs/ariane-bridge/site-feed-v1-samples/
只解析 notify-*.json 和 site-*.json。清单和错误样本不进这里。

datalink_bridge.contract 要有：
- parse_notification(数据) ：数据是 json.loads 得到的 dict
- parse_site(数据)
- SchemaError ：schema 不是 "ariane.site-feed/1" 就抛这个（缺 schema、null、别的字符串都算）

返回值可以是 dict，或带同名属性的对象。
通知字段：schema, event_id, seq, type, site_key, site_id, version, occurred_at, test
站点字段：schema, site_key, site_id, name, seq_no, region, subcontractors,
status, ready, version, updated_at
occ 可以是 dict 或对象，字段：date, time, confirmed, timezone
类型按 JSON 来（整数仍是 int，null 是 None，bool 是 bool）。
不认识的字段不出现在返回值上，occ 里面多出来的也不出现。
"""
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

NOTIFY_FIELDS = (
    "schema",
    "event_id",
    "seq",
    "type",
    "site_key",
    "site_id",
    "version",
    "occurred_at",
    "test",
)
SITE_FIELDS = (
    "schema",
    "site_key",
    "site_id",
    "name",
    "seq_no",
    "region",
    "subcontractors",
    "status",
    "ready",
    "version",
    "updated_at",
)
OCC_FIELDS = ("date", "time", "confirmed", "timezone")


def _load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def _has_field(obj, name):
    if isinstance(obj, Mapping):
        return name in obj
    return hasattr(obj, name)


def _field(obj, name):
    if isinstance(obj, Mapping):
        if name not in obj:
            raise AssertionError("缺少字段 %s" % name)
        return obj[name]
    if not hasattr(obj, name):
        raise AssertionError("缺少字段 %s" % name)
    return getattr(obj, name)


class TestContract(unittest.TestCase):
    def test_parses_each_notification_and_site_sample(self):
        from datalink_bridge.contract import parse_notification, parse_site

        notify_paths = sorted(SAMPLES.glob("notify-*.json"))
        site_paths = sorted(SAMPLES.glob("site-*.json"))
        self.assertGreaterEqual(len(notify_paths), 4)
        self.assertGreaterEqual(len(site_paths), 5)
        for path in notify_paths:
            with self.subTest(path=path.name):
                raw = json.loads(path.read_text(encoding="utf-8"))
                parsed = parse_notification(raw)
                for name in NOTIFY_FIELDS:
                    self.assertEqual(_field(parsed, name), raw[name])
        for path in site_paths:
            with self.subTest(path=path.name):
                raw = json.loads(path.read_text(encoding="utf-8"))
                parsed = parse_site(raw)
                for name in SITE_FIELDS:
                    self.assertEqual(_field(parsed, name), raw[name])
                occ = _field(parsed, "occ")
                for name in OCC_FIELDS:
                    self.assertEqual(_field(occ, name), raw["occ"][name])

    def test_schema_other_than_v1_raises(self):
        from datalink_bridge.contract import SchemaError, parse_notification, parse_site

        note = _load("notify-site-changed.json")
        site = _load("site-not-ready.json")
        cases = (
            ("notification-v2", parse_notification, note, "ariane.site-feed/2"),
            ("notification-missing", parse_notification, note, _Missing),
            ("notification-null", parse_notification, note, None),
            ("site-v2", parse_site, site, "ariane.site-feed/2"),
            ("site-missing", parse_site, site, _Missing),
            ("site-null", parse_site, site, None),
        )
        for label, parser, raw, schema in cases:
            with self.subTest(label=label):
                payload = json.loads(json.dumps(raw))
                if schema is _Missing:
                    payload.pop("schema", None)
                else:
                    payload["schema"] = schema
                with self.assertRaises(SchemaError):
                    parser(payload)

    def test_unknown_fields_are_dropped(self):
        from datalink_bridge.contract import parse_notification, parse_site

        note = _load("notify-site-ready.json")
        note["future_field"] = "ignore-me"
        parsed = parse_notification(note)
        self.assertFalse(_has_field(parsed, "future_field"))
        self.assertEqual(_field(parsed, "event_id"), note["event_id"])

        site = _load("site-ready.json")
        site["future_field"] = "ignore-me"
        site["occ"] = dict(site["occ"])
        site["occ"]["future_field"] = "ignore-me-too"
        parsed_site = parse_site(site)
        self.assertFalse(_has_field(parsed_site, "future_field"))
        occ = _field(parsed_site, "occ")
        self.assertFalse(_has_field(occ, "future_field"))
        self.assertEqual(_field(occ, "date"), "2026-12-01")
        self.assertEqual(_field(occ, "time"), "09:00")

    def test_ping_test_true_and_ids_none(self):
        from datalink_bridge.contract import parse_notification

        parsed = parse_notification(_load("notify-ping.json"))
        self.assertIs(_field(parsed, "test"), True)
        self.assertIsNone(_field(parsed, "site_key"))
        self.assertIsNone(_field(parsed, "site_id"))
        self.assertIsNone(_field(parsed, "version"))


class _Missing:
    pass
