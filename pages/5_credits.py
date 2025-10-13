import streamlit as st
import pandas as pd 
st.set_page_config(page_title="致謝與授權")

st.title("🤝 專案致謝與貢獻者名單 (Credits)")
st.caption("本平台能夠順利上線，感謝所有貢獻者的時間、專業與支持。")

st.markdown("---")

# === 授權與引用說明區塊===
st.header("📝 專案與資料授權說明 (Licensing)")

st.subheader("程式碼與架構授權 (Code & Architecture)")
st.markdown("""
<div class="cc-signal-container" style="display:none;" vocab="http://creativecommons.org/ns#"
    typeof="License" resource="https://creativecommons.org/licenses/by/4.0/">
<span property="cc:use-ai" content="permitted"></span>
<span property="cc:exception" content="cc-cr-op"></span>  <span property="cc:attribution-url" content="[https://github.com/jokctseng/lt25dashboard-demo]"></span>
<span property="cc:attribution-name" content="青年代號：GenAI 協作平台"></span>
</div>
本專案採用雙重授權模式，以區分底層程式碼和面向使用者的內容：

* ** 程式碼 (Python Code & Logic)：**
  * **授權類型：** **MIT 授權 (The MIT License)**
  * **適用範圍：** 專案中所有的 Python (`.py`) 檔案。

* **儀表板設計與內容 (Content & Data Schema)：**
  * **授權類型：** [CC BY 4.0 (姓名標示 4.0 國際)](https://creativecommons.org/licenses/by/4.0/deed.zh_TW)
  * **適用範圍：** Streamlit的設計、排版、資料結構定義及所有文案內容。
  * **AI使用授權：** CC Credit Open 0.1


這表示您可以自由地：
* **分享** — 以任何媒介或格式重製及散布本材料。
* **改編** — 重製、編輯、轉換或改作本材料。

**唯一條件：**
* **姓名標示 (Attribution)：** 您必須適當標示我們的名稱，提供本平台原始程式碼的連結，指明是否修改本資料。標註範例如下：
    > 參考來源：[青年代號：GenAI 協作平台] (連結)，原作者：[KC Tseng & 教育部青年發展署]。
""")

st.subheader("引用資料集授權 (Data Licensing)")
st.markdown("""
**資料集引用：** **依原授權條件**

本平台在大會資料頁面引用的所有資料集或資料庫（例如：iTaiwan 熱點數、AI 專才推估、AIGO 課程等），皆**不適用**於上述 CC BY 4.0 授權。

* **使用條件：** 任何欲使用這些資料集的人，必須**嚴格遵守原資料提供者或政府機關設定的授權條款**（例如：政府資料開放授權條款）。
* **免責聲明：** 本平台僅為數據之彙整與視覺化展示，不對原始數據的內容、準確性或原授權條件負擔任何法律責任。

""")

st.markdown("---")


st.header("👥 致謝 (Credits)")
st.caption("感謝所有貢獻者的時間與專業。")

st.markdown("---")

# 開發與維護
st.subheader("開發與維護")
st.markdown("""
* **總體設計與開發：** [小工](https://jokctseng.github.io)
* **網頁架構：** Streamlit
* **S資料庫管理：** Supabase
""")

# 內容與資料
st.subheader("活動與資料支援")
st.markdown("""
* **資料集：** 政府開放資料平台
* **議題內容彙整：** 台灣經濟研究院．小工
* **分組洞見彙整：** 豆泥．Peter．小工
* **活動策劃：** 小工．Peter．豆泥．57．小軟
* **審議桌長：** 請參考大會資料頁面主持團隊表格，感謝出席與貢獻
* **議題專家：** 請參考大會資料頁面專家教練表格，感謝出席與貢獻
""")

# 協辦與支援單位
st.subheader("協辦與支援單位")
st.markdown("""
* **指導單位：** 教育部
* **主辦機關：** 教育部青年發展署
* **協辦機關單位：** 請參考大會資料頁面相關單位表格，感謝出席與貢獻
* **幕僚與執行單位：** 台灣經濟研究院研究八所、台灣經濟研究院研究九所
* **場地與硬體支援：** 交通部集思會議中心
""")

st.markdown("---")
