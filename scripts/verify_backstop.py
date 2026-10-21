"""Read-only verification of BACKSTOP's recorded Studionet deployment and demo."""

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
    assert deployment["phase"] == "verified" and demo["phase"] == "verified"
    assert deployment["address"] == demo["contract"]
    committed = subprocess.check_output(
        ["git", "show", deployment["commit"] + ":contracts/backstop.py"], cwd=ROOT
    )
    expected_digest = hashlib.sha256(committed).hexdigest()
    assert expected_digest == deployment["source_sha256"]
    client = create_client(chain=studionet, account=Account.create())
    encoded = retry(lambda: client.provider.make_request(
        method="gen_getContractCode", params=[deployment["address"]]
    ).get("result"))
    assert isinstance(encoded, str)
    deployed = base64.b64decode(encoded, validate=True)
    assert hashlib.sha256(deployed.replace(b"\r\n", b"\n")).hexdigest() == expected_digest

    def receipt(tx_hash: str) -> None:
        value = retry(lambda: client.wait_for_transaction_receipt(
            transaction_hash=tx_hash, status=TransactionStatus.FINALIZED,
            interval=3000, retries=3, full_transaction=True,
        ))
        assert (value.get("status_name") or value.get("statusName")) == "FINALIZED"
        assert tx_execution_succeeded(value)

    receipt(deployment["deploy_tx"])
    for label, entry in demo["transactions"].items():
        assert entry["phase"] == "checked", label
        assert entry["status"] == "FINALIZED" and entry["execution"] == "SUCCESS", label
        receipt(entry["hash"])
        print("verified_transaction=" + label, flush=True)

    def read(method: str, args: list):
        return retry(lambda: client.read_contract(
            address=deployment["address"], function_name=method, args=args,
            transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
        ))

    config = read("get_config", [])
    assert config == deployment["config"]
    suite_id = demo["suite_id"]
    suite = read("get_suite", [suite_id])
    attack_1, attack_2 = demo["attack_1"], demo["attack_2"]
    partial, final = demo["partial_candidate"], demo["final_candidate"]
    assert suite["status"] == "CERTIFIED" and suite["revision"] == 2
    assert suite["regression_ids"] == [attack_1, attack_2]
    assert suite["active_candidate_id"] == final
    for attack_id in (attack_1, attack_2):
        assert read("get_attack", [attack_id])["status"] == "BROKEN"
    first = read("get_candidate", [partial])
    assert first["status"] == "CERTIFIED" and first["revision"] == 1
    assert first["golden_checks"] == ["PASS", "PASS"]
    assert first["attack_checks"][attack_1] == "PASS"
    if demo.get("unexpected_attempt"):
        failed = read("get_candidate", [demo["unexpected_attempt"]["candidate"]])
        assert failed["revision"] == 2 and failed["golden_checks"][0] == "FAIL"
        assert failed["attack_checks"] == {attack_1: "PASS", attack_2: "PASS"}
    second = read("get_candidate", [final])
    assert second["status"] == "CERTIFIED" and second["revision"] == 2
    assert second["golden_checks"] == ["PASS", "PASS"]
    assert second["attack_checks"] == {attack_1: "PASS", attack_2: "PASS"}
    active = read("get_active_policy", [suite_id])
    assert active == {"usable": True, "candidate_id": final,
                      "revision": 2, "prompt": second["prompt"]}
    print("verified_backstop_suite=" + suite_id, "contract=" + deployment["address"], flush=True)


if __name__ == "__main__":
    main()
