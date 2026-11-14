# risk: high
"""假 ARIANE。模块还不存在，现在跑必须失败。

fakes.fake_ariane.handle 按关键字收：
- method：HTTP 方法，测试传 "GET"
- path：路径加查询串。取一个站是
  /api/feed/v1/sites/one?key=<url 编码后的 site_key>
  清单是 /api/feed/v1/sites
- headers：dict，口令在 "Authorization"，值是 "Bearer <口令>"
- token：这只假服务认的口令
- enabled：False 表示功能关闭
- samples_dir：样本目录的字符串路径。测试传
  docs/ariane-bridge/site-feed-v1-samples/，不依赖复制件

返回 (status, body)。status 是 int。body 是 dict，或 JSON 文本 / bytes。
多返回的项忽略。
"""
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import quote

_BRIDGE = Path(__file__).resolve().parents[1]
_REPO = _BRIDGE.parent
if str(_BRIDGE) not in sys.path:
    sys.path.insert(0, str(_BRIDGE))

SAMPLES = _REPO / "docs" / "ariane-bridge" / "site-feed-v1-samples"
TOKEN = "secret-token"
LIST_PATH = "/api/feed/v1/sites"


def _load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def _site_path(site_key):
    return "/api/feed/v1/sites/one?key=" + quote(site_key, safe="")


def _as_data(body):
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8")
    if isinstance(body, str):
        return json.loads(body)
    return body


def _call(method, path, presented_token, enabled):
    from fakes.fake_ariane import handle

    result = handle(
        method=method,
        path=path,
        headers={"Authorization": "Bearer " + presented_token},
        token=TOKEN,
        enabled=enabled,
        samples_dir=str(SAMPLES),
    )
    if not isinstance(result, tuple) or len(result) < 2:
        raise AssertionError("handle 应返回 (status, body)")
    body = _as_data(result[1])
    if not isinstance(body, dict):
        raise AssertionError("body 应为 JSON 对象")
    return result[0], body


class TestFakeAriane(unittest.TestCase):
    def test_wrong_token_returns_401_sample(self):
        status, body = _call(
            "GET", _site_path("CHATILLON LA PALUD #1"), "wrong-token", True
        )
        self.assertEqual(status, 401)
        self.assertEqual(body, _load("error-401.json"))

    def test_disabled_returns_404_sample(self):
        status, body = _call(
            "GET", _site_path("CHATILLON LA PALUD #1"), TOKEN, False
        )
        self.assertEqual(status, 404)
        self.assertEqual(body, _load("error-404-disabled.json"))

    def test_unknown_site_key_returns_404_with_requested_key(self):
        requested = "UNKNOWN SITE #42"
        status, body = _call("GET", _site_path(requested), TOKEN, True)
        sample = _load("error-404-site.json")
        self.assertEqual(status, 404)
        self.assertEqual(set(body), set(sample))
        detail = body["detail"]
        sample_detail = sample["detail"]
        self.assertEqual(set(detail), set(sample_detail))
        self.assertEqual(detail["code"], sample_detail["code"])
        self.assertEqual(detail["message"], sample_detail["message"])
        self.assertEqual(set(detail["params"]), set(sample_detail["params"]))
        self.assertEqual(detail["params"]["key"], requested)

    def test_chatillon_returns_200_ready(self):
        status, body = _call(
            "GET", _site_path("CHATILLON LA PALUD #1"), TOKEN, True
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["site_key"], "CHATILLON LA PALUD #1")
        self.assertIs(body["ready"], True)

    def test_site_list_count_matches_sample(self):
        status, body = _call("GET", LIST_PATH, TOKEN, True)
        sample = _load("sites-list.json")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["sites"]), len(sample["sites"]))
