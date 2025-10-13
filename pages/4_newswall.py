import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time
import uuid 


# 設置頁面標題
st.set_page_config(page_title="共創新聞牆")

# --- 分頁自我連線初始化 ---
@st.cache_resource(ttl=None) 
def init_connection_for_page() -> Client:
    """初始化 Supabase 連線並快取"""
    if "supabase" in st.secrets and "url" in st.secrets["supabase"]:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"] 
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


if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "guest"
if "username" not in st.session_state:
    st.session_state.username = None


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
    """從 Supabase 獲取所有貼文、作者暱稱及 Reactions (使用雙查詢穩定版)"""
    
    try:
        # 查詢 1 (主貼文)
        posts_res = supabase.table('posts').select(
            "id, content, created_at, user_id, topic, post_type"
        ).order("created_at", desc=True).execute()
        
        df_posts = pd.DataFrame(posts_res.data)
        
        # 查詢 2 (作者暱稱和角色)
        if not df_posts.empty:
            user_ids = df_posts['user_id'].unique().tolist()
            profiles_res = supabase.table('profiles').select("id, username, role").in_("id", user_ids).execute()
            df_profiles = pd.DataFrame(profiles_res.data).rename(columns={'id': 'user_id'})
            
            # 將 profiles 數據合併到 posts 數據中
            df_merged = pd.merge(df_posts, df_profiles, on='user_id', how='left')
            
        else:
            # 如果沒有貼文，建立空 DataFrame
            df_merged = df_posts
            
        reactions_res = supabase.table('reactions').select("post_id, reaction_type").execute()
        df_reactions = pd.DataFrame(reactions_res.data)
        
        if 'username' not in df_merged.columns:
            df_merged['username'] = None
        if 'role' not in df_merged.columns:
            df_merged['role'] = 'user'
            
        return df_merged, df_reactions
        
    except Exception as e:
        st.error(f"新聞牆數據載入失敗。請檢查您的 RLS 策略是否允許 SELECT 'posts' 和 'profiles' 表格。錯誤：{e}")
        return pd.DataFrame(), pd.DataFrame()


# --- 貼文提交邏輯---
def submit_post(topic, post_type, content):
    try:
        if st.session_state.user is None:
            st.error("請先登入才能發表貼文。")
            return
        
        user_id_str = str(st.session_state.user.id) 
        
        supabase.table('posts').insert({
            "user_id": user_id_str, 
            "topic": topic, 
            "post_type": post_type, 
            "content": content
        }).execute()
        
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
            
        user_id_str = str(st.session_state.user.id)
        
        supabase.table('reactions').upsert({
            "post_id": post_id, 
            "user_id": user_id_str, # UUID
            "reaction_type": reaction_type
        }, on_conflict="post_id, user_id").execute()
        
        st.toast(f"已表達 '{reaction_type}'！")
        st.cache_data.clear()
    except Exception as e:
        st.error(f"操作失敗: {e}")

# --- 管理員刪除貼文邏輯---
def delete_post(post_id):
    if is_admin_or_moderator:
        try:
            supabase.table('posts').delete().eq('id', post_id).execute()
            st.toast("貼文已刪除。")
            st.cache_data.clear()
            st.experimental_rerun()
        except Exception as e:
            st.error(f"刪除失敗: {e}")

# --- 介面渲染 ---

if not is_logged_in:
    st.warning("您目前是訪客模式。發言、投票和反應功能需要登入後才能使用。")

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

    #  topic 欄位
    if 'topic' in posts_df.columns:
        reaction_counts = reactions_df.groupby(['post_id', 'reaction_type']).size().reset_index(name='count')
        merged_df = pd.merge(reaction_counts, posts_df[['id', 'topic']], left_on='post_id', right_on='id')
        
        topic_summary = merged_df.groupby(['topic', 'reaction_type'])['count'].sum().reset_index()
        
        fig = px.bar(topic_summary, x='topic', y='count', color='reaction_type',
                     title="各主題意見反應分佈",
                     labels={'topic': '主題', 'count': '反應數量'},
                     color_discrete_map={'支持': 'green', '中立': 'gray', '反對': 'red'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("無法繪製圖表：貼文數據結構不完整。")
else:
    st.info("目前沒有任何貼文反應數據。")
    
st.markdown("---")
st.subheader("📰 所有貼文列表")

for index, row in posts_df.iterrows():
    col_content, col_react = st.columns([4, 1])
    
    # 1. 匿名化與角色名稱顯示邏輯 (使用雙查詢結果的 username 和 role 欄位)
    username = row.get('username')
    author_role = row.get('role', 'user')
    user_id = row['user_id']
    
    # 決定顯示名稱
    if author_role == 'system_admin':
        short_uid = user_id[:4]
        final_author_name = f"管理員 - {username or f'UID:{short_uid}...'}"
    elif author_role == 'moderator':
        short_uid = user_id[:4]
        final_author_name = f"版主 - {username or f'UID:{short_uid}...'}"
    elif username:
        final_author_name = f"{username}選手"
    else:
        final_author_name = "匿名演練選手"


    with col_content:
        st.markdown(f"**[{row['topic']}] ({row['post_type']}) - {final_author_name}**") 
        st.write(row['content'])
        
        # reactions_df 
        post_reactions = reactions_df[reactions_df['post_id'] == row['id']] if not reactions_df.empty else pd.DataFrame()
        reaction_summary = post_reactions.groupby('reaction_type').size().to_dict()
        
        summary_text = f"👍 {reaction_summary.get('支持', 0)} | 😐 {reaction_summary.get('中立', 0)} | 👎 {reaction_summary.get('反對', 0)}"
        st.caption(summary_text)

    # 2. React 按鈕 
    with col_react:
        if is_logged_in:
            react_col1, react_col2, react_col3 = st.columns(3)
            if react_col1.button("👍", key=f"sup_{row['id']}"):
                handle_reaction(row['id'], '支持')
            if react_col2.button("😐", key=f"neu_{row['id']}"):
                handle_reaction(row['id'], '中立')
            if react_col3.button("👎", key=f"opp_{row['id']}"):
                handle_reaction(row['id'], '反對')
        else:
            # 訪客模式：顯示總計數
            st.caption(f"反應: {summary_text}")
    
    # 3. 版主刪除按鈕
    if is_admin_or_moderator:
        st.write("---") 
        col_admin, _ = st.columns([1, 4])
        col_admin.write(f"作者 UID: `{row['user_id']}`")
        if col_admin.button("🗑️ 刪除留言", key=f"del_post_{row['id']}"):
            delete_post(row['id'])

    st.markdown("---")
