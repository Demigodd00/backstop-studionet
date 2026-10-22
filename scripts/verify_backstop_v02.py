"""Read-only verification of BACKSTOP v0.2 source, receipts, and recovery demo."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import time

from eth_account import Account
from genlayer_py import create_client
from genlayer_py.assertions import tx_execution_succeeded
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant, TransactionStatus

from deploy_backstop import PROOF, ROOT
from demo_backstop import JOURNAL


def retry(fn):
    for attempt in range(3):
        try:
            return fn()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def main() -> None:
    deployment = json.loads(PROOF.read_text(encoding="utf-8"))
    demo = json.loads(JOURNAL.read_text(encoding="utf-8"))
    assert deployment["phase"] == "verified"
    assert demo["phase"] == "verified"
    assert deployment["address"] == demo["contract"]
    assert deployment["commit"] == demo["source_commit"]
    source = subprocess.check_output(
        ["git", "show", deployment["commit"] + ":contracts/backstop.py"], cwd=ROOT,
    )
    assert hashlib.sha256(source).hexdigest() == deployment["source_sha256"]
    assert subprocess.check_output(
        ["git", "rev-parse", deployment["commit"] + ":contracts/backstop.py"], cwd=ROOT, text=True,
    ).strip() == deployment["contract_blob"]

    client = create_client(chain=studionet, account=Account.create())
    encoded = retry(lambda: client.provider.make_request(
        method="gen_getContractCode", params=[deployment["address"]],
    ).get("result"))
    assert isinstance(encoded, str)
    deployed = base64.b64decode(encoded, validate=True)
    assert hashlib.sha256(deployed.replace(b"\r\n", b"\n")).hexdigest() == deployment["source_sha256"]

    def receipt(tx_hash: str):
        value = retry(lambda: client.wait_for_transaction_receipt(
            transaction_hash=tx_hash, status=TransactionStatus.FINALIZED,
            interval=3000, retries=3, full_transaction=True,
        ))
        assert (value.get("status_name") or value.get("statusName")) == "FINALIZED"
        assert tx_execution_succeeded(value)
        return value

    receipt(deployment["deploy_tx"])
    for label, entry in demo["transactions"].items():
        assert entry["phase"] == "checked", label
        assert entry["status"] == "FINALIZED" and entry["execution"] == "SUCCESS", label
        value = receipt(entry["hash"])
        assert value["to_address"].lower() == deployment["address"].lower(), label
        assert value["from_address"].lower() == entry["sender"].lower(), label
        assert value.get("consensus_data", {}).get("votes", {}) == entry["votes"], label
        print("verified_transaction=" + label, flush=True)

    def read(method: str, args: list):
        return retry(lambda: client.read_contract(
            address=deployment["address"], function_name=method, args=args,
            transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
        ))

    assert read("get_config", []) == deployment["config"]
    suite_id = demo["suite_id"]
    suite = read("get_suite", [suite_id])
    assert suite["status"] == "CERTIFIED" and suite["revision"] == 2
    assert suite["regression_ids"] == [demo["attack_1"], demo["attack_2"]]
    assert suite["candidate_total"] >= 9
    assert len(suite["candidate_ids"]) == 8
    history = read("list_candidate_history", [suite_id, 0, 20])
    assert history["total"] == suite["candidate_total"]
    assert history["items"][:9] == (
        [demo["partial_candidate"]] + demo["outsider_candidates"]
        + [demo["initial_repair_candidate"]]
    )
    assert len(demo["outsider_candidates"]) == 7
    assert all(read("get_candidate", [id_])["author"].lower() == demo["hunter"].lower()
               for id_ in demo["outsider_candidates"])
    final = read("get_candidate", [demo["final_candidate"]])
    assert final["status"] == "CERTIFIED"
    assert final["author"].lower() == demo["builder"].lower()
    assert final["golden_checks"] == ["PASS", "PASS"]
    assert final["attack_checks"] == {demo["attack_1"]: "PASS", demo["attack_2"]: "PASS"}
    active = read("get_active_policy", [suite_id])
    assert active == {"usable": True, "candidate_id": final["id"],
                      "revision": 2, "prompt": final["prompt"]}
    print("verified_backstop_v02_suite=" + suite_id, "contract=" + deployment["address"], flush=True)


if __name__ == "__main__":
    main()
