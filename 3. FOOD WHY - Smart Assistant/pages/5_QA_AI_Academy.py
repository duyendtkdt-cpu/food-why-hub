import streamlit as st
import firebase_utils

# ── Firebase sync (chỉ 1 lần/session) ──
if "firebase_synced" not in st.session_state:
    with st.spinner("🔄 Đang kết nối Firebase..."):
        firebase_utils.init_sync_from_firebase()
        st.session_state.firebase_synced = True

import json, os, re, time, io, base64
import PyPDF2
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="QA AI Academy", page_icon="🎓", layout="wide")

# ═══════════════════════════════════════════════════════════════════
# CSS — LMS Style + FOOD WHY Orange Theme
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

/* ── Course Grid ── */
.course-card {
    background: white; border-radius: 18px; overflow: hidden;
    border: 1.5px solid #f0ede9;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.course-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 40px rgba(249,115,22,0.18);
    border-color: #f97316;
}
.course-cover {
    height: 130px;
    display: flex; align-items: center; justify-content: center;
    font-size: 3.8rem; position: relative;
    background: linear-gradient(135deg, #fff7ed, #ffedd5);
}
.course-badge {
    position: absolute; top: 10px; right: 10px;
    background: #f97316; color: white;
    font-size: 0.62rem; font-weight: 700;
    padding: 3px 9px; border-radius: 20px;
    letter-spacing: 0.5px;
}
.course-badge.custom { background: #6366f1; }
.course-body { padding: 14px 16px 16px; }
.course-category { font-size: 0.65rem; color: #f97316; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 5px; }
.course-title { font-size: 0.92rem; font-weight: 700; color: #1c1917; margin-bottom: 5px; line-height: 1.35; }
.course-desc { font-size: 0.75rem; color: #78716c; line-height: 1.5; margin-bottom: 10px; }
.course-meta { font-size: 0.7rem; color: #a8a29e; display: flex; align-items: center; gap: 6px; }

/* ── Sidebar Session Menu ── */
.sidebar-unit-hdr {
    background: linear-gradient(135deg, #f97316, #ea580c);
    color: white; padding: 14px 16px; border-radius: 12px; margin-bottom: 10px;
}
.sidebar-unit-hdr small { font-size: 0.7rem; opacity: 0.82; display: block; }
.sidebar-unit-hdr h4 { margin: 4px 0 0; font-size: 0.92rem; font-weight: 800; line-height: 1.3; }

.sess-item {
    display: flex; align-items: center; gap: 9px;
    padding: 9px 11px; border-radius: 10px; margin-bottom: 4px;
    border: 1.5px solid transparent; transition: all 0.2s;
}
.sess-item:hover { background: #fff7ed; border-color: #fed7aa; }
.sess-item.active { background: #fff7ed; border-color: #f97316; }
.sess-dot {
    width: 28px; height: 28px; border-radius: 50%;
    background: #e7e5e4; color: #78716c;
    font-size: 0.72rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.sess-dot.active { background: #f97316; color: white; }
.sess-dot.done { background: #16a34a; color: white; }
.sess-text small { font-size: 0.62rem; color: #a8a29e; }
.sess-text span { font-size: 0.78rem; font-weight: 600; color: #44403c; display: block; line-height: 1.3; }

/* ── Academy Hero ── */
.acad-hero {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 50%, #c2410c 100%);
    color: white; padding: 28px 36px; border-radius: 20px;
    margin-bottom: 24px; position: relative; overflow: hidden;
    box-shadow: 0 10px 28px -6px rgba(249,115,22,0.45);
}
.acad-hero::before {
    content: ''; position: absolute; top: -60%; right: -10%;
    width: 280px; height: 280px; border-radius: 50%;
    background: rgba(255,255,255,0.07);
}
.acad-hero h1 { font-size: 1.7rem; font-weight: 900; margin: 0 0 4px; }
.acad-hero p { font-size: 0.9rem; opacity: 0.88; margin: 0; }

/* ── Session Content ── */
.step-hdr {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px; border-radius: 12px;
    background: linear-gradient(135deg, #fff7ed, #ffedd5);
    border-left: 4px solid #f97316; margin-bottom: 16px;
}
.step-num {
    width: 34px; height: 34px; background: #f97316;
    color: white; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.95rem; flex-shrink: 0;
}
.step-label { font-size: 0.68rem; color: #a8a29e; margin: 0; }
.step-title { font-size: 0.95rem; font-weight: 700; color: #c2410c; margin: 2px 0 0; }

.content-box {
    background: white; border: 1.5px solid #f0ede9;
    border-radius: 14px; padding: 22px;
    line-height: 1.8; color: #292524; font-size: 0.9rem;
}

/* ── Progress Bar ── */
.prog-bar-wrap { background: #f5f5f4; border-radius: 99px; height: 8px; margin: 12px 0 4px; }
.prog-bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #f97316, #ea580c); transition: width 0.5s; }

/* ── Stats Pills ── */
.stat-pill {
    background: white; border: 1.5px solid #fed7aa; border-radius: 12px;
    padding: 12px 16px; text-align: center;
}
.stat-pill .num { font-size: 1.6rem; font-weight: 900; color: #f97316; }
.stat-pill .lbl { font-size: 0.72rem; color: #78716c; margin-top: 2px; }

/* ── Access Box ── */
.access-box {
    background: linear-gradient(135deg, #fff7ed, #ffedd5);
    border: 1.5px solid #fdba74; border-radius: 12px;
    padding: 15px; margin-bottom: 14px;
}
.access-box h4 { color: #c2410c; margin: 0 0 6px; font-size: 0.88rem; }

/* ── Ref chips ── */
.ref-chip {
    display: inline-block; background: #fff7ed; border: 1px solid #fed7aa;
    color: #9a3412; font-size: 0.72rem; padding: 3px 9px;
    border-radius: 8px; margin: 2px; font-weight: 600;
}

/* Nav button styling */
div[data-testid="stButton"] button[kind="secondary"] {
    border: 1.5px solid #f97316 !important;
    color: #f97316 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# DATA LAYER
# ═══════════════════════════════════════════════════════════════════
UNITS_BASE = {
    "unit_1":  {"icon": "🐷", "short": "Thịt Heo & Gà",     "desc": "PSE, DFD, phúc lợi động vật, cảm quan thịt tươi"},
    "unit_2":  {"icon": "🦠", "short": "Vi Sinh Vật",        "desc": "Salmonella, Listeria, E.coli, Biofilm"},
    "unit_3":  {"icon": "💧", "short": "Nước & Nước Đá",    "desc": "QCVN, Clo hoạt tính, nước chiller"},
    "unit_4":  {"icon": "❄️", "short": "Chuỗi Lạnh",        "desc": "Cấp đông, rã đông, drip loss"},
    "unit_5":  {"icon": "🧂", "short": "Phụ Gia Thịt",      "desc": "Nitrite, Phosphate, Ascorbic acid"},
    "unit_6":  {"icon": "📦", "short": "Đóng Gói",          "desc": "MAP, Vacuum, màng co PA/PE"},
    "unit_7":  {"icon": "🚧", "short": "Lây Nhiễm Chéo",   "desc": "Raw vs Cooked, Allergen, phân vùng"},
    "unit_8":  {"icon": "🔍", "short": "Dị Vật",            "desc": "Xương, kim loại, X-ray, dò kim loại"},
    "unit_9":  {"icon": "🧹", "short": "SSOP",              "desc": "7 bước vệ sinh, hóa chất, Swab test"},
    "unit_10": {"icon": "📜", "short": "Pháp Chế & Thú Y",  "desc": "Luật ATTP, truy xuất, thu hồi"},
}

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
DATA_DIR      = os.path.join(os.path.dirname(__file__), "..", "data")
CUSTOM_UNITS_FILE  = os.path.join(KNOWLEDGE_DIR, "custom_units.json")
CASE_STUDIES_FILE  = os.path.join(DATA_DIR, "case_studies.json")
EXAM_FILE          = os.path.join(DATA_DIR, "monthly_exam.json")
RESULTS_FILE       = os.path.join(DATA_DIR, "exam_results.json")
RESEARCH_TASK_FILE = os.path.join(DATA_DIR, "research_tasks.json")
RESEARCH_SUB_FILE  = os.path.join(DATA_DIR, "research_submissions.json")
os.makedirs(DATA_DIR, exist_ok=True)

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

def get_next_custom_unit_key():
    cu = load_custom_units()
    if not cu: return "unit_11"
    nums = [int(k.split("_")[1]) for k in cu if k.startswith("unit_")]
    return f"unit_{max(nums)+1}" if nums else "unit_11"

@st.cache_data
def load_knowledge():
    kb_path = os.path.join(KNOWLEDGE_DIR, "knowledge_base.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def reload_knowledge():
    st.cache_data.clear()
    kb_path = os.path.join(KNOWLEDGE_DIR, "knowledge_base.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_knowledge(kb):
    kb_path = os.path.join(KNOWLEDGE_DIR, "knowledge_base.json")
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    st.cache_data.clear()

def load_saved_docs(unit_key):
    unit_dir = os.path.join(KNOWLEDGE_DIR, unit_key)
    combined = ""
    if os.path.isdir(unit_dir):
        for fname in sorted(os.listdir(unit_dir)):
            fpath = os.path.join(unit_dir, fname)
            if os.path.isfile(fpath) and fname.endswith(".txt"):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        combined += f"\n--- [{fname}] ---\n" + f.read()
                except: pass
    return combined

def save_doc_permanently(unit_key, filename, content):
    unit_dir = os.path.join(KNOWLEDGE_DIR, unit_key)
    os.makedirs(unit_dir, exist_ok=True)
    safe_name = re.sub(r'[^\w\-.]', '_', filename)
    if not safe_name.endswith(".txt"): safe_name += ".txt"
    fpath = os.path.join(unit_dir, safe_name)
    with open(fpath, "w", encoding="utf-8") as f: f.write(content)
    firebase_utils.save_knowledge_text(unit_key, safe_name, content)
    return safe_name

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)
    firebase_utils.sync_all_to_firebase()

# ── API Key Logic ──
def get_api_key():
    if st.session_state.get("user_role") and st.session_state.get("active_api_key"):
        return st.session_state.active_api_key, "internal"
    if st.session_state.get("internal_unlocked"):
        for k in ["TRAINING_API_KEY", "GEMINI_API_KEY"]:
            try:
                v = st.secrets[k]
                if v: return v, "internal"
            except: pass
    user_key = (st.session_state.get("user_api_key") or "").strip()
    if user_key: return user_key, "user_key"
    for k in ["TRAINING_API_KEY", "GEMINI_API_KEY"]:
        try:
            v = st.secrets[k]
            if v: return v, "public_free"
        except: pass
    return None, None

MAX_FREE_Q = 3

# ── Session State Init ──
_defaults = {
    "user_role": None, "active_api_key": None, "internal_unlocked": False,
    "selected_unit": None, "selected_session": None,
    "daily_question_count": 0, "user_api_key": None, "uploaded_docs_text": {},
    "unit_chat_history": {}, "quiz_answered": {}, "challenge_feedback": {}
}
for k, v in _defaults.items():
    if k not in st.session_state: st.session_state[k] = v

knowledge = load_knowledge()
UNITS = get_all_units()

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    sel_unit = st.session_state.selected_unit
    sel_sess = st.session_state.selected_session

    if sel_unit:
        # ── Session navigation ──
        unit_info = UNITS.get(sel_unit, {"icon": "📄", "short": sel_unit})
        kb_unit   = knowledge.get(sel_unit, {})
        sessions  = kb_unit.get("sessions", [])

        st.markdown(f"""
        <div class="sidebar-unit-hdr">
            <small>{unit_info['icon']} ĐANG HỌC</small>
            <h4>{unit_info['short']}</h4>
        </div>
        """, unsafe_allow_html=True)

        if st.button("← Quay lại danh sách khóa học", use_container_width=True):
            st.session_state.selected_unit = None
            st.session_state.selected_session = None
            st.rerun()

        st.markdown("**📚 Danh sách bài học:**")
        if sessions:
            completed = st.session_state.get("completed_sessions", {}).get(sel_unit, [])
            for s in sessions:
                is_active = (sel_sess == s["id"])
                is_done   = s["id"] in completed
                dot_cls   = "active" if is_active else ("done" if is_done else "")
                dot_icon  = "✓" if is_done else s.get("week", "?")
                st.markdown(f"""
                <div class="sess-item {'active' if is_active else ''}">
                    <div class="sess-dot {dot_cls}">{dot_icon}</div>
                    <div class="sess-text">
                        <small>Tuần {s.get('week','?')}</small>
                        <span>{s['title']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Vào bài →", key=f"sess_nav_{s['id']}", use_container_width=True):
                    st.session_state.selected_session = s["id"]
                    st.rerun()
        else:
            st.info("⏳ Chưa có bài học. Admin hãy dùng Auto-Content Engine để tạo!")

        # Progress
        if sessions:
            completed = st.session_state.get("completed_sessions", {}).get(sel_unit, [])
            pct = int(len(completed) / len(sessions) * 100) if sessions else 0
            st.markdown(f"""
            <div style="margin-top:12px;">
                <small style="color:#78716c;">Tiến độ học tập: {pct}%</small>
                <div class="prog-bar-wrap">
                    <div class="prog-bar-fill" style="width:{pct}%"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

    else:
        # ── Default sidebar: brand + login ──
        st.markdown("""
        <div style="background:linear-gradient(135deg,#f97316,#ea580c);color:white;
                    padding:16px;border-radius:12px;margin-bottom:14px;
                    box-shadow:0 6px 16px -4px rgba(249,115,22,0.4);">
            <div style="font-size:1.2rem;font-weight:900;">🎓 QA AI ACADEMY</div>
            <div style="font-size:0.78rem;opacity:0.85;margin-top:3px;">Trường Đào Tạo Thực Chiến Ngành Thịt</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Auth block (always shown) ──
    st.markdown('<div class="access-box"><h4>🔐 Truy cập Nội bộ</h4></div>', unsafe_allow_html=True)
    if st.session_state.get("user_role"):
        roles = {"admin": "Admin (Sếp)", "qm": "Quản lý (QM)", "qa": "Nhân viên (QA)"}
        st.success(f"✅ **{roles.get(st.session_state.user_role, '')}**")
        if st.button("🔒 Đăng xuất", use_container_width=True):
            st.session_state.update({"user_role": None, "active_api_key": None, "internal_unlocked": False})
            st.rerun()
    else:
        pw = st.text_input("Nhập mật khẩu nội bộ:", type="password", key="pw_input")
        if st.button("Đăng nhập", use_container_width=True):
            try: admin_pw = st.secrets["INTERNAL_PASSWORD"]
            except: admin_pw = "LeaderFoodWhy"
            if pw == admin_pw:
                st.session_state.update({"user_role": "admin", "internal_unlocked": True})
                try: st.session_state.active_api_key = st.secrets["TRAINING_API_KEY"]
                except:
                    try: st.session_state.active_api_key = st.secrets["GEMINI_API_KEY"]
                    except: pass
                st.rerun()
            elif pw == "QMMML8386":
                st.session_state.update({"user_role": "qm", "internal_unlocked": True})
                try: st.session_state.active_api_key = st.secrets.get("QM_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
                except: pass
                st.rerun()
            elif pw == "LeaderQA2026":
                st.session_state.update({"user_role": "qa", "internal_unlocked": True})
                try: st.session_state.active_api_key = st.secrets.get("QA_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
                except: pass
                st.rerun()
            else:
                st.error("❌ Sai mật khẩu!")

    # Free questions counter
    api_key, source = get_api_key()
    if not st.session_state.get("user_role") and not st.session_state.get("user_api_key"):
        remaining = max(0, MAX_FREE_Q - st.session_state.daily_question_count)
        st.divider()
        st.markdown(f"**Câu hỏi miễn phí còn lại:** `{remaining}/{MAX_FREE_Q}`")
        st.caption("Hoặc nhập API Key cá nhân:")
        ukey = st.text_input("API Key:", type="password", key="api_key_input")
        if ukey:
            st.session_state.user_api_key = ukey
            st.success("✅ Đã nhận Key!")

    st.divider()
    st.caption("© 2026 FOOD WHY Studio")

# ═══════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════
knowledge = load_knowledge()
UNITS     = get_all_units()

tab_academy, tab_ask, tab_arena, tab_research, tab_admin = st.tabs([
    "  📖 Học Tập  ", "  💬 Hỏi AI Mentor  ",
    "  🏆 Đấu Trường QA  ", "  ⚔️ Nghiên Cứu Leader  ",
    "  🤖 Auto-Content Engine  "
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: HỌC TẬP
# ═══════════════════════════════════════════════════════════════════
with tab_academy:
    sel_unit = st.session_state.selected_unit
    sel_sess = st.session_state.selected_session

    # ── VIEW 1: Course Grid ──
    if not sel_unit:
        st.markdown("""
        <div class="acad-hero">
            <h1>🎓 QA AI ACADEMY</h1>
            <p>Trường Đào Tạo Thực Chiến — Chuyên Ngành Giết Mổ & Chế Biến Thịt</p>
        </div>
        """, unsafe_allow_html=True)

        # Stats row
        all_units_now = get_all_units()
        kb_now = load_knowledge()
        total_sessions = sum(len(kb_now.get(uk, {}).get("sessions", [])) for uk in all_units_now)
        c1, c2, c3, c4 = st.columns(4)
        for col, num, lbl in [
            (c1, len(all_units_now), "Khóa Học"),
            (c2, total_sessions, "Bài Học"),
            (c3, "🤖", "AI Mentor"),
            (c4, "🏆", "Thi Tháng"),
        ]:
            col.markdown(f'<div class="stat-pill"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

        st.write("")
        st.subheader("📚 Chọn Khóa Học")

        unit_keys = list(all_units_now.keys())
        for row_start in range(0, len(unit_keys), 5):
            cols = st.columns(5)
            for i, col in enumerate(cols):
                idx = row_start + i
                if idx >= len(unit_keys): break
                uk   = unit_keys[idx]
                unit = all_units_now[uk]
                unum = uk.split("_")[1]
                is_custom = unit.get("custom", False)
                unit_kb = kb_now.get(uk, {})
                n_sess = len(unit_kb.get("sessions", []))
                badge_cls = "custom" if is_custom else ""
                badge_lbl = f"⚔️ Custom" if is_custom else f"Unit {unum}"

                with col:
                    st.markdown(f"""
                    <div class="course-card">
                        <div class="course-cover">
                            {unit['icon']}
                            <div class="course-badge {badge_cls}">{badge_lbl}</div>
                        </div>
                        <div class="course-body">
                            <div class="course-category">🏭 QA NGÀNH THỊT</div>
                            <div class="course-title">{unit['short']}</div>
                            <div class="course-desc">{unit['desc']}</div>
                            <div class="course-meta">📘 {n_sess} bài học</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Vào học →", key=f"go_{uk}", use_container_width=True,
                                 type="primary" if n_sess > 0 else "secondary"):
                        st.session_state.selected_unit = uk
                        st.session_state.selected_session = None
                        st.rerun()

    # ── VIEW 2: Unit → Session Content ──
    else:
        knowledge = load_knowledge()
        unit_info = UNITS.get(sel_unit, {"icon": "📄", "short": sel_unit, "desc": ""})
        kb_unit   = knowledge.get(sel_unit, {})
        sessions  = kb_unit.get("sessions", [])

        # Find session object
        current_session = None
        current_idx     = 0
        if sel_sess:
            for i, s in enumerate(sessions):
                if s["id"] == sel_sess:
                    current_session = s
                    current_idx = i
                    break

        if not current_session:
            # ── Unit overview ──
            st.markdown(f"""
            <div class="acad-hero" style="padding:22px 30px;">
                <h1 style="font-size:1.4rem;">{unit_info['icon']} {unit_info['short']}</h1>
                <p>{kb_unit.get('title', unit_info['desc'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Hiển thị Kiến thức cốt lõi & Tài liệu tham khảo
            core = kb_unit.get("core_knowledge", [])
            refs = kb_unit.get("references", [])
            
            if core:
                st.markdown("### 🧠 Kiến Thức Trọng Tâm")
                for item in core:
                    st.markdown(f"""
                    <div style="background-color:#fffbeb; border-left:4px solid #f59e0b; padding:12px 18px; border-radius:6px; margin-bottom:10px; font-size:0.9rem; line-height:1.6; color:#451a03;">
                        {item}
                    </div>
                    """, unsafe_allow_html=True)
                    
            if refs:
                st.markdown("### 📚 Nguồn Tài Liệu Tham Khảo")
                chips = "".join([f'<span class="ref-chip" style="margin-right:8px; margin-bottom:8px;">📗 {r}</span>' for r in refs])
                st.markdown(f'<div style="margin-bottom:20px;">{chips}</div>', unsafe_allow_html=True)
            
            st.divider()
            
            if sessions:
                st.info(f"👈 Chọn bài học từ menu bên trái để bắt đầu học. Khóa này có **{len(sessions)} bài** tương ứng **{len(sessions)} tuần** học.")
            else:
                st.warning("⏳ Khóa học này chưa có bài học chi tiết theo tuần. Admin có thể mở tab **🤖 Auto-Content Engine** để tạo tự động bằng AI!")
        else:
            # ── Session 5-step content ──
            s = current_session
            # Header
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                <div style="font-size:2rem;">{unit_info['icon']}</div>
                <div>
                    <div style="font-size:0.72rem;color:#a8a29e;font-weight:600;letter-spacing:1px;text-transform:uppercase;">
                        {unit_info['short']} · Tuần {s.get('week','?')}
                    </div>
                    <div style="font-size:1.25rem;font-weight:800;color:#1c1917;">{s['title']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ─── STEP 1: Pre-Question ───────────────────────────
            st.markdown("""
            <div class="step-hdr">
                <div class="step-num">1</div>
                <div><p class="step-label">KHỞI ĐỘNG</p><p class="step-title">Câu hỏi gợi mở trước bài học</p></div>
            </div>
            """, unsafe_allow_html=True)

            pq = s.get("pre_question", {})
            if pq:
                quiz_key = f"quiz_{sel_unit}_{sel_sess}"
                answered = st.session_state.quiz_answered.get(quiz_key)

                st.markdown(f"**{pq.get('question', '')}**")
                opts = pq.get("options", [])
                correct_idx = pq.get("correct", 0)

                if answered is None:
                    for idx, opt in enumerate(opts):
                        if st.button(opt, key=f"qopt_{quiz_key}_{idx}", use_container_width=True):
                            st.session_state.quiz_answered[quiz_key] = idx
                            st.rerun()
                else:
                    for idx, opt in enumerate(opts):
                        if idx == correct_idx:
                            st.success(f"✅ {opt}")
                        elif idx == answered and answered != correct_idx:
                            st.error(f"❌ {opt}")
                        else:
                            st.markdown(f"<div style='padding:9px 14px;border-radius:8px;border:1.5px solid #e7e5e4;margin:5px 0;font-size:0.88rem;color:#78716c;'>{opt}</div>", unsafe_allow_html=True)

                    exp = pq.get("explanation", "")
                    if exp:
                        st.info(f"📖 **Giải thích:** {exp}")
            else:
                st.info("❓ Câu hỏi gợi mở chưa được thiết lập cho bài học này.")

            st.divider()

            # ─── STEP 2: Video ───────────────────────────────────
            st.markdown("""
            <div class="step-hdr">
                <div class="step-num">2</div>
                <div><p class="step-label">VIDEO BÀI GIẢNG</p><p class="step-title">Xem video minh họa trực quan</p></div>
            </div>
            """, unsafe_allow_html=True)

            video_url = s.get("video_url", "")
            if video_url and "youtube.com/embed/" in video_url:
                components.html(
                    f'<iframe width="100%" height="380" src="{video_url}?rel=0" '
                    f'frameborder="0" allow="accelerometer; autoplay; clipboard-write; '
                    f'encrypted-media; gyroscope; picture-in-picture" allowfullscreen '
                    f'style="border-radius:14px;"></iframe>',
                    height=390
                )
            elif video_url:
                st.video(video_url)
            else:
                st.markdown("""
                <div style="background:#f5f5f4;border-radius:14px;height:200px;
                            display:flex;align-items:center;justify-content:center;
                            color:#a8a29e;font-size:1rem;">
                    🎬 Video bài giảng đang được sản xuất — Sắp ra mắt!
                </div>
                """, unsafe_allow_html=True)

            if st.session_state.get("user_role") == "admin":
                new_url = st.text_input("🔧 Admin: Cập nhật link video YouTube (embed URL):", key=f"vid_input_{sel_unit}_{sel_sess}")
                if st.button("💾 Lưu link video", key=f"vid_save_{sel_unit}_{sel_sess}"):
                    kb = load_knowledge()
                    for sess in kb.get(sel_unit, {}).get("sessions", []):
                        if sess["id"] == sel_sess:
                            sess["video_url"] = new_url; break
                    save_knowledge(kb)
                    st.success("✅ Đã lưu link video!")
                    st.rerun()

            st.divider()

            # ─── STEP 3: Nội dung ────────────────────────────────
            st.markdown("""
            <div class="step-hdr">
                <div class="step-num">3</div>
                <div><p class="step-label">NỘI DUNG BÀI HỌC</p><p class="step-title">Kiến thức chuyên sâu & Khoa học</p></div>
            </div>
            """, unsafe_allow_html=True)

            content = s.get("content", "")
            if content:
                with st.container():
                    st.markdown(f'<div class="content-box">', unsafe_allow_html=True)
                    st.markdown(content)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("📝 Nội dung bài học chưa được tạo. Admin hãy dùng Auto-Content Engine!")

            # Tài liệu bổ sung của QM
            saved_docs = load_saved_docs(sel_unit)
            if saved_docs:
                with st.expander("📁 Xem tài liệu bổ sung từ QM"):
                    st.markdown(f"<div style='font-size:0.83rem;max-height:300px;overflow-y:auto;'>{saved_docs[:5000]}</div>", unsafe_allow_html=True)

            st.divider()

            # ─── STEP 4: Flashcards ──────────────────────────────
            st.markdown("""
            <div class="step-hdr">
                <div class="step-num">4</div>
                <div><p class="step-label">FLASHCARDS</p><p class="step-title">3 Key Takeaways — Lật thẻ để xem đáp án</p></div>
            </div>
            """, unsafe_allow_html=True)

            flashcards = s.get("flashcards", [])
            if flashcards:
                fc_html = """
                <style>
                .fc-wrap { display:flex; gap:14px; margin:10px 0; flex-wrap:wrap; }
                .fc { width:31%; min-width:200px; height:170px; perspective:900px; cursor:pointer; }
                .fc-inner { position:relative; width:100%; height:100%;
                             transition:transform 0.55s; transform-style:preserve-3d; }
                .fc.flipped .fc-inner { transform:rotateY(180deg); }
                .fc-f, .fc-b {
                    position:absolute; width:100%; height:100%;
                    backface-visibility:hidden; border-radius:14px;
                    display:flex; flex-direction:column; align-items:center;
                    justify-content:center; padding:18px; text-align:center;
                    box-sizing:border-box;
                }
                .fc-f {
                    background:linear-gradient(135deg,#f97316,#ea580c);
                    color:white; font-weight:700; font-size:0.92rem; line-height:1.4;
                }
                .fc-b {
                    background:white; border:2px solid #f97316; color:#44403c;
                    font-size:0.83rem; transform:rotateY(180deg); line-height:1.5;
                }
                .tap-hint { font-size:0.6rem; opacity:0.7; margin-top:8px; }
                </style>
                <div class="fc-wrap">
                """
                for i, fc in enumerate(flashcards[:3]):
                    front = fc.get("front", "").replace('\n', '<br>')
                    back  = fc.get("back", "").replace('\n', '<br>')
                    fc_html += f"""
                    <div class="fc" id="fc{i}" onclick="this.classList.toggle('flipped')">
                        <div class="fc-inner">
                            <div class="fc-f">{front}<span class="tap-hint">👆 Nhấn để lật</span></div>
                            <div class="fc-b">{back}</div>
                        </div>
                    </div>"""
                fc_html += "</div>"
                components.html(fc_html, height=200)
            else:
                st.info("🃏 Flashcards chưa được tạo cho bài học này.")

            st.divider()

            # ─── STEP 5: Challenge ────────────────────────────────
            st.markdown("""
            <div class="step-hdr">
                <div class="step-num">5</div>
                <div><p class="step-label">BÀI TẬP THỬ THÁCH</p><p class="step-title">Tình huống thực tế tại nhà máy — AI chấm điểm</p></div>
            </div>
            """, unsafe_allow_html=True)

            challenge = s.get("challenge", "")
            if challenge:
                st.markdown(f'<div class="content-box" style="border-left:4px solid #f97316;">{challenge}</div>', unsafe_allow_html=True)
                st.write("")
                answer_key = f"challenge_ans_{sel_unit}_{sel_sess}"
                user_answer = st.text_area("✍️ Câu trả lời của bạn:", height=160, key=answer_key,
                                           placeholder="Viết phân tích và giải pháp xử lý của bạn tại đây...")
                col_btn1, col_btn2 = st.columns([1, 3])
                with col_btn1:
                    submit_ch = st.button("🤖 Nhờ AI chấm điểm", type="primary", use_container_width=True,
                                          key=f"ch_submit_{sel_unit}_{sel_sess}")
                if submit_ch:
                    api_key, source = get_api_key()
                    if user_answer.strip() and api_key:
                        with st.spinner("AI đang chấm bài..."):
                            try:
                                import google.generativeai as genai
                                genai.configure(api_key=api_key, transport="rest")
                                m = genai.GenerativeModel("gemini-2.5-flash")
                                core_kb = "\n".join(kb_unit.get("core_knowledge", []))
                                grade_p = f"""Bạn là Giám khảo chuyên ngành An toàn Thực phẩm (ngành Thịt) của FOOD WHY Academy.

BÀI HỌC: {s['title']}
TÌNH HUỐNG BÀI TẬP:
{challenge}

BÀI LÀM CỦA HỌC VIÊN:
{user_answer}

KIẾN THỨC CHUẨN:
{core_kb}
{s.get('content','')[:2000]}

Hãy chấm điểm trên thang 10 điểm và phản hồi theo format:
## 🎯 Điểm số: X/10
### ✅ Điểm đúng & tốt:
[liệt kê]
### ⚠️ Điểm cần bổ sung hoặc sai:
[liệt kê]
### 💡 Đáp án tham khảo đầy đủ:
[đáp án chuẩn ngắn gọn]

Phản hồi bằng tiếng Việt, thực tiễn, khích lệ học viên."""
                                resp = m.generate_content(grade_p)
                                st.session_state.challenge_feedback[f"{sel_unit}_{sel_sess}"] = resp.text
                                if source == "public_free":
                                    st.session_state.daily_question_count += 1
                            except Exception as e:
                                st.error(f"Lỗi AI: {e}")
                    elif not api_key:
                        st.warning("⚠️ Cần API Key để AI chấm bài!")
                    else:
                        st.warning("✍️ Vui lòng viết câu trả lời trước!")

                fb = st.session_state.challenge_feedback.get(f"{sel_unit}_{sel_sess}")
                if fb:
                    st.markdown("---")
                    st.markdown("### 📊 Kết quả chấm điểm của AI:")
                    st.markdown(fb)

                    # Mark as completed
                    if "completed_sessions" not in st.session_state:
                        st.session_state.completed_sessions = {}
                    if sel_unit not in st.session_state.completed_sessions:
                        st.session_state.completed_sessions[sel_unit] = []
                    if sel_sess not in st.session_state.completed_sessions[sel_unit]:
                        st.session_state.completed_sessions[sel_unit].append(sel_sess)
            else:
                st.info("💪 Bài tập thử thách chưa được tạo cho bài học này.")

            st.divider()
            # ─── Navigation buttons ──────────────────────────────
            prev_idx = current_idx - 1
            next_idx = current_idx + 1
            col_p, col_space, col_n = st.columns([1, 2, 1])
            with col_p:
                if prev_idx >= 0:
                    if st.button(f"← Bài trước", use_container_width=True):
                        st.session_state.selected_session = sessions[prev_idx]["id"]
                        st.rerun()
            with col_n:
                if next_idx < len(sessions):
                    if st.button(f"Bài tiếp →", type="primary", use_container_width=True):
                        st.session_state.selected_session = sessions[next_idx]["id"]
                        st.rerun()
                else:
                    st.success("🎉 Bạn đã hoàn thành tất cả bài học của khóa này!")

# ═══════════════════════════════════════════════════════════════════
# TAB 2: HỎI AI MENTOR
# ═══════════════════════════════════════════════════════════════════
with tab_ask:
    sel_unit = st.session_state.selected_unit
    if not sel_unit:
        st.info("👈 Hãy chọn một Khóa Học ở tab **📖 Học Tập** trước, sau đó quay lại đây để hỏi AI Mentor!")
    else:
        unit_info = UNITS.get(sel_unit, {"short": sel_unit})
        kb_unit   = knowledge.get(sel_unit, {})
        core      = kb_unit.get("core_knowledge", [])

        st.markdown(f"### 💬 Hỏi AI Mentor về **{unit_info['short']}**")

        api_key, source = get_api_key()
        can_ask = True
        if source == "public_free":
            remaining = MAX_FREE_Q - st.session_state.daily_question_count
            if remaining <= 0: can_ask = False; st.warning("⚠️ Hết lượt miễn phí! Nhập mật khẩu hoặc API Key cá nhân.")
            else: st.info(f"🎁 Còn **{remaining}** câu hỏi miễn phí hôm nay.")
        elif source == "internal": st.success("🔓 Chế độ Nội bộ — Không giới hạn!")
        elif source == "user_key": st.success("🔑 API Key cá nhân — Không giới hạn!")
        elif not api_key: can_ask = False; st.error("⚠️ Chưa có API Key!")

        chat_key = f"chat_{sel_unit}"
        if chat_key not in st.session_state: st.session_state[chat_key] = []

        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        question = st.chat_input(f"Hỏi về {unit_info['short']}..." if can_ask else "Hết lượt...", disabled=not can_ask)
        if question and can_ask and api_key:
            st.session_state[chat_key].append({"role": "user", "content": question})
            with st.chat_message("user"): st.markdown(question)

            context_parts = []
            if core: context_parts.append("KIẾN THỨC NỀN TẢNG:\n" + "\n".join(core))
            saved = load_saved_docs(sel_unit)
            if saved: context_parts.append("TÀI LIỆU CHUYÊN SÂU:\n" + saved[:5000])
            context = "\n\n".join(context_parts)

            # Also add session contents
            sessions = kb_unit.get("sessions", [])
            sel_sess = st.session_state.selected_session
            if sel_sess:
                for sess in sessions:
                    if sess["id"] == sel_sess:
                        context += f"\n\nNỘI DUNG BÀI HỌC HIỆN TẠI ({sess['title']}):\n{sess.get('content','')[:3000]}"
                        break

            system = f"""Bạn là AI Mentor CHUYÊN GIA ngành Giết mổ & Chế biến Thịt của FOOD WHY Academy.
Chuyên đề: {unit_info['short']}.

{context}

Quy tắc:
- Trả lời bằng tiếng Việt, rõ ràng, có ví dụ thực tế từ nhà máy thịt.
- Ưu tiên kiến thức từ tài liệu nội bộ. Có thể bổ sung từ kiến thức chuyên ngành.
- Trình bày bằng Markdown với tiêu đề và bullet points."""

            with st.chat_message("assistant"):
                with st.spinner("AI đang suy nghĩ..."):
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=api_key, transport="rest")
                        m = genai.GenerativeModel("gemini-2.5-flash")
                        resp = m.generate_content(system + "\n\nCÂU HỎI: " + question)
                        answer = resp.text
                        st.markdown(answer)
                        st.session_state[chat_key].append({"role": "assistant", "content": answer})
                        if source == "public_free": st.session_state.daily_question_count += 1
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

# ═══════════════════════════════════════════════════════════════════
# TAB 3: ĐẤU TRƯỜNG QA
# ═══════════════════════════════════════════════════════════════════
EXAM_DURATION = 300  # 5 phút = 300 giây

with tab_arena:
    user_role   = st.session_state.get("user_role")
    is_qm_admin = user_role in ["admin", "qm"]
    exam_data   = load_json(EXAM_FILE, {"active": False, "question": "", "month": "", "created_at": 0})

    st.markdown("### 🏆 Đấu Trường QA — Kỳ Thi Tháng")

    if is_qm_admin:
        is_active_now = exam_data.get("active", False)
        default_month = exam_data.get("month", "") if is_active_now else datetime.now().strftime("Tháng %m/%Y")
        default_q = exam_data.get("question", "") if is_active_now else ""
        btn_label = "🔄 CẬP NHẬT KỲ THI" if is_active_now else "🚀 KÍCH HOẠT KỲ THI"

        with st.expander("👨‍💼 Bảng Điều Khiển Kỳ Thi (QM Only)", expanded=not is_active_now):
            new_month = st.text_input("Kỳ thi tháng:", value=default_month)
            new_q = st.text_area("Đề thi chung:", value=default_q, placeholder="Nhập tình huống hóc búa nhất tháng này...\n(Xuống dòng tự do — format sẽ được giữ nguyên khi hiển thị)", height=200)
            cb1, cb2 = st.columns(2)
            if cb1.button(btn_label, type="primary", use_container_width=True):
                if new_q and new_month:
                    save_json(EXAM_FILE, {"active": True, "question": new_q, "month": new_month, "created_at": time.time()})
                    st.success("✅ Đã kích hoạt / cập nhật!"); st.rerun()
            if cb2.button("🚫 KẾT THÚC KỲ THI", use_container_width=True):
                exam_data["active"] = False
                save_json(EXAM_FILE, exam_data); st.rerun()

    st.markdown("---")
    if not exam_data["active"]:
        st.info("🏁 Không có kỳ thi đang diễn ra. Chờ QM kích hoạt!")
    else:
        st.markdown(f"#### 📅 Kỳ thi: <span style='color:#f97316'>{exam_data['month']}</span>", unsafe_allow_html=True)
        arena_key = "arena_global"

        # ── Hàm chấm bài & lưu kết quả (dùng chung cho nộp sớm + hết giờ) ──
        def grade_and_save(answer_text, time_taken_sec):
            """Chấm bài bằng AI, lưu kết quả kèm thời gian làm bài."""
            api_key, _ = get_api_key()
            if not api_key:
                st.error("⚠️ Không có API Key để chấm bài!")
                return
            nm = st.session_state.get(f"qa_real_name_{arena_key}", "Unknown")
            results = load_json(RESULTS_FILE, [])
            already = any(r["name"] == nm and r["month"] == exam_data["month"] for r in results)
            if already:
                st.warning(f"⚠️ {nm} đã nộp bài tháng này rồi!")
                if f"exam_started_{arena_key}" in st.session_state:
                    del st.session_state[f"exam_started_{arena_key}"]
                return

            if not answer_text or not answer_text.strip():
                answer_text = "(Thí sinh không trả lời hoặc hết giờ mà chưa viết gì.)"

            with st.spinner("🤖 AI đang chấm bài..."):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key, transport="rest")
                    m = genai.GenerativeModel("gemini-2.5-flash")
                    gp = f"""Bạn là Giám khảo chuyên gia của Kỳ thi Tháng QA — FOOD WHY Academy (Ngành Giết mổ & Chế biến Thịt).
Chấm điểm bài làm trên thang 10. Dòng đầu tiên PHẢI là: [DIEM: X/10]

ĐỀ THI:
{exam_data['question']}

BÀI LÀM CỦA THÍ SINH:
{answer_text}

Hãy chấm công bằng, chi tiết và phản hồi bằng tiếng Việt ĐÚNG theo format sau:

## 🎯 Điểm số: X/10

### ✅ Những điểm thí sinh làm tốt:
(Liệt kê cụ thể các ý đúng, kiến thức chính xác mà thí sinh đã nêu)

### ⚠️ Những điểm cần cải thiện:
(Liệt kê cụ thể các ý còn thiếu, sai hoặc chưa đầy đủ)

### 📝 ĐÁP ÁN ĐÚNG & GIẢI THÍCH CHI TIẾT:
(Đưa ra đáp án mẫu hoàn chỉnh, đầy đủ cho đề bài trên. Giải thích rõ ràng tại sao đây là đáp án đúng, viện dẫn kiến thức chuyên ngành cụ thể. Phần này phải đủ chi tiết để thí sinh đọc xong hiểu được vấn đề và học hỏi được kiến thức mới.)

### 🎓 Lời khuyên cho thí sinh:
(1-2 câu ngắn gọn khuyến khích và gợi ý hướng học tập thêm)"""
                    resp = m.generate_content(gp)
                    full = resp.text
                    sm = re.search(r'\[DIEM:\s*(\d+\.?\d*)/10\]', full)
                    score = float(sm.group(1)) if sm else 5.0

                    # Format thời gian
                    t_mins = int(time_taken_sec) // 60
                    t_secs = int(time_taken_sec) % 60
                    time_display = f"{t_mins} phút {t_secs:02d} giây"

                    results.append({
                        "name": nm,
                        "month": exam_data["month"],
                        "score": score,
                        "time_taken": round(time_taken_sec, 1),
                        "time_display": time_display,
                        "feedback": full,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_json(RESULTS_FILE, results)
                    st.balloons()
                    st.success(f"🎉 **{nm}**: **{score}/10** điểm — Hoàn thành trong **{time_display}**!")
                    st.markdown(full)
                    if f"exam_started_{arena_key}" in st.session_state:
                        del st.session_state[f"exam_started_{arena_key}"]
                except Exception as e:
                    st.error(f"Lỗi kết nối AI: {e}. Hệ thống sẽ lưu tạm bài thi của bạn.")
                    # Lưu kết quả dự phòng để không bị kẹt
                    t_mins = int(time_taken_sec) // 60
                    t_secs = int(time_taken_sec) % 60
                    time_display = f"{t_mins} phút {t_secs:02d} giây"
                    
                    results.append({
                        "name": nm,
                        "month": exam_data["month"],
                        "score": 0.0,
                        "time_taken": round(time_taken_sec, 1),
                        "time_display": time_display,
                        "feedback": "⚠️ LỖI CHẤM TỰ ĐỘNG: Hệ thống AI bị quá tải trong lúc chấm. Bài thi đã được ghi nhận thời gian. Vui lòng báo Admin để chấm điểm tay.",
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    save_json(RESULTS_FILE, results)
                    if f"exam_started_{arena_key}" in st.session_state:
                        del st.session_state[f"exam_started_{arena_key}"]
                    st.rerun()

        # ── Giao diện thi ──
        if f"exam_started_{arena_key}" not in st.session_state:
            st.markdown("""
            <div style="background:#fffbeb;border:1.5px solid #fde68a;border-radius:12px;padding:18px;margin-bottom:16px;">
                <h4 style="color:#92400e;margin:0 0 8px;">📋 Quy tắc Kỳ Thi</h4>
                <ul style="color:#78350f;font-size:0.88rem;line-height:1.7;margin:0;padding-left:18px;">
                    <li>⏱️ Thời gian làm bài: <b>5 phút</b> (đồng hồ đếm ngược)</li>
                    <li>📝 Nộp sớm sẽ được ghi nhận thời gian thực tế</li>
                    <li>⏰ Hết giờ hệ thống <b>tự động thu bài</b></li>
                    <li>🏆 Xếp hạng: <b>Điểm cao nhất</b> → nếu bằng điểm thì <b>thời gian ngắn nhất</b> lên top</li>
                    <li>🚫 Mỗi người chỉ được thi <b>1 lần/tháng</b></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            qa_name = st.text_input("👤 Nhập Họ và Tên để bắt đầu:", key=f"qa_name_arena")
            if st.button("🔥 BẮT ĐẦU LÀM BÀI", type="primary", use_container_width=True):
                if qa_name.strip():
                    st.session_state[f"exam_started_{arena_key}"] = True
                    st.session_state[f"exam_start_time_{arena_key}"] = time.time()
                    st.session_state[f"qa_real_name_{arena_key}"] = qa_name.strip()
                    st.session_state[f"auto_submitted_{arena_key}"] = False
                    st.rerun()
                else:
                    st.error("Vui lòng nhập tên!")
        else:
            start_time = st.session_state[f"exam_start_time_{arena_key}"]
            elapsed    = time.time() - start_time
            remain_sec = max(0, EXAM_DURATION - int(elapsed))
            time_taken = min(elapsed, EXAM_DURATION)
            mins, secs = divmod(remain_sec, 60)

            # ── Đồng hồ đếm ngược realtime bằng JavaScript ──
            timer_color = "#16a34a" if remain_sec > 120 else ("#f97316" if remain_sec > 60 else "#ef4444")
            components.html(f"""
            <div id="timer-box" style="text-align:center;padding:14px;border-radius:14px;
                background:{timer_color};color:white;margin-bottom:16px;
                box-shadow:0 4px 12px -2px rgba(0,0,0,0.15);">
                <div style="font-size:0.75rem;opacity:0.85;letter-spacing:1px;">⏳ THỜI GIAN CÒN LẠI</div>
                <div id="timer-display" style="font-size:2.5rem;font-weight:900;letter-spacing:2px;margin:4px 0;">
                    {mins:02d}:{secs:02d}
                </div>
                <div style="font-size:0.7rem;opacity:0.7;">Hệ thống tự động thu bài khi hết giờ</div>
            </div>
            <script>
                let remaining = {remain_sec};
                const display = document.getElementById('timer-display');
                const box = document.getElementById('timer-box');
                const interval = setInterval(() => {{
                    remaining--;
                    if (remaining <= 0) {{
                        clearInterval(interval);
                        display.textContent = "HẾT GIỜ!";
                        display.style.fontSize = "1.8rem";
                        box.style.background = "#dc2626";
                    }} else {{
                        const m = Math.floor(remaining / 60);
                        const s = remaining % 60;
                        display.textContent = String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
                        if (remaining <= 60) box.style.background = '#ef4444';
                        else if (remaining <= 120) box.style.background = '#f97316';
                    }}
                }}, 1000);
            </script>
            """, height=110)

            # ── Hết giờ → Tự động thu bài ──
            if remain_sec <= 0:
                auto_done = st.session_state.get(f"auto_submitted_{arena_key}", False)
                if not auto_done:
                    st.session_state[f"auto_submitted_{arena_key}"] = True
                    st.warning("⏰ **HẾT GIỜ!** Hệ thống đang tự động thu bài và chấm điểm...")
                    ans = st.session_state.get("arena_ans", "")
                    grade_and_save(ans, EXAM_DURATION)
                else:
                    st.info("📋 Bài thi đã được thu và chấm. Xem kết quả ở Bảng Xếp Hạng bên dưới.")
                    if st.button("🔄 Quay lại", use_container_width=True):
                        for k in [f"exam_started_{arena_key}", f"auto_submitted_{arena_key}"]:
                            if k in st.session_state: del st.session_state[k]
                        st.rerun()
            else:
                # ── Hiển thị đề thi — GIỮ NGUYÊN FORMAT XUỐNG DÒNG ──
                st.markdown("#### 📝 ĐỀ BÀI:")
                question_html = exam_data['question'].replace('\n', '<br>')
                st.markdown(f"""
                <div style="background:white;border:1.5px solid #e5e7eb;border-radius:12px;
                            padding:20px 24px;margin-bottom:16px;line-height:1.8;
                            font-size:0.92rem;color:#1f2937;white-space:pre-wrap;">
                    {question_html}
                </div>
                """, unsafe_allow_html=True)

                qa_ans = st.text_area("✍️ Câu trả lời của bạn:", height=250, key="arena_ans",
                                      placeholder="Viết phân tích và giải pháp xử lý của bạn tại đây...")

                col_submit, col_time_info = st.columns([1, 1])
                with col_submit:
                    if st.button("✅ NỘP BÀI & CHẤM ĐIỂM", type="primary", use_container_width=True):
                        if qa_ans.strip():
                            actual_time = time.time() - start_time
                            grade_and_save(qa_ans, actual_time)
                            st.rerun()
                        else:
                            st.warning("✍️ Vui lòng viết câu trả lời trước khi nộp!")
                with col_time_info:
                    done_mins = int(elapsed) // 60
                    done_secs = int(elapsed) % 60
                    st.caption(f"⏱️ Đã làm: {done_mins} phút {done_secs:02d} giây")

    # ══════════════════════════════════════
    # LEADERBOARD — Xếp hạng: Điểm cao → Thời gian ngắn
    # ══════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📊 Bảng Xếp Hạng Team QA")
    all_results = load_json(RESULTS_FILE, [])
    if not all_results:
        st.info("Chưa có kết quả thi nào.")
    else:
        # Lọc theo tháng nếu kỳ thi đang active
        filtered = all_results
        if exam_data.get("active"):
            filtered = [r for r in all_results if r.get("month") == exam_data.get("month", "")]

        if not filtered:
            st.info("Chưa có kết quả thi tháng này.")
        else:
            # Đảm bảo tương thích dữ liệu cũ
            for r in filtered:
                if "time_taken" not in r: r["time_taken"] = 300.0
                if "time_display" not in r: r["time_display"] = f"{int(r['time_taken'])//60}p {int(r['time_taken'])%60:02d}s"

            # Xếp hạng: Điểm CAO → Thời gian NGẮN
            filtered.sort(key=lambda x: (-x["score"], x["time_taken"]))

            rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}

            # Header row
            if is_qm_admin:
                hc = st.columns([0.6, 2.5, 0.8, 1, 2, 0.6])
                headers = ["🏆", "Họ Tên", "Điểm", "Thời Gian", "Ngày Thi", "Xóa"]
            else:
                hc = st.columns([0.6, 3, 0.8, 1, 2])
                headers = ["🏆", "Họ Tên", "Điểm", "Thời Gian", "Ngày Thi"]
            for col, h in zip(hc, headers):
                col.markdown(f"**{h}**")

            st.markdown("<hr style='margin:4px 0;border-color:#e5e7eb;'>", unsafe_allow_html=True)

            # Data rows
            to_delete = None
            for rank_idx, r in enumerate(filtered):
                rank_num = rank_idx + 1
                icon = rank_icons.get(rank_num, f"#{rank_num}")

                if is_qm_admin:
                    rc = st.columns([0.6, 2.5, 0.8, 1, 2, 0.6])
                else:
                    rc = st.columns([0.6, 3, 0.8, 1, 2])

                rc[0].markdown(f"**{icon}**")
                rc[1].markdown(r["name"])
                rc[2].markdown(f"**{r['score']}**/10")
                rc[3].markdown(r.get("time_display", "—"))
                rc[4].markdown(r.get("date", "—"))

                if is_qm_admin:
                    if rc[5].button("🗑️", key=f"del_result_{rank_idx}_{r['name']}_{r.get('date','')}"):
                        to_delete = r

                # Nút xem phản hồi AI (ai cũng xem được bài của mình / admin xem tất cả)
                feedback = r.get("feedback", "")
                if feedback:
                    with st.expander(f"📋 Xem phản hồi AI — {r['name']} ({r['score']}/10)", expanded=False):
                        st.markdown(feedback)

            # Xử lý xóa sau khi render xong
            if to_delete is not None:
                all_results_updated = [
                    r for r in all_results
                    if not (r["name"] == to_delete["name"]
                            and r.get("month") == to_delete.get("month")
                            and r.get("date") == to_delete.get("date"))
                ]
                save_json(RESULTS_FILE, all_results_updated)
                st.rerun()

        if is_qm_admin and st.button("🗑️ Xóa toàn bộ kết quả", use_container_width=False):
            save_json(RESULTS_FILE, []); st.rerun()

# ═══════════════════════════════════════════════════════════════════
# TAB 4: NGHIÊN CỨU LEADER
# ═══════════════════════════════════════════════════════════════════
with tab_research:
    user_role   = st.session_state.get("user_role")
    is_qm_admin = user_role in ["admin", "qm"]
    ICONS_LIST  = ["🔬","🧬","🌡️","⚗️","🦷","🩺","🥼","📊","🧪","🏭","🌾","🐄","🫁","🧫","💉"]

    if is_qm_admin:
        with st.expander("👨‍💼 GIAO NHIỆM VỤ NGHIÊN CỨU (QM)", expanded=True):
            with st.form("research_assign"):
                topic_type = st.radio("Loại:", ["✅ Có sẵn (Unit 1–10+)", "🆕 Chuyên đề MỚI"], horizontal=True)
                all_u = get_all_units()
                unit_options = [f"{v['short']} ({k})" for k, v in all_u.items()]
                sel_u_opt = st.selectbox("Chọn Unit có sẵn:", unit_options)
                tnew = st.text_input("— Hoặc — Tên chuyên đề mới:", placeholder="Unit 11 — Kiểm soát Aflatoxin...")
                new_icon = st.selectbox("Icon:", ICONS_LIST)
                new_desc = st.text_input("Mô tả ngắn:")
                desc_req = st.text_area("Yêu cầu cụ thể:", height=70)
                assigned = st.text_input("Giao cho:", placeholder="Để trống = tất cả")
                deadline = st.date_input("Deadline:")
                if st.form_submit_button("🚀 GIAO NHIỆM VỤ", type="primary"):
                    all_u2 = get_all_units()
                    u_keys = list(all_u2.keys())
                    if "Có sẵn" in topic_type:
                        idx2 = unit_options.index(sel_u_opt)
                        final_key = u_keys[idx2]
                        final_topic = all_u2[final_key]["short"]
                        is_new = False
                    else:
                        if not tnew.strip(): st.error("Nhập tên chuyên đề!"); st.stop()
                        final_key = get_next_custom_unit_key()
                        final_topic = tnew.strip()
                        save_custom_unit(final_key, new_icon, final_topic, new_desc)
                        is_new = True
                    tasks = load_json(RESEARCH_TASK_FILE, [])
                    tasks.append({"id": int(time.time()), "topic_name": final_topic, "unit_key": final_key,
                                  "is_new_unit": is_new, "description": desc_req, "assigned_to": assigned or "Tất cả Leader",
                                  "deadline": str(deadline), "month": datetime.now().strftime("Tháng %m/%Y"),
                                  "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "active": True})
                    save_json(RESEARCH_TASK_FILE, tasks)
                    st.success(f"✅ Đã giao nhiệm vụ '{final_topic}'!"); st.rerun()

        tasks = load_json(RESEARCH_TASK_FILE, [])
        active = [t for t in tasks if t.get("active")]
        if active:
            st.markdown("**📌 Nhiệm vụ đang hoạt động:**")
            for t in active:
                ct, cb = st.columns([4,1])
                ct.markdown(f"🔬 **{t['topic_name']}** → {t['assigned_to']} | Deadline: {t['deadline']}")
                if cb.button("Đóng", key=f"close_{t['id']}"):
                    for task in tasks:
                        if task["id"] == t["id"]: task["active"] = False
                    save_json(RESEARCH_TASK_FILE, tasks); st.rerun()

    st.markdown("---")
    st.markdown("### 🔬 Khu Vực Leader — Làm Bài Nghiên Cứu")
    tasks = load_json(RESEARCH_TASK_FILE, [])
    active = [t for t in tasks if t.get("active")]
    if not active:
        st.info("⏳ Chưa có nhiệm vụ nghiên cứu. Chờ QM giao bài!")
    else:
        task = st.selectbox("Chọn nhiệm vụ:", active, format_func=lambda x: f"{x['topic_name']} (Deadline: {x['deadline']})")
        topic = task["topic_name"]
        desc  = task.get("description","")
        st.info(f"📋 **Chuyên đề:** {topic} | **Yêu cầu:** {desc or 'Theo 4 bước.'} | ⏰ **Deadline:** {task['deadline']}")

        STEPS = [
            {"num":1,"title":"Thu thập Dữ liệu & Lập Đề cương","tool":"🤖 Gemini","link":"https://gemini.google.com",
             "color":"#f0fdf4","border":"#86efac","action":"Mở Gemini → Copy prompt bên dưới → Lưu kết quả.",
             "prompt":f"""Nghiên cứu về [{topic}]. {f'Yêu cầu: {desc}' if desc else ''}
1. Liệt kê quy định hiện hành từ Codex, FDA, EFSA, Bộ Y tế VN (kèm số hiệu, năm).
2. Lập đề cương 6 mục: Tổng quan, Cơ chế, Giới hạn cho phép, Phương pháp kiểm nghiệm, Rủi ro, Giải pháp.
3. Gợi ý 5 từ khóa tiếng Anh tìm trên Google Scholar."""},
            {"num":2,"title":"Thẩm định & Trích dẫn Khoa học","tool":"📚 NotebookLM","link":"https://notebooklm.google.com",
             "color":"#eff6ff","border":"#93c5fd","action":"Upload PDF từ Google Scholar → Dùng prompt bên dưới.",
             "prompt":f"""Dựa trên tài liệu đã upload về [{topic}]:
1. Các thông số kỹ thuật quan trọng (số liệu, ngưỡng...)? Kèm tên tài liệu và số trang.
2. Khác biệt giữa tiêu chuẩn quốc tế và Việt Nam?
3. Phương pháp kiểm nghiệm/kiểm soát được khuyến nghị? Kèm trích dẫn."""},
            {"num":3,"title":"Soạn thảo Báo cáo","tool":"🤖 Gemini","link":"https://gemini.google.com",
             "color":"#fefce8","border":"#fde047","action":"Copy kết quả NotebookLM → Paste cùng prompt vào Gemini.",
             "prompt":f"""Dữ liệu đã xác thực về [{topic}]:
[PASTE NỘI DUNG NOTEBOOKLM VÀO ĐÂY]
Viết Báo cáo: (1)Tóm tắt, (2)Tổng quan, (3)Kết quả (giữ trích dẫn), (4)Áp dụng tại nhà máy thịt, (5)Kết luận, (6)Tài liệu tham khảo APA."""},
            {"num":4,"title":"Xuất PDF & Nộp Bài","tool":"📄 Google Docs","link":"https://docs.google.com",
             "color":"#fff7ed","border":"#fdba74","action":"Gemini → Chia sẻ & Xuất → Export to Docs → Tải PDF → Nộp bài ↓","prompt":""},
        ]
        for step in STEPS:
            st.markdown(f"""<div style="border-radius:12px;padding:14px;margin:8px 0;background:{step['color']};border:1.5px solid {step['border']};">
<b>Bước {step['num']}: {step['title']}</b> &nbsp;|&nbsp; 🛠️ <a href="{step['link']}" target="_blank">{step['tool']}</a><br>
⚡ {step['action']}</div>""", unsafe_allow_html=True)
            if step["prompt"]: st.code(step["prompt"], language="text")

        st.markdown("---")
        st.markdown("### 📤 Nộp Bài & Lưu Vào Knowledge Base")
        leader_name  = st.text_input("Họ và Tên Leader:", key="leader_name_r")
        uploaded_pdf = st.file_uploader("Upload file PDF báo cáo:", type=["pdf"], key="research_pdf")
        if st.button("🏁 NỘP BÀI & CHỜ DUYỆT", type="primary", use_container_width=True):
            if leader_name and uploaded_pdf:
                pdf_bytes = uploaded_pdf.getvalue()
                try:
                    reader   = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                    pdf_text = "\n".join(p.extract_text() or "" for p in reader.pages)
                except: pdf_text = ""
                sub_data = {"task_id": task["id"], "topic": topic, "leader": leader_name,
                            "unit_key": task.get("unit_key"), "filename": uploaded_pdf.name,
                            "text_content": pdf_text, "approved": False,
                            "month": task["month"], "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
                with st.spinner("Đang đẩy lên Cloud..."):
                    firebase_utils.save_research_submission(sub_data, pdf_bytes)
                st.balloons()
                st.success(f"✅ Đã nộp! QM sẽ duyệt bài của {leader_name}.")
            else: st.warning("Vui lòng nhập tên và upload PDF!")

    # Dashboard
    st.markdown("---")
    st.markdown("### 📊 Dashboard Tiến Độ & Duyệt Bài")
    cloud_subs = firebase_utils.get_research_submissions()
    subs_list  = []
    if cloud_subs:
        if isinstance(cloud_subs, dict):
            for sid, sdata in cloud_subs.items():
                if isinstance(sdata, dict): sdata["id"] = sid; subs_list.append(sdata)
        elif isinstance(cloud_subs, list):
            for i, sdata in enumerate(cloud_subs):
                if isinstance(sdata, dict): sdata["id"] = str(i); subs_list.append(sdata)
    cur_month  = datetime.now().strftime("Tháng %m/%Y")
    all_tasks  = load_json(RESEARCH_TASK_FILE, [])
    act_tasks  = [t for t in all_tasks if t.get("active")]
    month_subs = [s for s in subs_list if s.get("month") == cur_month]
    c1, c2, c3 = st.columns(3)
    c1.metric("Nhiệm vụ đang giao", len(act_tasks))
    c2.metric("Đã nộp tháng này", len(month_subs))
    c3.metric("Chưa nộp", max(0, len(act_tasks) - len(month_subs)))
    for s in sorted(month_subs, key=lambda x: x.get("submitted_at",""), reverse=True):
        icon = "✅" if s.get("approved") else "⏳"
        with st.expander(f"{icon} **{s['leader']}** — {s['topic']} — `{s.get('submitted_at','')}`"):
            cc1, cc2, cc3 = st.columns([2,1,1])
            with cc1: st.caption(f"Unit: `{s.get('unit_key','?')}`")
            with cc2:
                try:
                    pdf_d = base64.b64decode(s["pdf_base64"])
                    st.download_button("📥 Tải PDF", pdf_d, f"Report_{s['leader']}.pdf", "application/pdf", key=f"dl_{s['id']}")
                except: st.caption("(Không có PDF)")
            with cc3:
                if is_qm_admin and not s.get("approved"):
                    if st.button("🌟 DUYỆT & NẠP AI", key=f"appr_{s['id']}", type="primary"):
                        with st.spinner("Đang nạp kiến thức..."):
                            firebase_utils.approve_research_submission(s["id"], s["unit_key"],
                                f"{s['leader']}_approved_{s['id']}.txt", s.get("text_content",""))
                            st.success("✅ Đã phê duyệt!"); st.rerun()

# ═══════════════════════════════════════════════════════════════════
# TAB 5: AUTO-CONTENT ENGINE (Admin only)
# ═══════════════════════════════════════════════════════════════════
with tab_admin:
    user_role = st.session_state.get("user_role")
    if user_role != "admin":
        st.warning("🔐 Chức năng này chỉ dành cho **Admin (Sếp)**. Vui lòng đăng nhập ở thanh bên trái.")
        st.stop()

    st.markdown("""
    <div class="acad-hero">
        <h1>🤖 Auto-Content Engine</h1>
        <p>AI tự động tạo nội dung khóa học — Sếp chỉ cần ra lệnh & duyệt!</p>
    </div>
    """, unsafe_allow_html=True)

    api_key, _ = get_api_key()
    if not api_key:
        st.error("⚠️ Cần API Key để sử dụng tính năng này!"); st.stop()

    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown("### 🎯 Cài đặt Tạo Nội Dung")

        all_units_e = get_all_units()
        unit_options_e = [f"{v['icon']} {v['short']} ({k})" for k, v in all_units_e.items()]
        sel_unit_e = st.selectbox("Chọn khóa học cần tạo bài:", unit_options_e, key="auto_unit_sel")
        unit_key_e = list(all_units_e.keys())[unit_options_e.index(sel_unit_e)]
        unit_info_e = all_units_e[unit_key_e]

        st.markdown("---")
        st.markdown("**Hoặc tạo Khóa học HOÀN TOÀN MỚI:**")
        new_unit_topic = st.text_input("Chủ đề mới:", placeholder="VD: Chứng nhận FSSC 22000 phiên bản 6")
        new_unit_icon  = st.text_input("Icon:", value="🆕", max_chars=5)
        new_unit_desc  = st.text_input("Mô tả ngắn:", placeholder="Yêu cầu, điều kiện, điểm mới...")

        st.markdown("---")
        st.markdown("**Thông tin bổ sung cho AI:**")
        extra_context = st.text_area("Nội dung tài liệu (paste từ NotebookLM/Google):", height=180,
                                     placeholder="Paste nội dung tài liệu đào tạo của bạn vào đây. AI sẽ dùng làm nguồn kiến thức chính...")
        youtube_link = st.text_input("Link Video YouTube của FOOD WHY (tùy chọn):", placeholder="https://www.youtube.com/watch?v=...")
        n_sessions   = st.slider("Số Sessions cần tạo:", 1, 6, 4)

        generate_btn = st.button("⚡ TẠO NỘI DUNG TỰ ĐỘNG", type="primary", use_container_width=True)

    with col_r:
        st.markdown("### 📊 Trạng thái & Kết quả")

        if generate_btn:
            # Determine unit
            if new_unit_topic.strip():
                final_unit_key  = get_next_custom_unit_key()
                final_unit_name = new_unit_topic.strip()
                save_custom_unit(final_unit_key, new_unit_icon or "🆕", final_unit_name, new_unit_desc)
            else:
                final_unit_key  = unit_key_e
                final_unit_name = unit_info_e["short"]

            # Build YouTube embed
            yt_embed = ""
            if youtube_link:
                yt_id = ""
                if "v=" in youtube_link:
                    yt_id = youtube_link.split("v=")[1].split("&")[0]
                elif "youtu.be/" in youtube_link:
                    yt_id = youtube_link.split("youtu.be/")[1].split("?")[0]
                if yt_id: yt_embed = f"https://www.youtube.com/embed/{yt_id}"

            progress_bar = st.progress(0, text="Đang chuẩn bị...")
            status_area  = st.empty()

            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key, transport="rest")
                m = genai.GenerativeModel("gemini-2.5-flash")

                knowledge_curr = load_knowledge()
                all_sessions   = []

                for sess_i in range(1, n_sessions + 1):
                    progress_bar.progress(int((sess_i - 1) / n_sessions * 90), text=f"⚡ Đang tạo Session {sess_i}/{n_sessions}...")
                    status_area.info(f"🔄 Session {sess_i}: AI đang nghiên cứu và soạn thảo...")

                    prompt = f"""Bạn là chuyên gia đào tạo ngành An toàn Thực phẩm (Giết mổ & Chế biến Thịt) của FOOD WHY Academy.

Chủ đề khóa học: {final_unit_name}
Session số: {sess_i}/{n_sessions}

{"Tài liệu tham khảo:" + extra_context[:4000] if extra_context else ""}

Hãy tạo nội dung đầy đủ cho Session {sess_i} theo định dạng JSON sau (trả về JSON thuần túy, không có markdown code block):
{{
  "id": "session_{sess_i}",
  "title": "Tên bài học ngắn gọn, hấp dẫn (tối đa 8 từ)",
  "week": {sess_i},
  "video_url": "",
  "pre_question": {{
    "question": "Câu hỏi tình huống gợi mở liên quan đến vibe FOOD WHY (Sasa, Ran, Rento). Thực tế, gây tò mò.",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct": 0,
    "explanation": "Giải thích khoa học ngắn gọn tại sao đáp án đúng (2-3 câu)"
  }},
  "content": "Nội dung bài học chi tiết 400-600 từ dùng Markdown. Có tiêu đề ##, bullet, bảng so sánh nếu phù hợp. Thực tiễn, ứng dụng ngay tại nhà máy.",
  "flashcards": [
    {{"front": "Thuật ngữ/câu hỏi ngắn", "back": "Định nghĩa/đáp án ngắn gọn có icon emoji"}},
    {{"front": "...", "back": "..."}},
    {{"front": "...", "back": "..."}}
  ],
  "challenge": "Tình huống thực tế tại nhà máy giết mổ/chế biến thịt chi tiết. Yêu cầu QA phân tích và đề xuất giải pháp cụ thể."
}}

QUAN TRỌNG: Chỉ trả về JSON hợp lệ, không thêm text ngoài JSON."""

                    resp = m.generate_content(prompt)
                    raw  = resp.text.strip()

                    # Clean JSON
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"): raw = raw[4:]
                    raw = raw.strip().rstrip("```").strip()

                    sess_data = json.loads(raw)
                    if yt_embed and sess_i == 1:
                        sess_data["video_url"] = yt_embed
                    all_sessions.append(sess_data)
                    status_area.success(f"✅ Session {sess_i}: **{sess_data.get('title','')}** — Hoàn thành!")

                # Save to knowledge_base
                progress_bar.progress(95, text="Đang lưu vào hệ thống...")
                kb = load_knowledge()
                if final_unit_key not in kb:
                    kb[final_unit_key] = {"title": final_unit_name, "references": [], "core_knowledge": [], "sessions": []}
                kb[final_unit_key]["sessions"] = all_sessions
                save_knowledge(kb)
                firebase_utils.sync_all_to_firebase()

                progress_bar.progress(100, text="✅ Hoàn thành!")
                st.success(f"""🎉 **Tạo xong {n_sessions} Sessions cho khóa '{final_unit_name}'!**
                
Hãy chuyển sang tab **📖 Học Tập** để xem kết quả!""")
                st.balloons()

            except json.JSONDecodeError as e:
                st.error(f"❌ AI trả về dữ liệu không đúng format JSON: {e}")
                st.code(raw[:2000] if 'raw' in dir() else "Không có dữ liệu")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")

        else:
            st.markdown("""
            <div style="background:#f9fafb;border-radius:14px;padding:24px;text-align:center;color:#78716c;margin-top:20px;">
                <div style="font-size:3rem;">🤖</div>
                <h4 style="color:#44403c;margin:12px 0 8px;">Sẵn sàng tạo nội dung</h4>
                <p style="font-size:0.85rem;line-height:1.6;">
                    Chọn khóa học hoặc nhập chủ đề mới ở cột bên trái.<br>
                    AI sẽ tự động tạo: <b>Câu hỏi gợi mở → Nội dung → Flashcards → Bài tập thử thách</b><br>
                    cho mỗi Session trong vài giây!
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        # Manage existing sessions
        st.markdown("### 📋 Quản lý Sessions Hiện Tại")
        kb_now2 = load_knowledge()
        all_u2  = get_all_units()
        for uk, udata in kb_now2.items():
            sessions_now = udata.get("sessions", [])
            if sessions_now:
                uinfo = all_u2.get(uk, {"short": uk, "icon": "📄"})
                with st.expander(f"{uinfo.get('icon','')} {uinfo['short']} — {len(sessions_now)} Sessions"):
                    for s in sessions_now:
                        sc1, sc2 = st.columns([4,1])
                        sc1.markdown(f"**Tuần {s.get('week','?')}: {s['title']}**")
                        if sc2.button("🗑️", key=f"del_sess_{uk}_{s['id']}", help="Xóa session"):
                            kb2 = load_knowledge()
                            kb2[uk]["sessions"] = [x for x in kb2[uk]["sessions"] if x["id"] != s["id"]]
                            save_knowledge(kb2)
                            st.rerun()
