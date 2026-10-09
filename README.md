# CIE/SIT Assessment V2 — bản sửa lỗi, dùng Google Sheets hiện tại

**Mục tiêu:** thay thế mã nguồn V2 đang deploy, đồng thời giữ nguyên Google Sheet database đã tạo trước đó. Không tạo tab mới, không đổi header, không yêu cầu di chuyển dữ liệu.

## 1. File dùng để deploy

```text
app.py                 # Entrypoint Streamlit hiện tại
engine_v2.py           # Engine V2 đã sửa
requirements.txt       # Dependencies
.streamlit/config.toml # Giao diện cơ bản
.gitignore             # Chặn credentials/secrets
secrets_template.toml  # Mẫu cấu hình; không chứa khóa thật
CHANGELOG_V2_FIXES.md  # Những gì đã sửa
IT_REVIEW_CHECKLIST.md # Checklist kiểm thử trước production
tests/                 # Offline regression tests
```

Không đổi tên `app.py` hoặc `engine_v2.py`: `app.py` import `engine_v2`.

## 2. Google Sheets được giữ nguyên

Mã nguồn nhắm tới Spreadsheet ID hiện có:

```text
1jnVg_ZM7DTnrxHBOCPwUviQJJrbhHwhoFGmNW5nES9Y
```

Các tab hiện hữu mà engine dùng:

- `Branches`
- `Students`
- `Assessments`
- `Analysis`
- `Settings`

Engine đã đổi hàm kiểm tra worksheet theo nguyên tắc **chỉ truy cập, không tự tạo tab và không sửa hàng header**. Nếu thiếu tab hoặc header không tương thích, ứng dụng dừng với thông báo lỗi thay vì tự điều chỉnh Google Sheet.

Các header được kiểm tra theo cấu trúc V2 hiện hành:

```text
Branches:
branch_id | branch_name | brand | status

Students:
student_id | branch_id | source | student_name | class_name | level | school_name | phone | status

Assessments:
assessment_id | student_id | branch_id | assessment_type | assessment_date | level | listening | speaking | reading | writing | overall_score | weakest_skill | overall_level | teacher_check | ai_check | final_status

Analysis:
assessment_id | student_id | listening_comment | speaking_comment | reading_comment | writing_comment | overall_comment | recommendation | study_duration | target_level | generated_at

Settings:
setting_key | setting_value | description
```

**Lưu ý:** engine vẫn ghi dữ liệu assessment/comment vào các tab hiện có theo đúng luồng V2; “không thay đổi Google Sheet” ở đây nghĩa là không tạo tab, không đổi cấu trúc/header. Khi sửa điểm, engine có thể đổi `final_status` từ `ACTIVE` sang `REPLACED` và thêm phiên bản mới, không xóa lịch sử.

## 3. Đưa code lên GitHub để deploy lại

1. Tải ZIP và giải nén.
2. Mở repository GitHub đang được Streamlit dùng.
3. Thay `app.py`, `engine_v2.py`, `requirements.txt` và các file cấu hình trong repository bằng file cùng tên từ folder này. Có thể thêm thư mục `tests/` và tài liệu đi kèm.
4. Không xóa hay thay Google Sheet hiện tại.
5. Commit/push lên branch đang deploy (thường là `main`).
6. Streamlit Community Cloud sẽ build lại app từ repository. Entrypoint vẫn là `app.py`.

Nếu deploy từ repository mới, chọn `app.py` làm Main file path và dùng cùng Google Sheet hiện tại.

## 4. Secrets/credentials

- **Không commit** `service_account.json` hoặc `.streamlit/secrets.toml`.
- Với Streamlit Cloud, cấu hình Google Service Account trong App Settings → Secrets, theo mẫu `secrets_template.toml`.
- Service Account phải có quyền truy cập Google Sheet hiện tại.
- Chạy local có thể đặt `service_account.json` cạnh `app.py`; file này đã được `.gitignore` chặn khỏi commit.

## 5. Cách chạy kiểm thử local

Cài dependencies:

```bash
pip install -r requirements.txt
```

Kiểm tra cú pháp:

```bash
python -m py_compile app.py engine_v2.py
```

Chạy regression tests:

```bash
python -m unittest discover -s tests -v
```

Các test dùng worksheet giả lập trong bộ nhớ. Chúng kiểm tra logic nhưng **không thay thế kiểm tra với Google Sheet thật**.

## 6. Lưu ý với dữ liệu demo cũ

Bản sửa không tự xóa dòng cũ để bảo toàn lịch sử. Nếu database đã có bản ghi trùng từ phiên bản trước, khi re-upload cùng file mới, engine sẽ nhận diện các bản cùng kỳ, đánh dấu bản ACTIVE trùng cũ là `REPLACED` và giữ một bản đang có hiệu lực. Tổng số dòng có thể vẫn còn cao do các phiên bản cũ được lưu lại; cần nhìn cột `final_status` để phân biệt dữ liệu đang có hiệu lực với lịch sử thay thế.

Không reset hoặc xóa dữ liệu Google Sheet trước khi IT kiểm thử, trừ khi bạn chủ động muốn bắt đầu lại demo sạch.
