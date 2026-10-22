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

from deploy_backstop import ROOT

PROOF = ROOT / "deploy" / "proof.json"
JOURNAL = ROOT / "deploy" / "demo.json"

QA = ROOT / "deploy" / "browser-qa.json"
FLOW_QA = ROOT / "deploy" / "browser-flow-qa.json"


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
    browser_qa = json.loads(QA.read_text(encoding="utf-8"))
    flow_qa = json.loads(FLOW_QA.read_text(encoding="utf-8"))
    assert deployment["phase"] == "verified" and demo["phase"] == "verified"
    assert deployment["address"] == demo["contract"]
    assert browser_qa["contract"] == deployment["address"]
    assert flow_qa["contract"] == deployment["address"]
    assert flow_qa["source_commit"] == deployment["commit"]
    assert flow_qa["network"] == "studionet"
    assert browser_qa["method"] == "create_suite"
    assert browser_qa["status"] == "FINALIZED" and browser_qa["execution"] == "SUCCESS"
    assert browser_qa["value_wei"] == "0"
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

    def receipt(tx_hash: str) -> dict:
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
        receipt(entry["hash"])
        print("verified_transaction=" + label, flush=True)
    qa_receipt = receipt(browser_qa["transaction"])
    assert str(qa_receipt["value"]) == browser_qa["value_wei"]
    print("verified_transaction=browser_draft_create_suite", flush=True)
    expected_flow = {
        "create_suite": "create_suite",
        "validate_golden_0": "validate_golden",
        "validate_golden_1": "validate_golden",
        "open_suite": "open_suite",
        "submit_attack": "submit_attack",
        "judge_attack": "judge_attack",
        "propose_candidate": "propose_candidate",
        "check_exploit": "check_exploit",
        "check_golden_0": "check_golden",
        "check_golden_1": "check_golden",
        "certify_candidate": "certify_candidate",
    }
    assert tuple(flow_qa["transactions"]) == tuple(expected_flow)
    for label, entry in flow_qa["transactions"].items():
        assert entry["method"] == expected_flow[label], label
        assert entry["status"] == "FINALIZED" and entry["execution"] == "SUCCESS", label
        assert entry["value_wei"] == "0", label
        flow_receipt = receipt(entry["hash"])
        assert flow_receipt["to_address"].lower() == deployment["address"].lower(), label
        assert flow_receipt["from_address"].lower() == flow_qa["wallet"].lower(), label
        assert entry["sender"].lower() == flow_qa["wallet"].lower(), label
        assert str(flow_receipt["value"]) == entry["value_wei"], label
        assert entry["votes"], label
        assert flow_receipt.get("consensus_data", {}).get("votes", {}) == entry["votes"], label
        print("verified_transaction=browser_" + label, flush=True)

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
    qa_readback = browser_qa["readback"]
    qa_suite = read("get_suite", [qa_readback["suite_id"]])
    assert qa_suite["id"] == qa_readback["suite_id"]
    assert qa_suite["name"] == qa_readback["name"]
    assert qa_suite["terms_digest"] == qa_readback["terms_digest"]
    flow_suite = read("get_suite", [flow_qa["suite_id"]])
    flow_attack = read("get_attack", [flow_qa["attack_id"]])
    flow_candidate = read("get_candidate", [flow_qa["candidate_id"]])
    flow_active = read("get_active_policy", [flow_qa["suite_id"]])
    flow_readback = flow_qa["readback"]
    assert flow_suite["builder"].lower() == flow_qa["wallet"].lower()
    for field in ("status", "revision", "golden_validation", "regression_ids",
                  "active_candidate_id", "terms_digest"):
        recorded = flow_readback["suite_status"] if field == "status" else flow_readback[field]
        assert flow_suite[field] == recorded, field
    assert flow_attack["suite_id"] == flow_qa["suite_id"]
    assert flow_attack["status"] == flow_readback["attack_status"]
    assert flow_candidate["status"] == flow_readback["candidate_status"]
    assert flow_candidate["attack_checks"] == flow_readback["attack_checks"]
    assert flow_candidate["golden_checks"] == flow_readback["golden_checks"]
    assert flow_candidate["revision"] == flow_readback["revision"]
    assert flow_active == {"usable": flow_readback["active_policy_usable"],
                           "candidate_id": flow_qa["candidate_id"],
                           "revision": flow_readback["revision"],
                           "prompt": flow_candidate["prompt"]}
    print("verified_backstop_suite=" + suite_id, "contract=" + deployment["address"], flush=True)


if __name__ == "__main__":
    main()
