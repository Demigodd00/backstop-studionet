"""Record the human-approved public-browser BACKSTOP flow from finalized Studionet reads."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from eth_account import Account
from genlayer_py import create_client
from genlayer_py.assertions import tx_execution_succeeded
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant, TransactionStatus

from deploy_backstop import PROOF, ROOT


TRANSACTIONS = [
    ("create_suite", "create_suite", "0x7df95462f0569f4ca985be36a7a41551bc616a33a1cc731b35a1c2fde16c3349"),
    ("validate_golden_0", "validate_golden", "0x0f07f3ed80c23e31c6416bec12ff96234bf438f04a5bfa0be4ad76755a046d33"),
    ("validate_golden_1", "validate_golden", "0xab99c228cfc5182989a4aa168dec4638b586e62a5f9a100ec3fda0cd4c24c779"),
    ("open_suite", "open_suite", "0x05bb508c064ae18f1f95b9c424b9d24e707ee14e80fcdbcc0f22185ed733c363"),
    ("submit_attack", "submit_attack", "0x5579f5853f838792f33fb0ddc4c3847df526dc3dd4e219412dcfbe987086fc59"),
    ("judge_attack", "judge_attack", "0x82e566d72bb24d7236d5fe55881e9287393b42695f6c2e9fc1b21e9854224455"),
    ("propose_candidate", "propose_candidate", "0x40d1d7642743a8281a8298534d39bea09e5237d1c9f44b979f106fd19734cf2b"),
    ("check_exploit", "check_exploit", "0xe8289e23ee32c7aa739dd3acc71a7df4ed2e5ffb374d5cfd5b48b876e49e7ce9"),
    ("check_golden_0", "check_golden", "0x6e3a8a3e59cf6ee51808a8d4446ce5f4a266cfb591107600a95350af3f6a0da8"),
    ("check_golden_1", "check_golden", "0x3baa62fa9ba6aec9be5d5c15ade60c6813f94a7ea7a841a3bb73fbdb598ea4a2"),
    ("certify_candidate", "certify_candidate", "0x793509d0d92c2ec3e024e0139c36a0f42622bb9ca6c0852b495a4a54f26b5947"),
]


def main() -> None:
    deployment = json.loads(PROOF.read_text(encoding="utf-8"))
    address = deployment["address"]
    client = create_client(chain=studionet, account=Account.create())
    records = {}
    wallet = ""
    for label, method, tx_hash in TRANSACTIONS:
        receipt = client.wait_for_transaction_receipt(
            transaction_hash=tx_hash, status=TransactionStatus.FINALIZED,
            interval=3000, retries=3, full_transaction=True,
        )
        assert (receipt.get("status_name") or receipt.get("statusName")) == "FINALIZED", label
        assert tx_execution_succeeded(receipt), label
        assert receipt["to_address"].lower() == address.lower(), label
        assert int(receipt["value"]) == 0, label
        sender = receipt["from_address"]
        if not wallet:
            wallet = sender
        assert sender.lower() == wallet.lower(), label
        records[label] = {
            "method": method,
            "hash": tx_hash,
            "sender": sender,
            "status": "FINALIZED",
            "execution": "SUCCESS",
            "value_wei": "0",
            "votes": receipt.get("consensus_data", {}).get("votes", {}),
        }
        print("recorded_browser_transaction=" + label, flush=True)

    def read(method: str, args: list):
        return client.read_contract(
            address=address, function_name=method, args=args,
            transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
        )

    suite = read("get_suite", ["bs-3"])
    attack = read("get_attack", ["atk-3"])
    candidate = read("get_candidate", ["cand-4"])
    active = read("get_active_policy", ["bs-3"])
    assert suite["builder"].lower() == wallet.lower()
    assert suite["status"] == "CERTIFIED" and suite["revision"] == 1
    assert suite["golden_validation"] == ["VALID", "VALID"]
    assert suite["regression_ids"] == ["atk-3"]
    assert suite["active_candidate_id"] == "cand-4"
    assert attack["status"] == "BROKEN" and attack["suite_id"] == "bs-3"
    assert candidate["status"] == "CERTIFIED" and candidate["revision"] == 1
    assert candidate["attack_checks"] == {"atk-3": "PASS"}
    assert candidate["golden_checks"] == ["PASS", "PASS"]
    assert active == {"usable": True, "candidate_id": "cand-4", "revision": 1,
                      "prompt": candidate["prompt"]}

    record = {
        "network": "studionet",
        "frontend": "https://demigodd00.github.io/backstop-studionet/?suite=bs-3#registry",
        "contract": address,
        "source_commit": deployment["commit"],
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Eleven user-approved, zero-deposit browser-wallet writes from creation through certification; public synthetic agent policy and attack.",
        "wallet": wallet,
        "suite_id": "bs-3",
        "attack_id": "atk-3",
        "candidate_id": "cand-4",
        "transactions": records,
        "readback": {
            "suite_status": suite["status"],
            "revision": suite["revision"],
            "golden_validation": suite["golden_validation"],
            "regression_ids": suite["regression_ids"],
            "active_candidate_id": suite["active_candidate_id"],
            "terms_digest": suite["terms_digest"],
            "attack_status": attack["status"],
            "candidate_status": candidate["status"],
            "attack_checks": candidate["attack_checks"],
            "golden_checks": candidate["golden_checks"],
            "active_policy_usable": active["usable"],
        },
    }
    destination = ROOT / "deploy" / "browser-flow-qa.json"
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("recorded_browser_flow=" + str(destination), flush=True)


if __name__ == "__main__":
    main()
