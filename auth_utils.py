import streamlit as st
from supabase import Client
import uuid
from streamlit_hcaptcha import hcaptcha 

def fetch_user_profile(supabase_client: Client, user_id):
    """表格獲取使用者角色與暱稱"""
    try:
        if supabase_client:
            response = supabase_client.table('profiles').select("role, username").eq('id', user_id).single().execute()
            st.session_state.role = response.data['role']
            st.session_state.username = response.data['username']
    except Exception:
        st.session_state.role = "user"
        st.session_state.username = None

def auto_update_username(supabase: Client, new_username):
    """無按鈕自動儲存暱稱"""
    try:
        if st.session_state.user:
            supabase.table('profiles').update({"username": new_username}).eq('id', st.session_state.user.id).execute()
            st.session_state.username = new_username
            st.toast("暱稱已自動儲存！")
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        
# --- 主渲染函式：只定義一次，並隔離 Admin 登入 ---

def render_sidebar_auth(supabase: Client | None, is_connected: bool):
    """
    渲染 Admin 專用登入入口和用戶資訊。
    """
    
    if not is_connected or supabase is None:
        st.sidebar.error("連線錯誤，無法登入/註冊。")
        return
        
    # --- 登入/權限邏輯 ---
    if st.session_state.user is None:
        
        # 訪客模式：只顯示 Admin 入口
        st.sidebar.subheader("🔑 權限認證入口")
        st.sidebar.info("一般訪客無需登入。此通道僅供管理員/版主使用。")

        # --- Admin 專用登入區塊 ---
        with st.sidebar.expander("管理員/版主登入", expanded=True):
            
            # 兩種登入方式選擇
            auth_mode = st.radio(
                "選擇登入方式", 
                ["Google OAuth (推薦)", "傳統 Email/密碼"], 
                key="admin_auth_mode_select"
            )
            
            st.markdown("---")
            
            if auth_mode == "Google OAuth (推薦)":
                if st.button("🚀 Google 登入 (Admin)", use_container_width=True):
                    try:
                        response = supabase.auth.sign_in_with_oauth(
                            "google", 
                            options={"redirectTo": "https://lt25.streamlit.app/"}
                        )
                        st.markdown(f'<script>window.location.href = "{response.url}";</script>', unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.sidebar.error(f"Google 登入失敗: {e}")
            
            else: # Email/密碼登入
                with st.form("admin_pwd_form"):
                    admin_email = st.text_input("Admin Email", key="admin_email_input")
                    admin_password = st.text_input("Admin 密碼", type="password", key="admin_password_input")
                    
                    if st.form_submit_button("執行登入"):
                        if admin_email and admin_password:
                            try:
                                user = supabase.auth.sign_in_with_password({"email": admin_email, "password": admin_password})
                                st.session_state.user = user.user
                                fetch_user_profile(supabase, user.user.id)
                                st.rerun()
                            except Exception as e:
                                st.error("登入失敗，請檢查 Email/密碼。")
                        else:
                            st.error("請輸入憑證。")
                        
            # 忘記密碼按鈕
            st.markdown("---")
            if st.button("忘記密碼？", key="forget_password_button"):
                 st.info("請聯繫系統管理員協助重設密碼。") 
    # --- 已登入邏輯 ---
    else:
        # 已登入：顯示稱謂
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
            st.session_state.user = None
            st.session_state.role = "guest"
            st.session_state.username = None
            st.rerun()
            
        # 個人設定和 Admin 提示 
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 個人設定")
        current_username = st.session_state.username or ""
        st.sidebar.text_input(
            "公開暱稱 (發文用)", 
            value=current_username,
            key="page_new_username_input",
            on_change=lambda: auto_update_username(supabase, st.session_state.page_new_username_input)
        )
        
        if st.session_state.role == 'system_admin':
            st.sidebar.markdown("---")
            st.sidebar.warning("🔑 系統管理員：請至 [Admin Dashboard] 頁面管理使用者權限與個資。")



