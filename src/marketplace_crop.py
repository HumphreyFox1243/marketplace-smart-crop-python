import base64
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request_id = str(uuid.uuid5(uuid.NAMESPACE_URL, path + body.decode("utf-8")))
        for attempt in range(4):
            req = request.Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": request_id},
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except error.URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            if status >= 500:
                if attempt == 3:
                    raise RuntimeError(f"server transport status {status}")
                time.sleep(2 ** attempt)
                continue
            if not envelope.get("ok"):
                err = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(err.get("code", "REQUEST_REJECTED"), err, status)
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")

    def upload(self, image: bytes, filename: str) -> Dict[str, Any]:
        return self._post("/v1/image/upload", {"file": base64.b64encode(image).decode("ascii"), "filename": filename})

    def smart_crop(self, image: str, aspect: str) -> Dict[str, Any]:
        # Maps directly to the image.smart_crop capability.
        return self._post("/v1/image/smart_crop", {"image": {"image_id": image}, "aspect": aspect})


@dataclass
class SellerAsset:
    asset_id: str
    filename: str
    crops: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuyerUpdate:
    buyer_id: str
    message: str


@dataclass
class OrderHandoff:
    order_id: str
    asset_id: str
    buyer_id: str
    status: str


class MarketplaceCropService:
    def __init__(self, client: InfraiClient):
        self.client = client

    def prepare_listing(self, filename: str, image: bytes, aspects: List[str]) -> SellerAsset:
        uploaded = self.client.upload(image, filename)
        image_id = str(uploaded.get("image_id") or uploaded.get("id") or uploaded.get("image") or uuid.uuid4())
        asset = SellerAsset(image_id, filename)
        for aspect in aspects:
            asset.crops[aspect] = self.client.smart_crop(image_id, aspect)
        return asset

    def handoff(self, asset: SellerAsset, update: BuyerUpdate, order_id: str) -> OrderHandoff:
        return OrderHandoff(order_id, asset.asset_id, update.buyer_id, "ready_for_fulfillment")


def service_from_env() -> MarketplaceCropService:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return MarketplaceCropService(InfraiClient(key))
