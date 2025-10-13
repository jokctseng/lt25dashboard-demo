import streamlit as st
import pandas as pd
from supabase import Client, create_client
import uuid 
import os # 用於環境變數或 secrets 檢查
st.set_page_config(page_title="管理員後台")

# --- 初始化與權限檢查 ---

if "supabase" not in st.session_state:
    st.warning("請先在主頁登入。")
    st.stop()

# 權限檢查：只有系統管理員可以存取此頁面
if st.session_state.role != 'system_admin':
    st.error("❌ 權限不足：您不是系統管理員。")
    st.stop()

# 獲取已存在的匿名 Client (用於低權限操作)
supabase: Client = st.session_state.supabase

# --- 創建高權限 Admin Client ---

# 修正點 G: 確保讀取 st.secrets 時，使用小寫鍵名 (url, service_role_key)
if 'supabase' in st.secrets and 'service_role_key' in st.secrets.supabase:
    try:
        # 使用 Service Role Key 創建一個高權限 Client
        supabase_admin: Client = create_client(
            # 使用小寫鍵名
            st.secrets.supabase.url,
            st.secrets.supabase.service_role_key 
        )
    except Exception as e:
        st.error(f"管理員金鑰連線錯誤：{e}")
        supabase_admin = None
else:
    st.warning("金鑰遺失或格式錯誤：無法執行帳號創建功能。請在系統管理員 Streamlit 檢查設定。")
    supabase_admin = None # 設為 None 以在後面跳過該功能

st.title("🔒 系統管理員後台：敏感個資與權限管理")
st.warning("此頁面包含使用者真實 Email 和姓名等敏感資訊，請謹慎操作。")
st.markdown("---")


# --- 資料讀取與快取 ---
@st.cache_data(ttl=5) 
def fetch_all_profiles():
    # 使用當前登入的 Client 即可，因為 RLS 政策允許 system_admin 查看所有資料
    try:
        response = supabase.table('profiles').select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df.set_index('id', inplace=True)
            df['Select'] = False 
            # 確保 role 欄位在 data_editor 中顯示正確
            if 'role' not in df.columns:
                 df['role'] = 'user' # 預設值，如果資料庫中 role 欄位遺失
        return df
    except Exception as e:
        st.error(f"資料庫讀取失敗：{e}")
        return pd.DataFrame()

df_profiles = fetch_all_profiles()

# --- 批次權限調整功能 ---

st.header("⚙️ 批次角色權限調整")
st.caption("您可以直接在表格中修改角色，或勾選多筆使用者後統一變更角色。")

if not df_profiles.empty:
    
    # 使用 data_editor
    df_edited = st.data_editor(
        df_profiles,
        # ... column_order 和 column_config 保持不變 ...
        column_order=['Select', 'email', 'role', 'username', 'real_name', 'id'],
        column_config={
            'Select': st.column_config.CheckboxColumn(required=True),
            'id': st.column_config.TextColumn("UID", disabled=True),
            'email': st.column_config.TextColumn("Email (敏感個資)", disabled=True),
            'username': st.column_config.TextColumn("暱稱", disabled=True),
            'role': st.column_config.SelectboxColumn(
                "角色",
                options=['system_admin', 'moderator', 'user'],
                required=True
            )
        },
        height=300,
        use_container_width=True
    )

    # 獲取變更 (Modified rows)
    modifications = st.session_state["data_editor"]["edited_rows"]
    
    # 批次變更選單 (針對勾選)
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
            # 執行批次更新 (使用當前登入的 Client)
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
        for index, values in modifications.items():
            uid = df_edited.index[index]
            if 'role' in values:
                updates.append({
                    "id": str(uid),
                    "role": values['role']
                })
        
        if st.button(f"儲存單行角色變更 ({len(updates)} 筆)"):
            try:
                # 執行單行更新 (使用當前登入的 Client)
                supabase.table('profiles').upsert(updates).execute()
                st.toast(f"成功更新 {len(updates)} 筆單行變更！")
                st.cache_data.clear()
                st.experimental_rerun()
            except Exception as e:
                st.error(f"儲存失敗: {e}")

else:
    st.info("目前沒有使用者資料可供管理。")
    

# --- 手動匯入 ---

st.header("📧 手動匯入創建帳號")
st.caption("這將創建帳號並發送「設定密碼」郵件給使用者。")

if supabase_admin:
    with st.form("manual_create_user"):
        new_email = st.text_input("要創建帳號的 Email 地址 (必填)")
        initial_role = st.selectbox(
            "初始角色設定",
            options=['moderator', 'user'],
            index=0 
        )
        submitted = st.form_submit_button("創建帳號並發送密碼設定郵件")

        if submitted:
            if new_email:
                try:
                    # **使用 Admin Client 執行高權限操作：邀請用戶**
                    # Supabase Admin SDK 會自動處理發送郵件和創建 auth.users 記錄
                    response = supabase_admin.auth.admin.invite_user_by_email(
                        email=new_email
                    )
                    
                    new_user_id = response.user.id
                    
                    # 1. 確保 profiles 記錄被創建 
                    # 2. 手動更新 profiles 記錄中的角色，以確保角色是正確的
                    # 使用 Admin Client 進行更新，以繞過 profiles 表格中 user_can_only_update_own_profile 的 RLS 策略 (如果存在)
                    supabase_admin.table('profiles').update({"role": initial_role}).eq("id", new_user_id).execute()

                    st.success(f"帳號創建成功！已發送密碼設定郵件到 {new_email}。")
                    st.info(f"使用者 ID: {new_user_id}，初始角色已設定為 '{initial_role}'。")
                    
                    st.cache_data.clear()
                    st.experimental_rerun()

                except Exception as e:
                    # 捕獲常見的錯誤，例如使用者已存在
                    if "User already exists" in str(e):
                        st.error(f"創建失敗：Email {new_email} 已經存在。")
                    else:
                        st.error(f"創建失敗: {e}")
            else:
                st.error("Email 地址不可為空。")
else:
    st.error("❌ Admin Client 未初始化：無法執行創建帳號功能。")
