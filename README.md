# Common Ground — Community Proposal Board

Đồ án cá nhân DS 441 A · Võ Khắc Tuyên · MSSV 30219042961.

## Các file chính để kiểm tra và nộp

- `contracts/CommunityProposalBoard.sol`: smart contract Solidity.
- `community_board.py`: Python CLI kết nối và tương tác với Ganache bằng web3.py.
- **`CommunityProposalBoard.ipynb`: notebook có output thực tế đã chạy, dành cho giảng viên kiểm tra.**
- `docs/notebook-output.txt`: bản text của output notebook.
- `web/`: giao diện HTML/CSS/JavaScript dùng ethers.js.
- `scripts/`, `tests/`, `screenshots/`: triển khai, kiểm thử và ảnh demo giao diện.

## Chuẩn bị

Cần Node.js 20+, Python 3.10+ và MetaMask nếu dùng giao diện. Mọi tài khoản, Ether và khóa ví đều phải là tài khoản thử nghiệm Ganache.

Chạy tại thư mục gốc dự án bằng PowerShell:

```powershell
npm.cmd ci
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
.\.venv\Scripts\python.exe -m ipykernel install --prefix .venv --name community-board --display-name "Python (Community Board)"
```

## Chạy blockchain và triển khai

Terminal thứ nhất:

```powershell
npm.cmd run ganache
```

RPC mặc định: `http://127.0.0.1:7545`, Chain ID: `1337`, currency: `ETH`. Nếu đã có Ganache GUI/CLI chạy ở cổng này thì sử dụng mạng đó, không khởi động thêm. CLI cung cấp 10 tài khoản thử nghiệm đã mở khóa. Chain ID cần theo kết quả deploy; Network ID trong Ganache có thể khác Chain ID.

Terminal thứ hai:

```powershell
npm.cmd run deploy
```

Script tự biên dịch và triển khai bằng tài khoản Ganache đầu tiên, sinh ABI/địa chỉ vào `deployment.json` và `web/deployment.json`. Hai file này là cấu hình cục bộ và được bỏ qua trong Git. Nếu Ganache được reset thì phải deploy lại. Ganache CLI theo lệnh mẫu không lưu dữ liệu sau khi tắt.

## Đọc và chạy notebook

Để chấm kết quả, mở `CommunityProposalBoard.ipynb`: output đã được lưu trong file, có thể xem trên GitHub hoặc VS Code. Không cần Ganache đang chạy để đọc output đã lưu.

Để chạy lại qua VS Code: mở notebook, chọn **Select Kernel → Python Environments → `.venv`**, rồi **Restart Kernel and Run All Cells**. Mỗi lần Run All tạo một đề xuất mới, không phụ thuộc ID cũ. Giữ Ganache chạy trong suốt quá trình.

Hoặc chạy toàn bộ notebook bằng terminal sau khi đã cài kernel:

```powershell
.\.venv\Scripts\python.exe scripts\run_notebook.py
```

Nếu muốn mở bằng Jupyter Notebook:

```powershell
$env:JUPYTER_PATH = "$PWD\.venv\share\jupyter"
.\.venv\Scripts\python.exe -m notebook CommunityProposalBoard.ipynb
```

Notebook ưu tiên `deployment.json` nếu tồn tại. ABI và cấu hình lúc tạo cũng được nhúng trong notebook; địa chỉ nhúng chỉ đúng với blockchain đã dùng khi chạy. Để thay bằng cấu hình deploy mới và tạo lại notebook từ đầu (xóa output cũ):

```powershell
.\.venv\Scripts\python.exe scripts\build_notebook.py
.\.venv\Scripts\python.exe scripts\run_notebook.py
```

Sau khi chạy, lưu notebook giữ nguyên output. Không dùng Clear All Outputs trước khi push bài nộp.

Notebook kiểm tra 11 trường hợp: tạo đề xuất, cấm tự ủng hộ, ủng hộ hợp lệ, cấm ủng hộ trùng, cấm người khác đóng, tác giả đóng, cấm ủng hộ sau đóng, cấm đóng lần hai, ID không tồn tại, tiêu đề rỗng và trạng thái cuối. Các thao tác sai được xác minh lý do revert rồi gửi thành giao dịch thật với gas cố định để có receipt `status = 0`. Đây là thất bại dự kiến; notebook bắt và kiểm tra lỗi để Run All vẫn hoàn tất.

## Python CLI

```powershell
.\.venv\Scripts\python.exe community_board.py info
.\.venv\Scripts\python.exe community_board.py list
.\.venv\Scripts\python.exe community_board.py create --account 0 --title "Plant trees" --description "Add shade in our park"
.\.venv\Scripts\python.exe community_board.py endorse --account 1 --id 0
.\.venv\Scripts\python.exe community_board.py close --account 0 --id 0
.\.venv\Scripts\python.exe community_board.py demo
```

CLI kiểm tra RPC cục bộ, client Ganache, Chain ID, ABI, địa chỉ và mã contract. Chỉ dùng tài khoản mở khóa của Ganache; không lưu private key. `--account` và `--id` bắt đầu từ 0; UI hiển thị ID 0 thành #1. CLI demo cần ba tài khoản; tạo đề xuất mới mỗi lần chạy. Khác với notebook, các lần bị từ chối trong CLI demo được kiểm tra bằng eth_call, không gửi lên block.

## Giao diện Web3

```powershell
npm.cmd start
```

Mở `http://127.0.0.1:3000`, thêm mạng Ganache vào MetaMask và import các tài khoản thử nghiệm. Dùng A tạo đề xuất, B ủng hộ rồi A đóng. Thay đổi tài khoản sẽ tải lại trang; bấm kết nối lại. Bấm Làm mới để đọc thay đổi từ Python hoặc tài khoản khác.

UI hiển thị tài khoản, mạng, contract, đề xuất, số lượt, trạng thái đóng, hash và trạng thái giao dịch, event và lỗi. Quy tắc được thực thi trong contract, không chỉ kiểm tra trên giao diện.

## Kiểm thử

```powershell
npm.cmd test
```

Test dùng Ganache trong bộ nhớ độc lập với mạng cổng 7545. Kiểm tra quyền, dữ liệu, event, revert, ID và giới hạn đầu vào. Node 24 có thể hiện cảnh báo µWS; Ganache dùng implementation JavaScript thay thế.

Kiểm thử UI tùy chọn, cần Ganache và server đang chạy:

```powershell
npm.cmd install --no-save playwright
npx.cmd playwright install chromium
node tests/ui.mjs
```

Có thể đặt `CHROME_PATH` tới Chrome có sẵn. UI test dùng ví EIP-1193 mô phỏng và giao dịch thật tới Ganache; thao tác xác nhận trong extension MetaMask vẫn cần kiểm tra thủ công khi quay demo. Ảnh desktop/mobile đã lưu trong `screenshots/`.

## Quy tắc contract

Bất kỳ địa chỉ nào được tạo đề xuất. Địa chỉ khác tác giả được ủng hộ đúng một lần cho từng đề xuất. Chỉ tác giả được đóng; đề xuất đã đóng không nhận thêm lượt. Event gồm ProposalCreated, ProposalEndorsed, ProposalClosed. Tiêu đề 1–120 byte, mô tả 1–2000 byte UTF-8; tiếng Việt có thể chiếm nhiều byte mỗi ký tự. Quyền gắn với địa chỉ, không xác minh danh tính thật. Contract không có admin hoặc chức năng thanh toán. Danh sách đọc tuần tự, phù hợp phạm vi đồ án nhỏ.

## Tự push GitHub

Git đã được khởi tạo. Tạo repo trống rồi chạy:

```powershell
git add .
git commit -m "Build proposal board with Solidity, Python and executed notebook"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Kiểm tra GitHub có đủ `.sol`, `.py` và `.ipynb` cùng output. `.gitignore` loại môi trường Python, node_modules, file .env và cấu hình deploy cục bộ. Không commit khóa ví thật.

## Tham khảo và hỗ trợ

- Đề bài: `32_30219042961_Vo_Khac_Tuyen.pdf`.
- https://docs.soliditylang.org/
- https://docs.ethers.org/v6/getting-started/
- https://web3py.readthedocs.io/en/stable/overview.html
- https://jupyter.org/install
- https://github.com/trufflesuite/ganache
- Mã nguồn, giao diện, notebook, kiểm thử và tài liệu được xây dựng với sự hỗ trợ của OpenAI Codex. Sinh viên cần kiểm tra, hiểu và giải thích được mã trước khi nộp.
