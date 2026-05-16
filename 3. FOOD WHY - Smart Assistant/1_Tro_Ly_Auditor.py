import streamlit as st
import google.generativeai as genai
import PyPDF2
from PIL import Image
import io

# Cấu hình trang
st.set_page_config(
    page_title="FoodAuditor AI",
    page_icon="⚖️",
    layout="wide"
)

# Thiết lập giao diện CSS
st.markdown("""
<style>
    .persona-box {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(249, 115, 22, 0.4);
    }
    .food-why-logo {
        color: white;
        font-weight: 900;
        font-size: 28px;
        letter-spacing: 1px;
        margin-bottom: 5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .stChatMessage { border-radius: 10px; }
    /* Đổi màu một số thành phần cơ bản của Streamlit sang cam (nếu có thể) */
    div.stButton > button:first-child {
        background-color: #f97316;
        color: white;
        border-color: #f97316;
    }
    div.stButton > button:first-child:hover {
        background-color: #ea580c;
        border-color: #ea580c;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# CẤU HÌNH API KEY (Lấy từ file TXT của Sếp hoặc Cloud)
# -------------------------------------------------------------
API_KEY = None

# Thử lấy từ Cloud (nếu đã đưa lên mạng)
try:
    secret_key = st.secrets["GEMINI_API_KEY"]
    if secret_key and "Sếp_dán" not in secret_key:
        API_KEY = secret_key
except:
    pass

# Nếu chưa đưa lên mạng, lấy từ file TXT của Sếp ở máy tính
if not API_KEY:
    try:
        import re
        with open("API_KEY_CUA_SEP.txt", "r", encoding="utf-8") as f:
            key_in_file = f.read()
            # Bỏ chữ mẫu nếu Sếp quên xóa
            if "Sếp" in key_in_file or "dán" in key_in_file:
                pass
            else:
                # Dọn sạch ký tự thừa
                API_KEY = re.sub(r'[^a-zA-Z0-9_-]', '', key_in_file)
    except:
        pass

if API_KEY:
    # Bắt buộc dùng giao thức REST để tránh lỗi gRPC (Illegal header value) do mạng
    genai.configure(api_key=API_KEY, transport="rest")
    api_configured = True
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    api_configured = False
    model = None

# -------------------------------------------------------------
# KHAI BÁO NHÂN VẬT VÀ LỆNH CỐT LÕI (SYSTEM INSTRUCTION)
# -------------------------------------------------------------
SYSTEM_PROMPT = """Bạn là trợ lý ảo tên "Em", một CHUYÊN GIA HÀNG ĐẦU VỀ LUẬT THỰC PHẨM VÀ TIÊU CHUẨN AUDIT.
Người dùng là "Sếp". LUÔN xưng hô là "Em" và "Sếp".
Nhiệm vụ của bạn:
1. Trả lời các câu hỏi về luật/tiêu chuẩn dựa trên TÀI LIỆU SẾP TẢI LÊN.
2. Nếu có tải hình ảnh, hãy phân tích lỗi vi phạm an toàn thực phẩm trong ảnh, trích dẫn rõ ràng cơ sở pháp lý (Tên tài liệu, Chương, Điều, Khoản).
3. Không trả lời các câu hỏi ngoài lề (giải trí, thời tiết...).
4. Trình bày bằng Markdown rõ ràng, dễ đọc.
"""

# Khởi tạo bộ nhớ tạm (Context)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "document_context" not in st.session_state:
    st.session_state.document_context = ""

# -------------------------------------------------------------
# SIDEBAR: KHU VỰC TẢI TÀI LIỆU
# -------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="persona-box"><div class="food-why-logo">FOOD WHY</div><h4 style="margin-top: 0; color: white;">⚖️ Trợ Lý Auditor</h4><p style="font-size:13px; color: #ffe8d6; margin-bottom: 0;">Chuyên gia xử lý tài liệu và soi lỗi hiện trường.</p></div>', unsafe_allow_html=True)
    
    if not api_configured:
        st.error("⚠️ Hệ thống chưa được cấp API Key. Sếp vui lòng thiết lập file secrets.toml để kích hoạt não bộ AI.")
    
    st.subheader("📁 Tải Tài Liệu Tiêu Chuẩn")
    st.caption("Cho phép tải nhiều file (PDF/TXT). Tổng dung lượng < 5MB để đảm bảo hệ thống không bị quá tải.")
    
    uploaded_files = st.file_uploader(
        "Chọn file tài liệu:", 
        type=['pdf', 'txt'], 
        accept_multiple_files=True
    )
    
    # XỬ LÝ ĐỌC FILE KHI CÓ UPLOAD
    if uploaded_files:
        total_size = sum([f.size for f in uploaded_files])
        # Kiểm tra dung lượng (5MB = 5 * 1024 * 1024 bytes)
        if total_size > 5 * 1024 * 1024:
            st.error("🚨 Sếp ơi, tổng dung lượng các file Sếp chọn lớn hơn 5MB mất rồi. Sếp bỏ bớt file ra giúp em nhé!")
            st.session_state.document_context = "" # Reset context
        else:
            with st.spinner("Em đang đọc và tổng hợp tất cả tài liệu Sếp giao..."):
                combined_text = ""
                for file in uploaded_files:
                    try:
                        if file.name.endswith('.pdf'):
                            pdf_reader = PyPDF2.PdfReader(file)
                            for page in pdf_reader.pages:
                                combined_text += page.extract_text() + "\n"
                        elif file.name.endswith('.txt'):
                            combined_text += file.getvalue().decode("utf-8") + "\n"
                    except Exception as e:
                        st.warning(f"Lỗi khi đọc file {file.name}: {e}")
                
                # Lưu vào bộ nhớ
                if combined_text.strip():
                    st.session_state.document_context = combined_text
                    st.success(f"✅ Đã đọc xong {len(uploaded_files)} file (Tổng: {round(total_size/1024/1024, 2)} MB). Sếp bắt đầu hỏi em được rồi ạ!")
    else:
        st.info("Sếp chưa tải tài liệu nào. Em sẽ dùng kiến thức nền mặc định.")
        st.session_state.document_context = ""

# -------------------------------------------------------------
# MAIN CHAT VÀ VISION
# -------------------------------------------------------------
st.title("💬 Phòng Trò Chuyện & Audit Hiện Trường")

# Vùng chứa ảnh tải lên để soi lỗi
with st.expander("📸 SOI HÌNH ẢNH HIỆN TRƯỜNG (VISION)", expanded=False):
    st.write("Sếp gửi ảnh khu vực nghi ngờ vi phạm lên đây, em sẽ dùng Mắt Thần đối chiếu với tài liệu để lập biên bản ạ!")
    image_file = st.file_uploader("Tải ảnh hiện trường (JPG/PNG)", type=['jpg', 'jpeg', 'png'])
    if image_file:
        img = Image.open(image_file)
        st.image(img, width=300, caption="Ảnh Sếp vừa gửi")

# Hiển thị lịch sử chat
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Xử lý khi người dùng nhập câu hỏi
prompt = st.chat_input("Sếp dặn gì em ạ? (Ví dụ: Lỗi trong ảnh vi phạm điều mấy?)")

if prompt and api_configured:
    # 1. Hiển thị câu hỏi của Sếp
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Xây dựng nội dung gửi cho AI
    # Ghép Prompt + Tài Liệu + Image
    context_text = f"\n\n--- TÀI LIỆU THAM KHẢO ---\n{st.session_state.document_context}\n--- HẾT TÀI LIỆU ---" if st.session_state.document_context else ""
    
    full_prompt = [SYSTEM_PROMPT + context_text + "\n\nCÂU HỎI CỦA SẾP: " + prompt]
    
    # Nếu Sếp có tải ảnh lên, chèn ảnh vào List gửi cho mô hình
    if image_file:
        img = Image.open(image_file)
        full_prompt.insert(0, img) # Mắt thần Gemini tự động đọc ảnh

    # 3. Giao tiếp với Gemini API
    with st.chat_message("assistant"):
        with st.spinner("Em đang lục tung tài liệu và suy nghĩ..."):
            try:
                response = model.generate_content(full_prompt)
                ai_reply = response.text
                st.markdown(ai_reply)
                st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
            except Exception as e:
                st.error(f"Dạ Sếp, mạng bên em bị trục trặc rồi ạ: {e}")
                
elif prompt and not api_configured:
    st.error("Chưa có API Key, em không thể suy nghĩ được Sếp ơi!")
