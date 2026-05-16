import streamlit as st
import firebase_utils

# Đồng bộ dữ liệu từ Cloud khi khởi chạy (chỉ chạy 1 lần mỗi session)
if "firebase_synced" not in st.session_state:
    with st.spinner("🔄 Đang kết nối và đồng bộ dữ liệu từ Firebase..."):
        firebase_utils.init_sync_from_firebase()
        st.session_state.firebase_synced = True
import json
import os
import re
import time
import PyPDF2
import pandas as pd
from datetime import datetime

# ── Cấu hình trang ──
st.set_page_config(page_title="QA AI Academy", page_icon="🎓", layout="wide")

# ── CSS chuyên nghiệp tông Cam FOOD WHY ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
* { font-family: 'Inter', sans-serif; }

.academy-hero {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 50%, #c2410c 100%);
    color: white; padding: 35px 40px; border-radius: 20px;
    text-align: center; margin-bottom: 30px;
    box-shadow: 0 12px 30px -8px rgba(249,115,22,0.5);
    position: relative; overflow: hidden;
}
.academy-hero::before {
    content: ''; position: absolute; top: -50%; right: -20%;
    width: 300px; height: 300px; border-radius: 50%;
    background: rgba(255,255,255,0.08);
}
.academy-hero h1 { font-size: 2.2rem; font-weight: 900; margin: 0 0 5px 0; letter-spacing: 1px; }
.academy-hero p { font-size: 1rem; opacity: 0.9; margin: 0; }

.unit-card {
    background: white; border: 2px solid #fed7aa; border-radius: 16px;
    padding: 22px 18px; text-align: center; cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04); height: 100%;
}
.unit-card:hover {
    border-color: #f97316; transform: translateY(-6px);
    box-shadow: 0 12px 24px -6px rgba(249,115,22,0.25);
}
.unit-card .icon { font-size: 2.8rem; margin-bottom: 10px; }
.unit-card .title {
    font-size: 0.95rem; font-weight: 700; color: #c2410c;
    margin-bottom: 6px; line-height: 1.3;
}
.unit-card .desc { font-size: 0.78rem; color: #78716c; line-height: 1.4; }

.unit-badge {
    display: inline-block; background: #f97316; color: white;
    font-size: 0.7rem; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; margin-bottom: 8px;
}

.access-box {
    background: linear-gradient(135deg, #fff7ed, #ffedd5);
    border: 2px solid #fdba74; border-radius: 14px;
    padding: 20px; margin-bottom: 20px;
}
.access-box h4 { color: #c2410c; margin: 0 0 8px 0; }

.ref-chip {
    display: inline-block; background: #fff7ed; border: 1px solid #fed7aa;
    color: #9a3412; font-size: 0.75rem; padding: 4px 10px;
    border-radius: 8px; margin: 3px 2px; font-weight: 600;
}

.knowledge-block {
    background: #fffbeb; border-left: 4px solid #f97316;
    padding: 14px 18px; border-radius: 0 10px 10px 0;
    margin-bottom: 10px; font-size: 0.88rem; color: #44403c;
}

.stat-pill {
    background: white; border: 2px solid #fed7aa; border-radius: 12px;
    padding: 12px 16px; text-align: center;
}
.stat-pill .num { font-size: 1.6rem; font-weight: 900; color: #f97316; }
.stat-pill .label { font-size: 0.75rem; color: #78716c; }

.sidebar-brand {
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: white; padding: 18px; border-radius: 12px; margin-bottom: 15px;
    box-shadow: 0 8px 16px -4px rgba(249,115,22,0.4);
}
.sidebar-brand h3 { margin: 0; font-weight: 900; font-size: 1.3rem; }
.sidebar-brand p { margin: 4px 0 0 0; font-size: 0.8rem; opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# ── Dữ liệu Unit (10 cố định + custom từ Leader) ──
UNITS_BASE = {
    "unit_1":  {"icon": "🐷", "short": "Thịt Heo & Gà", "desc": "PSE, DFD, phúc lợi động vật, cảm quan thịt tươi"},
    "unit_2":  {"icon": "🦠", "short": "Vi Sinh Vật", "desc": "Salmonella, Listeria, E.coli, Biofilm"},
    "unit_3":  {"icon": "💧", "short": "Nước & Nước Đá", "desc": "QCVN, Clo hoạt tính, nước chiller"},
    "unit_4":  {"icon": "❄️", "short": "Chuỗi Lạnh", "desc": "Cấp đông, rã đông, drip loss"},
    "unit_5":  {"icon": "🧂", "short": "Phụ Gia Thịt", "desc": "Nitrite, Phosphate, Ascorbic acid"},
    "unit_6":  {"icon": "📦", "short": "Đóng Gói", "desc": "MAP, Vacuum, màng co PA/PE"},
    "unit_7":  {"icon": "🚧", "short": "Lây Nhiễm Chéo", "desc": "Raw vs Cooked, Allergen, phân vùng"},
    "unit_8":  {"icon": "🔍", "short": "Dị Vật", "desc": "Xương, kim loại, X-ray, dò kim loại"},
    "unit_9":  {"icon": "🧹", "short": "SSOP", "desc": "7 bước vệ sinh, hóa chất, Swab test"},
    "unit_10": {"icon": "📜", "short": "Pháp Chế & Thú Y", "desc": "Luật ATTP, truy xuất, thu hồi"},
}

KNOWLEDGE_DIR_EARLY = os.path.join(os.path.dirname(__file__), "..", "knowledge")
CUSTOM_UNITS_FILE = os.path.join(KNOWLEDGE_DIR_EARLY, "custom_units.json")

def load_custom_units():
    if os.path.exists(CUSTOM_UNITS_FILE):
        with open(CUSTOM_UNITS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def save_custom_unit(key, icon, short, desc):
    cu = load_custom_units()
    cu[key] = {"icon": icon, "short": short, "desc": desc, "custom": True}
    with open(CUSTOM_UNITS_FILE, "w", encoding="utf-8") as f: json.dump(cu, f, ensure_ascii=False)
    firebase_utils.sync_all_to_firebase()

def get_all_units():
    merged = dict(UNITS_BASE)
    merged.update(load_custom_units())
    return merged

UNITS = get_all_units()

# ── Load Knowledge Base (Tầng 1: JSON gốc + Tầng 2: Tài liệu Sếp đã lưu vĩnh viễn) ──
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")

@st.cache_data
def load_knowledge():
    kb_path = os.path.join(KNOWLEDGE_DIR, "knowledge_base.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def load_saved_docs(unit_key):
    """Đọc tất cả file .txt đã lưu vĩnh viễn trong thư mục knowledge/unit_X/"""
    unit_dir = os.path.join(KNOWLEDGE_DIR, unit_key)
    combined = ""
    if os.path.isdir(unit_dir):
        for fname in sorted(os.listdir(unit_dir)):
            fpath = os.path.join(unit_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".txt"):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        combined += f"\n--- [{fname}] ---\n" + f.read()
                except:
                    pass
    return combined

def save_doc_permanently(unit_key, filename, content):
    """Lưu tài liệu vĩnh viễn vào thư mục knowledge/unit_X/ và Firebase"""
    unit_dir = os.path.join(KNOWLEDGE_DIR, unit_key)
    os.makedirs(unit_dir, exist_ok=True)
    safe_name = re.sub(r'[^\w\-.]', '_', filename)
    if not safe_name.endswith(".txt"):
        safe_name += ".txt"
    fpath = os.path.join(unit_dir, safe_name)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Đồng bộ văn bản lên mây vĩnh viễn
    firebase_utils.save_knowledge_text(unit_key, safe_name, content)
    
    return safe_name

knowledge = load_knowledge()

# ── Research Master Data (Lưu vĩnh viễn) ──
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
RESEARCH_TASK_FILE = os.path.join(DATA_DIR, "research_tasks.json")
RESEARCH_SUB_FILE  = os.path.join(DATA_DIR, "research_submissions.json")

def load_research_tasks():
    if os.path.exists(RESEARCH_TASK_FILE):
        with open(RESEARCH_TASK_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return []
def save_research_tasks(d):
    with open(RESEARCH_TASK_FILE, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False)
    firebase_utils.sync_all_to_firebase()
def load_research_subs():
    if os.path.exists(RESEARCH_SUB_FILE):
        with open(RESEARCH_SUB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return []
def append_research_sub(sub):
    subs = load_research_subs()
    subs.append(sub)
    with open(RESEARCH_SUB_FILE, "w", encoding="utf-8") as f: json.dump(subs, f, ensure_ascii=False)
    firebase_utils.sync_all_to_firebase()

def get_next_custom_unit_key():
    """Tính key tiếp theo: unit_11, unit_12..."""
    cu = load_custom_units()
    if not cu: return "unit_11"
    nums = [int(k.split("_")[1]) for k in cu if k.startswith("unit_")]
    return f"unit_{max(nums)+1}" if nums else "unit_11"

# ── Quản lý Dữ liệu Kỳ thi ──
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

EXAM_FILE = os.path.join(DATA_DIR, "monthly_exam.json")
RESULTS_FILE = os.path.join(DATA_DIR, "exam_results.json")

def load_exam():
    if os.path.exists(EXAM_FILE):
        with open(EXAM_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"active": False, "question": "", "month": "", "created_at": 0}

def save_exam(exam_data):
    with open(EXAM_FILE, "w", encoding="utf-8") as f: json.dump(exam_data, f, ensure_ascii=False)
    firebase_utils.sync_all_to_firebase()

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return []

def save_result(result):
    results = load_results()
    # Kiểm tra nếu người này đã thi tháng này chưa (tránh thi nhiều lần)
    for r in results:
        if r["name"] == result["name"] and r["month"] == result["month"]:
            return False # Đã thi rồi
    results.append(result)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f: json.dump(results, f, ensure_ascii=False)
    firebase_utils.sync_all_to_firebase()
    return True

CASE_STUDIES_FILE = os.path.join(DATA_DIR, "case_studies.json")
def load_case_studies():
    if os.path.exists(CASE_STUDIES_FILE):
        with open(CASE_STUDIES_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}
def save_case_studies(d):
    with open(CASE_STUDIES_FILE, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False)
    firebase_utils.sync_all_to_firebase()

# ── Cấu hình API & Xác thực ──
def get_api_key_and_model():
    """Trả về (api_key, source) dựa trên quyền truy cập."""
    # 1. Nội bộ đã phân quyền (Admin, QM, QA)
    if st.session_state.get("user_role") and st.session_state.get("active_api_key"):
        return st.session_state.active_api_key, "internal"
        
    # Giữ fallback cho internal_unlocked cũ
    if st.session_state.get("internal_unlocked"):
        try:
            key = st.secrets["TRAINING_API_KEY"]
            if key: return key, "internal"
        except: pass
        try:
            key = st.secrets["GEMINI_API_KEY"]
            if key: return key, "internal"
        except: pass
    # 2. Người dùng tự nhập Key
    user_key = (st.session_state.get("user_api_key") or "").strip()
    if user_key:
        return user_key, "user_key"
    # 3. Public miễn phí (giới hạn 3 câu/ngày)
    try:
        key = st.secrets["TRAINING_API_KEY"]
        if key: return key, "public_free"
    except: pass
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if key: return key, "public_free"
    except: pass
    return None, None

# ── Session State khởi tạo ──
for key in ["user_role", "active_api_key", "internal_unlocked", "selected_unit", "unit_chat_history",
            "daily_question_count", "user_api_key", "uploaded_docs_text"]:
    if key not in st.session_state:
        if key == "internal_unlocked":
            st.session_state[key] = False
        elif key == "daily_question_count":
            st.session_state[key] = 0
        elif key in ("unit_chat_history", "uploaded_docs_text"):
            st.session_state[key] = {}
        else:
            st.session_state[key] = None

MAX_FREE_QUESTIONS = 3

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h3>🎓 QA AI Academy</h3>
        <p>Trường Đào Tạo QA Ngành Thịt</p>
    </div>
    """, unsafe_allow_html=True)

    # Cổng bảo vệ nội bộ
    st.markdown('<div class="access-box"><h4>🔐 Truy cập Nội bộ</h4></div>', unsafe_allow_html=True)
    if st.session_state.get("user_role"):
        roles = {"admin": "Admin (Sếp)", "qm": "Quản lý (QM)", "qa": "Nhân viên (QA)"}
        role_name = roles.get(st.session_state.user_role, "")
        st.success(f"✅ Đã đăng nhập: **{role_name}**")
        if st.button("🔒 Đăng xuất", use_container_width=True):
            st.session_state.user_role = None
            st.session_state.active_api_key = None
            st.session_state.internal_unlocked = False
            st.rerun()
    else:
        pw = st.text_input("Nhập mật khẩu nội bộ:", type="password", key="pw_input")
        if st.button("Đăng nhập", use_container_width=True):
            # 1. Sếp (Admin)
            try: admin_pw = st.secrets["INTERNAL_PASSWORD"]
            except: admin_pw = "LeaderFoodWhy2024"
            
            if pw == admin_pw:
                st.session_state.user_role = "admin"
                try: admin_key = st.secrets["TRAINING_API_KEY"]
                except: admin_key = st.secrets.get("GEMINI_API_KEY", "")
                st.session_state.active_api_key = admin_key
                st.session_state.internal_unlocked = True
                st.rerun()
            # 2. QM (Quản lý)
            elif pw == "QMMML8386":
                st.session_state.user_role = "qm"
                try: qm_key = st.secrets["QM_API_KEY"]
                except: qm_key = st.secrets.get("GEMINI_API_KEY", "")
                st.session_state.active_api_key = qm_key
                st.session_state.internal_unlocked = True
                st.rerun()
            # 3. QA (Nhân viên)
            elif pw == "LeaderQA2026":
                st.session_state.user_role = "qa"
                try: qa_key = st.secrets["QA_API_KEY"]
                except: qa_key = st.secrets.get("GEMINI_API_KEY", "")
                st.session_state.active_api_key = qa_key
                st.session_state.internal_unlocked = True
                st.rerun()
            else:
                st.error("❌ Sai mật khẩu!")

    st.divider()

    # Thống kê
    remaining = max(0, MAX_FREE_QUESTIONS - st.session_state.daily_question_count)
    if not st.session_state.get("user_role") and not st.session_state.get("user_api_key"):
        st.markdown("Câu hỏi miễn phí còn lại")
        st.markdown(f"<h1 style='color:#44403c; margin:0;'>{remaining}/{MAX_FREE_QUESTIONS}</h1>", unsafe_allow_html=True)
        # Nhập API Key cá nhân (cho cộng đồng)
        st.markdown("**🔑 Hoặc nhập API Key cá nhân:**")
        st.caption("Lấy Key miễn phí tại [Google AI Studio](https://aistudio.google.com/apikey)")
        user_key_input = st.text_input("API Key của bạn:", type="password", key="api_key_input")
        if user_key_input:
            st.session_state.user_api_key = user_key_input
            st.success("✅ Đã nhận Key — Không giới hạn câu hỏi!")
        st.divider()

    st.divider()
    st.caption("© 2026 FOOD WHY Studio")

# ── TRANG CHÍNH ──
# Hero
st.markdown("""
<div class="academy-hero">
    <h1>🎓 QA AI ACADEMY</h1>
    <p>Trường Đào Tạo Thực Chiến — Chuyên Ngành Giết Mổ & Chế Biến Thịt</p>
</div>
""", unsafe_allow_html=True)

# Thống kê nhanh
all_units_now = get_all_units()
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="stat-pill"><div class="num">{len(all_units_now)}</div><div class="label">Chuyên Đề</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="stat-pill"><div class="num">🤖</div><div class="label">AI Mentor</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="stat-pill"><div class="num">📝</div><div class="label">Bài Tập Tình Huống</div></div>', unsafe_allow_html=True)
with c4:
    cloud_subs_header = firebase_utils.get_research_submissions()
    subs_count = len(cloud_subs_header) if cloud_subs_header else 0
    st.markdown(f'<div class="stat-pill"><div class="num">{subs_count}</div><div class="label">Bài Nghiên Cứu</div></div>', unsafe_allow_html=True)

st.write("")

# ── Top-level tabs: Học Tập vs Nghiên Cứu ──
tab_academy, tab_research = st.tabs(["  📖 Học Tập   ", "  ⚔️ Nghiên Cứu Leader   "])

# ================== TAB HỌc TẬP ==================
with tab_academy:
  UNITS = get_all_units()  # reload để bắt được unit mới nhất
  if st.session_state.selected_unit is None:
    st.subheader("📖 Chọn Chuyên Đề Học Tập")
    unit_keys = list(UNITS.keys())
    for row_start in range(0, len(unit_keys), 5):
        cols = st.columns(5)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(unit_keys): break
            unit_key = unit_keys[idx]
            unit_num = unit_key.split("_")[1]
            unit = UNITS[unit_key]
            badge_color = "#4338ca" if unit.get("custom") else "#f97316"
            with col:
                st.markdown(f"""
                <div class="unit-card">
                    <div class="unit-badge" style="background:{badge_color}">{'⚔️ ' if unit.get('custom') else ''}Unit {unit_num}</div>
                    <div class="icon">{unit["icon"]}</div>
                    <div class="title">{unit["short"]}</div>
                    <div class="desc">{unit["desc"]}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Vào học →", key=f"btn_{unit_key}", use_container_width=True):
                    st.session_state.selected_unit = unit_key
                    st.rerun()

  # ── Bên trong Unit ──
  else:
    unit_key = st.session_state.selected_unit
    unit_num = unit_key.split("_")[1]
    UNITS = get_all_units()
    unit_info = UNITS.get(unit_key, {"icon": "📄", "short": unit_key, "desc": ""})
    kb = knowledge.get(unit_key, {})

    # Nút quay lại
    if st.button("← Quay lại danh sách chuyên đề"):
        st.session_state.selected_unit = None
        st.rerun()

    # Header Unit
    st.markdown(f"""
    <div class="academy-hero" style="padding: 25px 30px; text-align: left;">
        <h1>{unit_info["icon"]} Unit {unit_num}: {unit_info["short"]}</h1>
        <p>{kb.get("title", unit_info["desc"])}</p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs chính
    tab_learn, tab_ask, tab_exam, tab_arena, tab_docs = st.tabs([
        "📖 Kiến Thức Cốt Lõi", "💬 Hỏi AI Mentor", "📝 Bài Tập Tình Huống", "🏆 Đấu Trường QA (Tháng)", "📁 Tài Liệu Bổ Sung"
    ])

    # ── TAB 1: Kiến thức ──
    with tab_learn:
        st.markdown("### 📚 Nguồn Tài Liệu Tham Khảo")
        refs = kb.get("references", [])
        if refs:
            chips_html = "".join([f'<span class="ref-chip">📗 {r}</span>' for r in refs])
            st.markdown(chips_html, unsafe_allow_html=True)
        else:
            st.info("Chưa có tài liệu tham khảo.")

        st.markdown("### 🧠 Kiến Thức Trọng Tâm")
        core = kb.get("core_knowledge", [])
        if core:
            for item in core:
                st.markdown(f'<div class="knowledge-block">{item}</div>', unsafe_allow_html=True)
        else:
            st.info("Kiến thức đang được cập nhật.")

        # Hiện tài liệu bổ sung nếu đã upload
        extra = st.session_state.uploaded_docs_text.get(unit_key, "")
        if extra:
            st.markdown("### 📄 Kiến Thức Bổ Sung (Tạm thời)")
            st.markdown(f'<div class="knowledge-block">{extra[:2000]}...</div>' if len(extra) > 2000 
                       else f'<div class="knowledge-block">{extra}</div>', unsafe_allow_html=True)

    # ── TAB 2: Hỏi AI ──
    with tab_ask:
        st.markdown(f"### 💬 Hỏi AI Mentor về **{unit_info['short']}**")

        api_key, source = get_api_key_and_model()
        can_ask = True

        if source == "public_free":
            remaining = MAX_FREE_QUESTIONS - st.session_state.daily_question_count
            if remaining <= 0:
                can_ask = False
                st.warning("⚠️ Bạn đã hết 3 câu hỏi miễn phí hôm nay! Nhập mật khẩu nội bộ hoặc API Key cá nhân ở thanh bên trái để tiếp tục.")
            else:
                st.info(f"🎁 Bạn còn **{remaining}** câu hỏi miễn phí hôm nay.")
        elif source == "internal":
            st.success("🔓 Chế độ Nội bộ — Không giới hạn câu hỏi!")
        elif source == "user_key":
            st.success("🔑 Đang dùng API Key cá nhân — Không giới hạn!")
        elif api_key is None:
            can_ask = False
            st.error("⚠️ Chưa có API Key. Vui lòng nhập mật khẩu nội bộ hoặc API Key cá nhân.")

        # Chat history cho unit này
        chat_key = f"chat_{unit_key}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        question = st.chat_input(f"Hỏi về {unit_info['short']}..." if can_ask else "Hết lượt hỏi miễn phí...", disabled=not can_ask)

        if question and can_ask and api_key:
            st.session_state[chat_key].append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            # Xây context từ: Tầng 1 (JSON gốc) + Tầng 2 (Tài liệu lưu vĩnh viễn) + Tầng 3 (Upload tạm)
            context_parts = []
            if core:
                context_parts.append("KIẾN THỨC NỀN TẢNG (Nguồn: FAO, Codex, USDA, WHO):\n" + "\n".join(core))
            saved_docs = load_saved_docs(unit_key)
            if saved_docs:
                context_parts.append("TÀI LIỆU CHUYÊN SÂU (Đã được Quản lý lưu trữ):\n" + saved_docs[:5000])
            extra_doc = st.session_state.uploaded_docs_text.get(unit_key, "")
            if extra_doc:
                context_parts.append("TÀI LIỆU BỔ SUNG TẠM THỜI (Người dùng upload):\n" + extra_doc[:3000])
            context = "\n\n".join(context_parts)

            system = f"""Bạn là AI Mentor CHUYÊN GIA ngành Giết mổ & Chế biến Thịt, thuộc hệ thống FOOD WHY Academy.
Bạn đang hỗ trợ học viên về chuyên đề: {unit_info['short']}.

Dưới đây là tài liệu tham khảo NỘI BỘ được cung cấp:

{context}

Quy tắc trả lời:
- BẮT BUỘC trả lời bằng tiếng Việt, rõ ràng, có ví dụ thực tế từ nhà máy giết mổ/chế biến thịt.
- ƯU TIÊN dùng kiến thức từ tài liệu nội bộ ở trên. Nếu tài liệu nội bộ chưa đủ chi tiết, bạn ĐƯỢC PHÉP bổ sung thêm kiến thức chuyên ngành của bạn (khoa học thực phẩm, an toàn thực phẩm, công nghệ chế biến thịt) để trả lời đầy đủ hơn.
- Khi dùng kiến thức bổ sung, hãy ghi rõ nguồn (ví dụ: "Theo tiêu chuẩn BRCGS...", "Theo nghiên cứu của...").
- Nếu câu hỏi hoàn toàn nằm ngoài lĩnh vực thực phẩm, nhắc nhở học viên.
- Trình bày bằng Markdown, có tiêu đề phụ và bullet points."""

            with st.chat_message("assistant"):
                with st.spinner("AI đang suy nghĩ..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key, transport="rest")
                        m = genai.GenerativeModel('gemini-2.5-flash')
                        resp = m.generate_content(system + "\n\nCÂU HỎI: " + question)
                        answer = resp.text
                        st.markdown(answer)
                        st.session_state[chat_key].append({"role": "assistant", "content": answer})
                        if source == "public_free":
                            st.session_state.daily_question_count += 1
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

    # ── TAB 3: Bài tập tình huống ──
    with tab_exam:
        st.markdown(f"### 📝 Bài Tập Tình Huống — Unit {unit_num}: {unit_info['short']}")

        api_key, source = get_api_key_and_model()
        case_studies = load_case_studies()
        active_scenario = case_studies.get(unit_key)

        col_qm, col_qa = st.columns(2)

        with col_qm:
            st.markdown("""
            <div class="access-box">
                <h4>👨‍💼 Khu vực QM (Ra đề)</h4>
            </div>
            """, unsafe_allow_html=True)
            if active_scenario:
                st.success("✅ Đang có bài tập được giao cho QA.")
                st.info(f"**Nội dung:** {active_scenario}")
                with st.popover("🔒 Đóng bài tập"):
                    close_pw = st.text_input("Mật khẩu nội bộ:", type="password", key=f"close_pw_{unit_key}")
                    if st.button("Xác nhận Đóng", type="primary", key=f"close_btn_{unit_key}"):
                        try: cpw = st.secrets["INTERNAL_PASSWORD"]
                        except: cpw = "LeaderFoodWhy2024"
                        if close_pw == cpw:
                            del case_studies[unit_key]
                            save_case_studies(case_studies)
                            st.success("Đã đóng bài tập!")
                            st.rerun()
                        else:
                            st.error("Sai mật khẩu!")
            else:
                exam_key = f"exam_scenario_{unit_key}"
                scenario = st.text_area(
                    "Nhập tình huống / số liệu thực tế:",
                    placeholder=f"Ví dụ: Kết quả Swab test bề mặt thớt cắt sau vệ sinh: TPC = 850 CFU/cm². Yêu cầu nội bộ < 100 CFU/cm². Hãy phân tích...",
                    height=200, key=exam_key
                )
                if st.button("📤 Giao bài cho QA", key=f"submit_exam_{unit_key}", use_container_width=True):
                    if scenario:
                        case_studies[unit_key] = scenario
                        save_case_studies(case_studies)
                        st.success("✅ Đã giao bài! QA hãy chuyển sang ô bên phải để làm bài.")
                        st.rerun()
                    else:
                        st.warning("Vui lòng nhập tình huống trước!")

        with col_qa:
            st.markdown("""
            <div class="access-box">
                <h4>👩‍🔬 Khu vực QA (Làm bài)</h4>
            </div>
            """, unsafe_allow_html=True)
            if active_scenario:
                st.info(f"📋 **Đề bài:** {active_scenario}")
                answer_key = f"qa_answer_{unit_key}"
                qa_answer = st.text_area("Viết câu trả lời của bạn:", height=200, key=answer_key)
                if st.button("🤖 Nhờ AI chấm điểm", key=f"grade_{unit_key}", use_container_width=True):
                    if qa_answer and api_key:
                        with st.spinner("AI đang chấm bài..."):
                            try:
                                import google.generativeai as genai
                                genai.configure(api_key=api_key, transport="rest")
                                m = genai.GenerativeModel('gemini-2.5-flash')
                                grade_prompt = f"""Bạn là Giám khảo chuyên ngành An toàn Thực phẩm (ngành Thịt).
Chấm điểm bài làm của QA dựa trên thang 10 điểm.

TÌNH HUỐNG: {active_scenario}

BÀI LÀM CỦA QA: {qa_answer}

KIẾN THỨC CHUẨN: {chr(10).join(core)}

Hãy:
1. Cho điểm (X/10) và nhận xét tổng quan.
2. Chỉ ra điểm ĐÚNG và điểm SAI/THIẾU SÓT.
3. Đưa ra đáp án mẫu ngắn gọn.
Trình bày bằng Markdown, tiếng Việt."""
                                resp = m.generate_content(grade_prompt)
                                st.markdown(resp.text)
                                if source == "public_free":
                                    st.session_state.daily_question_count += 1
                            except Exception as e:
                                st.error(f"Lỗi: {e}")
                    elif not api_key:
                        st.error("Cần API Key để chấm bài!")
            else:
                st.info("⏳ Chưa có bài tập. Chờ QM ra đề ở ô bên trái.")

    # ── TAB 4: Đấu trường QA (Tháng) ──
    with tab_arena:
        st.markdown(f"### 🏆 Đấu Trường QA — Kỳ Thi Tháng")
        
        user_role = st.session_state.get("user_role")
        is_qm_admin = user_role in ["admin", "qm"]
        exam_data = load_exam()
        
        # 1. GIAO DIỆN CHO QUẢN LÝ (QM)
        if is_qm_admin:
            with st.expander("👨‍💼 Bảng Điều Khiển Kỳ Thi (QM Only)", expanded=not exam_data["active"]):
                st.write("Sếp hãy đặt đề bài cho kỳ thi tháng này. Khi bấm 'Kích hoạt', tất cả nhân viên sẽ nhận được đề.")
                new_month = st.text_input("Kỳ thi tháng (Vd: Tháng 05/2024):", value=datetime.now().strftime("Tháng %m/%Y"))
                new_q = st.text_area("Đề thi chung:", placeholder="Nhập tình huống hóc búa nhất tháng này...")
                
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("🚀 KÍCH HOẠT KỲ THI", use_container_width=True, type="primary"):
                    if new_q and new_month:
                        exam_data = {"active": True, "question": new_q, "month": new_month, "created_at": time.time()}
                        save_exam(exam_data)
                        st.success("✅ Đã kích hoạt kỳ thi! Nhân viên có thể bắt đầu thi.")
                        st.rerun()
                
                if c_btn2.button("🚫 KẾT THÚC KỲ THI", use_container_width=True):
                    exam_data["active"] = False
                    save_exam(exam_data)
                    st.warning("Đã đóng kỳ thi. Nhân viên không thể nộp bài mới.")
                    st.rerun()

        # 2. GIAO DIỆN CHO NHÂN VIÊN (QA)
        st.markdown("---")
        if not exam_data["active"]:
            st.info("🏁 Hiện tại không có kỳ thi nào đang diễn ra. Chờ QM kích hoạt đề thi mới!")
        else:
            st.markdown(f"#### 📅 Kỳ thi: <span style='color:#f97316'>{exam_data['month']}</span>", unsafe_allow_html=True)
            
            # Form bắt đầu thi
            if f"exam_started_{unit_key}" not in st.session_state:
                st.write("🔔 **Quy tắc:** Sếp cho bạn đúng **5 phút** để hoàn thành bài thi này. AI sẽ chấm điểm và xếp hạng ngay lập tức!")
                qa_name = st.text_input("Nhập Họ và Tên của bạn để bắt đầu:", key=f"qa_name_input_{unit_key}")
                if st.button("🔥 BẮT ĐẦU LÀM BÀI (5 PHÚT)", key=f"start_exam_{unit_key}", type="primary"):
                    if qa_name.strip():
                        st.session_state[f"exam_started_{unit_key}"] = True
                        st.session_state[f"exam_start_time_{unit_key}"] = time.time()
                        st.session_state[f"qa_real_name_{unit_key}"] = qa_name.strip()
                        st.rerun()
                    else:
                        st.error("Vui lòng nhập tên trước khi thi!")
            
            # Màn hình đang thi
            else:
                elapsed = time.time() - st.session_state[f"exam_start_time_{unit_key}"]
                remaining_sec = max(0, 300 - int(elapsed)) # 5 phút = 300 giây
                
                # Hiển thị đồng hồ
                mins, secs = divmod(remaining_sec, 60)
                timer_color = "#f97316" if remaining_sec > 60 else "#ef4444"
                st.markdown(f"""
                <div style="text-align:center; padding:10px; border-radius:10px; background:{timer_color}; color:white; margin-bottom:20px;">
                    <span style="font-size:14px;">⏳ Thời gian còn lại:</span><br>
                    <span style="font-size:32px; font-weight:900;">{mins:02d}:{secs:02d}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if remaining_sec <= 0:
                    st.error("⌛ HẾT GIỜ! Bạn không thể nộp bài nữa.")
                    if st.button("Quay lại"): 
                        del st.session_state[f"exam_started_{unit_key}"]
                        st.rerun()
                else:
                    st.markdown(f"**ĐỀ BÀI:**\n> {exam_data['question']}")
                    qa_ans = st.text_area("Câu trả lời của bạn:", height=250, key=f"arena_ans_{unit_key}")
                    
                    if st.button("✅ NỘP BÀI & CHẤM ĐIỂM", key=f"submit_arena_{unit_key}", use_container_width=True):
                        if qa_ans.strip():
                            with st.spinner("AI đang chấm điểm bài thi của bạn..."):
                                try:
                                    api_key, _ = get_api_key_and_model()
                                    import google.generativeai as genai
                                    genai.configure(api_key=api_key, transport="rest")
                                    m = genai.GenerativeModel('gemini-2.5-flash')
                                    
                                    grade_prompt = f"""Bạn là Giám khảo Kỳ thi Tháng QA.
ĐỀ THI: {exam_data['question']}
BÀI LÀM: {qa_ans}
Hãy chấm điểm cực kỳ nghiêm túc trên thang 10. Trả lời đúng 1 số điểm duy nhất ở dòng đầu tiên, sau đó là nhận xét ngắn gọn.
Định dạng dòng 1: [DIEM: X/10]"""
                                    resp = m.generate_content(grade_prompt)
                                    full_resp = resp.text
                                    
                                    # Trích xuất điểm
                                    score_match = re.search(r'\[DIEM:\s*(\d+\.?\d*)/10\]', full_resp)
                                    score = float(score_match.group(1)) if score_match else 5.0
                                    
                                    # Lưu kết quả vĩnh viễn
                                    new_res = {
                                        "name": st.session_state[f"qa_real_name_{unit_key}"],
                                        "month": exam_data["month"],
                                        "score": score,
                                        "answer": qa_ans,
                                        "feedback": full_resp,
                                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    }
                                    if save_result(new_res):
                                        st.balloons()
                                        st.success(f"🎉 Chúc mừng {new_res['name']}! AI đã chấm bạn: **{score}/10** điểm.")
                                        st.markdown(full_resp)
                                        # Reset trạng thái thi
                                        del st.session_state[f"exam_started_{unit_key}"]
                                    else:
                                        st.warning("Bạn đã nộp bài thi cho tháng này rồi, không thể nộp thêm!")
                                except Exception as e:
                                    st.error(f"Lỗi AI: {e}")
                        else:
                            st.warning("Vui lòng viết câu trả lời!")

        # 3. BẢNG XẾP HẠNG (LEADERBOARD)
        st.markdown("---")
        st.markdown("### 📊 Bảng Xếp Hạng Team QA")
        all_results = load_results()
        if not all_results:
            st.info("Chưa có kết quả thi nào.")
        else:
            df = pd.DataFrame(all_results)
            # Chỉ lọc kết quả của tháng hiện tại
            if exam_data["active"]:
                df = df[df["month"] == exam_data["month"]]
            
            if not df.empty:
                df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
                df.index += 1 # Xếp hạng từ 1
                
                # Hiển thị bảng đẹp
                st.dataframe(
                    df[["name", "score", "date"]].rename(columns={"name": "Họ Tên", "score": "Điểm AI", "date": "Ngày thi"}),
                    use_container_width=True
                )
                
                # QM có quyền xóa kết quả hoặc xuất file
                if user_role in ["admin", "qm"]:
                    if st.button("🗑️ Xóa toàn bộ kết quả (Cẩn thận!)"):
                        with open(RESULTS_FILE, "w", encoding="utf-8") as f: json.dump([], f)
                        firebase_utils.sync_all_to_firebase()
                        st.rerun()
            else:
                st.info("Tháng này chưa có ai nộp bài.")

    # ── TAB 5: Tài liệu bổ sung ──
    with tab_docs:
        st.markdown(f"### 📁 Tải Tài Liệu Bổ Sung cho Unit {unit_num}")

        user_role = st.session_state.get("user_role")
        is_qm_admin = user_role in ["admin", "qm"]

        if is_qm_admin:
            st.success("🔓 **Chế độ Quản lý:** Tài liệu bạn upload sẽ được LƯU VĨNH VIỄN vào hệ thống. Tất cả người dùng khác đều sẽ được hưởng lợi từ tài liệu này.")
        else:
            st.info("📌 **Chế độ Học viên:** Tài liệu bạn upload chỉ lưu TẠM THỜI trong phiên làm việc này. Khi đóng trình duyệt, tài liệu sẽ không còn.")

        uploaded = st.file_uploader(
            "Chọn file (PDF/TXT):", type=["pdf", "txt"],
            accept_multiple_files=True, key=f"upload_{unit_key}"
        )
        if uploaded:
            combined = ""
            saved_names = []
            for f in uploaded:
                try:
                    raw_bytes = f.getvalue()
                    if f.name.endswith(".pdf"):
                        import io
                        import PyPDF2
                        reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
                        file_text = ""
                        for page in reader.pages:
                            file_text += (page.extract_text() or "") + "\n"
                        # QM/Admin -> lưu PDF gốc + txt cho AI
                        if is_qm_admin:
                            # Lưu PDF gốc
                            udir = os.path.join(KNOWLEDGE_DIR, unit_key)
                            os.makedirs(udir, exist_ok=True)
                            import re
                            pdf_safe = re.sub(r'[^\w\-.]', '_', f.name)
                            with open(os.path.join(udir, pdf_safe), "wb") as pf:
                                pf.write(raw_bytes)
                            # Lưu txt cho AI đọc
                            if file_text.strip():
                                sname = save_doc_permanently(unit_key, f.name, file_text)
                                saved_names.append(pdf_safe)
                    else:
                        file_text = raw_bytes.decode("utf-8")
                        if is_qm_admin and file_text.strip():
                            sname = save_doc_permanently(unit_key, f.name, file_text)
                            saved_names.append(sname)
                    combined += file_text + "\n"
                except Exception as e:
                    st.warning(f"Lỗi đọc {f.name}: {e}")

            if combined.strip():
                st.session_state.uploaded_docs_text[unit_key] = combined
                if is_qm_admin and saved_names:
                    st.success(f"✅ Đã LƯU VĨNH VIỄN {len(saved_names)} file vào kho tri thức Unit {unit_num}: {', '.join(saved_names)}")
                    st.cache_data.clear()
                else:
                    st.success(f"✅ Đã nạp TẠM THỜI {len(uploaded)} file. AI sẽ dùng tài liệu này trong phiên làm việc hiện tại.")

        # Hiện danh sách tài liệu đã lưu vĩnh viễn
        unit_dir = os.path.join(KNOWLEDGE_DIR, unit_key)
        if os.path.isdir(unit_dir):
            all_files = [fn for fn in sorted(os.listdir(unit_dir)) if fn.endswith((".pdf",".txt"))]
            if all_files:
                st.markdown("---")
                st.markdown("### 📚 Tài Liệu Đã Lưu Vĩnh Viễn")
                for fname in all_files:
                    fpath = os.path.join(unit_dir, fname)
                    if fname.endswith(".pdf"):
                        with st.expander(f"📕 {fname} ({os.path.getsize(fpath)//1024} KB)"):
                            with open(fpath, "rb") as pf:
                                pdf_data = pf.read()
                            
                            c1, c2 = st.columns([4, 1])
                            with c1:
                                st.download_button(
                                    label=f"⬇️ Tải về PDF: {fname}",
                                    data=pdf_data, file_name=fname,
                                    mime="application/pdf",
                                    key=f"dl_pdf_{unit_key}_{fname}"
                                )
                            with c2:
                                if is_qm_admin:
                                    with st.popover("🗑️ Xóa file"):
                                        del_pw = st.text_input("Nhập mật khẩu nội bộ:", type="password", key=f"del_pw_pdf_{unit_key}_{fname}")
                                        if st.button("Xác nhận Xóa", type="primary", key=f"del_btn_pdf_{unit_key}_{fname}"):
                                            try: cpw = st.secrets["INTERNAL_PASSWORD"]
                                            except: cpw = "LeaderFoodWhy2024"
                                            if del_pw == cpw or del_pw == "QMMML8386":
                                                # Xóa file local
                                                os.remove(fpath)
                                                companion_txt = fname + ".txt"
                                                companion_path = os.path.join(unit_dir, companion_txt)
                                                
                                                # Xóa trên Firebase Cloud (cho AI học)
                                                firebase_utils.delete_knowledge_text(unit_key, companion_txt)
                                                
                                                if os.path.exists(companion_path): os.remove(companion_path)
                                                
                                                st.success("✅ Đã xóa file vĩnh viễn trên cả Cloud!")
                                                st.rerun()
                                            else:
                                                st.error("Sai mật khẩu!")
                            # Embed PDF để đọc trực tiếp trên app
                            import base64
                            b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}#toolbar=0" width="100%" height="600px" style="border:1px solid #ccc; border-radius: 8px; margin-top: 10px;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                            
                            # Hiển thị text trích xuất nếu có file .txt kèm theo
                            companion_txt = fname + ".txt"
                            companion_path = os.path.join(unit_dir, companion_txt)
                            if os.path.exists(companion_path):
                                with open(companion_path, "r", encoding="utf-8") as tf:
                                    txt_preview = tf.read()
                                st.markdown("**📖 AI đã trích xuất nội dung sau từ PDF để học:**")
                                st.markdown(f"<div style='max-height:200px;overflow-y:auto;padding:12px;background:#f9fafb;border-radius:8px;font-size:0.85rem;line-height:1.6;white-space:pre-wrap;'>{txt_preview[:3000]}...</div>", unsafe_allow_html=True)
                    elif fname.endswith(".txt") and not fname.endswith(".pdf.txt"):
                        # File txt thuần (không phải companion của PDF)
                        with st.expander(f"📄 {fname}"):
                            try:
                                with open(fpath, "r", encoding="utf-8") as rf:
                                    fcontent = rf.read()
                            except: fcontent = "(Không đọc được)"
                            
                            c1, c2 = st.columns([4, 1])
                            with c1:
                                st.download_button(
                                    label="⬇️ Tải về file",
                                    data=fcontent.encode("utf-8"),
                                    file_name=fname, mime="text/plain",
                                    key=f"dl_txt_{unit_key}_{fname}"
                                )
                            with c2:
                                if is_qm_admin:
                                    with st.popover("🗑️ Xóa file"):
                                        del_pw = st.text_input("Nhập mật khẩu nội bộ:", type="password", key=f"del_pw_txt_{unit_key}_{fname}")
                                        if st.button("Xác nhận Xóa", type="primary", key=f"del_btn_txt_{unit_key}_{fname}"):
                                            try: cpw = st.secrets["INTERNAL_PASSWORD"]
                                            except: cpw = "LeaderFoodWhy2024"
                                            if del_pw == cpw or del_pw == "QMMML8386":
                                                os.remove(fpath)
                                                firebase_utils.sync_all_to_firebase()
                                                st.success("✅ Đã xóa file!")
                                                st.rerun()
                                            else:
                                                st.error("Sai mật khẩu!")
                                            
                            st.markdown(f"<div style='max-height:400px;overflow-y:auto;padding:12px;background:#f9fafb;border-radius:8px;font-size:0.85rem;line-height:1.6;white-space:pre-wrap;'>{fcontent[:8000]}</div>", unsafe_allow_html=True)

# ================== TAB NGHIÊN CỨU LEADER ==================
with tab_research:
    user_role = st.session_state.get("user_role")
    is_qm_admin = user_role in ["admin", "qm"]
    ICONS_LIST = ["🔬","🧬","🌡️","⚗️","🦷","🩺","🥼","📊","🧪","🏭","🌾","🐄","🫁","🧫","💉"]

    # ── QM Giao Nhiệm Vụ ──
    if is_qm_admin:
        with st.expander("👨‍💼 GIAO NHIỆM VỤ NGHIÊN CỨU (QM)", expanded=True):
            with st.form("research_assign"):
                topic_type = st.radio("Loại chuyên đề:", ["✅ Có sẵn (Unit 1–10+)", "🆕 Chuyên đề MỚI"], horizontal=True)

                # ── Luôn khai báo hết các widget (tránh NameError) ──
                all_u = get_all_units()
                unit_options = [f"{v['short']} ({k})" for k, v in all_u.items()]
                sel_unit = st.selectbox("Chọn Unit có sẵn:", unit_options)
                topic_name_new = st.text_input("— Hoặc — Tên chuyên đề mới:", placeholder="Unit 11 — Kiểm soát Aflatoxin...")
                new_icon = st.selectbox("Icon cho chuyên đề mới:", ICONS_LIST)
                new_desc = st.text_input("Mô tả ngắn chuyên đề mới:", placeholder="Giới hạn, phương pháp kiểm nghiệm...")

                description = st.text_area("Yêu cầu cụ thể cho Leader:", height=80)
                assigned_to = st.text_input("Giao cho Leader:", placeholder="Để trống = tất cả")
                deadline = st.date_input("Deadline:")

                if st.form_submit_button("🚀 GIAO NHIỆM VỤ", type="primary"):
                    if "Có sẵn" in topic_type:
                        # Xác định đúng unit_key từ selectbox
                        unit_keys_list = list(all_u.keys())
                        sel_idx = unit_options.index(sel_unit)
                        final_unit_key = unit_keys_list[sel_idx]
                        final_topic_name = all_u[final_unit_key]["short"]
                        is_new = False
                    else:
                        # Tạo unit mới NGAY BÂY GIờ khi QM giao bài
                        if not topic_name_new.strip():
                            st.error("❗ Vui lòng nhập tên chuyên đề mới!")
                            st.stop()
                        final_unit_key = get_next_custom_unit_key()
                        final_topic_name = topic_name_new.strip()
                        save_custom_unit(final_unit_key, new_icon, final_topic_name, new_desc)
                        is_new = True

                    task = {
                        "id": int(time.time()),
                        "topic_name": final_topic_name,
                        "unit_key": final_unit_key,   # ✅ luôn có đúng unit_key
                        "is_new_unit": is_new,
                        "description": description,
                        "assigned_to": assigned_to or "Tất cả Leader",
                        "deadline": str(deadline),
                        "month": datetime.now().strftime("Tháng %m/%Y"),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "active": True
                    }
                    tasks = load_research_tasks()
                    tasks.append(task)
                    save_research_tasks(tasks)
                    if is_new:
                        st.success(f"✅ Đã tạo chuyên đề mới **{final_unit_key}** và giao cho {task['assigned_to']}!")
                    else:
                        st.success(f"✅ Đã giao nghiên cứu '{final_topic_name}' ({final_unit_key}) cho {task['assigned_to']}!")
                    st.rerun()

        # Danh sách nhiệm vụ đang chạy
        tasks = load_research_tasks()
        active_tasks = [t for t in tasks if t.get("active")]
        if active_tasks:
            st.markdown("**📌 Nhiệm vụ đang hoạt động:**")
            for t in active_tasks:
                col_t, col_b = st.columns([4,1])
                col_t.markdown(f"🔬 **{t['topic_name']}** → {t['assigned_to']} | Deadline: {t['deadline']}")
                if col_b.button("Đóng", key=f"close_{t['id']}"):
                    for task in tasks:
                        if task["id"] == t["id"]: task["active"] = False
                    save_research_tasks(tasks)
                    st.rerun()

    # ── Leader Nhận & Nghiên Cứu ──
    st.markdown("---")
    st.markdown("### 🔬 Khu Vực Leader — Làm Bài Nghiên Cứu")
    tasks = load_research_tasks()
    active_tasks = [t for t in tasks if t.get("active")]
    if not active_tasks:
        st.info("⏳ Chưa có nhiệm vụ nghiên cứu. Chờ QM giao bài!")
    else:
        task = st.selectbox("Chọn nhiệm vụ:", active_tasks, format_func=lambda x: f"{x['topic_name']} (Deadline: {x['deadline']})")
        topic = task["topic_name"]
        desc = task.get("description","")
        st.info(f"📋 **Chuyên đề:** {topic} | **Yêu cầu:** {desc or 'Theo 4 bước hướng dẫn.'} | ⏰ **Deadline:** {task['deadline']}")

        STEPS = [
            {"num":1,"title":"Thu thập Dữ liệu & Lập Đề cương","tool":"🤖 Gemini","link":"https://gemini.google.com",
             "color":"#f0fdf4","border":"#86efac",
             "action":"Mở Gemini → Copy prompt → Lưu lại các URL nguồn Gemini cung cấp.",
             "prompt":f"""Tôi đang nghiên cứu về [{topic}]. {f'Yêu cầu: {desc}' if desc else ''}
1. Liệt kê quy định hiện hành từ Codex, FDA, EFSA, Bộ Y tế VN (kèm số hiệu, năm ban hành).
2. Lập đề cương 6 mục: Tổng quan, Cơ chế tác động, Giới hạn cho phép, Phương pháp kiểm nghiệm, Rủi ro thực tế, Giải pháp kiểm soát.
3. Gợi ý 5 từ khóa tiếng Anh để tìm trên Google Scholar."""},
            {"num":2,"title":"Thẩm định & Trích dẫn Khoa học","tool":"📚 NotebookLM","link":"https://notebooklm.google.com",
             "color":"#eff6ff","border":"#93c5fd",
             "action":"Tải PDF từ Google Scholar → Upload lên NotebookLM → Dùng prompt bên dưới.",
             "prompt":f"""Dựa trên tài liệu đã upload về [{topic}]:
1. Các thông số kỹ thuật quan trọng (số liệu, ngưỡng, nhiệt độ...)? Kèm tên tài liệu và số trang.
2. Khác biệt giữa tiêu chuẩn quốc tế và Việt Nam?
3. Phương pháp kiểm nghiệm/kiểm soát được khuyến nghị? Kèm trích dẫn.
BẮT BUỘC kèm tên tài liệu và số trang."""},
            {"num":3,"title":"Soạn thảo Báo cáo Chuyên nghiệp","tool":"🤖 Gemini","link":"https://gemini.google.com",
             "color":"#fefce8","border":"#fde047",
             "action":"Copy toàn bộ kết quả từ NotebookLM → Paste vào Gemini cùng prompt.",
             "prompt":f"""Dưới đây là dữ liệu đã xác thực về [{topic}]:
[PASTE NỘI DUNG NOTEBOOKLM VÀO ĐÂY]
Viết Báo cáo Kỹ thuật gồm: (1) Tóm tắt, (2) Tổng quan, (3) Kết quả nghiên cứu (giữ nguyên trích dẫn), (4) Áp dụng thực tiễn tại nhà máy thịt, (5) Kết luận & Kiến nghị, (6) Tài liệu tham khảo (chuẩn APA)."""},
            {"num":4,"title":"Xuất PDF & Nộp Bài","tool":"📄 Google Docs","link":"https://docs.google.com",
             "color":"#fff7ed","border":"#fdba74",
             "action":"Gemini → Chia sẻ & Xuất → Export to Docs → Google Docs → Tải xuống PDF → Nộp bài bên dưới ↓","prompt":""},
        ]
        for step in STEPS:
            st.markdown(f"""<div style="border-radius:14px;padding:16px;margin:10px 0;background:{step['color']};border:2px solid {step['border']};">
<b>Bước {step['num']}: {step['title']}</b> &nbsp;|&nbsp; 🛠️ <a href="{step['link']}" target="_blank">{step['tool']}</a><br>
⚡ {step['action']}</div>""", unsafe_allow_html=True)
            if step["prompt"]:
                st.code(step["prompt"], language="text")

        st.markdown("---")
        st.markdown("### 📤 Nộp Bài & Lưu Vào Knowledge Base")
        leader_name = st.text_input("Họ và Tên Leader:", key="leader_name_r")
        uploaded_pdf = st.file_uploader("Upload file PDF báo cáo:", type=["pdf"], key="research_pdf")

        if st.button("🏁 NỘP BÀI & CHỜ DUYỆT", type="primary", use_container_width=True):
            if leader_name and uploaded_pdf:
                # Đọc bytes PDF
                pdf_bytes = uploaded_pdf.getvalue()

                # Trích xuất text từ PDF (để QM duyệt sau này)
                try:
                    import io
                    import PyPDF2
                    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                    pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages)
                except: pdf_text = ""

                target_key = task.get("unit_key")
                if not target_key:
                    st.error("❌ Nhiệm vụ này thiếu thông tin unit_key. Vui lòng nhờ QM giao lại!")
                    st.stop()
                
                # Lưu toàn bộ bài nộp lên Firebase (kèm Base64 PDF)
                sub_data = {
                    "task_id": task["id"], "topic": topic, "leader": leader_name,
                    "unit_key": target_key, "filename": uploaded_pdf.name,
                    "text_content": pdf_text, "approved": False,
                    "month": task["month"], "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                with st.spinner("Đang đẩy bài nghiên cứu lên Cloud..."):
                    firebase_utils.save_research_submission(sub_data, pdf_bytes)
                
                st.balloons()
                st.success(f"✅ Đã nộp bài thành công! QM sẽ duyệt bài của {leader_name} trước khi đưa vào kho tri thức đào tạo.")
                st.cache_data.clear()
            else:
                st.warning("Vui lòng nhập tên và upload file PDF!")

    # ── Dashboard ──
    st.markdown("---")
    st.markdown("### 📊 Dashboard Tiến Độ & Duyệt Bài")
    
    # Lấy dữ liệu từ Firebase
    cloud_subs = firebase_utils.get_research_submissions()
    subs_list = []
    if cloud_subs:
        if isinstance(cloud_subs, dict):
            for sid, sdata in cloud_subs.items():
                if isinstance(sdata, dict):
                    sdata["id"] = sid
                    subs_list.append(sdata)
        elif isinstance(cloud_subs, list):
            for i, sdata in enumerate(cloud_subs):
                if isinstance(sdata, dict):
                    sdata["id"] = str(i)
                    subs_list.append(sdata)
    
    cur_month = datetime.now().strftime("Tháng %m/%Y")
    tasks = load_research_tasks()
    active_tasks = [t for t in tasks if t.get("active")]
    month_subs = [s for s in subs_list if s.get("month") == cur_month]
    
    c1,c2,c3 = st.columns(3)
    c1.metric("Nhiệm vụ đang giao", len(active_tasks))
    c2.metric("Đã nộp tháng này", len(month_subs))
    c3.metric("Chưa nộp", max(0, len(active_tasks)-len(month_subs)))
    
    if month_subs:
        for s in sorted(month_subs, key=lambda x: x["submitted_at"], reverse=True):
            status_icon = "✅" if s.get("approved") else "⏳"
            with st.expander(f"{status_icon} **{s['leader']}** — *{s['topic']}* — `{s['submitted_at']}`"):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.caption(f"📌 Unit: `{s.get('unit_key','?')}` | File: {s['filename']}")
                
                with c2:
                    # Nút tải PDF từ Base64
                    try:
                        pdf_data = base64.b64decode(s["pdf_base64"])
                        st.download_button(
                            label="📥 Tải PDF bài nộp",
                            data=pdf_data,
                            file_name=f"Report_{s['leader']}_{s['unit_key']}.pdf",
                            mime="application/pdf",
                            key=f"dl_res_{s['id']}"
                        )
                    except:
                        st.error("Lỗi file PDF")

                with c3:
                    if is_qm_admin:
                        if not s.get("approved"):
                            if st.button("🌟 DUYỆT & NẠP AI", key=f"appr_{s['id']}", type="primary"):
                                with st.spinner("Đang nạp kiến thức vào Academy..."):
                                    firebase_utils.approve_research_submission(
                                        s["id"], s["unit_key"], 
                                        f"{s['leader']}_approved_{s['id']}.txt", 
                                        s.get("text_content", "")
                                    )
                                    st.success("Đã phê duyệt và nạp kiến thức!")
                                    st.rerun()
                        
                        with st.popover("🗑️ Xóa"):
                            del_pw = st.text_input("Mật khẩu nội bộ:", type="password", key=f"del_pw_rs_{s['id']}")
                            if st.button("Xác nhận Xóa", type="primary", key=f"del_btn_rs_{s['id']}"):
                                try: cpw = st.secrets["INTERNAL_PASSWORD"]
                                except: cpw = "LeaderFoodWhy2024"
                                if del_pw == cpw:
                                    firebase_utils.delete_research_submission(s["id"])
                                    st.success("✅ Đã xóa bài nộp!")
                                    st.rerun()
                                else:
                                    st.error("Sai mật khẩu!")

                # Preview PDF trực tiếp từ Base64
                try:
                    if s.get("pdf_base64"):
                        pdf_display = f'<iframe src="data:application/pdf;base64,{s["pdf_base64"]}#toolbar=0" width="100%" height="600px" style="border:1px solid #ccc; border-radius: 8px; margin-top: 10px;"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                except:
                    st.warning("Không thể hiển thị bản xem trước file này.")
                
                # Hiển thị nội dung text AI đã trích xuất
                if s.get("text_content"):
                    with st.expander("🔍 Xem nội dung văn bản AI trích xuất (Sẽ được nạp vào kho kiến thức)"):
                        st.markdown(f"<div style='font-size:0.85rem; padding:10px; background:#f9fafb; border-radius:5px;'>{s['text_content'][:2000]}...</div>", unsafe_allow_html=True)

