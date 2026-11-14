"""本地 SQLite 账本。event_id 只记一次；同一站点后一次覆盖前一次。"""

import sqlite3


class Ledger:
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sites (
                site_key TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                dispatched INTEGER NOT NULL,
                has_feedback INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def record_event(self, event_id: str) -> bool:
        seen = self._conn.execute(
            "SELECT 1 FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if seen is not None:
            return True
        self._conn.execute(
            "INSERT INTO events (event_id) VALUES (?)",
            (event_id,),
        )
        self._conn.commit()
        return False

    def record_site(
        self,
        site_key: str,
        *,
        version: str,
        dispatched: bool,
        has_feedback: bool,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO sites (site_key, version, dispatched, has_feedback)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(site_key) DO UPDATE SET
                version = excluded.version,
                dispatched = excluded.dispatched,
                has_feedback = excluded.has_feedback
            """,
            (site_key, version, _as_int(dispatched), _as_int(has_feedback)),
        )
        self._conn.commit()

    def get_site(self, site_key: str) -> dict:
        row = self._conn.execute(
            """
            SELECT version, dispatched, has_feedback
            FROM sites
            WHERE site_key = ?
            """,
            (site_key,),
        ).fetchone()
        if row is None:
            raise KeyError(site_key)
        return {
            "version": row[0],
            "dispatched": _as_bool(row[1]),
            "has_feedback": _as_bool(row[2]),
        }

    def close(self) -> None:
        self._conn.commit()
        self._conn.close()


def _as_int(value: bool) -> int:
    if value is True:
        return 1
    if value is False:
        return 0
    raise TypeError("需要 bool")


def _as_bool(value: int) -> bool:
    if value == 1:
        return True
    if value == 0:
        return False
    raise ValueError("账本标记不是 0 或 1")
