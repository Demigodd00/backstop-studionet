import assert from "node:assert/strict";
import test from "node:test";
import { assertSuccessfulExecution, transactionStatus } from "../src/lib/backstop.ts";

test("requires finalized successful GenLayer execution", () => {
  const success = { status_name: "FINALIZED", consensus_data: { leader_receipt: [{ execution_result: "SUCCESS", result: { status: "return" } }] } };
  assert.equal(transactionStatus(success), "FINALIZED");
  assert.doesNotThrow(() => assertSuccessfulExecution(success));
  assert.throws(() => assertSuccessfulExecution({ ...success, status_name: "ACCEPTED" }), /not finalized/);
  assert.throws(() => assertSuccessfulExecution({ status_name: "FINALIZED", consensus_data: { leader_receipt: [{ execution_result: "ERROR", result: { status: "error", payload: "Agent failed" } }] } }), /Agent failed/);
});
