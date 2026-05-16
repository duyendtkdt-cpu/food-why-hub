import streamlit as st
import firebase_utils

# Đồng bộ dữ liệu từ Cloud khi khởi chạy (chỉ chạy 1 lần mỗi session)
if "firebase_synced" not in st.session_state:
    with st.spinner("🔄 Đang kết nối và đồng bộ dữ liệu từ Firebase..."):
        firebase_utils.init_sync_from_firebase()
        st.session_state.firebase_synced = True

st.set_page_config(
    page_title="FOOD WHY - Hub",
    page_icon="🍊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Giao diện CSS
st.markdown("""
<style>
    .hero-box {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        color: white;
        padding: 50px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(249, 115, 22, 0.4);
        margin-bottom: 40px;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    .card {
        background: white;
        border: 2px solid #ffedd5;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        height: 100%;
    }
    .card:hover {
        border-color: #f97316;
        box-shadow: 0 10px 15px -3px rgba(249, 115, 22, 0.2);
        transform: translateY(-5px);
    }
    .card-icon {
        font-size: 3rem;
        margin-bottom: 15px;
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #f97316;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Phần Hero
st.markdown("""
<div class="hero-box">
    <div class="hero-title">FOOD WHY</div>
    <p style="font-size: 1.2rem; opacity: 0.9;">Hệ Sinh Thái Ứng Dụng Kỹ Thuật & An Toàn Thực Phẩm</p>
</div>
""", unsafe_allow_html=True)

st.write("### 🚀 Khám Phá Công Cụ")

# Hàng 1: 3 ứng dụng chính
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-icon">⚖️</div>
        <div class="card-title">Trợ Lý Auditor</div>
        <p style="font-size: 14px; color: #666;">Đọc hiểu tiêu chuẩn (ISO, FSSC, Luật), đối chiếu tài liệu và soi lỗi hiện trường bằng AI.</p>
        <span style="background: #f97316; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">Đang mở</span>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card" style="border-color: #f97316; box-shadow: 0 6px 20px -4px rgba(249,115,22,0.3);">
        <div class="card-icon">🎓</div>
        <div class="card-title">QA AI Academy</div>
        <p style="font-size: 14px; color: #666;">10 chuyên đề đào tạo thực chiến ngành thịt. AI Mentor hỏi đáp, bài tập tình huống có chấm điểm.</p>
        <span style="background: #f97316; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">🔥 MỚI</span>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-icon">👅</div>
        <div class="card-title">Sensory Panel</div>
        <p style="font-size: 14px; color: #666;">Quản lý dữ liệu cảm quan, phân tích phổ vị và gợi ý cải tiến công thức sản phẩm.</p>
        <span style="background: #ccc; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">Sắp ra mắt</span>
    </div>
    """, unsafe_allow_html=True)

# Hàng 2: 2 ứng dụng còn lại
col4, col5, _ = st.columns(3)

with col4:
    st.markdown("""
    <div class="card">
        <div class="card-icon">🏷️</div>
        <div class="card-title">Nutri-Label</div>
        <p style="font-size: 14px; color: #666;">Tạo nhãn dinh dưỡng tự động theo chuẩn FDA và quy định nhãn mác Việt Nam.</p>
        <span style="background: #ccc; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">Sắp ra mắt</span>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="card">
        <div class="card-icon">🧪</div>
        <div class="card-title">E-Number Decoder</div>
        <p style="font-size: 14px; color: #666;">Giải mã phụ gia thực phẩm, kiểm tra giới hạn ADI và mức độ an toàn theo Codex.</p>
        <span style="background: #ccc; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">Sắp ra mắt</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption("© 2026 FOOD WHY Studio. All rights reserved.")
