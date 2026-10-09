# IT review checklist — trước khi đưa V2 trở lại sử dụng

## A. Xác nhận không đổi Google Sheet

- [ ] Spreadsheet ID của app vẫn là `1jnVg_ZM7DTnrxHBOCPwUviQJJrbhHwhoFGmNW5nES9Y`.
- [ ] Các tab giữ nguyên: `Branches`, `Students`, `Assessments`, `Analysis`, `Settings`.
- [ ] Mỗi hàng header còn nguyên như trước deploy.
- [ ] Nếu thiếu một tab/header không đúng, app báo lỗi và dừng; không tự tạo tab/sửa header.
- [ ] `service_account.json` và `.streamlit/secrets.toml` không xuất hiện trong GitHub commit.

## B. Kiểm thử chống trùng

Dùng một file Excel có 67 học viên; ghi lại row count ban đầu và số bản ghi ACTIVE.

- [ ] Upload lần 1: tạo 67 đánh giá mới (nếu dữ liệu thực sự chưa có).
- [ ] Upload lại file y hệt lần 2, kể cả sau khi Streamlit tạo đường dẫn tạm khác: không thêm assessment mới.
- [ ] Đổi tên file Excel rồi upload lại lần 3: vẫn không thêm assessment mới.
- [ ] Không tăng số dòng `Analysis` chỉ vì re-upload cùng điểm; có thể cập nhật nội dung của dòng Analysis đã tồn tại.
- [ ] Nếu dữ liệu trước đây đã có bản trùng, re-upload không xóa lịch sử; trạng thái các bản trùng cũ được đánh dấu `REPLACED`, để lại một bản có hiệu lực.

## C. Sửa điểm và phiên bản

- [ ] Sửa điểm của một học viên trong cùng kỳ và upload lại.
- [ ] Bản cũ chuyển `final_status = REPLACED`.
- [ ] Có một bản mới với `final_status = ACTIVE`.
- [ ] Không tạo hai bản ACTIVE cho cùng một học viên/lớp/loại đánh giá/ngày thi/chi nhánh/nguồn.

## D. Lịch sử và ngày thi

- [ ] Upload kỳ tháng 8 trước: lần đầu không hiện so sánh lịch sử.
- [ ] Upload kỳ tháng 7 sau: tháng 7 không lấy tháng 8 làm kỳ trước.
- [ ] Upload lại tháng 8: bản tháng 7 được chọn làm kỳ trước.
- [ ] Ngày dạng `07/09/2026-09/09/2026` được chuẩn hóa đúng.
- [ ] Kiểm tra thứ tự tháng 9, tháng 10, tháng 11: sắp theo ngày, không theo chuỗi.
- [ ] Re-upload cùng một kỳ không so sánh kỳ đó với chính nó.
- [ ] Đổi tên file không làm đổi định danh logic của assessment.

## E. Nhận xét và phiếu Word

- [ ] Nhận xét kỹ năng lần đầu dùng điểm hiện tại, không báo thiếu dữ liệu khi điểm có sẵn.
- [ ] Lớp KET/standard sử dụng tiêu chí standard; IELTS dùng Band.
- [ ] Thay đổi kỹ năng standard ghi theo điểm phần trăm, không trộn norm10 với 0–100.
- [ ] IELTS ghi delta theo Band.
- [ ] E CLASS chỉ nhận xét Speaking, không tạo nhận xét giả cho Listening/Reading/Writing.
- [ ] Phiếu standard còn đủ bảng 1, bảng 2, bảng 3; ô Other comments và vùng chữ ký/ngày vẫn tồn tại ở phần trang 1.
- [ ] Phần đánh giá phát triển xuất hiện khi có kỳ trước hợp lệ.
- [ ] Sau khi tháng 7 đã tồn tại, re-upload tháng 8 cùng điểm phải cập nhật nhận xét ở dòng Analysis có sẵn và phiếu Word mới.

## F. Kết quả kiểm thử trong package

Các test offline hiện tại:

```bash
python -m unittest discover -s tests -v
```

Kết quả build package: 11 bài test đạt. Đây là test logic với worksheet giả lập, không phải kiểm thử live trên Google Sheets. Ghi lại kết quả của các checklist trên khi IT chạy bằng credentials và spreadsheet thật.
