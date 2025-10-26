import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import Client
import time
import datetime
import pytz
import os
from auth_utils import init_global_session_state, render_page_sidebar_ui

st.set_page_config(page_title="紅隊儀表板")

# --- 初始化 ---
init_global_session_state() 

supabase = st.session_state.get('supabase')
is_connected = supabase is not None

# 側欄渲染
render_page_sidebar_ui(supabase, is_connected)

# 連線錯誤提示
if not is_connected:
    st.error("🚨 核心服務連線失敗，請檢查配置。")
    st.stop()


# 獲取 Clients 和角色資訊 
supabase_admin: Client = st.session_state.get('supabase_admin')
current_user_id = str(st.session_state.user.id) if st.session_state.user else None
is_logged_in = current_user_id is not None
is_admin_or_moderator = st.session_state.role in ['system_admin', 'moderator']

# 版本控制
if "dashboard_version" not in st.session_state:
    st.session_state.dashboard_version = 0

@st.cache_data(ttl=1) 
def fetch_dashboard_data(version): 
    """獲取建議列表及其投票狀態（呼叫 Supabase RPC）"""
    
    supabase_client = st.session_state.get('supabase')
    if supabase_client is None:
        st.error("資料讀取失敗：Supabase 客戶端未初始化。")
        return pd.DataFrame()
        
    try:
        response = supabase_client.rpc('get_suggestion_status', {}).execute()
        df = pd.DataFrame(response.data)
        
        numeric_cols = ['unresolved_count', 'partial_count', 'resolved_count']
        if not df.empty:
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"資料讀取失敗，請檢查 Supabase 後端: {e}")
        return pd.DataFrame()
        
# --- Time Zone ---
TAIPEI_TZ = pytz.timezone('Asia/Taipei')
current_time_taipei = datetime.datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')

st.title("🛡️ 紅隊演練儀表板")
st.caption(f"數據更新頻率：每秒自動更新 (上次更新: {current_time_taipei})")
st.markdown("---")

# 定義類別與狀態
CATEGORIES = ['所有類別', '建議', '洞察', '其他']
VALID_CATEGORIES = ['建議', '洞察', '其他']
VOTE_STATUSES = ['所有狀態', '未解決', '部分解決', '已解決/有共識']

# --- CAPTCHA或登入狀態 ---

if not is_logged_in and not st.session_state.get('captcha_passed', False):
    st.subheader("🤖 驗證 (投票前必點)")
    st.info("請點選下方方塊，啟用投票功能。")
    
    if st.checkbox("我不是機器人 (點擊驗證)", key="captcha_vote_checkbox"):
         st.session_state.captcha_passed = True
         st.rerun()
         
    st.markdown("---")

# --- 篩選邏輯與介面 ---

col_cat, col_status = st.columns(2)

selected_category = col_cat.selectbox(
    "按類別篩選", 
    options=CATEGORIES,
    index=0
)

selected_vote_status = col_status.selectbox(
    "按投票狀態篩選", 
    options=VOTE_STATUSES,
    index=0
)

df = fetch_dashboard_data(st.session_state.dashboard_version) 

# 執行篩選
df_filtered = df.copy()

# 類別篩選
if selected_category != '所有類別':
    if 'cate' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['cate'] == selected_category]

# 狀態篩選
if selected_vote_status != '所有狀態':
    status_col_map = {
        '未解決': 'unresolved_count',
        '部分解決': 'partial_count',
        '已解決/有共識': 'resolved_count' 
    }
    col_name = status_col_map.get(selected_vote_status)
    if col_name and col_name in df_filtered.columns:
        df_filtered = df_filtered[df_filtered[col_name] > 0]


# --- 視覺化呈現 ---

if not df_filtered.empty:
    df_melt = df_filtered.melt(id_vars=['content', 'id', 'cate'], 
                               value_vars=['unresolved_count', 'partial_count', 'resolved_count'],
                               var_name='投票狀態', value_name='計數')
    
    df_melt['投票狀態'] = df_melt['投票狀態'].str.replace('_count', '')
    df_melt['投票狀態'] = df_melt['投票狀態'].replace({'resolved': '已解決/有共識', 'unresolved': '未解決', 'partial': '部分解決'})
    
    # 視覺化圖表配色
    fig = px.bar(df_melt, x='content', y='計數', color='投票狀態', 
                 title='紅隊演練問題投票狀況即時視覺化',
                 labels={'content': '建議/意見'},
                 height=450,
                 color_discrete_map={'未解決': 'red', '部分解決': 'orange', '已解決/有共識': 'green'}) 
    st.plotly_chart(fig, config={'displayModeBar': False})
else:
    st.info("根據您的篩選條件，目前沒有任何建議或投票數據。")


# --- 建議列表與投票區 ---

def handle_vote(suggestion_id, vote_type):
    """處理投票邏輯，將顯示名稱轉換為 Supabase 內部名稱"""
    
    current_user_id = str(st.session_state.user.id) if st.session_state.user else None
    is_logged_in = current_user_id is not None
    is_admin_or_moderator = st.session_state.role in ['system_admin', 'moderator']
    supabase_admin = st.session_state.get('supabase_admin')
    
    can_interact = is_logged_in or st.session_state.get('captcha_passed', False)
    
    if not can_interact:
        st.error("投票失敗：請先登入或完成驗證！")
        return
    
    supabase_vote_type = '已解決' if vote_type == '已解決/有共識' else vote_type
    
    # 寫入邏輯
    upsert_client = supabase_admin if is_admin_or_moderator and supabase_admin else st.session_state.supabase
    
    if upsert_client is None:
         st.error("投票失敗: 缺少連線客戶端。")
         return
    
    try:
        user_id_to_use = current_user_id if is_logged_in else None
        
        # 進行投票寫入
        upsert_client.table('votes').upsert({
            "suggestion_id": suggestion_id, 
            "user_id": user_id_to_use, 
            "vote_type": supabase_vote_type
        }, on_conflict="suggestion_id, user_id").execute()
        
        st.toast(f"投票成功: {vote_type}")
        fetch_dashboard_data.clear() 
        st.session_state.dashboard_version += 1 
        st.rerun() 
        
    except Exception as general_e:
        st.error(f"投票失敗: {general_e}")


def admin_delete_suggestion(suggestion_id):
    
    is_admin_or_moderator = st.session_state.role in ['system_admin', 'moderator']
    supabase_admin = st.session_state.get('supabase_admin')
    
    if not is_admin_or_moderator:
        st.error("權限不足，無法刪除。")
        return
    
    delete_client = supabase_admin if is_admin_or_moderator and supabase_admin else st.session_state.supabase
    
    if delete_client is None:
         st.error("刪除失敗: 缺少連線客戶端。")
         return
        
    try:
        delete_client.table('suggestions').delete().eq('id', suggestion_id).execute()
        st.toast("建議已刪除！")
        fetch_dashboard_data.clear()
        st.session_state.dashboard_version += 1
        st.rerun() 
    except Exception as e:
        st.error(f"刪除失敗: {e}")

st.subheader("🗳️ 建議列表與投票")
st.caption(f"目前顯示 {len(df_filtered)} 筆建議 (總計 {len(df)} 筆)")

if not df_filtered.empty:
    df_filtered['Total_Votes'] = df_filtered['unresolved_count'] + df_filtered['partial_count'] + df_filtered['resolved_count']
    suggestions = df_filtered.sort_values(['Total_Votes', 'created_at'], ascending=[False, False]).to_dict('records')
    
    for item in suggestions:
        
        # 投票按鈕顯現
        can_interact_ui = st.session_state.user or st.session_state.get('captcha_passed', False)
        
        if can_interact_ui:
            col_content, col_un, col_par, col_res, col_del = st.columns([1.5, 1, 1, 1, 0.5])
            
            # 顯示內容
            with col_content:
                st.markdown(f"**[{item['cate']}]**")
                st.write(f"**{item['content']}**")
            
            # 投票按鈕
            with col_un:
                if st.button(f"🔴 未解決 ({int(item['unresolved_count'])})", key=f"un_{item['id']}", help="點擊投票為此狀態"):
                    handle_vote(item['id'], '未解決')
            with col_par:
                if st.button(f"🟡 部分解決 ({int(item['partial_count'])})", key=f"par_{item['id']}", help="點擊投票為此狀態"):
                    handle_vote(item['id'], '部分解決')
            with col_res:
                if st.button(f"🟢 已解決/有共識 ({int(item['resolved_count'])})", key=f"res_{item['id']}", help="點擊投票為此狀態"):
                    handle_vote(item['id'], '已解決/有共識')
            
            # 管理員刪除按鈕
            if is_admin_or_moderator:
                with col_del:
                    if st.button("🗑️", key=f"del_{item['id']}"):
                        admin_delete_suggestion(item['id'])

        else:
            # 訪客模式：顯示計數
            col_content, col_un, col_par, col_res = st.columns([1.5, 1, 1, 1])
            
            with col_content:
                st.markdown(f"**[{item['cate']}]**")
                st.write(f"**{item['content']}**")

            col_un.markdown(f"🔴 **未解決:** {int(item['unresolved_count'])}")
            col_par.markdown(f"🟡 **部分解決:** {int(item['partial_count'])}")
            col_res.markdown(f"🟢 **已解決/有共識:** {int(item['resolved_count'])}")
            
            st.info("請登入後才能投票。")

# --- 管理員/版主新增建議介面 (單筆 & 批次) ---

# 管理員功能：**只有管理員/版主才顯示**
if is_admin_or_moderator:
    st.subheader("🔑 管理員/版主操作：新增建議")
    
    tab1, tab2 = st.tabs(["單筆新增", "CSV 批次匯入"])

    with tab1:
        with st.form("add_suggestion_form", clear_on_submit=True):
            new_cate = st.selectbox(
                "建議類別 (必選)", 
                options=VALID_CATEGORIES,
                key="new_cate_select"
            )
            new_content = st.text_area("新的建議/意見內容")
            
            if st.form_submit_button("新增單筆建議"):
                if new_content and new_cate:
                    try:
                        supabase.table('suggestions').insert({
                            "content": new_content, 
                            "cate": new_cate,
                        }).execute()
                        st.toast("單筆建議新增成功！")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"新增失敗: {e}")
                else:
                    st.warning("類別和內容不可為空。")

    with tab2:
        st.info("上傳的 CSV 檔案必須包含兩欄：`content` (建議內容) 和 `cate` (類別，必須為 '建議', '洞察', 或 '其他')。")
        
        uploaded_file = st.file_uploader("選擇 CSV 檔案", type=["csv"])
        
        if st.button("確認批次匯入"):
            if uploaded_file is not None:
                try:
                    df_upload = pd.read_csv(uploaded_file)
                    required_cols = ['content', 'cate']
                    
                    if not all(col in df_upload.columns for col in required_cols):
                        st.error(f"CSV 欄位錯誤：檔案必須包含 {required_cols} 兩欄。")
                        st.stop()
                    
                    df_upload = df_upload[required_cols].dropna() 
                    
                    invalid_categories = df_upload[~df_upload['cate'].isin(VALID_CATEGORIES)]
                    if not invalid_categories.empty:
                        st.error("類別驗證失敗：`cate` 欄位值必須是 '建議', '洞察', 或 '其他'。")
                        st.dataframe(invalid_categories, width=True)
                        st.stop()

                    data_to_insert = df_upload.to_dict('records')
                    
                    if not data_to_insert:
                        st.warning("CSV 檔案中沒有找到有效數據可供插入。")
                        st.stop()
                        
                    supabase.table('suggestions').insert(data_to_insert).execute()
                    
                    st.success(f"成功匯入 {len(data_to_insert)} 筆建議/洞察！")
                    st.cache_data.clear()
                    st.rerun()

                except Exception as e:
                    st.error(f"批次匯入失敗: {e}")
            else:
                st.warning("請先上傳一個 CSV 檔案。")
