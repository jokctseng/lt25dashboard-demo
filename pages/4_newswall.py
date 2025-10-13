import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time

# 設置頁面標題
st.set_page_config(page_title="共創新聞牆")

# --- 分頁自我連線初始化 ---
@st.cache_resource(ttl=None) 
def init_connection_for_page() -> Client:
    """初始化 Supabase 連線並快取"""
    if "supabase" in st.secrets and "url" in st.secrets["supabase"]:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["anon_key"] 
            return create_client(url, key)
        except Exception:
            return None
    return None 

# 檢查 Session State 或初始化
if "supabase" not in st.session_state or st.session_state.supabase is None:
    st.session_state.supabase = init_connection_for_page()

# 如果連線仍為 None，顯示錯誤並中斷
if st.session_state.supabase is None:
    st.error("🚨 無法建立 Supabase 連線。請檢查 secrets 配置或重新載入主頁。")
    st.stop()
    
# 連線成功
supabase: Client = st.session_state.supabase


# 確定使用者 ID 
current_user_id = st.session_state.user.id if "user" in st.session_state and st.session_state.user else None
is_logged_in = current_user_id is not None
is_admin_or_moderator = st.session_state.role in ['system_admin', 'moderator'] if "role" in st.session_state else False


st.title("📢 共創新聞牆")
st.markdown("---")

TOPICS = [
    "教育與素養培育", "勞動與產業轉型", "文化與地方發展", 
    "資訊與社會防護", "數位平權與共融治理", "其他"
]
REACTION_TYPES = ["支持", "中立", "反對"]

# --- 資料讀取與處理 ---
@st.cache_data(ttl=1)
def fetch_posts_and_reactions():
    """從 Supabase 獲取所有貼文、作者暱稱及 Reactions (新增降級邏輯)"""
    
    # 修正點 1: 使用 try/except 包裝成功邏輯
    try:
        # 嘗試進行完整查詢
        posts_res = supabase.table('posts').select(
            "id, content, created_at, user_id, topic, post_type, profiles(username, role)" # 確保抓取 role
        ).order("created_at", desc=True).execute()
        
        reactions_res = supabase.table('reactions').select("post_id, reaction_type").execute()
        
        # 如果成功，返回完整數據
        return pd.DataFrame(posts_res.data), pd.DataFrame(reactions_res.data)
        
    except Exception as e:
        # 修正點 2: 捕獲 APIError，並執行降級策略
        st.error(f"新聞牆載入失敗，已嘗試降級讀取。原因：{e}")
        try:
             # 降級：只選擇 posts 的欄位，不進行 JOIN
             posts_res_fallback = supabase.table('posts').select(
                 "id, content, created_at, user_id, topic, post_type"
             ).order("created_at", desc=True).execute()
             
             # 為 posts_df 創建一個空的 profiles 欄位以避免後續程式碼崩潰
             df_posts_fallback = pd.DataFrame(posts_res_fallback.data)
             df_posts_fallback['profiles'] = [{}] * len(df_posts_fallback)
             
             # 返回退化數據和空的 reactions
             return df_posts_fallback, pd.DataFrame()
        except Exception as fallback_e:
             st.error(f"退化載入失敗：{fallback_e}")
             return pd.DataFrame(), pd.DataFrame()

# --- 貼文提交邏輯---
def submit_post(topic, post_type, content):
    try:
        if st.session_state.user is None:
            st.error("請先登入才能發表貼文。")
            return
        
        supabase.table('posts').insert({"user_id": st.session_state.user.id, "topic": topic, "post_type": post_type, "content": content}).execute()
        st.toast("貼文已成功發布！")
        st.cache_data.clear()
        st.experimental_rerun()
    except Exception as e:
        st.error(f"發布失敗: {e}")

# --- React 處理邏輯  ---
def handle_reaction(post_id, reaction_type):
    try:
        if st.session_state.user is None:
            st.error("請先登入才能進行反應。")
            return
            
        supabase.table('reactions').upsert({"post_id": post_id, "user_id": st.session_state.user.id, "reaction_type": reaction_type}, on_conflict="post_id, user_id").execute()
        st.toast(f"已表達 '{reaction_type}'！")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"操作失敗: {e}")

# --- 管理員刪除貼文邏輯---
def delete_post(post_id):
    if st.session_state.role in ['system_admin', 'moderator']:
        try:
            supabase.table('posts').delete().eq('id', post_id).execute()
            st.toast("貼文已刪除。")
            st.cache_data.clear()
            st.experimental_rerun()
        except Exception as e:
            st.error(f"刪除失敗: {e}")

# --- 介面渲染 ---

posts_df, reactions_df = fetch_posts_and_reactions()

if is_logged_in:
    st.subheader("📝 發表您的回饋、意見或想法")
    with st.form("new_post_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        topic = col1.selectbox("選擇主題", options=TOPICS)
        post_type = col2.selectbox("選擇意見類型", options=['回饋', '小組共創', '其他'])
        content = st.text_area("內容")
        
        if st.form_submit_button("發布貼文"):
            if content:
                submit_post(topic, post_type, content)
            else:
                st.warning("請填寫內容！")

st.markdown("---")
# --- 新增篩選器 ---
st.subheader("主題篩選")
selected_topic = st.selectbox("選擇主題以篩選列表", options=['所有主題'] + TOPICS)
if selected_topic != '所有主題' and not posts_df.empty:
    posts_df = posts_df[posts_df['topic'] == selected_topic]

st.subheader("📈 主題意見群聚圖（即時）")

if not reactions_df.empty and not posts_df.empty:
    posts_df['id'] = posts_df['id'].astype(str)
    reactions_df['post_id'] = reactions_df['post_id'].astype(str)

    reaction_counts = reactions_df.groupby(['post_id', 'reaction_type']).size().reset_index(name='count')
    merged_df = pd.merge(reaction_counts, posts_df[['id', 'topic']], left_on='post_id',
