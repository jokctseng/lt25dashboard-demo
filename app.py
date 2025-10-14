import streamlit as st
from supabase import create_client, Client
import pandas as pd
import os 

# --- 0. 配置與初始化 ---
st.set_page_config(
    page_title="全國青年會議協作平台",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("全國青年會議協作與意見彙整平台") 

# ---  Session State  ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "guest"
if "username" not in st.session_state:
    st.session_state.username = None
if "supabase" not in st.session_state:
    st.session_state.supabase = None 
if "supabase_admin" not in st.session_state:
    st.session_state.supabase_admin = None


# --- Supabase 連線邏輯 ---
@st.cache_resource
def init_connection(is_admin=False) -> Client:
    """初始化 Supabase 連線 (可選擇 Admin 或 Anon)"""
    config_section = st.secrets["supabase"]
    url = config_section["url"]
    
    if is_admin:
        if 'service_role_key' in config_section:
            return create_client(url, config_section["service_role_key"])
        else:
            st.warning("Admin Key 遺失，無法執行高權限操作。")
            return None
    else:
        return create_client(url, config_section["anon_key"])

# 連線初始
if st.session_state.supabase is None:
    try:
        st.session_state.supabase = init_connection(is_admin=False)
        st.session_state.supabase_admin = init_connection(is_admin=True) # 初始化 Admin Client
    except Exception as e:
        st.error(f"連線初始化失敗：請檢查 secrets.toml 配置。")

is_connected = st.session_state.supabase is not None
supabase = st.session_state.supabase


# --- 認證與權限檢查 ---
def fetch_user_profile(user_id):
    """從 profiles 表格獲取使用者角色與暱稱"""
    try:
        if st.session_state.supabase:
            response = st.session_state.supabase.table('profiles').select("role, username").eq('id', user_id).single().execute()
            st.session_state.role = response.data['role']
            st.session_state.username = response.data['username']
    except Exception:
        st.session_state.role = "user"
        st.session_state.username = None

def authenticate_user():
    """處理使用者登入/登出和角色檢查 """
    
    if not is_connected:
        st.sidebar.error("連線錯誤，無法登入/註冊。")
        return
        
    elif st.session_state.user is None:
        st.sidebar.subheader("使用者登入/註冊")
        
        with st.sidebar.form("auth_form"):
            auth_type = st.radio("選擇操作", ["登入", "註冊"])
            email = st.text_input("Email")
            password = st.text_input("密碼", type="password")
            submitted = st.form_submit_button("執行")

            if submitted:
                try:
                    if auth_type == "註冊":
                        user = st.session_state.supabase.auth.sign_up({"email": email, "password": password})
                        st.success("註冊成功！請檢查 Email 以驗證帳號。")
                    else:
                        user = st.session_state.supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = user.user
                        fetch_user_profile(user.user.id)
                        st.rerun() # 
                except Exception as e:
                    st.error(f"認證失敗: {e}")
        
    else:
        # 已登入 
        user_role = st.session_state.role
        user_email = st.session_state.user.email
        display_name = st.session_state.username
        
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
        
        if st.sidebar.button("登出"):
            st.session_state.supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.role = "guest"
            st.session_state.username = None
            st.rerun()
        

# --- 自動儲存 ---
def auto_update_username(new_username):

    try:
        if st.session_state.user and st.session_state.supabase:
            st.session_state.supabase.table('profiles').update({"username": new_username}).eq('id', st.session_state.user.id).execute()
            st.session_state.username = new_username
            st.toast("暱稱已自動儲存！")
    except Exception as e:
        st.error(f"儲存失敗: {e}")

# --- 儀表板主邏輯 ---
def main():
    
    st.markdown("""<style>header {visibility: hidden;}</style>""", unsafe_allow_html=True)
    
    # 置頂公告區塊 (這裡保持不變)
    st.warning("""
    🚨 **重要聲明：** 本平台由全國青年會議青年工作小組設置與維護，輸入意見及投票需註冊並以電郵驗證，但使用本平台非必須項。本平台所有紅隊演練的投票及共創新聞牆回饋均為**公開資訊**。
    為保障個資，強烈建議您不要在留言內容中透露任何個人資訊。
    """)
    
    # 頁面內容和卡片 (只在未登入時顯示)
    if st.session_state.user is None:
        page_summary = [
            {"title": "大會資料", "icon": "📄", "desc": "查看活動議程、規則與行為準則，掌握活動基本資訊。"},
            {"title": "補充資訊", "icon": "🔗", "desc": "查閱核心政策、數據圖表與統計分析，快速了解背景知識。"},
            {"title": "紅隊儀表板", "icon": "🛡️", "desc": "即時查看所有建議的投票與共識狀態，並進行篩選。"},
            {"title": "共創新聞牆", "icon": "📢", "desc": "發表主題貼文、意見，並對其他人的回饋表達 Reaction。"},
            {"title": "致謝與授權", "icon": "🤝", "desc": "查看專案開發團隊、貢獻者名單與程式碼授權說明。"},
        ]
        
        st.subheader("平台功能總覽")
        st.markdown("---")

        cols = st.columns(2)
        
        for i, item in enumerate(page_summary):
            col = cols[i % 2]
            
            card_html = f"""
            <div style="
                background-color: #383838; 
                padding: 15px; 
                border-radius: 12px; 
                margin-bottom: 15px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            ">
                <h3 style="color: #1DB954; margin-top: 0; margin-bottom: 5px;">{item['icon']} {item['title']}</h3>
                <p style="color: #DDDDDD; font-size: 14px;">{item['desc']}</p>
            </div>
            """
            col.markdown(card_html, unsafe_allow_html=True)
        
    # 個人設定與 Admin 提示 
    if st.session_state.user is not None:
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 個人設定")
        current_username = st.session_state.username or ""
        st.sidebar.text_input(
            "公開暱稱 (發文用)", 
            value=current_username,
            key="new_username_input",
            on_change=lambda: auto_update_username(st.session_state.new_username_input)
        )
        
        if st.session_state.role == 'system_admin':
            st.sidebar.markdown("---")
            st.sidebar.warning("🔑 系統管理員：請至 [Admin Dashboard] 頁面管理使用者權限與個資。")


if __name__ == "__main__":
    authenticate_user()
    main()
