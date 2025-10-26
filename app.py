import streamlit as st
from supabase import create_client, Client
import pandas as pd
import os 
import time
from auth_utils import init_global_session_state, render_page_sidebar_ui, fetch_user_profile


# ---設置與初始化 ---
st.set_page_config(
    page_title="全國青年會議協作平台",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    /* 隱藏元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 圓角卡片風格 */
    .stButton>button {
        border-radius: 12px;
        transition: background-color 0.3s;
    }
    
    /* 輸入框、選單及數據框 */
    .stSelectbox, .stTextInput, .stTextArea, .stExpander, [data-testid="stDataFrame"], .stTabs {
        border-radius: 12px;
        background-color: #282828; 
        padding: 10px;
    }

    /* 內容區域邊距 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* 側邊欄 */
    [data-testid="stSidebar"] {
        background-color: #191414; 
        border-right: 3px solid #1DB954; 
    }

    /* 標題層次 */
    h1, h2, h3, h4 {
        color: #FFFFFF !important; 
        font-weight: 600;
    }
    
    /* Footer  */
    .dark-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #191414; 
        color: #AAAAAA; 
        text-align: center;
        padding: 8px 0;
        font-size: 0.75rem;
        z-index: 10;
        border-top: 1px solid #282828;
    }
    .credit-link {
        color: #1DB954; 
        text-decoration: none;
        margin: 0 5px;
        font-weight: bold;
    }
    .credit-text {
        color: #AAAAAA;
        margin: 0 10px;
    }

    </style>
    <meta name="robots" content="noindex, nofollow">
    
    <div class="dark-footer">
        版權所有 © 2025 青年代號：GenAI 協作平台｜<span class="credit-text">技術支援：</span> 
        <a href="https://jokctseng.github.io" class="credit-link">小工</a> 
        <span class="credit-text">｜完整致謝：請查看致謝與授權頁面</span> 
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")
st.title("全國青年會議協作與意見彙整平台")

init_global_session_state()
def init_connection(is_admin=False) -> Client | None:
    """初始化 Supabase 連線"""
    
    if "supabase" not in st.secrets or "url" not in st.secrets["supabase"]:
        return None
        
    try:
        config_section = st.secrets["supabase"]
        url = config_section["url"]
        
        if is_admin:
            key = config_section.get("service_role_key")
        else:
            key = config_section.get("key")

        if key:
            return create_client(url, key)
        else:
            return None
    except Exception:
        return None

if st.session_state.supabase is None:
    st.session_state.supabase = init_connection(is_admin=False)
if st.session_state.supabase_admin is None:
    st.session_state.supabase_admin = init_connection(is_admin=True)

# 獲取 Clients 和連線狀態 
is_connected = st.session_state.supabase is not None
supabase = st.session_state.supabase


# --- RLS狀態恢復機制 ---
if is_connected and st.session_state.user is None:
    try:
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state.user = session.user
            fetch_user_profile(supabase, session.user.id) 
            st.rerun() 
    except Exception:
        pass

# --- 置頂公告區塊 ---
st.warning("""
🚨 **重要聲明：** 本平台由全國青年會議青年工作小組設置與維護，輸入意見及投票需註冊並以電郵驗證，但使用本平台非必須項。本平台所有紅隊演練的投票及共創新聞牆回饋均為**公開資訊**。
為保障個資，強烈建議您不要在留言內容中透露任何個人資訊。
""")


# --- 儀表板主邏輯 ---
def main():
    render_page_sidebar_ui(supabase, is_connected)
    if st.session_state.user is None:
        st.subheader("平台功能總覽")
        page_summary = [
            {"title": "大會資料", "icon": "📄", "desc": "查看活動議程、規則與行為準則，掌握活動基本資訊。"},
            {"title": "補充資訊", "icon": "🔗", "desc": "查閱核心政策、數據圖表與統計分析，快速了解背景知識。"},
            {"title": "紅隊儀表板", "icon": "🛡️", "desc": "即時查看所有建議的投票與共識狀態，並進行篩選。"},
            {"title": "共創新聞牆", "icon": "📢", "desc": "發表主題貼文、意見，並對其他人的回饋表達 Reaction。"},
            {"title": "致謝與授權", "icon": "🤝", "desc": "查看專案開發團隊、貢獻者名單與程式碼授權說明。"},
        ]
        
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
        

if __name__ == "__main__":
    main()
