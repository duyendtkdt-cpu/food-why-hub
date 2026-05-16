import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, storage
import json
import os
import base64

def init_firebase():
    if not firebase_admin._apps:
        try:
            # Thử lấy từ st.secrets (Streamlit mode)
            try:
                secrets = st.secrets
                creds_dict = dict(secrets["firebase"])
                db_url = secrets["FIREBASE_DATABASE_URL"]
            except:
                # Fallback cho Script mode (chạy bằng py -c)
                import tomllib
                base_dir = os.path.dirname(__file__)
                secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")
                with open(secrets_path, "rb") as f:
                    secrets = tomllib.load(f)
                creds_dict = secrets["firebase"]
                db_url = secrets["FIREBASE_DATABASE_URL"]

            # Firebase cần private_key có dấu xuống dòng thực sự
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred, {
                'databaseURL': db_url,
                'storageBucket': f"{creds_dict['project_id']}.appspot.com"
            })
        except Exception as e:
            print(f"Lỗi khởi tạo Firebase: {e}")

def sync_all_to_firebase():
    """Đẩy toàn bộ file JSON trong thư mục data/ lên Firebase"""
    init_firebase()
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir): return

    ref = db.reference("/")
    for f in os.listdir(data_dir):
        if f.endswith(".json"):
            path = os.path.join(data_dir, f)
            key = f.replace(".json", "")
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    ref.child(key).set(data)
            except Exception as e:
                print(f"Lỗi sync {f}: {e}")

    # Đồng bộ cả custom_units trong knowledge
    know_dir = os.path.join(os.path.dirname(__file__), "knowledge")
    custom_file = os.path.join(know_dir, "custom_units.json")
    if os.path.exists(custom_file):
        try:
            with open(custom_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                ref.child("custom_units").set(data)
        except: pass

def init_sync_from_firebase():
    """Tải dữ liệu từ Firebase về máy khi khởi động app"""
    init_firebase()
    ref = db.reference("/")
    cloud_data = ref.get()
    
    if not cloud_data: return

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Khôi phục các file JSON trong data/
    for key, value in cloud_data.items():
        if key in ["knowledge_store", "research_submissions"]: continue # Xử lý riêng
        
        if key == "custom_units":
            know_dir = os.path.join(os.path.dirname(__file__), "knowledge")
            os.makedirs(know_dir, exist_ok=True)
            path = os.path.join(know_dir, "custom_units.json")
        else:
            path = os.path.join(data_dir, f"{key}.json")
            
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False)
        except: pass

    # Khôi phục Knowledge Text (cho AI học)
    know_store = cloud_data.get("knowledge_store", {})
    for unit_key, docs in know_store.items():
        unit_dir = os.path.join(os.path.dirname(__file__), "knowledge", unit_key)
        os.makedirs(unit_dir, exist_ok=True)
        for safe_fname, text in docs.items():
            # Khôi phục dấu chấm (ví dụ: file_txt -> file.txt)
            real_fname = safe_fname
            if "_" in safe_fname:
                parts = safe_fname.rsplit("_", 1)
                real_fname = parts[0] + "." + parts[1]
            
            try:
                with open(os.path.join(unit_dir, real_fname), "w", encoding="utf-8") as f:
                    f.write(text)
            except: pass

def save_knowledge_text(unit_key, filename, text):
    """Lưu văn bản rút trích từ PDF lên mây vĩnh viễn và lưu local"""
    init_firebase()
    # Firebase key không được chứa dấu chấm
    safe_fname = filename.replace(".", "_")
    ref = db.reference(f"/knowledge_store/{unit_key}/{safe_fname}")
    ref.set(text)
    
    # Lưu local để hiện ngay trong danh sách
    base_dir = os.path.dirname(__file__)
    unit_dir = os.path.join(base_dir, "knowledge", unit_key)
    os.makedirs(unit_dir, exist_ok=True)
    try:
        with open(os.path.join(unit_dir, filename), "w", encoding="utf-8") as f:
            f.write(text)
    except: pass

def save_research_submission(sub_data, pdf_bytes):
    """Lưu bài nộp của Leader kèm file PDF (Base64)"""
    init_firebase()
    # Mã hóa PDF sang Base64
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    sub_data["pdf_base64"] = b64_pdf
    
    ref = db.reference("/research_submissions").push()
    sub_data["id"] = ref.key
    ref.set(sub_data)
    return ref.key

def get_research_submissions():
    init_firebase()
    ref = db.reference("/research_submissions")
    return ref.get() or {}

def approve_research_submission(sub_id, unit_key, filename, text):
    """QM duyệt bài: Chuyển text sang Knowledge Store để AI học"""
    init_firebase()
    # 1. Lưu vào Knowledge Store
    save_knowledge_text(unit_key, filename, text)
    # 2. Đánh dấu đã duyệt
    ref = db.reference(f"/research_submissions/{sub_id}")
    ref.update({"approved": True})

def delete_research_submission(sub_id):
    init_firebase()
    db.reference(f"/research_submissions/{sub_id}").delete()

def delete_knowledge_text(unit_key, filename):
    """Xóa văn bản kiến thức trên Firebase"""
    init_firebase()
    safe_fname = filename.replace(".", "_")
    db.reference(f"/knowledge_store/{unit_key}/{safe_fname}").delete()
