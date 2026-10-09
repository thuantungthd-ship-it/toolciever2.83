import base64
import io
import json
import os
import re
import shutil
import tempfile

import streamlit as st
import streamlit.components.v1 as components

import engine_v2 as engine

SHEET_ID = "1jnVg_ZM7DTnrxHBOCPwUviQJJrbhHwhoFGmNW5nES9Y"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

st.set_page_config(
    page_title="Phiếu Đánh Giá Học Tập | CIE & SIT",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

BG_B64 = getattr(engine, "DEFAULT_BACKGROUND_B64", "")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root {{
    --navy:#123B66;
    --navy-2:#1F4E79;
    --crimson:#C62828;
    --gray-badge:#EEF1F5;
    --border:#D9E2EC;
}}
html, body, [class*="css"] {{font-family:'Be Vietnam Pro',sans-serif; color:#000000 !important;}}
#MainMenu, footer, header {{visibility:hidden;}}
.stApp {{
    background-image: linear-gradient(rgba(255,255,255,.78),rgba(255,255,255,.78)),
                      url("data:image/png;base64,{BG_B64}");
    background-size:cover;
    background-position:center center;
    background-attachment:fixed;
    min-height:100vh;
}}
/* General text: black. Main headings/titles: navy. */
.stMarkdown, .stMarkdown *, p, span, label, div, li, td, th {{color:#000000 !important;}}
h1, h2, h3, .card-title, .section-title {{color:var(--navy) !important;}}
.hero {{
    background:rgba(255,255,255,.96);
    border:1px solid rgba(18,59,102,.16);
    border-radius:22px;
    padding:30px;
    margin-bottom:20px;
    box-shadow:0 12px 34px rgba(18,59,102,.14);
    text-align:center;
    color:#000000 !important;
}}
.hero h1 {{font-size:1.75rem;font-weight:800;margin:8px 0 7px;color:var(--navy) !important;}}
.hero p {{font-size:.92rem;margin:0 auto;max-width:650px;color:#000000 !important;}}
.hero-brand {{font-size:.78rem;font-weight:800;letter-spacing:.03em;margin-bottom:2px;}}
.cie-brand {{color:var(--crimson) !important;}}
.sit-brand {{color:var(--navy) !important;}}
.brand-sep {{color:#8A8F98 !important;margin:0 5px;}}
.badge {{
    display:inline-block;background:var(--gray-badge);border:1px solid #D5DAE1;
    color:#000000 !important;border-radius:999px;padding:5px 13px;font-size:.75rem;font-weight:700;
}}
.card {{
    position:relative;background:rgba(255,255,255,.97);border:1px solid var(--border);
    border-radius:16px;padding:20px 20px 12px;margin-bottom:16px;
    box-shadow:0 8px 24px rgba(18,59,102,.09);overflow:hidden;
}}
.card::before {{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--navy);}}
.card-title {{font-weight:800;color:var(--navy) !important;font-size:1.05rem;margin-bottom:8px;}}
.muted, .black-note, .footer-note {{color:#000000 !important;}}
.branch-box {{
    position:relative;border:1px solid var(--border);border-radius:14px;padding:14px 16px 14px 19px;
    background:rgba(255,255,255,.98);margin:8px 0 16px;box-shadow:0 6px 18px rgba(18,59,102,.07);overflow:hidden;
}}
.branch-box::before {{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--navy);}}
.brand {{font-weight:800;font-size:1.05rem;color:var(--navy) !important;}}
.branch-code {{font-family:monospace;color:#000000 !important;background:var(--gray-badge);border-radius:7px;padding:3px 7px;display:inline-block;margin-top:5px;}}
.stRadio label, .stSelectbox label, .stTextInput label, .stFileUploader label {{color:#000000 !important;}}
.stRadio div, .stRadio span {{color:#000000 !important;}}
div[data-baseweb="select"] {{background:#FFFFFF !important;border:1px solid var(--border) !important;border-radius:10px !important;box-shadow:0 3px 10px rgba(18,59,102,.05);}}
div[data-baseweb="select"] * {{color:#000000 !important;}}
input, textarea {{color:#000000 !important;background:#FFFFFF !important;border:1px solid var(--border) !important;border-radius:10px !important;}}
input:focus, textarea:focus {{border-color:var(--navy) !important;box-shadow:0 0 0 1px var(--navy) !important;}}
input::placeholder, textarea::placeholder {{color:#666666 !important;}}
button {{border-radius:10px !important;}}
button, button * {{color:#000000 !important;}}
button[kind="primary"], button[kind="primary"] * {{color:#FFFFFF !important;}}
button[kind="primary"] {{background:var(--navy) !important;border:1px solid var(--navy) !important;}}
button[kind="primary"]:hover {{background:#0D2F52 !important;border-color:#0D2F52 !important;}}
[data-testid="stFileUploader"], [data-testid="stFileUploader"] * {{color:#000000 !important;}}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{color:#000000 !important;}}
[data-testid="stAlert"], [data-testid="stAlert"] * {{color:#000000 !important;}}
[data-testid="stDownloadButton"] button, [data-testid="stDownloadButton"] button * {{color:#000000 !important;}}
.drive-read-btn {{background:var(--crimson);color:#FFFFFF !important;border:none;border-radius:10px;padding:9px 15px;font-weight:700;display:inline-block;}}
.footer-note {{text-align:center;color:#000000 !important;font-size:.78rem;margin-top:24px;margin-bottom:10px;}}
</style>
""", unsafe_allow_html=True)


def load_local_service_account():
    path = os.path.join(os.path.dirname(__file__), "service_account.json")
    if not os.path.exists(path):
        return None, path
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), path
    except Exception as exc:
        raise RuntimeError(f"Không đọc được service_account.json: {exc}") from exc


def get_secret():
    data, path = load_local_service_account()
    if data:
        return data, "local"
    try:
        if "gcp_service_account" in st.secrets:
            return dict(st.secrets["gcp_service_account"]), "streamlit"
    except Exception:
        pass
    try:
        raw = st.secrets.get("gcp_service_account_json")
        if raw:
            return json.loads(str(raw)), "streamlit"
    except Exception:
        pass
    return None, path


def google_client(secret):
    return engine._gs_credentials(secret)


def get_branches(secret):
    db = engine.get_google_database(secret, SHEET_URL)
    return engine.load_branches(db)


def extract_drive_id(url):
    url = str(url or "").strip()
    patterns = [r"/file/d/([\w-]+)", r"/spreadsheets/d/([\w-]+)", r"/document/d/([\w-]+)", r"/presentation/d/([\w-]+)", r"[?&]id=([\w-]+)"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if re.fullmatch(r"[\w-]{20,}", url):
        return url
    return None


def download_drive_file(url, secret):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload

    file_id = extract_drive_id(url)
    if not file_id:
        raise ValueError("Không nhận diện được File ID từ link Google Drive/Google Sheets.")
    _, creds = google_client(secret)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    meta = drive.files().get(fileId=file_id, fields="id,name,mimeType").execute()
    mime = meta.get("mimeType", "")
    if mime == "application/vnd.google-apps.spreadsheet":
        request = drive.files().export_media(
            fileId=file_id,
            mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        filename = (meta.get("name") or "drive") + ".xlsx"
    else:
        request = drive.files().get_media(fileId=file_id)
        filename = meta.get("name") or f"drive_{file_id}.xlsx"
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue(), filename


def safe_name(value):
    return re.sub(r'[\\/:*?"<>|]', "_", str(value)).strip()


def logo_temp_path():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "logo.png")
    with open(path, "wb") as f:
        f.write(base64.b64decode(engine.DEFAULT_LOGO_B64))
    return path


def build_zip(students, logo_path):
    tmp_dir = tempfile.mkdtemp()
    used = set()
    for student in students:
        doc = engine.build_phieu_v2(student, logo_path=logo_path)
        cls = safe_name((student.get("class_info") or {}).get("lop") or "Lop")
        name = safe_name(student.get("name") or "HocVien")
        base = f"{cls}__{name}"
        fn = base
        i = 2
        while fn in used:
            fn = f"{base}_{i}"
            i += 1
        used.add(fn)
        doc.save(os.path.join(tmp_dir, fn + ".docx"))
    zip_base = os.path.join(tempfile.mkdtemp(), "PhieuDanhGiaV2")
    zip_path = shutil.make_archive(zip_base, "zip", tmp_dir)
    with open(zip_path, "rb") as f:
        return f.read()


def render_music():
    music = getattr(engine, "DEFAULT_MUSIC_B64", "")
    if not music:
        return
    components.html(f"""
    <div style='display:flex;align-items:center;gap:10px;font-family:Arial,sans-serif'>
      <button id='music-btn' style='width:42px;height:42px;border:0;border-radius:50%;background:#123B66;color:white;font-size:18px;cursor:pointer'>🔊</button>
      <span style='color:#111;font-size:14px'>Nhạc nền</span>
      <audio id='bg-audio' loop><source src='data:audio/mp3;base64,{music}' type='audio/mpeg'></audio>
    </div>
    <script>
      const a=document.getElementById('bg-audio'); const b=document.getElementById('music-btn');
      a.volume=.35;
      b.onclick=()=>{{if(a.paused){{a.play();b.textContent='🔊';}}else{{a.pause();b.textContent='🔇';}}}};
    </script>
    """, height=54)


secret, secret_source = get_secret()

st.markdown("""
<div class='hero'>
  <div class='badge'><span class='cie-brand'>CIE VIET NAM</span><span class='brand-sep'>·</span><span class='sit-brand'>SIT VIET NAM</span><span class='brand-sep'>·</span>V2</div>
  <h1>Phiếu Đánh Giá & Nhận Xét Học Viên</h1>
  <p>sử dụng nội bộ</p>
</div>
""", unsafe_allow_html=True)

render_music()

if secret is None:
    st.error("Chưa kết nối Google Database.")
    st.markdown("""
    <div class='card'>
      <div class='card-title'>Cách đơn giản nhất để chạy V2 trên máy</div>
      <div class='black-note'>
      Đổi tên file JSON Service Account anh vừa tải về thành <b>service_account.json</b> và đặt cùng thư mục với <b>app.py</b>.<br><br>
      Không cần tạo <b>secrets.toml</b> khi chạy thử trên máy.<br><br>
      <b>Không đưa service_account.json lên GitHub.</b>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

try:
    branches = get_branches(secret)
except Exception as exc:
    st.error(f"Không đọc được sheet Branches: {exc}")
    st.caption(f"Database: {SHEET_URL}")
    st.stop()

if not branches:
    st.error("Sheet Branches chưa có chi nhánh ACTIVE.")
    st.stop()

branch_labels = {f"{r.get('branch_name')} ({r.get('branch_id')})": r for r in branches}
selected_label = st.selectbox("Chi nhánh", list(branch_labels.keys()), index=0)
branch = branch_labels[selected_label]
branch_id = str(branch.get("branch_id"))
brand = str(branch.get("brand", "CIE")).upper()

st.markdown(f"""
<div class='branch-box'>
  <div class='brand'>{branch.get('branch_name','')}</div>
  <div class='branch-code'>Mã chi nhánh: {branch_id} · Hệ thống: {brand}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='card-title'>1. Nguồn học viên</div>", unsafe_allow_html=True)
data_source = st.radio(
    "Nguồn học viên", ["CENTER", "SCHOOL"],
    format_func=lambda x: "Học viên Trung tâm" if x == "CENTER" else "Học viên Trường liên kết",
    horizontal=True,
)
st.caption("Không cần chọn trường. Trường là dữ liệu thuộc file điểm; mã học viên được tách theo chi nhánh + nguồn để tránh trộn dữ liệu.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='card-title'>2. Loại đánh giá</div>", unsafe_allow_html=True)
assessment_type = st.selectbox(
    "Loại đánh giá", ["Initial", "Final", "Certificate", "Other"], index=1,
    format_func=lambda x: {"Initial":"🟢 Đánh giá đầu vào","Final":"🏁 Cuối khóa","Certificate":"🏅 Thi chứng chỉ","Other":"📌 Khác"}[x],
)
operator = st.text_input("Người lập phiếu (không bắt buộc)", placeholder="Tên giáo viên / nhân viên")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='card-title'>3. Nhập bảng điểm</div>", unsafe_allow_html=True)
input_mode = st.radio("Nguồn file", ["Máy tính", "Google Drive"], horizontal=True)
file_bytes = None
file_name = None
if input_mode == "Máy tính":
    up = st.file_uploader("Chọn file Excel (.xlsx)", type=["xlsx"], label_visibility="collapsed")
    if up:
        file_bytes = up.getvalue()
        file_name = up.name
else:
    drive_url = st.text_input(
        "Link Google Drive / Google Sheets",
        placeholder="Dán link chia sẻ tại đây",
        key="drive_url",
    )
    # Nút luôn hiện ngay khi chọn Google Drive. Khi người dùng dán link,
    # chỉ cần bấm nút; không cần nhấn Enter trong ô link trước.
    read_drive = st.button(
        "Đọc file từ Drive",
        key="read_drive_btn",
        disabled=not bool(drive_url.strip()),
        use_container_width=False,
    )
    if read_drive:
        try:
            with st.spinner("Đang đọc file từ Google Drive..."):
                file_bytes, file_name = download_drive_file(drive_url, secret)
            st.session_state["drive_file_bytes"] = file_bytes
            st.session_state["drive_file_name"] = file_name
            st.success(f"Đã đọc: {file_name}")
        except Exception as exc:
            st.error(f"Không đọc được file Drive: {exc}")
    file_bytes = st.session_state.get("drive_file_bytes")
    file_name = st.session_state.get("drive_file_name")
st.markdown("</div>", unsafe_allow_html=True)

if file_bytes:
    if st.button("▶ Phân tích & xuất phiếu", type="primary", use_container_width=True):
        tmp_dir = tempfile.mkdtemp()
        path = os.path.join(tmp_dir, safe_name(file_name or "diem.xlsx"))
        with open(path, "wb") as f:
            f.write(file_bytes)
        progress = st.progress(0, text="Đang đọc lịch sử đánh giá...")
        try:
            progress.progress(.20, text="Đang đọc lịch sử đánh giá...")
            students, sync = engine.process_and_sync_workbook(
                path, secret, assessment_type=assessment_type,
                spreadsheet_url=SHEET_URL, operator=operator,
                branch_id=branch_id, data_source=data_source,
            )
            progress.progress(.65, text="Đang tạo nhận xét từng kỹ năng và phiếu Word...")
            logo_path = logo_temp_path()
            zip_data = build_zip(students, logo_path)
            progress.progress(1.0, text="Hoàn tất")
            progress.empty()
            zip_name = f"PhieuDanhGiaV2_{branch_id}_{safe_name(file_name or 'diem').replace('.xlsx','')}.zip"
            st.success(f"Đã tạo {len(students)} phiếu cho {branch.get('branch_name')}")
            st.info(f"Database: mới {sync.get('new',0)} · đã có {sync.get('existing',0)} · trùng file {sync.get('duplicates_in_file',0)}")
            st.download_button("⬇️ Tải bộ phiếu Word", zip_data, zip_name, "application/zip", use_container_width=True)
        except Exception as exc:
            progress.empty()
            st.error(f"Không thể xử lý file: {exc}")

st.markdown(f"<div class='footer-note'>CIE/SIT Assessment V2 · Database Google Sheet · {SHEET_ID}</div>", unsafe_allow_html=True)
