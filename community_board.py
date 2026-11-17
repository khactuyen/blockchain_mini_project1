"""Interact with CommunityProposalBoard on local Ganache; no private keys needed."""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from web3 import Web3

ROOT = Path(__file__).resolve().parent
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:7545")


def connect(config_path, rpc_url=None, contract_address=None):
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("Missing deployment.json. Run npm run deploy first.") from exc
    url = rpc_url or config.get("rpcUrl", RPC_URL)
    if urlparse(url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Use a local Ganache RPC URL only.")
    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to Ganache at {url}. Is Ganache running?")
    if not any(name in w3.client_version.lower() for name in ("ganache", "testrpc")):
        raise ValueError("The connected client is not Ganache.")
    address = contract_address or config.get("address", "")
    if not Web3.is_address(address):
        raise ValueError("Provide a valid deployed contract address.")
    if w3.eth.chain_id != int(config["chainId"]):
        raise ValueError("Chain ID differs from deployment.json. Check the network or deploy again.")
    abi = config.get("abi")
    if not isinstance(abi, list):
        raise ValueError("The deployment ABI must be a JSON array.")
    address = Web3.to_checksum_address(address)
    if not w3.eth.get_code(address):
        raise ValueError("No contract code at this address. If Ganache restarted, deploy again.")
    contract = w3.eth.contract(address=address, abi=abi)
    contract.functions.proposalCount().call()  # Verify the expected interface.
    print("Connected to Ganache and CommunityProposalBoard!")
    print("Chain ID:", w3.eth.chain_id)
    print("Contract:", address)
    print("Available unlocked accounts:", list(w3.eth.accounts))
    return w3, contract


def send(w3, function, account):
    tx_hash = function.transact({"from": account})
    print("Pending transaction:", Web3.to_hex(tx_hash))
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status != 1:
        raise RuntimeError("Transaction reverted.")
    print(f"Confirmed in block {receipt.blockNumber}; gas used: {receipt.gasUsed}")
    return receipt


def show(contract, proposal_id):
    proposal = contract.functions.getProposal(proposal_id).call()
    print(json.dumps(dict(zip(("id", "author", "title", "description", "endorsementCount", "closed"), proposal)), ensure_ascii=False, indent=2))


def demo(w3, contract):
    accounts = w3.eth.accounts
    if len(accounts) < 3:
        raise ValueError("Demo needs three unlocked Ganache test accounts.")
    author, supporter, newcomer = accounts[:3]
    receipt = send(w3, contract.functions.createProposal("Plant trees in our park", "Add shade and improve our shared green space."), author)
    proposal_id = contract.events.ProposalCreated().process_receipt(receipt)[0]["args"]["proposalId"]
    send(w3, contract.functions.endorseProposal(proposal_id), supporter)

    def reject(label, function, account):
        # eth_call executes contract rules without spending gas or modifying state.
        # Catch contract reverts only: network failures must fail the demo.
        from web3.exceptions import Web3Exception
        try:
            function.call({"from": account})
        except (Web3Exception, ValueError) as exc:
            message = str(exc)
            if "revert" not in message.lower():
                raise
            print(f"EXPECTED REJECTION ({label}): {message}")
        else:
            raise AssertionError(f"Invalid action unexpectedly accepted: {label}")

    reject("duplicate endorsement", contract.functions.endorseProposal(proposal_id), supporter)
    reject("self endorsement", contract.functions.endorseProposal(proposal_id), author)
    reject("unauthorized close", contract.functions.closeProposal(proposal_id), supporter)
    send(w3, contract.functions.closeProposal(proposal_id), author)
    reject("endorsement after closure", contract.functions.endorseProposal(proposal_id), newcomer)
    proposal = contract.functions.getProposal(proposal_id).call()
    assert proposal[4] == 1 and proposal[5] is True
    show(contract, proposal_id)
    print("Demo passed: successful transactions and contract-enforced rejections.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="info", choices=["info", "list", "create", "endorse", "close", "demo"])
    parser.add_argument("--config", type=Path, default=ROOT / "deployment.json")
    parser.add_argument("--rpc", default=os.getenv("RPC_URL"))
    parser.add_argument("--address", default=os.getenv("CONTRACT_ADDRESS"))
    parser.add_argument("--account", type=int, default=0, help="Index of unlocked Ganache test account")
    parser.add_argument("--id", type=int, help="Proposal ID (starts at 0)")
    parser.add_argument("--title")
    parser.add_argument("--description")
    args = parser.parse_args()
    if args.command in {"endorse", "close"} and (args.id is None or args.id < 0):
        parser.error("--id must be a non-negative proposal ID")
    if args.command == "create" and (not args.title or not args.description):
        parser.error("create requires --title and --description")
    w3, contract = connect(args.config, args.rpc, args.address)
    if args.command == "info":
        print("Proposal count:", contract.functions.proposalCount().call())
    elif args.command == "list":
        for proposal_id in range(contract.functions.proposalCount().call()):
            show(contract, proposal_id)
    elif args.command == "demo":
        demo(w3, contract)
    else:
        accounts = w3.eth.accounts
        if not 0 <= args.account < len(accounts):
            raise ValueError("Account index is outside the available Ganache accounts.")
        if args.command == "create":
            function = contract.functions.createProposal(args.title.strip(), args.description.strip())
        elif args.command == "endorse":
            function = contract.functions.endorseProposal(args.id)
        else:
            function = contract.functions.closeProposal(args.id)
        send(w3, function, accounts[args.account])
        if args.id is not None:
            show(contract, args.id)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
