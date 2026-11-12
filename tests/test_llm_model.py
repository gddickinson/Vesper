"""The Claude request body: default model claude-haiku-5-5, per-call override kept. No network.

A fake ``urlopen`` captures the request instead of calling the API, and a fake key (not
key-shaped) is injected through ``llm_keys.resolve``.
"""
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from breathsim import llm, llm_keys  # noqa: E402

FAKE = "vesper-local-test-token-0000abcd"   # not a real / key-shaped secret


class FakeClient:
    """Stands in for urllib.request.urlopen: records each request, returns a canned reply."""

    def __init__(self, reply):
        self.reply, self.requests = reply, []

    def __call__(self, req, timeout=None):
        self.requests.append({"url": req.full_url, "headers": dict(req.header_items()),
                              "body": json.loads(req.data.decode("utf-8"))})
        return io.BytesIO(json.dumps(self.reply).encode("utf-8"))


REPLY = {"content": [{"type": "thinking", "thinking": "", "signature": "x"},
                     {"type": "text", "text": "Breathe out slowly."},
                     {"type": "tool_use", "id": "t1", "name": "play", "input": {}}]}


@pytest.fixture
def fake(monkeypatch):
    client = FakeClient(REPLY)
    monkeypatch.setattr(llm_keys, "resolve", lambda: FAKE)
    monkeypatch.setattr(llm.urllib.request, "urlopen", client)
    return client


def test_default_model_is_haiku_5_5():
    assert llm.DEFAULT_CLAUDE_MODEL == "claude-haiku-5-5"


def test_default_request_body(fake):
    assert llm.complete("hello", max_tokens=300) == "Breathe out slowly."
    body = fake.requests[0]["body"]
    assert body["model"] == "claude-haiku-5-5"
    assert body["output_config"] == {"effort": "low"}
    assert body["max_tokens"] == 300
    # Haiku 5.5 rejects non-default sampling parameters, budget_tokens thinking and prefill
    for banned in ("temperature", "top_p", "top_k", "thinking"):
        assert banned not in body
    assert body["messages"][-1]["role"] == "user"


def test_model_override_kept(fake):
    llm.complete("hello", model="claude-haiku-4-5")
    body = fake.requests[0]["body"]
    assert body["model"] == "claude-haiku-4-5"
    assert "output_config" not in body      # effort is not sent to a model that may not take it


def test_chat_reads_blocks_by_type(fake):
    out = llm.chat([{"role": "user", "content": "play"}], tools=[{"name": "play"}])
    assert out["text"] == "Breathe out slowly."         # a leading thinking block is skipped
    assert out["tool_calls"] == [{"name": "play", "input": {}, "id": "t1"}]
    assert fake.requests[0]["body"]["model"] == "claude-haiku-5-5"
