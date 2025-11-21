# 青年代號：GenAI 協作平台

## 🚀 專案簡介 (Introduction)

本平台是為「全國青年會議：青年代號 GenAI」活動設計的即時協作與彙整工具。平台的核心目標是提供一個安全、高效的環境，讓青年參與者能夠**即時分享政策建議或洞察**、**對關鍵議題進行投票與共識建立**，並讓管理團隊能夠**即時追蹤進度**與**管理使用者權限**。

## ✨ 核心功能 (Features)

* **🛡️ 即時儀表板 (Dashboard)**：
    * 即時顯示所有政策建議與洞察。
    * 支援按**類別 (cate)** 和**投票狀態**進行篩選。
    * 視覺化展示各建議的共識程度（未解決/部分解決/已解決）。
* **🗳️ 投票與共識 (Voting)**：
    * 已登入用戶可對每個建議投出自己的意見（未解決、部分解決、已解決/有共識）。
    * 訪客模式 (未登入) 可自由瀏覽所有資料，保障資訊透明度。
* **📢 共創新聞牆 (News Wall)**：
    * 用戶可依據不同**主題 (topic)** 發表回饋、小組共創內容或想法。
    * 支援對貼文進行「支持、中立、反對」的即時 Reaction。
* **🔑 管理員後台 (Admin Panel)**：
    * **高權限管理：** 系統管理員可檢視使用者 Email、UID 等敏感資訊。
    * **角色控制：** 支援批次修改使用者角色（System Admin, Moderator, User）。
    * **帳號邀請：** 透過 Supabase Admin API 發送密碼設定郵件邀請使用者。
    * **數據匯入：** 支援管理員批次 CSV 匯入的政策建議/洞察。
 
## ⚠️ 待處理問題（Limitations）

* **🛜 連線設置**：目前各分頁登入與連線狀況依賴`app.py`進行，導致使用者需要反覆回到主頁再切換到分頁，未來可能需要將此功能獨立出來。
* **🆔 更多元的登入方式**：
    * supabase可使用Google、Apple、去中心化錢包等多元方式登入，但需有對應的權限；測試過程中streamlit在配合Google登入這塊會卡住，因此這次未使用。
    * 本版本有串電子報系統，以此來發送建立帳號的系統Email，如果要使用此功能務必要記得串其他的寄信系統，supabase免費版可寄發的數量極為有限。


## 🛠️ 技術棧 (Tech Stack)

| 服務/工具 | 用途 | 備註 |
| :--- | :--- | :--- |
| **Streamlit** | 框架 | 快速建構互動式儀表板和 UI。 |
| **Supabase** | 後端資料庫 (Backend/DB) | 實時 PostgreSQL 資料庫，負責儲存所有使用者、投票和內容。 |
| **Pandas / Plotly** | 資料處理與視覺化 | Python 核心數據分析工具。 |
| **Python** | 程式語言 | 專案主要開發語言。 |

## ⚙️ 部署與設定 (Deployment & Setup)

### Local Run

1.  複製此repo：`git clone []`
2.  安裝requirements：`pip install -r requirements.txt`
3.  密鑰文件：在專案目錄下建立 `.streamlit/secrets.toml`，並填寫您的 Supabase 密鑰（包括 `service_role_key`）。
4.  運行應用程式：`streamlit run app.py`

### 部署至 Streamlit Cloud
1. fork repo到自己的GitHub
2. 修改為自己活動的內容
3. 到Streamlit Cloud選擇自己的Repo部署

請勿將 `.streamlit/secrets.toml` 提交至 GitHub，請手動將密鑰貼入 Streamlit Cloud 的 **"Secrets"** 設定頁面中。

```toml
# Streamlit Cloud Secrets 內容範例
[supabase]
url = "YOUR_SUPABASE_URL"
key = "YOUR_ANON_KEY"
service_role_key = "YOUR_SERVICE_ROLE_KEY"
```
## ⚖️ 授權（License）

<a href="https://creativecommons.org">2025青年好政全國青年會議協作平台</a> © 2025 by <a href="https://jokctseng.github.io">KC Tseng&amp;教育部青年發展署</a> is licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a><img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;"><img src="https://mirrors.creativecommons.org/presskit/icons/by.svg" alt="" style="max-width: 1em;max-height:1em;margin-left: .2em;">

