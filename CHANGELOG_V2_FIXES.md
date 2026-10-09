# Changelog — V2 existing-sheet compatibility fix

## Các sửa đổi chính

1. **Chống trùng ổn định:** định danh một đánh giá theo chi nhánh, nguồn, học viên, lớp, loại đánh giá và ngày thi chuẩn hóa; không dùng tên file hoặc đường dẫn tạm để xác định kỳ đánh giá.
2. **Sửa phiên bản điểm:** cùng kỳ + cùng điểm thì không thêm assessment mới. Cùng kỳ + điểm thay đổi thì đánh dấu bản ACTIVE cũ là `REPLACED` và lưu phiên bản mới ở `Assessments` hiện có.
3. **Dọn trạng thái trùng cũ khi re-upload:** nếu phát hiện nhiều bản ACTIVE/legacy GENERATED thuộc cùng một kỳ, giữ bản mới nhất làm bản đối chiếu và đánh dấu những bản còn lại `REPLACED`.
4. **Sửa nhận xét kỹ năng:** `_skill_comment()` nhận đúng điểm hiện tại, điểm trước (nếu có) và cờ thang điểm IELTS. Lần đầu vẫn viết nhận xét theo điểm hiện tại. Không bịa nhận xét cho kỹ năng không có trong file; E CLASS giữ Speaking-only.
5. **Chuẩn hóa thang lịch sử:** điểm kỹ năng thường được lưu dưới dạng norm10 trong database V2, được đưa về phần trăm khi phân tích tiến bộ. IELTS giữ thang Band 0–9. Giá trị legacy đã lưu theo phần trăm được nhận diện để tránh nhân 10 hai lần.
6. **Ngày thi:** đọc ngày đơn và khoảng ngày không có khoảng trắng, ví dụ `07/09/2026-09/09/2026`; lịch sử sắp xếp theo ngày kết thúc thật, không sắp xếp chuỗi.
7. **Loại bản ghi hiện tại:** ghép `Assessments` với `Students` để lấy tên, lớp, nguồn và chi nhánh; loại kỳ hiện tại khỏi lịch sử của chính nó và chỉ so sánh với kỳ có ngày kết thúc sớm hơn.
8. **Analysis được làm mới khi re-upload cùng điểm:** nếu một kỳ đã upload trước, nhưng các kỳ cũ hơn chỉ xuất hiện sau đó, upload lại kỳ hiện tại sẽ làm mới nhận xét trong dòng `Analysis` có sẵn theo `assessment_id`; không tăng số dòng đánh giá/nhận xét chỉ vì đường dẫn file thay đổi.
9. **Khôi phục form V1:** bảng chuyên cần, bảng kết quả bài thi, bảng tổng/xếp loại/chú thích/nhận xét khác và phần chữ ký/ngày báo cáo được giữ trong phiếu standard; phần phát triển/lộ trình ở trang sau.
10. **Không đổi schema Google Sheets:** engine chỉ đọc/kiểm tra header worksheet đã tồn tại. Không tự thêm tab và không cập nhật hàng header. Nếu sheet/header không đúng thì báo lỗi và dừng.

## Những giới hạn cần biết

- Code không tự xóa dòng lịch sử cũ. Các dòng bản cũ được đánh dấu `REPLACED`; số dòng vật lý không nhất thiết giảm.
- Các kiểm thử là offline/mocked Google Sheets. Trước production, IT vẫn cần xác nhận với spreadsheet thật và dữ liệu thật.
- Không thay đổi logic chọn chi nhánh/giao diện đăng nhập trong bản này; `app.py` hiện tại vẫn giữ luồng V2 đã có.
