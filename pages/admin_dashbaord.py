import streamlit as st
import pandas as pd
from supabase import Client, create_client
import os 
from postgrest.exceptions import APIError 
import uuid 

st.set_page_config(page_title="管理員後台")

# --- 初始化與權限檢查 ---

# supabase client 
if "supabase" not in st.session_state or st.session_state.supabase is None:
    st.warning("請先在主頁登入並確保 Supabase 連線成功。")
    st.stop()

# 只有系統管理員可以存取此頁面
if st.session_state.role != 'system_admin':
    st.error("❌ 權限不足：您不是系統管理員。")
    st.stop()

supabase: Client = st.session_state.supabase


# --- Admin Client ---
if 'supabase' in st.secrets and 'service_role_key' in st.secrets.supabase:
    try:
        supabase_admin: Client = create_client(
            st.secrets.supabase.url,
            st.secrets.supabase.service_role_key 
        )
    except Exception as e:
        st.error(f"無法初始化管理員 Client (Admin Key 連線錯誤)：{e}")
        supabase_admin = None
else:
    st.warning("Admin Key 遺失或 secrets 格式錯誤：無法執行帳號創建功能。")
    supabase_admin = None 

st.title("🔒 系統管理員後台：敏感個資與權限管理")
st.warning("此頁面包含使用者真實 Email 和姓名等敏感資訊，請謹慎操作。")
st.markdown("---")


# --- 資料讀取與快取 ---
@st.cache_data(ttl=5) 
def fetch_all_profiles():
    try:
        response = supabase.table('profiles').select("*").execute() 
        df = pd.DataFrame(response.data)
        if not df.empty:
            df.set_index('id', inplace=True)
            df['Select'] = False 
            if 'role' not in df.columns:
                 df['role'] = 'user'
        return df
    except Exception as e:
        st.error(f"資料庫讀取失敗：{e}")
        return pd.DataFrame()

df_profiles = fetch_all_profiles()

# --- 2. 批次權限調整功能 ---

st.header("⚙️ 批次角色權限調整")
st.caption("您可以直接在表格中修改角色，或勾選多筆使用者後統一變更角色。")

if not df_profiles.empty:
        
    df_edited = st.data_editor(
        df_profiles,
        key="profile_editor", 
        column_order=['Select', 'email', 'role', 'username', 'id'],
        column_config={
            'Select': st.column_config.CheckboxColumn(required=True),
            'id': st.column_config.TextColumn("UID", disabled=True),
            'email': st.column_config.TextColumn("Email (敏感個資)", disabled=True),
            'username': st.column_config.TextColumn("暱稱", disabled=False), 
            'role': st.column_config.SelectboxColumn(
                "角色",
                options=['system_admin', 'moderator', 'user'],
                required=True
            )
        },
        height=300,
        use_container_width=True
    )

    modifications = st.session_state.get("profile_editor", {}).get("edited_rows", {})
    
    # 批次變更選單
    selected_uids = df_edited[df_edited['Select']].index.tolist()
    
    st.subheader("批次操作 (針對已勾選使用者)")
    col1, col2 = st.columns(2)
    
    with col1:
        batch_role = st.selectbox(
            "選擇要變更的新角色",
            options=['moderator', 'user'],
            key="batch_role_select"
        )
    
    def apply_batch_update():
        if not selected_uids:
            st.error("請先勾選要變更角色的使用者。")
            return
            
        updates = []
        for uid in selected_uids:
            updates.append({
                "id": str(uid),
                "role": batch_role
            })
            
        try:
            supabase.table('profiles').upsert(updates).execute()
            st.toast(f"成功將 {len(selected_uids)} 位使用者角色更新為 {batch_role}！")
            st.cache_data.clear()
            st.experimental_rerun()
        except Exception as e:
            st.error(f"批次更新失敗: {e}")


    if col2.button(f"確認批次變更 ({len(selected_uids)} 位使用者)"):
        apply_batch_update()
        
    st.markdown("---")


    # 提交單行變更
    if modifications:
        st.subheader("單行角色變更確認")
        
        updates = []
        for index_int, values in modifications.items():
            uid = df_edited.iloc[index_int].name 
            if 'role' in values:
                updates.append({
                    "id": str(uid),
                    "role": values['role']
                })
        
        if st.button(f"儲存單行角色變更 ({len(updates)} 筆)"):
            try:
                supabase.table('profiles').upsert(updates).execute()
                st.toast(f"成功更新 {len(updates)} 筆單行變更！")
                st.cache_data.clear()
                st.experimental_rerun()
            except Exception as e:
                st.error(f"儲存失敗: {e}")

else:
    st.info("目前沒有使用者資料可供管理。")
    

# --- 3. 手動匯入創建帳號功能 (保持不變) ---

st.header("📧 手動匯入新增帳號 (管理員 API)")
st.caption("這將建立帳號並發送「設定密碼」郵件給使用者。")

if supabase_admin:
    with st.form("manual_create_user"):
        new_email = st.text_input("要新增帳號的 Email 地址 (必填)")
        initial_role = st.selectbox(
            "初始角色設定",
            options=['moderator', 'user'],
            index=0,
            key="initial_role_select"
        )
        submitted = st.form_submit_button("建立帳號並發送密碼設定郵件")

        if submitted:
            if new_email:
                try:
                    response = supabase_admin.auth.admin.invite_user_by_email(
                        email=new_email
                    )
                    
                    new_user_id = response.user.id
                    
                    supabase_admin.table('profiles').update({"role": initial_role}).eq("id", new_user_id).execute()

                    st.success(f"帳號新增成功！已發送密碼設定郵件到 {new_email}。")
                    st.info(f"使用者 ID: {new_user_id}，初始角色已設定為 '{initial_role}'。")
                    
                    st.cache_data.clear()
                    st.experimental_rerun()

                except Exception as e:
                    if "User already exists" in str(e):
                        st.error(f"建立失敗：Email {new_email} 已經存在。")
                    else:
                        st.error(f"新增失敗: {e}")
            else:
                st.error("Email 地址不可為空。")
else:
    st.error("❌ Admin Client 未初始化：無法執行建立帳號功能。")
