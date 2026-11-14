# risk: high
"""账本去重。模块还不存在，现在跑必须失败。用临时 sqlite 文件，不碰别的库。

datalink_bridge.ledger.Ledger(path)
path 是 sqlite 文件的字符串路径，目录已存在，文件由 Ledger 自己建。

- record_event(event_id) -> bool
  这个 event_id 第一次记，返回 False（没见过）。
  再记同一次，返回 True（见过，不再另记一条）。
  返回值必须是 bool。
- record_site(site_key, *, version, dispatched, has_feedback)
  记下这个站当前的 version、是否派过、任务是否已有反馈。再记同一 site_key 覆盖旧值。
- get_site(site_key)
  返回 dict 或带属性的对象：version, dispatched, has_feedback。
  dispatched / has_feedback 必须是 bool，不是 0/1。
可以有 close()。测试在读文件前会调用它（如果有）。
"""
import sqlite3
import sys
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path

_BRIDGE = Path(__file__).resolve().parents[1]
if str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

_EVENT_A = "0b6f5c1e-8f0a-4c55-9a43-2f6f1f0c9d11"
_EVENT_B = "6a1d2e3f-4b5c-4d6e-8f70-112233445566"
_SITE = "CHATILLON LA PALUD #1"


def _field(obj, name):
    if isinstance(obj, sqlite3.Row):
        if name not in obj.keys():
            raise AssertionError("缺少字段 %s" % name)
        return obj[name]
    if isinstance(obj, Mapping):
        if name not in obj:
            raise AssertionError("缺少字段 %s" % name)
        return obj[name]
    if not hasattr(obj, name):
        raise AssertionError("缺少字段 %s" % name)
    return getattr(obj, name)


class TestLedger(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "ledger.sqlite")

    def _open(self):
        from datalink_bridge.ledger import Ledger

        return Ledger(self.db_path)

    def _finish(self, ledger):
        close = getattr(ledger, "close", None)
        if callable(close):
            close()
        self.assertTrue(Path(self.db_path).is_file(), "没有写下 sqlite 文件")
        conn = sqlite3.connect(self.db_path, timeout=2)
        try:
            check = conn.execute("PRAGMA integrity_check").fetchone()[0]
            self.assertEqual(check, "ok")
            tables = conn.execute(
                "SELECT count(*) FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchone()[0]
            self.assertGreaterEqual(tables, 1)
        finally:
            conn.close()

    def test_second_record_of_same_event_id_counts_as_seen(self):
        ledger = self._open()
        self.assertIs(ledger.record_event(_EVENT_A), False)
        self.assertIs(ledger.record_event(_EVENT_B), False)
        self.assertIs(ledger.record_event(_EVENT_A), True)
        self._finish(ledger)

    def test_site_key_stores_version_dispatch_and_feedback(self):
        ledger = self._open()
        ledger.record_site(
            _SITE,
            version="9f2c41d07a1e",
            dispatched=True,
            has_feedback=False,
        )
        row = ledger.get_site(_SITE)
        self.assertEqual(_field(row, "version"), "9f2c41d07a1e")
        self.assertIs(_field(row, "dispatched"), True)
        self.assertIs(_field(row, "has_feedback"), False)

        ledger.record_site(
            _SITE,
            version="c41d8e7f0a52",
            dispatched=True,
            has_feedback=True,
        )
        row = ledger.get_site(_SITE)
        self.assertEqual(_field(row, "version"), "c41d8e7f0a52")
        self.assertIs(_field(row, "dispatched"), True)
        self.assertIs(_field(row, "has_feedback"), True)
        self._finish(ledger)
