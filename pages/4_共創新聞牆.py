import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import time
import uuid 
import os 

# 設置頁面標題
st.set_page_config(page_title="共創新聞牆")

# --- 連線初始化與權限檢查 ---
supabase = st.session_state.get('supabase')

# 檢查連線狀態
if supabase is None:
    st.error("🚨 核心服務連線失敗。頁面已載入，但數據無法獲取。請檢查主頁連線。")
    
else:
    supabase: Client = supabase

supabase: Client = st.session_state.supabase 

# Admin Client
supabase_admin: Client = None 
if 'service_role_key' in st.secrets.supabase:
    if 'supabase_admin' not in st.session_state or st.session_state.supabase_admin is None:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["service_role_key"]
            st.session_state.supabase_admin = create_client(url, key)
        except Exception:
            st.session_state.supabase_admin = None 

    supabase_admin = st.session_state.supabase_admin


# --- Session 狀態處理 ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = "guest"
if "username" not in st.session_state:
    st.session_state.username = None
if "reaction_version" not in st.session_state:
    st.session_state.reaction_version = 0

# 確定使用者 ID 
current_user_id = str(st.session_state.user.id) if "user" in st.session_state and st.session_state.user else None
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
def fetch_posts_and_reactions(version):
    """從 Supabase 獲取所有貼文、作者暱稱及 Reaction"""
    empty_reactions_df = pd.DataFrame(columns=['post_id', 'reaction_type'])

    try:
        # 查詢 1 (主貼文)
        posts_res = supabase.table('posts').select(
            "id, content, created_at, user_id, topic, post_type"
        ).order("created_at", desc=True).execute()
        
        df_posts = pd.DataFrame(posts_res.data)
        
        # 查詢 2 (作者暱稱和角色)
        if not df_posts.empty:
            df_posts['id'] = df_posts['id'].astype(str)
            df_posts['user_id'] = df_posts['user_id'].astype(str)
            user_ids = df_posts['user_id'].unique().tolist()
            profiles_res = supabase.table('profiles').select("id, username, role").in_("id", user_ids).execute()
            df_profiles = pd.DataFrame(profiles_res.data).rename(columns={'id': 'user_id'})
            df_profiles['user_id'] = df_profiles['user_id'].astype(str)
            
            df_merged = pd.merge(df_posts, df_profiles, on='user_id', how='left')
            
        else:
            df_merged = df_posts
            
        reactions_res = supabase.table('reactions').select("post_id, reaction_type").execute()
        df_reactions = pd.DataFrame(reactions_res.data)
        
        if not df_reactions.empty:
            df_reactions['post_id'] = df_reactions['post_id'].astype(str)
        else:
            df_reactions = empty_reactions_df.copy()

        # 確保必要的欄位存在
        if 'username' not in df_merged.columns:
            df_merged['username'] = None
        if 'role' not in df_merged.columns:
            df_merged['role'] = 'user'
            
        return df_merged, df_reactions
        
    except Exception as e:
        # 讀取失敗時的處理
        st.error(f"新聞牆數據載入失敗，請檢查 RLS 策略。錯誤：{e}")
        empty_posts_df = pd.DataFrame(columns=['id', 'content', 'user_id', 'topic', 'post_type', 'username', 'role'])
        return empty_posts_df, empty_reactions_df.copy()

# --- 貼文提交邏輯---
def submit_post(topic, post_type, content):
    try:
        if not is_logged_in:
            st.error("請先登入才能發表貼文。")
            return
            
        insert_client = supabase_admin if supabase_admin else supabase 
        
        if insert_client is None:
             st.error("發布失敗: 缺少連線客戶端。")
             return

        insert_client.table('posts').insert({
            "user_id": current_user_id, 
            "topic": topic, 
            "post_type": post_type, 
            "content": content
        }).execute()
        
        st.toast("貼文已成功發布！")
        fetch_posts_and_reactions.clear()
        st.rerun() 
    except Exception as e:
        st.error(f"發布失敗: {e}")

# --- React 處理邏輯 ---
def handle_reaction(post_id, reaction_type):
    try:
        if not is_logged_in:
            st.error("請先登入才能進行反應。")
            return
            
        upsert_client = supabase_admin if supabase_admin else supabase 
        
        if upsert_client is None:
             st.error("操作失敗: 缺少連線客戶端。")
             return
            
        upsert_client.table('reactions').upsert({
            "post_id": post_id, 
            "user_id": current_user_id, 
            "reaction_type": reaction_type
        }, on_conflict="post_id, user_id").execute()
        
        st.toast(f"已表達 '{reaction_type}'！")
        st.session_state.reaction_version += 1
        fetch_posts_and_reactions.clear()
        st.rerun()
    except Exception as e:
        st.error(f"操作失敗: {e}")

# --- 管理員刪除貼文邏輯---
def delete_post(post_id):
    if is_admin_or_moderator:
        try:
            # 刪除操作應始終使用高權限客戶端
            delete_client = supabase_admin if supabase_admin else supabase
            
            if delete_client is None:
                 st.error("刪除失敗: 缺少連線客戶端。")
                 return
                 
            delete_client.table('posts').delete().eq('id', post_id).execute()
            st.toast("貼文已刪除。")
            fetch_posts_and_reactions.clear()
            st.rerun() 
        except Exception as e:
            st.error(f"刪除失敗: {e}")

# --- 介面渲染 ---

if not is_logged_in:
    st.warning("您目前是訪客模式。發言、投票和反應功能需要登入後才能使用。")

posts_df, reactions_df = fetch_posts_and_reactions(st.session_state.reaction_version)


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

# --- 計算支持比例 ---

if not posts_df.empty:
    
    # 每個貼文的 Reactions 數量
    reaction_counts = reactions_df.groupby(['post_id', 'reaction_type']).size().reset_index(name='count')

    # 樞紐化
    reaction_pivot = reaction_counts.pivot(index='post_id', columns='reaction_type', values='count').fillna(0).reset_index()
    reaction_pivot = reaction_pivot.rename(columns={'post_id': 'id'})
    
    # 合併 Reactions 數據到 Posts 中
    posts_df['id'] = posts_df['id'].astype(str)
    posts_df = pd.merge(posts_df, reaction_pivot, on='id', how='left').fillna(0)

    for col_name in ['支持', '中立', '反對']:
        if col_name not in posts_df.columns:
            posts_df[col_name] = 0
        else:
            post_df[col_name] = posts_df[col_name].astype(int)
    # 計算總數和支持比例
    posts_df['Total_Reactions'] = posts_df['支持'] + posts_df['中立'] + posts_df['反對']
    
    # 防止除以零
    posts_df['Support_Ratio'] = posts_df.apply(
        lambda row: row['支持'] / row['Total_Reactions'] if row['Total_Reactions'] > 0 else 0, axis=1
    )
    
    # 排序：支持比例 / 發布時間降序
    posts_df = posts_df.sort_values(
        ['Support_Ratio', 'created_at'], 
        ascending=[False, False]
    )
st.markdown("---")
# --- 新增篩選器 ---
st.subheader("主題篩選")
selected_topic = st.selectbox("選擇主題以篩選列表", options=['所有主題'] + TOPICS)
if selected_topic != '所有主題' and not posts_df.empty:
    posts_df = posts_df[posts_df['topic'] == selected_topic]
    
st.markdown("---")
st.subheader("📰 所有貼文列表")

for index, row in posts_df.iterrows():
    col_content, col_react = st.columns([4, 1])
    
    # 匿名化與角色名稱顯示邏輯
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
        
        support = int(row.get('支持', 0))
        neutral = int(row.get('中立', 0))
        oppose = int(row.get('反對', 0))
        
        summary_text = f"👍 {support} | 😐 {neutral} | 👎 {oppose}"
        st.caption(summary_text)

    #  React 按鈕 
    with col_react:
        if is_logged_in:
            react_col1, react_col2, react_col3 = st.columns([1, 1, 1])
            if react_col1.button("👍", key=f"sup_{row['id']}"):
                handle_reaction(row['id'], '支持')
            if react_col2.button("😐", key=f"neu_{row['id']}"):
                handle_reaction(row['id'], '中立')
            if react_col3.button("👎", key=f"opp_{row['id']}"):
                handle_reaction(row['id'], '反對')
        else:
            # 訪客模式：顯示總計數
            st.caption(f"反應: {summary_text}")
    
    #  版主刪除按鈕
    if is_admin_or_moderator:
        st.write("---") 
        col_admin, _ = st.columns([1, 4])
        col_admin.write(f"作者 UID: `{row['user_id']}`")
        if col_admin.button("🗑️ 刪除留言", key=f"del_post_{row['id']}"):
            delete_post(row['id'])

    st.markdown("---")
