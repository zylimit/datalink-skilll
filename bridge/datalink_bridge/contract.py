"""site-feed/1 的通知和站点。不认识的字段丢掉，类型保持 JSON 原样。"""

SCHEMA_V1 = "ariane.site-feed/1"

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

_MISSING = object()


class SchemaError(Exception):
    """schema 缺失、为 null，或不是 ariane.site-feed/1。"""


def parse_notification(data: dict) -> dict:
    _require_schema(data)
    return _pick(data, NOTIFY_FIELDS)


def parse_site(data: dict) -> dict:
    _require_schema(data)
    parsed = _pick(data, SITE_FIELDS)
    occ = data.get("occ", _MISSING)
    if not isinstance(occ, dict):
        raise SchemaError("缺少 occ")
    parsed["occ"] = _pick(occ, OCC_FIELDS)
    return parsed


def _require_schema(data: dict) -> None:
    if not isinstance(data, dict):
        raise SchemaError("数据不是对象")
    if data.get("schema", _MISSING) != SCHEMA_V1:
        raise SchemaError("schema 不是 ariane.site-feed/1")


def _pick(data: dict, names: tuple) -> dict:
    picked = {}
    for name in names:
        if name not in data:
            raise SchemaError("缺少字段 %s" % name)
        value = data[name]
        if isinstance(value, list):
            value = list(value)
        picked[name] = value
    return picked
