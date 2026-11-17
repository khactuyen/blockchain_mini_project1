# Kết quả kiểm tra — 17/11/2026

## Notebook: PASS

`CommunityProposalBoard.ipynb` đã được thực thi bằng Jupyter kernel của môi trường `.venv` qua `scripts/run_notebook.py`, kết nối Ganache GUI cục bộ ở `http://127.0.0.1:7545`, Chain ID 1337.

- 11 code cell đã chạy; không có output loại error.
- Kết quả cuối: **RESULT: 11/11 checks passed.**
- Có giao dịch thành công status 1, event và hash.
- Có giao dịch bị từ chối được đào vào block với status 0; lý do revert được kiểm tra trước bằng eth_call.
- Trạng thái cuối của đề xuất demo: 1 lượt ủng hộ, đã đóng, người ủng hộ là B, C chưa ủng hộ.
- Output được lưu trong notebook và `docs/notebook-output.txt`; có thể xem trên GitHub mà không khởi động Ganache.
- Notebook chạy lại được bằng cách tạo đề xuất mới và lấy ID từ event. Cấu hình deploy được đọc từ deployment.json nếu có, hoặc dùng bản nhúng trong notebook.

Các kiểm tra: tạo đề xuất, chặn tác giả tự ủng hộ, B ủng hộ, chặn trùng, chặn người khác đóng, tác giả đóng, chặn ủng hộ sau đóng bằng C, chặn đóng lần hai, ID không tồn tại, tiêu đề rỗng, trạng thái cuối.

Ganache GUI có thể trả JSON-RPC error cho giao dịch đã được đào nhưng revert. Notebook đọc hash từ error.data.hash và lấy receipt thực tế; không coi mọi lỗi RPC là một lần kiểm tra thành công.

## Python CLI: PASS

Đã chạy `community_board.py info` và `community_board.py demo` với web3.py trong `.venv`.

- Kết nối, Chain ID, địa chỉ contract, danh sách tài khoản và số đề xuất đọc thành công.
- Demo tạo, ủng hộ và đóng qua giao dịch thực tế.
- Demo từ chối ủng hộ trùng, tự ủng hộ, đóng sai quyền và ủng hộ sau đóng bằng eth_call.
- Trạng thái cuối đúng: 1 lượt ủng hộ và đã đóng.

## Contract: PASS

`npm.cmd test`: 1 integration test passed, 0 failed. Test bao gồm quyền, sự kiện, dữ liệu, revert, giới hạn đầu vào, ID không tồn tại và lượt ủng hộ độc lập giữa các đề xuất.

Công cụ: Node.js 24.14.1, solc 0.8.19, ethers 6.17.0, Ganache 7.9.2 trong test. Target EVM Paris để tương thích Ganache. Cảnh báo µWS trên Node 24 dẫn tới fallback JavaScript; test vẫn hoàn tất thành công.

## Giao diện: PASS với ví mô phỏng

Trước đó đã chạy tests/ui.mjs trên Chrome headless với ví EIP-1193 mô phỏng chuyển request đến Ganache thật. Luồng kết nối, tạo, đổi tài khoản, ủng hộ, khóa nút ủng hộ trùng và đóng đều đạt. Không có pageerror; mobile 390px không tràn ngang. Ảnh desktop/mobile đã được kiểm tra trực quan trong screenshots/.

Thao tác phê duyệt giao dịch bằng extension MetaMask thật chưa được kiểm tra tự động; cần demo thủ công nếu giảng viên yêu cầu xem extension. Không ảnh hưởng kết quả tích hợp Python và notebook nêu trên.
