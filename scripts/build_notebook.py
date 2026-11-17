"""Generate the demonstration notebook using the deployed ABI and address."""
import json
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "deployment.json").read_text(encoding="utf-8"))
cells = []
def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))
def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))

md('# Community Proposal Board — Bài thực hành Blockchain\n**Sinh viên:** Võ Khắc Tuyên · **MSSV:** 30219042961  \n**Môn:** DS 441 A — Blockchain: Theory & Practices\n\nNotebook kết nối smart contract Solidity trên Ganache bằng web3.py. Output đã lưu thể hiện giao dịch thật, receipt, event, lỗi bị từ chối và trạng thái cuối.\n\nChạy lại: bật Ganache, chạy `npm run deploy`, cài `requirements-notebook.txt`, chọn kernel Python (Community Board), rồi **Restart Kernel and Run All Cells**. Mỗi lần chạy tạo đề xuất mới. Chỉ dùng Ether và tài khoản thử nghiệm. ABI và cấu hình được nhúng trong cell; nếu có `deployment.json`, notebook ưu tiên cấu hình mới nhất. GitHub có thể hiển thị output đã lưu mà không chạy Ganache.')
md('## 1. Kết nối và kiểm tra cấu hình\nXác thực mạng Ganache, Chain ID, địa chỉ có bytecode và ABI. Dùng ba địa chỉ A/B/C làm tác giả, người ủng hộ và người chưa ủng hộ.')
code("""import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from importlib.metadata import version
from web3 import Web3
from web3.exceptions import Web3Exception

EMBEDDED_CONFIG = json.loads(r'''""" + json.dumps(config, ensure_ascii=False, indent=2) + """''')
config_path = Path("deployment.json")
config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else EMBEDDED_CONFIG
RPC_URL = config["rpcUrl"]
CONTRACT_ADDRESS = config["address"]
ABI = config["abi"]

assert urlparse(RPC_URL).hostname in {"localhost", "127.0.0.1", "::1"}, "Use local Ganache only"
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 10}))
assert w3.is_connected(), f"Cannot connect to Ganache: {RPC_URL}"
assert any(name in w3.client_version.lower() for name in ("ganache", "testrpc")), "Expected Ganache"
assert Web3.is_address(CONTRACT_ADDRESS), "Invalid contract address"
assert isinstance(ABI, list), "ABI must be a JSON array"
address = Web3.to_checksum_address(CONTRACT_ADDRESS)
assert w3.eth.chain_id == int(config["chainId"]), "Wrong Chain ID"
assert w3.eth.get_code(address), "Contract missing. Run npm run deploy again."
contract = w3.eth.contract(address=address, abi=ABI)
accounts = w3.eth.accounts
assert len(accounts) >= 3, "Need at least three unlocked Ganache accounts"
A, B, C = accounts[:3]
results = []
print("Connected to Ganache and CommunityProposalBoard!")
print("Python:", sys.version.split()[0], "| web3.py:", version("web3"))
print("Client:", w3.client_version)
print("RPC:", RPC_URL)
print("Chain ID:", w3.eth.chain_id)
print("Contract:", address)
print("ABI entries:", len(ABI))
print("Proposal count before demo:", contract.functions.proposalCount().call())
for role, account in zip(("A - author", "B - supporter", "C - newcomer"), (A, B, C)):
    print(role, ":", account, "| test ETH:", w3.from_wei(w3.eth.get_balance(account), "ether"))
""")
md('## 2. Hàm hỗ trợ\n`send` gửi giao dịch thật và kiểm tra receipt thành công. `reject` kiểm tra lý do revert bằng eth_call, sau đó gửi giao dịch thật với gas cố định và yêu cầu receipt **status = 0**. Giao dịch thất bại vẫn được ghi trong block và tốn gas thử nghiệm, nhưng thay đổi dữ liệu và event bị hoàn tác.')
code("""
def passed(label):
    results.append((label, "PASS"))
    print("PASS:", label)

def send(label, function, sender, event_name=None):
    tx_hash = function.transact({"from": sender})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print("Transaction:", Web3.to_hex(tx_hash))
    print("Block:", receipt.blockNumber, "| status:", receipt.status, "| gas:", receipt.gasUsed)
    assert receipt.status == 1, f"Transaction failed: {label}"
    if event_name:
        logs = getattr(contract.events, event_name)().process_receipt(receipt)
        assert len(logs) == 1, f"Expected event {event_name}"
        print("Event:", event_name, dict(logs[0]["args"]))
    passed(label)
    return receipt

def proposal_data(proposal_id):
    fields = ("id", "author", "title", "description", "endorsementCount", "closed")
    return dict(zip(fields, contract.functions.getProposal(proposal_id).call()))

def show(proposal_id):
    print(json.dumps(proposal_data(proposal_id), ensure_ascii=False, indent=2))

def reject(label, function, sender, expected_reason):
    try:
        function.call({"from": sender})
    except (Web3Exception, ValueError) as exc:
        message = str(exc)
        assert expected_reason in message and "revert" in message.lower(), message
        print("Expected reason:", expected_reason)
        rpc_error = (getattr(exc, "rpc_response", None) or {}).get("error", {})
        print("Contract error:", rpc_error.get("message", message))
    else:
        raise AssertionError("Invalid action was accepted: " + label)
    try:
        tx_hash = function.transact({"from": sender, "gas": 250000})
    except Web3Exception as exc:
        # Ganache GUI may return a JSON-RPC error even after mining the revert.
        error = (getattr(exc, "rpc_response", None) or {}).get("error", {})
        data = error.get("data", {})
        if not isinstance(data, dict) or not data.get("hash"):
            raise
        assert expected_reason in str(exc), str(exc)
        tx_hash = Web3.to_bytes(hexstr=data["hash"])
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print("Rejected transaction:", Web3.to_hex(tx_hash))
    print("Block:", receipt.blockNumber, "| status:", receipt.status, "| gas:", receipt.gasUsed)
    assert receipt.status == 0, "Invalid transaction must revert"
    assert len(receipt.logs) == 0, "Reverted transaction must not retain events"
    passed(label)
""")
md('## 3. A tạo đề xuất\nLấy ID từ event ProposalCreated để notebook có thể chạy lại trên blockchain đã có dữ liệu. Kiểm tra tác giả, số lượt ban đầu bằng 0 và trạng thái đang mở.')
code("""
receipt = send(
    "A creates a proposal",
    contract.functions.createProposal(
        "Trồng cây tại công viên",
        "Trồng thêm cây để tạo bóng mát và cải thiện không gian xanh cho cộng đồng."
    ),
    A,
    "ProposalCreated"
)
proposal_id = contract.events.ProposalCreated().process_receipt(receipt)[0]["args"]["proposalId"]
initial = proposal_data(proposal_id)
assert initial["author"] == A and initial["endorsementCount"] == 0 and initial["closed"] is False
print("New proposal ID:", proposal_id)
show(proposal_id)
""")
md('## 4. Chặn tác giả tự ủng hộ\nA tự ủng hộ phải bị contract từ chối. Số lượt vẫn bằng 0 và mapping không ghi nhận lượt ủng hộ.')
code("""
reject("Self endorsement rejected", contract.functions.endorseProposal(proposal_id), A, "Author cannot endorse own proposal")
assert proposal_data(proposal_id)["endorsementCount"] == 0
assert not contract.functions.hasEndorsed(proposal_id, A).call()
""")
md('## 5. B ủng hộ thành công\nSố lượt tăng lên 1; mapping ghi nhận B đã ủng hộ và event ProposalEndorsed được phát.')
code("""
send("B endorses the proposal", contract.functions.endorseProposal(proposal_id), B, "ProposalEndorsed")
assert proposal_data(proposal_id)["endorsementCount"] == 1
assert contract.functions.hasEndorsed(proposal_id, B).call()
show(proposal_id)
""")
md('## 6. Chặn ủng hộ trùng\nB ủng hộ lần nữa phải bị từ chối với lý do Already endorsed. Số lượt giữ nguyên bằng 1.')
code("""
reject("Duplicate endorsement rejected", contract.functions.endorseProposal(proposal_id), B, "Already endorsed")
assert proposal_data(proposal_id)["endorsementCount"] == 1
""")
md('## 7. Chặn người khác đóng đề xuất\nB không phải tác giả nên contract từ chối. Đề xuất vẫn đang mở.')
code("""
reject("Unauthorized close rejected", contract.functions.closeProposal(proposal_id), B, "Only author can close proposal")
assert proposal_data(proposal_id)["closed"] is False
""")
md('## 8. A đóng đề xuất\nGiao dịch thành công, phát event ProposalClosed và trạng thái closed chuyển thành true.')
code("""
send("A closes the proposal", contract.functions.closeProposal(proposal_id), A, "ProposalClosed")
assert proposal_data(proposal_id)["closed"] is True
show(proposal_id)
""")
md('## 9. Chặn ủng hộ sau khi đóng\nDùng C chưa từng ủng hộ để chứng minh lỗi do đề xuất đã đóng. Đồng thời kiểm tra tác giả không thể đóng lần thứ hai.')
code("""
assert not contract.functions.hasEndorsed(proposal_id, C).call()
reject("Endorsement after closure rejected", contract.functions.endorseProposal(proposal_id), C, "Proposal is closed")
assert not contract.functions.hasEndorsed(proposal_id, C).call()
reject("Repeated closure rejected", contract.functions.closeProposal(proposal_id), A, "Proposal is closed")
""")
md('## 10. Kiểm tra đầu vào không hợp lệ\nContract phải chặn ID không tồn tại và tiêu đề rỗng. Thao tác tạo đề xuất không hợp lệ không được làm tăng tổng số đề xuất.')
code("""
invalid_id = contract.functions.proposalCount().call() + 1000
reject("Unknown proposal rejected", contract.functions.endorseProposal(invalid_id), C, "Proposal does not exist")
count_before = contract.functions.proposalCount().call()
reject("Empty title rejected", contract.functions.createProposal("", "Description"), A, "Title must be 1-120 bytes")
assert contract.functions.proposalCount().call() == count_before
""")
md('## 11. Bảng kết quả và trạng thái cuối\nĐề xuất thuộc A, có đúng 1 lượt từ B, đã đóng; C chưa ủng hộ. Mỗi dòng PASS chỉ được thêm sau khi kiểm tra giao dịch tương ứng thành công. Bất kỳ assertion thất bại nào đều dừng notebook.')
code("""
final = proposal_data(proposal_id)
assert final["author"] == A
assert final["endorsementCount"] == 1
assert final["closed"] is True
assert contract.functions.hasEndorsed(proposal_id, B).call()
assert not contract.functions.hasEndorsed(proposal_id, C).call()
passed("Final state and endorsement mappings are correct")
show(proposal_id)
print("=" * 72)
for index, (label, outcome) in enumerate(results, 1):
    print(f"{index:02}. {outcome:4} | {label}")
print("=" * 72)
assert len(results) == 11
print(f"RESULT: {len(results)}/{len(results)} checks passed.")
print("All transaction hashes, receipts and events above were obtained from Ganache.")
""")
md('## Giải thích và nguồn tham khảo\n- Quyền được kiểm tra trong Solidity bằng msg.sender, không phụ thuộc giao diện.\n- Mapping hasEndorsed giới hạn một địa chỉ một lượt trên từng đề xuất.\n- Chỉ tác giả được đóng; khi đóng, contract ngừng nhận ủng hộ.\n- Dữ liệu output lấy từ Ganache cục bộ. Không chứa private key hoặc tiền thật.\n- [web3.py](https://web3py.readthedocs.io/en/stable/overview.html), [Solidity](https://docs.soliditylang.org/), [Ganache](https://github.com/trufflesuite/ganache).\n- Mã nguồn, notebook và tài liệu được xây dựng với sự hỗ trợ của OpenAI Codex. Sinh viên cần hiểu mã và tự giải thích trước khi nộp.')
notebook = nbf.v4.new_notebook(cells=cells)
notebook.metadata.kernelspec = {"display_name": "Python (Community Board)", "language": "python", "name": "community-board"}
notebook.metadata.language_info = {"name": "python"}
for index, cell in enumerate(notebook.cells):
    if cell.cell_type == 'code':
        compile(cell.source, f'cell_{index}', 'exec')
nbf.write(notebook, ROOT / "CommunityProposalBoard.ipynb")
print("Created CommunityProposalBoard.ipynb")
