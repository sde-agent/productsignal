import csv
import hashlib
import json
import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42

# Each entry contains:
# behavior, case count, evidence type, symptom descriptions.
BEHAVIORS = [
    (
        "password_reset_delay", 120, "reported_failure",
        [
            "The password recovery message arrives {minutes} minutes after I request it.",
            "I ask for a reset link, wait ages, then several emails arrive together.",
            "By the time the password reset email turns up, its link has expired.",
            "Nothing appears in my inbox for half an hour after clicking forgot password.",
            "I can eventually recover my account, but the email takes far too long.",
            "The reset message is delayed even though other account emails arrive immediately.",
        ],
    ),
    (
        "promo_cart_empty", 85, "reported_failure",
        [
            "Applying {coupon} makes all the items disappear from my basket.",
            "My shopping bag goes from several products to empty when I redeem a discount.",
            "I enter a coupon and the page responds, but my selected items are gone.",
            "The discount is accepted and then my cart total becomes zero with no items listed.",
            "Everything I added vanishes immediately after using {coupon}.",
            "The basket resets when I apply the offer; I have to add every product again.",
        ],
    ),
    (
        "checkout_address_blocked", 65, "reported_failure",
        [
            "Checkout stops responding immediately after I submit my shipping address.",
            "I fill in my street and postcode, but Continue never takes me to payment.",
            "The order page hangs when I finish entering delivery details.",
            "I cannot get beyond the address step, even with all required fields filled.",
            "Saving my delivery address leaves checkout stuck on the same screen.",
            "The spinner runs forever after I confirm where the order should be sent.",
        ],
    ),
    (
        "search_irrelevant", 110, "reported_failure",
        [
            "Searching for {product} returns unrelated products, although search loads normally.",
            "I enter the exact item name and get results from a different category.",
            "The search page works, but the products it shows do not match my query.",
            "Looking up {product} gives me accessories for something else.",
            "The item is available through browsing but missing from its search results.",
            "Search responds quickly with a list that has nothing to do with what I typed.",
        ],
    ),
    (
        "delivery_late", 150, "reported_failure",
        [
            "The promised delivery date passed {days} days ago and my order has not arrived.",
            "Tracking says in transit, but the package is already several days overdue.",
            "The delivery estimate keeps moving later; I still have no parcel.",
            "My order has not shipped even though its promised arrival date has passed.",
            "The carrier marked my parcel delayed after missing the expected delivery date.",
            "I paid for delivery by yesterday, but the order still has not reached me.",
        ],
    ),
    (
        "login_repeated_password", 45, "reported_failure",
        [
            "My password is accepted, but the next page asks me to sign in again.",
            "I can log in successfully and then get sent straight back to the password screen.",
            "Every page asks for my password again even though I just signed in.",
            "The site keeps forgetting my login during the same visit.",
            "Signing in works for a moment, then I am logged out when I open my account.",
            "I am stuck in a loop of entering my correct password and seeing another login form.",
        ],
    ),
    (
        "checkout_promo_freeze", 25, "reported_failure",
        [
            "Checkout freezes after I apply {coupon}; my items remain in the cart.",
            "Redeeming a discount leaves the payment page unresponsive without emptying my basket.",
            "The spinner never finishes after I enter a promo code during checkout.",
            "I can enter my address normally, but applying the offer locks the checkout page.",
            "The coupon makes Continue stop responding; the products are still listed.",
            "After submitting {coupon}, checkout hangs and I cannot complete payment.",
        ],
    ),
    (
        "search_unavailable", 15, "reported_failure",
        [
            "Every search returns a service-unavailable error instead of any results.",
            "The search endpoint shows an error page for every query I try.",
            "Searching for anything produces a blank error screen, not a product list.",
            "Search never loads; it keeps spinning until a timeout message appears.",
            "I cannot use search at all, although I can still browse categories.",
            "The search service is unavailable regardless of the product name.",
        ],
    ),

    # 115 legitimate long-tail cases, with distinct behavior labels.
    (
        "duplicate_charge", 23, "reported_failure",
        [
            "One completed purchase produced two settled charges on my statement.",
            "I placed a single order, but the same amount was charged twice.",
            "My bank shows two completed payments for the one order confirmation.",
        ],
    ),
    (
        "receipt_missing", 23, "reported_failure",
        [
            "My purchase completed, but no receipt was sent and none is available in my account.",
            "The order is confirmed, but downloading its receipt produces an error.",
            "The receipt link for my paid order opens a blank page.",
        ],
    ),
    (
        "wishlist_not_saved", 23, "reported_failure",
        [
            "Items I save to my wishlist disappear when I return later.",
            "The heart icon changes, but my saved-items list stays empty.",
            "Adding a product to favorites does not persist after refreshing.",
        ],
    ),
    (
        "image_upload_failure", 23, "reported_failure",
        [
            "Uploading a photo for my review fails with an error.",
            "My review text saves, but attaching a picture never completes.",
            "A supported JPEG is rejected when I add it to a product review.",
        ],
    ),
    (
        "notification_setting_not_saved", 23, "reported_failure",
        [
            "I switch off promotional notifications, but the setting turns back on after saving.",
            "My notification preferences revert each time I reopen settings.",
            "Saving the opt-out setting succeeds onscreen but does not persist.",
        ],
    ),

    # 120 feature requests, how-to questions, and intended behavior.
    (
        "howto_unsubscribe", 30, "how_to",
        [
            "Where can I unsubscribe from marketing emails?",
            "Could you explain how to change my email subscription preferences?",
            "Which account setting lets me stop promotional messages?",
        ],
    ),
    (
        "howto_order_history", 30, "how_to",
        [
            "Where can I view my previous purchases?",
            "How do I find an order I placed last month?",
            "Could you point me to my order history?",
        ],
    ),
    (
        "feature_dark_mode", 30, "feature_request",
        [
            "Please add a dark theme for browsing at night.",
            "I would like an option to switch the app to dark mode.",
            "A darker appearance would make the store more comfortable to read.",
        ],
    ),
    (
        "expired_coupon_explanation", 30, "intended_behavior",
        [
            "My coupon expired yesterday and checkout says expired; can you explain its validity period?",
            "The offer says it ended last week, so I understand why it cannot be redeemed.",
            "The discount ended yesterday and checkout rejects it as expired. Could you explain the expiry policy?",
        ],
    ),

    # 150 ambiguous cases: do not pretend their behavior is known.
    (
        "ambiguous", 150, "ambiguous",
        [
            "It stopped working again.",
            "I cannot finish what I was doing.",
            "Something is wrong with my account, but I cannot explain it.",
            "The page looks strange and I am not sure what changed.",
            "I got an error earlier but did not save the message.",
            "My order or payment seems wrong; I need to check the details.",
            "It is slow sometimes, but I do not know which screen causes it.",
            "I tried again and got a different result.",
            "I need help with the thing I mentioned before.",
            "There might be a problem, or perhaps I misunderstood the instructions.",
        ],
    ),
]

CONFUSION_PAIRS = [
    ["password_reset_delay", "login_repeated_password"],
    ["checkout_address_blocked", "checkout_promo_freeze"],
    ["promo_cart_empty", "checkout_promo_freeze"],
    ["search_irrelevant", "search_unavailable"],
    ["checkout_address_blocked", "delivery_late"],
    ["howto_unsubscribe", "notification_setting_not_saved"],
]


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def render(rng, behavior, kind, symptoms, index):
    symptom = rng.choice(symptoms).format(
        minutes=rng.choice([20, 35, 45, 60]),
        days=rng.choice([2, 3, 5, 7]),
        coupon=rng.choice(["SAVE10", "WELCOME", "my discount code"]),
        product=rng.choice(["running shoes", "a kettle", "a backpack", "headphones"]),
    )

    context = rng.choice([
        "I am using the mobile app.",
        "This was on the desktop website.",
        "I noticed this on my tablet.",
        "I was using a browser on my phone.",
        "",
    ])

    if kind == "reported_failure":
        detail = rng.choice([
            "I retried once and saw the same behavior.",
            "This happened during my latest visit.",
            "I have not tested another device yet.",
            "I do not know what caused it.",
            "",
        ])
    elif kind == "ambiguous":
        detail = rng.choice([
            "I do not have a screenshot.",
            "I cannot remember the exact steps.",
            "",
        ])
    else:
        detail = rng.choice([
            "A short explanation would help.",
            "I could not find guidance in the help section.",
            "",
        ])

    style = index % 5
    if style == 0:
        text = symptom
        tags = ["terse"]
    elif style == 1:
        text = f"Hello support, {symptom} {context}"
        tags = ["conversational"]
    elif style == 2:
        text = f"{symptom}\n{detail}\n{context}"
        tags = ["multiline"]
    elif style == 3:
        text = (
            f"{context} {symptom} {detail} "
            "Please let me know what information you need to investigate."
        )
        tags = ["longer"]
    else:
        text = f"{symptom} {context}".lower()
        tags = ["informal"]

    text = text.strip()
    if index % 11 == 0:
        original = text
        text = text.replace("the ", "teh ", 1).replace("Please", "Pls", 1)
        if text == original:
            text = text.replace(" ", "  ", 1)
        if text != original:
            tags.append("typing_variation")

    if behavior in {"checkout_promo_freeze", "search_unavailable"}:
        tags.append("small_issue")
    if kind == "ambiguous":
        tags.append("insufficient_context")

    return text, tags


def main():
    rng = random.Random(SEED)
    records = []

    for behavior, count, kind, symptoms in BEHAVIORS:
        for index in range(count):
            text, tags = render(rng, behavior, kind, symptoms, index)
            created_at = datetime(2026, 8, 1) + timedelta(
                minutes=rng.randrange(60 * 24 * 60)
            )
            records.append({
                "text": text,
                "created_at": created_at.isoformat(),
                "behavior": behavior,
                "evidence_type": kind,
                "edge_tags": tags,
            })

    rng.shuffle(records)
    raw = []
    golden = []

    for index, record in enumerate(records, start=1):
        case_id = f"M1-{index:04d}"
        raw.append({
            "case_id": case_id,
            "created_at": record["created_at"],
            "text": record["text"],
        })
        golden.append({
            "case_id": case_id,
            "behavior": record["behavior"],
            "evidence_type": record["evidence_type"],
            "meaningful_failure": record["evidence_type"] == "reported_failure",
            "edge_tags": record["edge_tags"],
        })

    assert len(raw) == 1000
    assert len({row["case_id"] for row in raw}) == 1000
    assert all(set(row) == {"case_id", "created_at", "text"} for row in raw)

    output = Path("data/milestone1")
    if output.exists():
        raise SystemExit(
            "data/milestone1 already exists. Preserve or rename it before regenerating."
        )
    (output / "raw").mkdir(parents=True)
    (output / "golden").mkdir()

    raw_path = output / "raw/support_cases.jsonl"
    write_jsonl(raw_path, raw)
    write_jsonl(output / "golden/labels.jsonl", golden)

    manifest = {
        "seed": SEED,
        "generator_version": "1.1",
        "cases": len(raw),
        "behavior_counts": dict(Counter(row["behavior"] for row in golden)),
        "evidence_type_counts": dict(
            Counter(row["evidence_type"] for row in golden)
        ),
        "confusion_pairs": CONFUSION_PAIRS,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "limitations": [
            "Template-based synthetic data; not evidence of production performance.",
            "Shared descriptions can create wording-based clusters.",
            "Dates are random; this dataset does not test emergence.",
            "Evidence types are evaluation labels, not pipeline inputs.",
        ],
    }
    (output / "golden/manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(raw)} cases in {output}")
    print("\nEvidence types:")
    for kind, count in manifest["evidence_type_counts"].items():
        print(f"  {kind}: {count}")
    print("\nBehavior counts:")
    for behavior, count in manifest["behavior_counts"].items():
        print(f"  {behavior}: {count}")
    print("\nRaw cases contain only IDs, timestamps, and text.")
    print("Existing 500-case data and embeddings were not changed.")


if __name__ == "__main__":
    main()
