import { chains, createClient } from "genlayer-js";
import { TransactionHashVariant, TransactionStatus } from "genlayer-js/types";

export interface Provider {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>;
  on?(event: string, listener: (...args: unknown[]) => void): void;
  removeListener?(event: string, listener: (...args: unknown[]) => void): void;
}

export interface WalletSession {
  address: string;
  provider: Provider;
  client: ReturnType<typeof createClient>;
}

export interface GoldenCase { task: string; rubric: string; expected_tool: string }
export interface SuiteSummary {
  id: string; name: string; builder: string; status: string; revision: number | string;
  regressions: number | string; active_candidate_id: string;
}
export interface Suite extends Omit<SuiteSummary, "regressions"> {
  base_prompt: string; allowed_tools: string[]; max_amount: number | string;
  goldens: GoldenCase[]; golden_validation: string[]; created_at: number | string;
  opened_at: number | string; attack_deadline: number | string;
  challenge_duration_secs: number | string; attack_ids: string[]; regression_ids: string[];
  candidate_ids: string[]; certified_revision: number | string; terms_digest: string;
}
export interface Attack {
  id: string; suite_id: string; hunter: string; message: string; message_digest: string;
  target_prompt_digest: string; status: string; submitted_at: number | string;
  expires_at: number | string; judged_at: number | string;
}
export interface Candidate {
  id: string; suite_id: string; author: string; prompt: string; prompt_digest: string;
  revision: number | string; regression_ids: string[]; attack_checks: Record<string, string>;
  golden_checks: string[]; status: string; created_at: number | string;
  expires_at: number | string; certified_at: number | string;
}
export interface ActivePolicy { usable: boolean; candidate_id: string; revision: number | string; prompt: string }

export const CONTRACT_ADDRESS = process.env.NEXT_PUBLIC_BACKSTOP_ADDRESS ?? "";
export const CONTRACT_READY = /^0x[0-9a-fA-F]{40}$/.test(CONTRACT_ADDRESS) && !/^0x0{40}$/i.test(CONTRACT_ADDRESS);
export const EXPLORER = "https://explorer-studio.genlayer.com";
const readClient = createClient({ chain: chains.studionet });

function address(): string {
  if (!CONTRACT_READY) throw new Error("BACKSTOP has not been deployed to Studionet yet.");
  return CONTRACT_ADDRESS;
}

export function short(value: string): string {
  return value.length > 15 ? `${value.slice(0, 7)}…${value.slice(-5)}` : value;
}

export function formatDate(value: number | string): string {
  const seconds = Number(value);
  if (!seconds || !Number.isFinite(seconds)) return "—";
  return new Date(seconds * 1000).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

async function read<T>(functionName: string, args: unknown[]): Promise<T> {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      return await readClient.readContract({
        address: address() as never, transactionHashVariant: TransactionHashVariant.LATEST_FINAL,
        functionName, args: args as never[],
      }) as T;
    } catch (error) {
      if (attempt === 2) throw error;
      await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)));
    }
  }
  throw new Error("Studionet read failed.");
}

export async function listSuites(): Promise<{ total: number; items: SuiteSummary[] }> {
  const first = await read<{ total: number | string; items: SuiteSummary[] }>("list_suites", [0, 20]);
  const total = Number(first.total);
  if (!Number.isSafeInteger(total) || total < 0 || total > 100 || !Array.isArray(first.items)) {
    throw new Error("Invalid suite list from Studionet.");
  }
  const items = [...first.items];
  for (let offset = 20; offset < total; offset += 20) {
    const page = await read<{ total: number | string; items: SuiteSummary[] }>("list_suites", [offset, 20]);
    if (Number(page.total) !== total || !Array.isArray(page.items)) throw new Error("Suite list changed during the finalized read.");
    items.push(...page.items);
  }
  return { total, items };
}
export const getSuite = (id: string) => read<Suite>("get_suite", [id]);
export const getAttack = (id: string) => read<Attack>("get_attack", [id]);
export const getCandidate = (id: string) => read<Candidate>("get_candidate", [id]);
export const getActivePolicy = (id: string) => read<ActivePolicy>("get_active_policy", [id]);

export async function connectWallet(provider: Provider): Promise<WalletSession> {
  const accounts = await provider.request({ method: "eth_requestAccounts" });
  if (!Array.isArray(accounts) || typeof accounts[0] !== "string" || !/^0x[0-9a-fA-F]{40}$/.test(accounts[0])) {
    throw new Error("The wallet did not return a valid account.");
  }
  const chain = chains.studionet;
  const chainId = `0x${chain.id.toString(16)}`;
  const currentChain = await provider.request({ method: "eth_chainId" });
  if (typeof currentChain !== "string" || BigInt(currentChain) !== BigInt(chain.id)) {
    try {
      await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId }] });
    } catch (error) {
      const code = error && typeof error === "object" && "code" in error ? (error as { code?: number }).code : undefined;
      if (code !== 4902) throw error;
      await provider.request({ method: "wallet_addEthereumChain", params: [{
        chainId, chainName: chain.name, rpcUrls: [...chain.rpcUrls.default.http],
        nativeCurrency: chain.nativeCurrency,
        ...(chain.blockExplorers?.default.url ? { blockExplorerUrls: [chain.blockExplorers.default.url] } : {}),
      }] });
      await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId }] });
    }
  }
  const activeAccounts = await provider.request({ method: "eth_accounts" });
  const activeChain = await provider.request({ method: "eth_chainId" });
  if (!Array.isArray(activeAccounts) || typeof activeAccounts[0] !== "string" ||
      typeof activeChain !== "string" || BigInt(activeChain) !== BigInt(chain.id)) {
    throw new Error("Connect a wallet on GenLayer Studionet.");
  }
  return { address: activeAccounts[0], provider, client: createClient({ chain, account: activeAccounts[0] as never, provider: provider as never }) };
}

interface Pending { hash: string; method: string; submittedAt: number }
function pendingKey(wallet: string): string { return `backstop:pending:61999:${CONTRACT_ADDRESS.toLowerCase()}:${wallet.toLowerCase()}`; }

export function getPending(wallet: string): Pending | null {
  if (typeof window === "undefined" || !CONTRACT_READY) return null;
  const raw = window.localStorage.getItem(pendingKey(wallet));
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Pending;
    if (/^0x[0-9a-fA-F]{64}$/.test(value.hash) && typeof value.method === "string") return value;
  } catch { /* Retain a corrupt journal as a write blocker. */ }
  throw new Error("Saved transaction data is unreadable. Inspect wallet activity before sending again.");
}

function object(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
export function transactionStatus(receipt: unknown): string {
  const tx = object(receipt);
  const status = tx.status_name ?? tx.statusName ?? tx.status;
  return typeof status === "string" ? status.toUpperCase() : "";
}
export function assertSuccessfulExecution(receipt: unknown): void {
  const tx = object(receipt);
  if (transactionStatus(receipt) !== TransactionStatus.FINALIZED) throw new Error("The transaction has not finalized.");
  const consensus = object(tx.consensus_data ?? tx.consensusData);
  const leaders = consensus.leader_receipt ?? consensus.leaderReceipt;
  const leader = object(Array.isArray(leaders) ? leaders[0] : leaders);
  const result = object(leader.result);
  const vm = object(leader.genvm_result ?? leader.genvmResult);
  const execution = leader.execution_result ?? leader.executionResult;
  const failed = Boolean(tx.error || vm.error_code || vm.error_description) || result.status === "rollback" || result.status === "error";
  if (!failed && (execution === "SUCCESS" || (execution === undefined && tx.txExecutionResultName === "FINISHED_WITH_RETURN"))) return;
  const payload = result.payload;
  const candidates = [typeof payload === "string" ? payload : object(payload).readable, vm.error_description,
    typeof tx.error === "string" ? tx.error : object(tx.error).message];
  const reason = candidates.find((item) => typeof item === "string" && item.trim());
  throw new Error(typeof reason === "string" ? reason : "GenLayer did not confirm successful execution.");
}

export async function writeContract(session: WalletSession, functionName: string, args: unknown[],
  onSubmitted?: (hash: string) => void): Promise<string> {
  if (!navigator.locks) throw new Error("Safe submission requires a modern browser on HTTPS or localhost.");
  return navigator.locks.request(pendingKey(session.address), { ifAvailable: true }, async (lock) => {
    if (!lock) throw new Error("Another tab is sending from this wallet.");
    const accounts = await session.provider.request({ method: "eth_accounts" });
    const chainId = await session.provider.request({ method: "eth_chainId" });
    if (!Array.isArray(accounts) || String(accounts[0] ?? "").toLowerCase() !== session.address.toLowerCase() ||
        typeof chainId !== "string" || BigInt(chainId) !== BigInt(chains.studionet.id)) {
      throw new Error("The active wallet or network changed. Reconnect before signing.");
    }
    if (getPending(session.address)) throw new Error("A transaction is saved for this wallet. Check it before sending another.");
    const probe = `${pendingKey(session.address)}:probe`;
    try {
      window.localStorage.setItem(probe, "1");
      if (window.localStorage.getItem(probe) !== "1") throw new Error("Storage unavailable");
      window.localStorage.removeItem(probe);
    } catch { throw new Error("Enable browser storage so BACKSTOP can recover a pending transaction."); }
    const hash = await session.client.writeContract({ address: address() as never, functionName, args: args as never[], value: 0n });
    const txHash = String(hash);
    window.localStorage.setItem(pendingKey(session.address), JSON.stringify({ hash: txHash, method: functionName, submittedAt: Date.now() }));
    onSubmitted?.(txHash);
    const receipt = await readClient.waitForTransactionReceipt({ hash: hash as never, status: TransactionStatus.FINALIZED, retries: 120 });
    if (transactionStatus(receipt) !== TransactionStatus.FINALIZED) throw new Error("Transaction pending. Check the saved hash before sending another.");
    try { assertSuccessfulExecution(receipt); }
    finally { window.localStorage.removeItem(pendingKey(session.address)); }
    return txHash;
  });
}

export async function reconcilePending(session: WalletSession): Promise<{ done: boolean; message: string; hash?: string }> {
  const pending = getPending(session.address);
  if (!pending) return { done: true, message: "No pending transaction is saved." };
  const receipt = await readClient.getTransaction({ hash: pending.hash as never });
  const status = transactionStatus(receipt);
  if (["UNDETERMINED", "CANCELED", "CANCELLED"].includes(status)) {
    window.localStorage.removeItem(pendingKey(session.address));
    return { done: true, message: `Transaction ended without successful execution (${status}).`, hash: pending.hash };
  }
  if (status !== TransactionStatus.FINALIZED) return { done: false, message: `Transaction is ${status || "pending"}.`, hash: pending.hash };
  try { assertSuccessfulExecution(receipt); return { done: true, message: "Saved transaction finalized successfully.", hash: pending.hash }; }
  catch (error) { return { done: true, message: error instanceof Error ? error.message : "Finalized execution failed.", hash: pending.hash }; }
  finally { window.localStorage.removeItem(pendingKey(session.address)); }
}
