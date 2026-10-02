import json
from email.message import Message
from urllib.error import HTTPError

import pytest

from marketplace_crop import BuyerUpdate, InfraiClient, MarketplaceCropService, SellerAsset


class FakeClient:
    def upload(self, image, filename):
        return {"id": "img-1"}

    def smart_crop(self, image, aspect):
        return {"url": f"https://cdn.test/{image}-{aspect}"}


def test_listing_crops_and_handoff_keep_buyer_order_context():
    service = MarketplaceCropService(FakeClient())
    asset = service.prepare_listing("mug.jpg", b"pixels", ["1:1", "4:5"])
    handoff = service.handoff(asset, BuyerUpdate("buyer-7", "gift wrap"), "order-9")
    assert set(asset.crops) == {"1:1", "4:5"}
    assert handoff.status == "ready_for_fulfillment"
    assert handoff.buyer_id == "buyer-7"


@pytest.mark.parametrize("status", [429, 503])
def test_transient_error_envelope_is_retried(monkeypatch, status):
    import io

    calls = []

    def urlopen(req, timeout):
        calls.append(req)
        if len(calls) == 1:
            body = io.BytesIO(json.dumps({"ok": False, "error": {"code": "TEMPORARY"}}).encode())
            raise HTTPError(req.full_url, status, "retry", Message(), body)

        class Response:
            status = 200
            headers = Message()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return b'{"ok":true,"data":{"id":"done"}}'

        return Response()

    monkeypatch.setattr("marketplace_crop.request.urlopen", urlopen)
    monkeypatch.setattr("marketplace_crop.time.sleep", lambda seconds: None)
    assert InfraiClient("test")._post("/v1/image/upload", {"file": "sample"}) == {"id": "done"}
    assert len(calls) == 2
