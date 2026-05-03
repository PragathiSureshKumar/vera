"""
load_dataset.py
===============
Helper script: loads all dataset files into the bot via POST /v1/context.
Run this locally to seed your bot before running the judge_simulator.

Usage:
    # 1. Start bot:  python bot.py
    # 2. In another terminal:
    python load_dataset.py --url http://localhost:8080 --dataset ./dataset
"""

import argparse
import json
import time
from pathlib import Path

try:
    import httpx
    _http = httpx
except ImportError:
    import urllib.request
    _http = None


def post_context(url_base: str, scope: str, context_id: str, version: int, payload: dict) -> dict:
    body = json.dumps({
        "scope": scope,
        "context_id": context_id,
        "version": version,
        "payload": payload,
        "delivered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }).encode()

    if _http:
        r = _http.post(f"{url_base}/v1/context", content=body, headers={"Content-Type": "application/json"}, timeout=10)
        return r.json()
    else:
        req = urllib.request.Request(
            f"{url_base}/v1/context",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())


def load_dataset(url_base: str, dataset_dir: Path):
    categories_dir = dataset_dir / "categories"
    merchants_file = dataset_dir / "merchants_seed.json"
    customers_file = dataset_dir / "customers_seed.json"
    triggers_file = dataset_dir / "triggers_seed.json"

    # Categories
    cat_count = 0
    for cat_file in categories_dir.glob("*.json"):
        payload = json.loads(cat_file.read_text())
        slug = payload.get("slug", cat_file.stem)
        r = post_context(url_base, "category", slug, 1, payload)
        print(f"  category/{slug}: {r.get('accepted', '?')}")
        cat_count += 1

    # Merchants
    merchants_data = json.loads(merchants_file.read_text())
    merchants = merchants_data.get("merchants", [])
    for m in merchants:
        mid = m.get("merchant_id", "unknown")
        r = post_context(url_base, "merchant", mid, 1, m)
        print(f"  merchant/{mid}: {r.get('accepted', '?')}")

    # Customers
    customers_data = json.loads(customers_file.read_text())
    customers = customers_data.get("customers", [])
    for c in customers:
        cid = c.get("customer_id", "unknown")
        r = post_context(url_base, "customer", cid, 1, c)
        print(f"  customer/{cid}: {r.get('accepted', '?')}")

    # Triggers
    triggers_data = json.loads(triggers_file.read_text())
    triggers = triggers_data.get("triggers", [])
    for trg in triggers:
        tid = trg.get("id", "unknown")
        r = post_context(url_base, "trigger", tid, 1, trg)
        print(f"  trigger/{tid}: {r.get('accepted', '?')}")

    print(f"\n✅ Loaded: {cat_count} categories, {len(merchants)} merchants, {len(customers)} customers, {len(triggers)} triggers")

    # Verify
    import urllib.request
    with urllib.request.urlopen(f"{url_base}/v1/healthz", timeout=5) as resp:
        health = json.loads(resp.read())
    print(f"Healthz: {health}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8080", help="Bot base URL")
    parser.add_argument("--dataset", default="./dataset", help="Path to dataset/ directory")
    args = parser.parse_args()

    load_dataset(args.url, Path(args.dataset))
