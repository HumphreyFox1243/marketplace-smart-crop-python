import base64
import json

from marketplace_crop import BuyerUpdate, service_from_env

SAMPLE_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABIMDRANCxIQDhAUExIVGywdGxgYGzYnKSAsQDlEQz85Pj1HUGZXR0thTT0+WXlaYWltcnNyRVV9hnxvhWZwcm7/"
    "2wBDARMUFBsXGzQdHTRuST5Jbm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm5ubm7/"
    "wAARCAAgACADASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFgEBAQEAAAAAAAAAAAAAAAAAAAQF/"
    "8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AmAhbwAAAAAD/2Q=="
)


def main() -> None:
    service = service_from_env()
    asset = service.prepare_listing("ceramic-mug.jpg", SAMPLE_JPEG, ["1:1", "4:5", "16:9"])
    handoff = service.handoff(asset, BuyerUpdate("buyer-42", "Please ship the blue mug."), "order-1007")
    print(json.dumps({"asset": asset.__dict__, "handoff": handoff.__dict__}, indent=2))


if __name__ == "__main__":
    main()
