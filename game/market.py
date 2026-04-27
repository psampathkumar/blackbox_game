"""
Market system for continuous-time trading of knowledge reports.
- Reports sold as copies (seller keeps ownership)
- Buyer pays energy, seller gains energy
- Supports relisting, price updates, multiple buyers
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
STATE_PATH = os.path.join(SHARED_DIR, "state.json")


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


def _ensure_player_state(state: dict, player: str):
    if player not in state["players"]:
        state["players"][player] = {
            "energy": 100.0,
            "experiment_score": 0.0,
            "knowledge_score": 0.0,
            "market_profit": 0.0,
            "total_score": 0.0,
        }


def list_report(player: str, report_id: int, price: float) -> dict:
    """
    List a report for sale. Player must own it.
    Returns {"ok": bool, "message": str}
    """
    ownership_path = os.path.join(OWNERSHIP_DIR, f"{player}.json")
    if not os.path.exists(ownership_path):
        return {"ok": False, "message": "Player has no ownership record."}
    with open(ownership_path, "r") as f:
        owned = json.load(f)
    if report_id not in owned:
        return {"ok": False, "message": "Player does not own this report."}

    report_path = os.path.join(REPORTS_DIR, f"report_{report_id}.json")
    if not os.path.exists(report_path):
        return {"ok": False, "message": "Report file missing."}

    listings = _load_listings()
    # Deactivate any previous listings for this report by this player
    for item in listings:
        if item.get("report_id") == report_id and item.get("seller") == player:
            item["active"] = False

    new_listing = {
        "report_id": report_id,
        "seller": player,
        "price": price,
        "active": True,
        "timestamp": time.time(),
    }
    listings.append(new_listing)
    _save_listings(listings)

    return {"ok": True, "message": f"Listed report {report_id} for {price} energy."}


def update_price(player: str, report_id: int, price: float) -> dict:
    """
    Update the price of an active listing.
    Returns {"ok": bool, "message": str}
    """
    listings = _load_listings()
    found = False
    for item in listings:
        if item.get("report_id") == report_id and item.get("seller") == player and item.get("active"):
            item["price"] = price
            item["timestamp"] = time.time()
            found = True
            break
    if not found:
        return {"ok": False, "message": "No active listing found for this report by this player."}
    _save_listings(listings)
    return {"ok": True, "message": f"Updated price of report {report_id} to {price}."}


def buy_report(state: dict, buyer: str, report_id: int) -> dict:
    """
    Buy a copy of a listed report.
    Buyer pays energy, seller gains energy.
    Modifies state in place.
    Returns {"ok": bool, "message": str}
    """
    _ensure_player_state(state, buyer)

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
    _ensure_player_state(state, seller)
    state["players"][seller]["energy"] += price
    state["players"][seller]["market_profit"] += price
    # Update total scores after profit change
    for p in state["players"]:
        pl = state["players"][p]
        pl["total_score"] = pl["experiment_score"] + pl["market_profit"] + pl["knowledge_score"]

    # Grant ownership to buyer
    buyer_own_path = os.path.join(OWNERSHIP_DIR, f"{buyer}.json")
    buyer_owned = []
    if os.path.exists(buyer_own_path):
        with open(buyer_own_path, "r") as f:
            buyer_owned = json.load(f)
    if report_id not in buyer_owned:
        buyer_owned.append(report_id)
    with open(buyer_own_path, "w") as f:
        json.dump(buyer_owned, f, indent=2)

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

    return {"ok": True, "message": f"Bought report {report_id} from {seller} for {price} energy."}
