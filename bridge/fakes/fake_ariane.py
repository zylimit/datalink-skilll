"""照样本目录回答的假 ARIANE。口令不对、功能关闭、站不存在都回样本里的错误体。"""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

_LIST_PATH = "/api/feed/v1/sites"
_ONE_PATH = "/api/feed/v1/sites/one"


def handle(
    *,
    method: str,
    path: str,
    headers: dict,
    token: str,
    enabled: bool,
    samples_dir: str,
) -> tuple:
    if enabled is False:
        return 404, _load(samples_dir, "error-404-disabled.json")
    if enabled is not True:
        raise TypeError("enabled 必须是 bool")
    if _bearer(headers) != token:
        return 401, _load(samples_dir, "error-401.json")
    if not isinstance(method, str) or method.upper() != "GET":
        return (
            405,
            {
                "detail": {
                    "code": "method_not_allowed",
                    "params": {},
                    "message": "only GET is allowed",
                }
            },
        )
    if not isinstance(path, str):
        raise TypeError("path 必须是字符串")

    parts = urlsplit(path)
    if parts.path == _LIST_PATH and parts.query == "":
        return 200, _load(samples_dir, "sites-list.json")
    if parts.path == _ONE_PATH:
        return _one_site(samples_dir, _one_key(parts.query))
    return (
        404,
        {
            "detail": {
                "code": "not_found",
                "params": {},
                "message": "unknown feed path",
            }
        },
    )


def _bearer(headers: dict) -> str | None:
    if not isinstance(headers, dict):
        return None
    raw = headers.get("Authorization")
    if not isinstance(raw, str) or not raw.startswith("Bearer "):
        return None
    return raw[len("Bearer ") :]


def _one_key(query: str) -> str:
    values = parse_qs(query, keep_blank_values=True).get("key")
    if values is None or len(values) != 1:
        raise ValueError("查询串里要有且只有一个 key")
    return values[0]


def _one_site(samples_dir: str, site_key: str) -> tuple:
    found = []
    root = Path(samples_dir)
    for path in sorted(root.glob("site-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError("站点样本不是对象: %s" % path.name)
        if data.get("site_key") == site_key:
            found.append(data)
    if len(found) > 1:
        raise RuntimeError("样本里 site_key 重复: %s" % site_key)
    if not found:
        return 404, _unknown_site(samples_dir, site_key)
    return 200, found[0]


def _unknown_site(samples_dir: str, site_key: str) -> dict:
    body = _load(samples_dir, "error-404-site.json")
    detail = body.get("detail")
    if not isinstance(detail, dict) or not isinstance(detail.get("params"), dict):
        raise TypeError("error-404-site.json 形状不对")
    params = dict(detail["params"])
    params["key"] = site_key
    detail["params"] = params
    return body


def _load(samples_dir: str, name: str) -> dict:
    path = Path(samples_dir) / name
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("%s 不是对象" % name)
    return data
