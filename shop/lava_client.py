from __future__ import annotations

import requests
from django.conf import settings


class LavaError(Exception):
    def __init__(self, message: str, status: int | None = None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload


def _headers():
    key = settings.LAVA_API_KEY
    if not key:
        raise LavaError("LAVA_API_KEY is empty. Put it in .env")
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Api-Key": key,
    }


def _req(method: str, path: str, **kwargs):
    url = f"{settings.LAVA_API_BASE}{path}"
    try:
        r = requests.request(method, url, headers=_headers(), timeout=30, **kwargs)
    except requests.RequestException as e:
        raise LavaError(f"Network error: {e}") from e
    try:
        data = r.json() if r.text else {}
    except Exception:
        data = {"raw": r.text}
    if r.status_code >= 400:
        msg = data.get("error") or data.get("message") or r.text or r.reason
        if not isinstance(msg, str):
            msg = str(msg)
        raise LavaError(msg, status=r.status_code, payload=data)
    return data


def get_products(feed_visibility: str = "ALL"):
    return _req("GET", f"/api/v2/products?feedVisibility={feed_visibility}")


def create_invoice_v3(email: str, offer_id: str, currency: str, amount: float, buyer_language: str = "RU"):
    body = {
        "email": email,
        "offerId": offer_id,
        "currency": currency,
        "amount": float(amount),
        "buyerLanguage": buyer_language,
    }
    return _req("POST", "/api/v3/invoice", json=body)


def create_invoice_v2(email: str, offer_id: str, currency: str, buyer_language: str = "RU"):
    body = {
        "email": email,
        "offerId": offer_id,
        "currency": currency,
        "buyerLanguage": buyer_language,
    }
    return _req("POST", "/api/v2/invoice", json=body)


def get_invoice(invoice_id: str):
    try:
        return _req("GET", f"/api/v1/invoice?id={invoice_id}")
    except LavaError:
        return _req("GET", f"/api/v2/invoices/{invoice_id}")


def get_sales_report(params: dict | None = None):
    """Best-effort reports endpoint; path may vary by API version."""
    q = ""
    if params:
        from urllib.parse import urlencode
        q = "?" + urlencode(params)
    # try common report paths
    last = None
    for path in (f"/api/v2/reports/sales{q}", f"/api/v1/reports{q}", f"/api/v2/invoices{q}"):
        try:
            return _req("GET", path)
        except LavaError as e:
            last = e
            continue
    if last:
        raise last
    raise LavaError("Reports endpoint unavailable")


def extract_offers(products_payload) -> list[dict]:
    """Normalize products response into list of {offer_id, title, product_id}."""
    items = products_payload
    if isinstance(products_payload, dict):
        items = (
            products_payload.get("items")
            or products_payload.get("products")
            or products_payload.get("data")
            or []
        )
    if not isinstance(items, list):
        return []
    out = []
    for p in items:
        title = p.get("name") or p.get("title") or "Product"
        pid = p.get("id") or p.get("productId") or ""
        offers = p.get("offers") or []
        if not isinstance(offers, list):
            offers = [offers] if offers else []
        if not offers:
            oid = p.get("offerId")
            if oid:
                out.append({"offer_id": str(oid), "title": title, "product_id": str(pid)})
            continue
        for o in offers:
            if not isinstance(o, dict):
                continue
            oid = o.get("id") or o.get("offerId")
            if not oid:
                continue
            oname = o.get("name") or title
            out.append({"offer_id": str(oid), "title": oname, "product_id": str(pid)})
    return out


def resolve_offer_id() -> str:
    if settings.LAVA_OFFER_ID:
        return settings.LAVA_OFFER_ID
    offers = extract_offers(get_products("ALL"))
    if not offers:
        raise LavaError(
            "No offers found. Create a product in lava.top with "
            "'Price on request via API' and set LAVA_OFFER_ID in .env"
        )
    return offers[0]["offer_id"]
