import streamlit as st
import streamlit.components.v1 as components
import json
import csv
import io
import urllib.request

# ── Cấu hình trang ──
st.set_page_config(page_title="Comply Food AI", page_icon="🍊", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════════════
# SKILL: Tải dữ liệu Google Sheets (Publish to web CSV) tự động
# Mỗi lần user chỉnh sửa trên Sheets → tải lại trang = data mới
# ══════════════════════════════════════════════════════════════

SHEET_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTKmpa4_UNCuJTkZsRFFJLRqqc7tFm3q8OnbMWHI55k0f5MaYTAmhQpjP3D0hRTTg/pub"
GID_MASTER  = "1209441296"   # 📋 Master_QCVN
GID_TUKHOA  = "840797265"    # 🔑 TuKhoa_Mapping

def fetch_csv(gid):
    """Tải CSV từ Google Sheets Publish-to-web, trả về list of dicts."""
    url = f"{SHEET_BASE}?gid={gid}&single=true&output=csv"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        return [row for row in reader]
    except Exception:
        return []

@st.cache_data(ttl=10)   # Cache 10 giây — gần như real-time
def fetch_live_data():
    """Parse Master_QCVN + TuKhoa_Mapping → JSON format phù hợp cho HTML."""
    rows_master = fetch_csv(GID_MASTER)
    rows_tukhoa = fetch_csv(GID_TUKHOA)

    # Xây bảng từ khóa: id_nhom → [kw1, kw2, ...]
    kw_map = {}
    for r in rows_tukhoa:
        kw = (r.get("Từ khóa / Cụm từ người dùng hay nhập") or "").strip()
        id_nhom = (r.get("ID nhóm SP") or "").strip()
        if kw and id_nhom:
            kw_map.setdefault(id_nhom, []).append(kw)

    nhom_sp = {}
    for r in rows_master:
        # Tìm cột chứa ID (tên cột CSV có thể bị lệch vì merge cell trên Sheets)
        id_nhom = None
        ten_nhom = None
        for k, v in r.items():
            v_clean = (v or "").strip()
            if not v_clean:
                continue
            # ID nhóm: dạng XX-NNN (vd: DU-001, SUA-002, TP-001...)
            if not id_nhom and len(v_clean) <= 12 and "-" in v_clean and v_clean[0].isalpha():
                id_nhom = v_clean
            # Tên nhóm: chuỗi dài hơn, thường có dấu tiếng Việt
            elif not ten_nhom and len(v_clean) > 15:
                ten_nhom = v_clean

        if not id_nhom or not ten_nhom:
            continue

        # Lấy các cột theo thứ tự xuất hiện (CSV từ Sheets không ổn định tên cột)
        vals = [v.strip() for v in r.values() if v and v.strip()]
        qcvn_chinh = vals[2] if len(vals) > 2 else ""
        vb_lienquan = vals[3] if len(vals) > 3 else ""
        trang_thai  = vals[4] if len(vals) > 4 else "Còn hiệu lực"
        dien_cb     = vals[5] if len(vals) > 5 else ""
        chi_tieu    = vals[6] if len(vals) > 6 else ""

        so_hieu = qcvn_chinh.split("\n")[0].strip() if qcvn_chinh else ""
        
        # Xác định diện công bố
        dien_lower = dien_cb.lower()
        dien_key = "d1" if "1" in dien_lower else ("d2" if "2" in dien_lower else "d3")

        # Xác định trạng thái hiệu lực
        tt_lower = trang_thai.lower()
        tt_key = "con_hieu_luc" if "còn" in tt_lower else "het_hl_mot_phan"

        # Lấy từ khóa từ sheet TuKhoa_Mapping
        tu_khoa = kw_map.get(id_nhom, [ten_nhom.lower().split("(")[0].strip()])

        nhom_sp[id_nhom] = {
            "id": id_nhom,
            "ten": ten_nhom.split("\n")[0].strip(),
            "moTa": ten_nhom if "\n" in ten_nhom else f"Diện: {dien_cb}",
            "qcvnChinh": {
                "soHieu": so_hieu,
                "ten": qcvn_chinh,
                "banHanh": "Bộ Y tế",
                "hieuLuc": "Hiện hành",
                "trangThai": tt_key
            },
            "vanBanLienQuan": [],
            "dien": dien_key,
            "chiTieu": {},
            "ccpNote": "",
            "tuKhoa": tu_khoa
        }

    return {"nhomSanPham": nhom_sp} if nhom_sp else None


# ── Tải dữ liệu live ──
live_db = fetch_live_data()

# ── Sidebar điều hướng ──
st.sidebar.markdown("<h3 style='color:#FF5722;'>🍊 ComplyFood</h3>", unsafe_allow_html=True)
app_mode = st.sidebar.radio(
    "Chọn ứng dụng:",
    ["📋 Quy trình Phase 1 & 2", "🔍 2.1 Mapping QCVN"]
)

if st.sidebar.button("🔄 Làm mới dữ liệu"):
    st.cache_data.clear()
    st.rerun()

if live_db and live_db.get("nhomSanPham"):
    n = len(live_db["nhomSanPham"])
    st.sidebar.success(f"✅ Đã đồng bộ {n} nhóm SP từ Google Sheets")
else:
    st.sidebar.warning("⚠️ Không tải được Sheets — dùng dữ liệu nền")

# ── CSS ẩn UI thừa của Streamlit ──
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    iframe {
        height: 92vh !important;
        width: 100% !important;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# RENDER
# ══════════════════════════════════════════════════════════════

if app_mode == "📋 Quy trình Phase 1 & 2":
    file_path = r"d:\.antigravity\3. FOOD WHY - Smart Assistant\complyfood_phase1_2.html"
    with open(file_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    # Chuyển theme sang cam FOOD WHY
    html_code = html_code.replace('#1A7A5E', '#FF5722')
    html_code = html_code.replace('#0F5441', '#E64A19')
    html_code = html_code.replace('#E6F4EF', '#FFF3E0')
    html_code = html_code.replace('#B2DDD0', '#FFCC80')
    html_code = html_code.replace('rgba(26,122,94,', 'rgba(255,87,34,')
    html_code = html_code.replace(
        'background: linear-gradient(135deg,#1A3D8A 0%,#1A5FA8 100%)',
        'background: linear-gradient(135deg, #E64A19 0%, #FF5722 100%)'
    )
    components.html(html_code, height=900, scrolling=True)

else:
    # Đọc HTML template Mapping QCVN (có FALLBACK_DB sẵn bên trong)
    file_path = r"d:\.antigravity\3. FOOD WHY - Smart Assistant\ComplyFood_UI.html"
    with open(file_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    # Inject dữ liệu live từ Google Sheets vào window.parentDb
    # HTML sẽ merge với FALLBACK_DB: nhóm mới thêm vào, từ khóa bổ sung
    if live_db:
        db_json = json.dumps(live_db, ensure_ascii=False)
        inject = f"<script>window.parentDb={db_json};</script>"
        html_code = html_code.replace("</head>", f"{inject}\n</head>")

    components.html(html_code, height=900, scrolling=True)
