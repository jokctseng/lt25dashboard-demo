import streamlit as st
from supabase import Client
import uuid 
from supabase import create_client 

# --- Session State 初始化 ---

def init_global_session_state():
    """初始化所有 Streamlit Session 狀態。"""
    
    if "supabase" not in st.session_state:
        st.session_state.supabase = None
    if "supabase_admin" not in st.session_state:
        st.session_state.supabase_admin = None
        
    # 註冊用戶狀態
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = "guest"
    if "username" not in st.session_state:
        st.session_state.username = None
        
    # 訪客專用狀態 
    if "guest_username" not in st.session_state:
        st.session_state.guest_username = "匿名演練選手"
    if "captcha_passed" not in st.session_state:
        st.session_state.captcha_passed = False 


# --- Helper Functions ---

def fetch_user_profile(supabase_client: Client, user_id):
    """從 profiles 表格獲取使用者角色與暱稱"""
    try:
        if supabase_client:
            response = supabase_client.table('profiles').select("role, username").eq('id', user_id).single().execute()
            st.session_state.role = response.data['role']
            st.session_state.username = response.data['username']
    except Exception:
        st.session_state.role = "user"
        st.session_state.username = None

def auto_update_username(supabase: Client, new_username):
    """自動儲存已登入使用者的暱稱"""
    try:
        if st.session_state.user:
            supabase.table('profiles').update({"username": new_username}).eq('id', st.session_state.user.id).execute()
            st.session_state.username = new_username
            st.toast("暱稱已自動儲存！")
    except Exception as e:
        st.error(f"儲存失敗: {e}")


# --- 介面渲染 ---

def render_page_sidebar_ui(supabase: Client | None, is_connected: bool):
    """
    渲染側欄：登入入口 + 已登入用戶資訊 + 訪客暱稱設定。
    """
    
    init_global_session_state() 

    if not is_connected or supabase is None:
        st.sidebar.error("連線錯誤，無法登入/註冊。")
        return
        
    # --- 訪客暱稱輸入框 ---
    if st.session_state.user is None:
        
        st.sidebar.subheader("😊 匿名演練選手設定")
        
        st.session_state.guest_username = st.sidebar.text_input(
            "匿名發言暱稱 (限本次瀏覽)",
            value=st.session_state.guest_username,
            key="sidebar_guest_username_input" 
        )
        st.sidebar.caption("您的暱稱將在所有互動功能中沿用。")
        st.sidebar.markdown("---")
        
        # --- 管理登入區 ---
        with st.sidebar.expander("🔑 管理員/版主登入入口", expanded=False):
            st.info("此區僅供管理員/版主使用。")
            with st.form("admin_auth_form"):
                email = st.text_input("Email", key="login_email_input")
                password = st.text_input("密碼", type="password", key="login_password_input")
                submitted = st.form_submit_button("登入")

                if submitted:
                    if not email or not password:
                        st.sidebar.error("請輸入 Email 和密碼。")
                        return
                        
                    try:
                        user_session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = user_session.user
                        fetch_user_profile(supabase, user_session.user.id)
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"認證失敗: {e}")
                
            # 忘記密碼提醒
            st.markdown("---")
            if st.button("忘記密碼？"):
                 st.info("請聯繫系統管理員協助重設密碼。")


    # --- 已登入使用者資訊與設定 ---
    else:
        # 已登入顯示稱謂
        user_role = st.session_state.role
        user_email = st.session_state.user.email
        display_name = st.session_state.username
        
        # 決定問候語的顯示名稱
        if user_role == 'system_admin':
            greeting_name = f"管理員 - {display_name or user_email}"
        elif user_role == 'moderator':
            greeting_name = f"版主 - {display_name or user_email}"
        elif display_name:
            greeting_name = f"{display_name}選手"
        else:
            greeting_name = "匿名演練選手"
            
        st.sidebar.write(f"👋 歡迎, **{greeting_name}**") 
        st.sidebar.caption(f"(角色: {user_role})")
        
        # 登出按鈕
        if st.sidebar.button("登出"):
            supabase.auth.sign_out()
            init_global_session_state() # 重置所有狀態
            st.rerun()
            
        # 個人設定和 Admin 提示
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 個人設定")
        current_username = st.session_state.username or ""
        st.sidebar.text_input(
            "公開暱稱", 
            value=current_username,
            key="page_new_username_input", 
            on_change=lambda: auto_update_username(supabase, st.session_state.page_new_username_input)
        )
        
        if st.session_state.role == 'system_admin':
            st.sidebar.markdown("---")
            st.sidebar.warning("🔑 系統管理員：請至 [Admin Dashboard] 頁面管理使用者權限與個資。")
