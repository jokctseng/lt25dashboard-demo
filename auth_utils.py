import streamlit as st
from supabase import Client



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


def render_sidebar_auth(supabase: Client | None, is_connected: bool):
    
    if not is_connected or supabase is None:
        st.sidebar.error("連線錯誤，無法登入/註冊。")
        return
        
# --- 登入/註冊邏輯 ---
    if st.session_state.user is None:
        st.sidebar.subheader("使用者登入/註冊")
        
        auth_mode = st.sidebar.radio(
            "選擇登入方式", 
            ["魔法連結", "帳號密碼"], 
            key="auth_mode_select"
        )
        
        with st.sidebar.form("auth_form_page"):
            
            if auth_mode == "魔法連結":
                st.info("輸入 Email，系統將發送無密碼登入連結至您的信箱。")
                email = st.text_input("Email", key="page_email_link")
                submitted = st.form_submit_button("發送登入連結")

                if submitted:
                    if not email:
                        st.sidebar.warning("請輸入 Email 地址。")
                        return
                    
                    try:
                        # sign_in_with_otp
                        supabase.auth.sign_in_with_otp(
                            email,
                            {
                                "email_redirect_to": "https://lt25dashboard.streamlit.app/", 
                                "create_user": True 
                            }
                        )
                        st.sidebar.success(f"連結已發送！請檢查 {email} 點擊信件中的連結完成登入。")
                        
                    except Exception as e:
                        st.sidebar.error(f"發送失敗: {e}")

            else: # auth_mode == "id/pw"
                auth_type = st.radio("選擇操作", ["登入", "註冊"], key="page_auth_type")
                email = st.text_input("Email", key="page_email_pwd")
                password = st.text_input("密碼", type="password", key="page_password_input")
                submitted = st.form_submit_button(auth_type) # 切換按鈕

                if submitted:
                    if not email or not password:
                        st.sidebar.warning("請輸入 Email 和密碼。")
                        return
                        
                    try:
                        if auth_type == "註冊":
                            # sign_up
                            user = supabase.auth.sign_up({"email": email, "password": password})
                            st.success("註冊成功！請檢查 Email 以驗證帳號。")
                        else:
                            #  sign_in_with_password
                            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state.user = user.user
                            fetch_user_profile(supabase, user.user.id)
                            st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"認證失敗: {e}")


        # --- 忘記密碼 ---
        st.sidebar.markdown("---") 
        if st.sidebar.button("忘記密碼？"):
            st.session_state.show_reset_form = True 

        if st.session_state.get("show_reset_form", False):
            with st.sidebar.form("reset_password_form"):
                st.subheader("重設密碼")
                reset_email = st.text_input("請輸入您的 Email 以接收重設連結", key="reset_email_input")
                reset_submitted = st.form_submit_button("發送重設密碼郵件")

                if reset_submitted:
                    if reset_email:
                        try:
                            # reset_password_for_email
                            supabase.auth.reset_password_for_email(
                                email=reset_email,
                                options={
                                    "redirect_to": "https://lt25dashboard.streamlit.app/" 
                                }
                            )
                            st.sidebar.success(f"已發送密碼重設連結至 {reset_email}，請檢查您的信箱。")
                            st.session_state.show_reset_form = False 
                        except Exception as e:
                            st.sidebar.error(f"發送失敗: {e}")
                    else:
                        st.sidebar.warning("請輸入 Email 地址。")
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


def auto_update_username(supabase: Client, new_username):
    """無按鈕自動儲存暱稱"""
    try:
        if st.session_state.user:
            supabase.table('profiles').update({"username": new_username}).eq('id', st.session_state.user.id).execute()
            st.session_state.username = new_username
            st.toast("暱稱已自動儲存！")
    except Exception as e:
        st.error(f"儲存失敗: {e}")
