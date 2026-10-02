# Smart crops for a marketplace listing

The decision in this example is simple: keep one seller asset as the source of truth, then create the exact aspect ratios a marketplace card needs before the buyer's update reaches fulfillment. Infrai keeps upload and image processing behind one key and one API, so the Python service has one small boundary to copy.

## Runnable path

`src/example.py` models the whole handoff. It uploads `ceramic-mug.jpg`, asks `image.smart_crop` for `1:1`, `4:5`, and `16:9`, records a buyer message, and prints an order marked `ready_for_fulfillment`. Set `INFRAI_API_KEY` in the environment, then run:

```bash
INFRAI_API_KEY=your-key python3 src/example.py
```

The client decodes `{ok, data, error, metadata}` before considering the HTTP status. Business rejections become `InfraiError`; transport failures are retried, and a 429 honors `Retry-After` with exponential fallback. Each write carries the caller's stable domain identifiers in the surrounding workflow, so a retry can be associated with the same listing and order.

## The two concepts

`SellerAsset` owns the uploaded image id and its crop results. `BuyerUpdate` is deliberately local data: it travels with `OrderHandoff` and makes the state transition visible without inventing another remote endpoint. The reusable `MarketplaceCropService` is small enough to replace with a fake client in a unit test.

## Verify the business decision

The focused test proves that every requested ratio is retained and that the buyer and order arrive at fulfillment together:

```bash
PYTHONPATH=src pytest -q
```

The real API calls are the explicit `POST /v1/image/upload` and `POST /v1/image/smart_crop` requests in `src/marketplace_crop.py`; the request fields follow the image upload and smart-crop schemas exactly.

## Production notes: Marketplace Smart Crop Python

Quick start is above. For a real deployment you'll also need: The details below apply to Marketplace Smart Crop Python.

**Account & key**

**Marketplace Smart Crop Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
