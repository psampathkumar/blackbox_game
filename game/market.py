"""
Market system for continuous-time trading of knowledge reports.
- Listings are permanent: only the report creator can list it.
- Buying grants read access (adds to buyer's ownership) but does NOT
  allow the buyer to resell — only the original creator can list.
- Listings never deactivate; they remain available for purchase forever.
- buy_count tracked so the dashboard can show how useful a listing is.
"""

import json
import os
import time

SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "shared")
MARKET_DIR = os.path.join(SHARED_DIR, "market")
REPORTS_DIR = os.path.join(SHARED_DIR, "reports")
OWNERSHIP_DIR = os.path.join(SHARED_DIR, "ownership")

LISTINGS_PATH = os.path.join(MARKET_DIR, "listings.jsonl")
TRANSACTIONS_PATH = os.path.join(MARKET_DIR, "transactions.jsonl")


def _load_listings() -> list:
    if not os.path.exists(LISTINGS_PATH):
        return []
    items = []
    with open(LISTINGS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def _save_listings(listings: list):
    with open(LISTINGS_PATH, "w") as f:
        for item in listings:
            f.write(json.dumps(item) + "\n")


def list_report(player: str, report_id: int, price: float) -> dict:
    """
    List a report for sale. Only the report's CREATOR can list it.
    Listings are permanent (never deactivate).
    Returns {"ok": bool, "message": str}
    """
    meta_path = os.path.join(REPORTS_DIR, f"report_{report_id}.meta.json")
    if not os.path.exists(meta_path):
        return {"ok": False, "message": "Report metadata missing."}

    with open(meta_path, "r") as f:
        meta = json.load(f)

    if meta.get("creator") != player:
        return {"ok": False, "message": "Only the report creator can list it for sale."}

    listings = _load_listings()

    # Check if already listed (any previous listing by this creator for this report)
    for item in listings:
        if item.get("report_id") == report_id and item.get("seller") == player:
            # Update price and reactivate if needed
            item["price"] = price
            item["timestamp"] = time.time()
            item["active"] = True
            _save_listings(listings)
            return {"ok": True, "message": f"Updated listing for report {report_id} to {price} energy."}

    # New permanent listing
    new_listing = {
        "report_id": report_id,
        "seller": player,
        "price": price,
        "active": True,
        "timestamp": time.time(),
        "buy_count": 0,
    }
    listings.append(new_listing)
    _save_listings(listings)

    return {"ok": True, "message": f"Listed report {report_id} for {price} energy (permanent listing)."}


def update_price(player: str, report_id: int, price: float) -> dict:
    """
    Update the price of a listing. Only the original creator can do this.
    Returns {"ok": bool, "message": str}
    """
    listings = _load_listings()
    found = False
    for item in listings:
        if item.get("report_id") == report_id and item.get("seller") == player:
            item["price"] = price
            item["timestamp"] = time.time()
            found = True
            break
    if not found:
        return {"ok": False, "message": "No listing found for this report by you."}
    _save_listings(listings)
    return {"ok": True, "message": f"Updated price of report {report_id} to {price}."}


def buy_report(state: dict, buyer: str, report_id: int) -> dict:
    """
    Buy read-access to a listed report.
    - Buyer pays energy, seller (creator) gains energy.
    - Buyer gains read access (added to ownership/<buyer>.json).
    - Buyer CANNOT resell the report; only the creator can list it.
    - Listing stays active forever; buy_count increments.
    Modifies state in place.
    Returns {"ok": bool, "message": str}
    """
    if buyer not in state["players"]:
        state["players"][buyer] = {
            "energy": 100.0,
            "experiment_score": 0.0,
            "market_profit": 0.0,
            "total_score": 0.0,
        }

    listings = _load_listings()
    listing = None
    for item in listings:
        if item.get("report_id") == report_id and item.get("active"):
            listing = item
            break
    if listing is None:
        return {"ok": False, "message": "Report not listed for sale."}

    seller = listing["seller"]
    price = listing["price"]

    if buyer == seller:
        return {"ok": False, "message": "Cannot buy your own report."}

    if state["players"][buyer]["energy"] < price:
        return {"ok": False, "message": "Insufficient energy."}

    # Transfer energy
    state["players"][buyer]["energy"] -= price
    if seller not in state["players"]:
        state["players"][seller] = {
            "energy": 100.0,
            "experiment_score": 0.0,
            "market_profit": 0.0,
            "total_score": 0.0,
        }
    state["players"][seller]["energy"] += price
    state["players"][seller]["market_profit"] += price
    # Update total scores after profit change
    for p in state["players"]:
        pl = state["players"][p]
        pl["total_score"] = pl["experiment_score"] + pl["market_profit"]

    # Grant ownership (read access) to buyer
    buyer_own_path = os.path.join(OWNERSHIP_DIR, f"{buyer}.json")
    buyer_owned = []
    if os.path.exists(buyer_own_path):
        with open(buyer_own_path, "r") as f:
            buyer_owned = json.load(f)
    if report_id not in buyer_owned:
        buyer_owned.append(report_id)
    with open(buyer_own_path, "w") as f:
        json.dump(buyer_owned, f, indent=2)

    # Increment buy_count on the listing
    listing["buy_count"] = listing.get("buy_count", 0) + 1
    _save_listings(listings)

    # Log transaction
    transaction = {
        "buyer": buyer,
        "seller": seller,
        "report_id": report_id,
        "price": price,
        "time": time.time(),
    }
    with open(TRANSACTIONS_PATH, "a") as f:
        f.write(json.dumps(transaction) + "\n")

    return {"ok": True, "message": f"Bought read access to report {report_id} from {seller} for {price} energy."}
