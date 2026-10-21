"""Deploy a pinned BACKSTOP source on Studionet and verify final execution.

The journal is saved before broadcast. If interrupted without a recorded hash,
inspect the chain before attempting another deployment.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from eth_account import Account
from genlayer_py import create_client
from genlayer_py.assertions import tx_execution_succeeded
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionHashVariant, TransactionStatus


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "contracts" / "backstop.py"
PROOF = ROOT / "deploy" / "proof.json"
KEY = Path.home() / ".codex" / "private" / "backstop_studionet_deployer.json"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def save(record: dict) -> None:
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    record["updated_at"] = datetime.now(timezone.utc).isoformat()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=PROOF.parent,
                                     prefix="backstop-", suffix=".tmp", delete=False) as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
        staged = Path(handle.name)
    staged.replace(PROOF)


def signer():
    if not KEY.exists():
        KEY.parent.mkdir(parents=True, exist_ok=True)
        account = Account.create()
        with KEY.open("x", encoding="utf-8") as handle:
            json.dump({"private_key": account.key.hex()}, handle)
    return Account.from_key(json.loads(KEY.read_text(encoding="utf-8"))["private_key"])


def source_from_pushed_commit() -> tuple[str, bytes, str]:
    if git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("tracked source has local edits; commit and push first")
    commit = git("rev-parse", "HEAD")
    if git("rev-parse", "origin/main") != commit:
        raise RuntimeError("local HEAD differs from origin/main; push first")
    source = SOURCE.read_bytes()
    committed = subprocess.check_output(["git", "show", "HEAD:contracts/backstop.py"], cwd=ROOT)
    if source.replace(b"\r\n", b"\n") != committed:
        raise RuntimeError("contract source differs from pushed Git blob")
    return commit, source, git("rev-parse", "HEAD:contracts/backstop.py")


def verify_receipt(client, record: dict, account) -> None:
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=record["deploy_tx"], status=TransactionStatus.FINALIZED,
        interval=3000, retries=120, full_transaction=True,
    )
    status = receipt.get("status_name") or receipt.get("statusName")
    record["receipt_status"] = status
    record["execution_result"] = "SUCCESS" if tx_execution_succeeded(receipt) else "ERROR"
    consensus = receipt.get("consensus_data") or receipt.get("consensusData") or {}
    record["votes"] = consensus.get("votes", {})
    record["consensus_result"] = receipt.get("result_name") or receipt.get("resultName")
    save(record)
    if status != TransactionStatus.FINALIZED.value or not tx_execution_succeeded(receipt):
        raise RuntimeError("deployment did not finalize with successful execution")
    address = None
    for key in ("tx_data_decoded", "data"):
        item = receipt.get(key)
        if isinstance(item, dict) and item.get("contract_address"):
            address = str(item["contract_address"])
            break
    if not address or len(address) != 42 or not address.startswith("0x"):
        raise RuntimeError("finalized receipt has no contract address")
    encoded = client.provider.make_request(method="gen_getContractCode", params=[address]).get("result")
    if not isinstance(encoded, str):
        raise RuntimeError("deployed source unavailable")
    deployed = base64.b64decode(encoded, validate=True)
    if digest(deployed) != record["source_sha256"]:
        raise RuntimeError("deployed source differs from pushed contract blob")
    config = client.read_contract(
        address=address, function_name="get_config", args=[], account=account,
        transaction_hash_variant=TransactionHashVariant.LATEST_FINAL,
    )
    if not isinstance(config, dict) or config.get("version") != "0.1.0" or config.get("max_regressions") != 4:
        raise RuntimeError("deployed configuration differs from BACKSTOP source")
    record.update(address=address, config=config, deployed_source_verified=True, phase="verified")
    save(record)
    print("verified_contract=" + address, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deploy", action="store_true", help="broadcast one deployment")
    args = parser.parse_args()
    commit, source, blob = source_from_pushed_commit()
    print("commit=" + commit, "blob=" + blob, flush=True)
    if PROOF.exists():
        record = json.loads(PROOF.read_text(encoding="utf-8"))
        if record.get("commit") != commit or record.get("source_sha256") != digest(source):
            raise RuntimeError("saved deployment journal does not match this source")
        if record.get("phase") == "verified":
            print("verified_contract=" + record["address"], flush=True)
            return
        if not record.get("deploy_tx"):
            raise RuntimeError("broadcast outcome uncertain; inspect account history before retrying")
    elif args.deploy:
        account = signer()
        record = {
            "project": "BACKSTOP", "network": "studionet", "commit": commit,
            "contract_blob": blob, "source_sha256": digest(source),
            "runner_dependency": source.decode("utf-8").splitlines()[0],
            "toolchain": {"genlayer_py": "0.16.3"}, "constructor_args": [],
            "deployer": account.address, "phase": "broadcasting", "deploy_tx": "",
        }
        save(record)
        client = create_client(chain=studionet, account=account)
        record["deploy_tx"] = str(client.deploy_contract(code=source.decode("utf-8"), account=account, args=[]))
        record["phase"] = "submitted"
        save(record)
        print("deploy_tx=" + record["deploy_tx"], flush=True)
    else:
        print("preflight passed; use --deploy to broadcast", flush=True)
        return
    account = signer()
    client = create_client(chain=studionet, account=account)
    verify_receipt(client, record, account)


if __name__ == "__main__":
    main()
