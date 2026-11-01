#!/usr/bin/env python3
"""Minimal offline Surfpool RPC harness for retained original Solana binaries."""
from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path

from solders.account import Account
from solders.hash import Hash
from solders.litesvm import LiteSVM
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.transaction import Transaction

ROOT = Path(__file__).resolve().parents[3]
BPF_LOADER_2 = "BPFLoader2111111111111111111111111111111111"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def original(program: str) -> Path:
    if program == "donation_relay":
        return ROOT / "evidence/dependencies/donation_relay/deployed.so"
    return ROOT / f"evidence/original/{program}/deployed.so"


def dependency(name: str) -> Path:
    return ROOT / f"evidence/dependencies/{name}/deployed.so"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def elf_image(path: Path) -> bytes:
    blob = path.read_bytes()
    extent = (struct.unpack_from("<Q", blob, 40)[0]
              + struct.unpack_from("<H", blob, 58)[0]
              * struct.unpack_from("<H", blob, 60)[0])
    if any(blob[extent:]):
        raise ValueError(f"nonzero bytes after ELF section table: {path}")
    return blob[:extent]


def account_json(account: Account) -> dict:
    return {
        "lamports": account.lamports,
        "data": bytes(account.data).hex(),
        "owner": str(account.owner),
        "executable": account.executable,
    }


class Surfpool:
    """Owns one foreground child process and terminates it on every exit path."""

    def __init__(self, workdir: Path, port: int | None = None,
                 binary: Path | None = None):
        self.workdir = workdir.resolve()
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.port = port or free_port()
        self.binary = (binary or Path("surfpool")).resolve() if binary else Path("surfpool")
        self.process = None
        self.log = None
        self.loaded_programs = {}

    def rpc(self, method: str, params=None, timeout: int = 60):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                             "params": params or []}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.load(response)
        if "error" in result:
            raise RuntimeError({"method": method, "error": result["error"]})
        return result["result"]

    def __enter__(self):
        log_path = self.workdir / f"surfpool-{self.port}.log"
        self.log = log_path.open("w")
        command = [str(self.binary), "start", "--offline", "--no-deploy", "--no-tui",
                   "--no-studio", "--host", "127.0.0.1", "--port", str(self.port),
                   "--ws-port", str(self.port + 1), "--airdrop-amount", "0",
                   "--db", ":memory:", "--log-bytes-limit", "0"]
        self.process = subprocess.Popen(command, cwd=self.workdir, stdout=self.log,
                                        stderr=subprocess.STDOUT)
        for _ in range(150):
            if self.process.poll() is not None:
                raise RuntimeError(f"Surfpool exited during startup; see {log_path}")
            try:
                if self.rpc("getHealth", timeout=2) == "ok":
                    return self
            except (OSError, RuntimeError):
                pass
            time.sleep(0.1)
        raise TimeoutError(f"Surfpool startup; see {log_path}")

    def __exit__(self, exc_type, exc, tb):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        if self.log is not None:
            self.log.close()

    def set_account(self, address: Pubkey | str, value: dict | Account):
        self.rpc("surfnet_setAccount", [str(address),
                 account_json(value) if isinstance(value, Account) else value])

    def load_program(self, address: Pubkey | str, path: Path):
        path = path.resolve()
        digest = sha256(path)
        self.rpc("surfnet_setAccount", [str(address), {
            "lamports": 10**10, "data": elf_image(path).hex(),
            "owner": BPF_LOADER_2, "executable": True}])
        self.loaded_programs[str(address)] = {"path": str(path), "sha256": digest}

    def get_account(self, address: Pubkey | str):
        value = self.rpc("getAccountInfo", [str(address), {"encoding": "base64"}])["value"]
        if value is None:
            return None
        raw = base64.b64decode(value["data"][0])
        return {"lamports": value["lamports"], "owner": value["owner"],
                "executable": value["executable"], "data": raw.hex(),
                "data_sha256": hashlib.sha256(raw).hexdigest()}

    def latest_blockhash(self) -> Hash:
        return Hash.from_string(self.rpc("getLatestBlockhash")["value"]["blockhash"])

    def simulate(self, transaction: Transaction, sig_verify: bool = True):
        encoded = base64.b64encode(bytes(transaction)).decode()
        return self.rpc("simulateTransaction", [encoded, {
            "encoding": "base64", "sigVerify": sig_verify,
            "innerInstructions": True}])["value"]

    def send(self, transaction: Transaction):
        if not all(transaction.verify_with_results()):
            raise ValueError("transaction signature verification failed")
        simulation = self.simulate(transaction, sig_verify=True)
        encoded = base64.b64encode(bytes(transaction)).decode()
        signature = self.rpc("sendTransaction", [encoded, {
            "encoding": "base64", "skipPreflight": True}])
        status = None
        for _ in range(150):
            status = self.rpc("getSignatureStatuses", [[signature]])["value"][0]
            if status is not None:
                break
            time.sleep(0.05)
        if status is None:
            raise TimeoutError("transaction confirmation")
        if simulation.get("err") != status.get("err"):
            raise AssertionError({"simulation": simulation.get("err"),
                                  "committed": status.get("err")})
        return {"signature": signature, "error": status.get("err"),
                "logs": simulation.get("logs", []),
                "return_data": simulation.get("returnData"),
                "simulation": simulation, "signature_verification": True}


class RecordingVM:
    """Capture LiteSVM fixture setup and its transaction for Surfpool replay."""

    def __init__(self):
        self.vm = LiteSVM()
        self.accounts = {}
        self.transaction = None

    def __getattr__(self, name):
        return getattr(self.vm, name)

    def with_sigverify(self, enabled):
        if not enabled:
            raise ValueError("recorded Surfpool fixtures require genuine signatures")
        self.vm = self.vm.with_sigverify(True)
        return self

    def with_transaction_history(self, capacity):
        self.vm = self.vm.with_transaction_history(capacity)
        return self

    def with_blockhash_check(self, enabled):
        self.vm = self.vm.with_blockhash_check(enabled)
        return self

    def with_log_bytes_limit(self, limit):
        self.vm = self.vm.with_log_bytes_limit(limit)
        return self

    def set_account(self, address, account):
        self.accounts[str(address)] = account_json(account)
        return self.vm.set_account(address, account)

    def airdrop(self, address, lamports):
        result = self.vm.airdrop(address, lamports)
        self.accounts[str(address)] = account_json(self.vm.get_account(address))
        return result

    def send_transaction(self, transaction):
        self.transaction = transaction
        for address in transaction.message.account_keys:
            if str(address) in self.accounts:
                continue
            value = self.vm.get_account(address)
            if value is not None and value.executable:
                continue
            self.accounts[str(address)] = (account_json(value) if value is not None else {
                "lamports": 0, "data": "", "owner": str(Pubkey.default()),
                "executable": False})
        return self.vm.send_transaction(transaction)


def install_fixture(pool: Surfpool, fixture: RecordingVM):
    for address, value in fixture.accounts.items():
        pool.set_account(address, value)


def resign(transaction: Transaction, payer: Pubkey, signers, blockhash: Hash) -> Transaction:
    message = transaction.message
    header, keys = message.header, message.account_keys
    def writable(index):
        if index < header.num_required_signatures:
            return index < header.num_required_signatures - header.num_readonly_signed_accounts
        return index < len(keys) - header.num_readonly_unsigned_accounts
    instructions = [Instruction(keys[ix.program_id_index], bytes(ix.data),
        [AccountMeta(keys[n], n < header.num_required_signatures, writable(n))
         for n in ix.accounts]) for ix in message.instructions]
    return Transaction.new_signed_with_payer(instructions, payer, signers, blockhash)
