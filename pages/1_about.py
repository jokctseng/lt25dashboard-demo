import streamlit as st
import pandas as pd 
import os

st.set_page_config(page_title="大會資料")

st.title("📄 大會資料")

# --- 核心活動設計與目標 ---
st.header("活動設計與核心目標")
st.markdown("""
青年世代，生成未來，青年如何定義AI世代？

當GenerativeAI成為趨勢，我們從Generation著手，不只是使用者，更是規則的參與者，讓青年的聲音成為未來的prompt，打造屬於我們的GenAI——以青年世代領航的AI相關政策策論。

「青年代號：GenAI」是一場小規模政策紅隊演練，借用資安界紅隊的意象，透過資訊釐清、議題對焦與討論，針對AI政策的機會與風險展開深化交流。青年團隊將化身「紅隊」，從不同的視角挑戰既有構想，檢驗既有狀態的漏洞與盲點，並與部會協作，為社會輸入具創造性的政策建議或洞見。
""")

st.info("💡 請注意：所有回饋與投票將會進行即時彙整。")


# --- 規則與須知總覽 ---
st.markdown("---")
with st.expander("🛠️ 活動須知與規則總覽", expanded=False):
    
    # CoC
    st.header("🤝 大會行為準則 (Code of Conduct)")
    st.caption("點擊下方展開查看詳細準則，以確保所有交流都是開放、尊重和建設性的。")
    with st.expander("點擊展開查看【青年代號：GenAI】行為準則", expanded=False):
        st.markdown("""
        本行為準則適用於所有活動參與者及相關人員，確保所有人能在**開放、尊重和安全**的環境中交流與學習

        
        ## 我們的期望
        致力於提供一個無騷擾、具包容性的體驗，因此所有參與者都應遵守以下準則：

        ### 互相尊重與開放心態
        * **尊重對待他人：** 避免攻擊性、侮辱、貶低或歧視性的評論或行為
        * **尊重差異，保持開放：** 鼓勵聆聽不同的意見和視角，保持專業和友善的態度。
        
        ### 專業與共創
        * **保持專注與積極參與：** 積極貢獻您的想法，共同創造價值
        * **尊重智慧財產權：** 除非明確允許，請勿未經許可分享他人的機密資訊或受保護的內容

        ### 禁止的行為
        以下行為會被視為違反本行為準則
        * **騷擾：** 任何基於性別、性向、障礙、生理外觀、體型、種族、宗教等的冒犯性言語評論；包含但不限於不當的性圖像、故意恐嚇、跟蹤、騷擾攝影或錄影、不當的身體接觸以及不必要的關注等。
        * **歧視與排斥：** 任何形式的歧視、仇恨言論或蓄意排斥他人參與的行為。
        * **破壞性行為：** 任何持續或嚴重的破壞、滋擾或攻擊行為，導致其他人感到不安全或被冒犯。
        * **不遵守規則：** 違反場地、活動主辦方或法律規定的任何行為。

        ### 回報與處理方式
        * **如何回報：** 如果您經歷或目睹任何違反本準則的行為，請立即回報工作人員以利立即處理。
        * **處理方式：** 參與者若違反本行為準則，主辦方可採取任何認為適當的行動，包括但不限於警告、要求離開活動會場或禁止參與未來的活動。

        """)
        
    st.markdown("---")
    
    # 分組教室資訊
    st.header("📍 分組教室資訊")
    st.markdown("""
    以下為各組教室分配，其餘皆在 **5樓集會堂**：
    
    * **A組** 於 201 教室
    * **B組** 於 202 教室
    * **F組** 於 大廳
    """)
    st.caption("🚨 **請注意：** 具體位置請以大會現場公告為準。")

st.markdown("---")

# --- 活動議程 ---
st.header("📅 活動議程")

data_day1 = {
    "時間": ["10:00 - 10:30", "10:30 - 10:45", "10:45 - 11:20", "11:20 - 12:00", "12:00 - 13:00", "13:00 - 15:35", "15:35 - 15:45", "15:45 - 17:15", "17:15 - 17:40"],
    "內容": ["報到", "開場", "議題說明與暖身", "地方成果分享與交流", "午餐", "演練I：資訊對齊", "休息時間", "演練II：議題對焦", "Day 1小結"],
    "地點": ["5樓集會堂", "5樓集會堂", "5樓集會堂", "5樓大廳", "5樓集會堂", "分組教室", "分組教室","分組教室","5樓集會堂"] 
}

data_day2 = {
    "時間": ["9:00 - 09:30", "09:30 - 09:50", "09:50 - 11:40", "11:40 - 11:50", "11:50 - 12:20", "12:20 - 12:40"],
    "內容": ["第二天報到", "Talk計畫說明", "部會入桌討論", "致詞", "成果發表", "閉幕"],
    "地點": ["5樓集會堂", "5樓集會堂", "分組教室", "5樓集會堂", "5樓集會堂", "5樓集會堂"]
}

tab1, tab2 = st.tabs(["Day 1", "Day 2"])

with tab1:
    st.subheader("🗓️ 第一天：演練準備")
    with st.expander("點擊展開查看第一天議程表", expanded=True): # 預設展開第一天
        st.dataframe(pd.DataFrame(data_day1), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🗓️ 第二天：正式上場")
    with st.expander("點擊展開查看第二天議程表"):
        st.dataframe(pd.DataFrame(data_day2), use_container_width=True, hide_index=True)

st.markdown("---")
# --- 團隊名單 ---
st.header("主持與專家團隊")

data_host = {
    "角色": ["大場", "大場", "大場", "大場", "桌長", "桌長", "桌長", "桌長", "桌長"],
    "姓名": ["曾廣芝", "崔家瑋", "林玟圻", "阮敬瑩", "沈鈺琪", "洪堃斌", "待確認", "廖宇雯", "張為然"],
    "簡歷": [
        "青年好政審議業師 \n第二/三屆行政院青年諮詢委員", 
        "青年好政審議業師 \n中研院法律學研究所研究助理", 
        "教育部青發署青諮小組", 
        "青年好政審議業師", 
        "青年好政審議業師", 
        "青年好政審議業師", 
        "青年好政審議業師", 
        "青年好政審議業師",
        "青年好政審議業師"
    ] 
}

data_coach = {
    "組別": ["AI教育與素養培育", "勞動轉型與產業應用", "文化傳承與地方發展", "資訊安全與社會防護", "數位平權與共融治理"],
    "姓名": ["陳以婕", "丁玉珍", "趙式隆", "詹婷怡", "李欣穎"],
    "簡歷": [
        "g0v 社群", 
        "勞動部秘書處處長", 
        "臺北市資訊局長 \n曾任行政院青年顧問團", 
        "人工智慧基金會董事長 <br>曾任NCC主委", 
        "開放文化基金會執行長"
    ]
}

data_department = {
    "角色": ["主辦單位", "入桌討論部會", "入桌討論部會", "入桌討論部會", "入桌討論部會", "出席部會", "出席部會", "出席局處"],
    "機關單位": ["教育部青年發展署", "數位發展部", "教育部", "勞動部", "文化部", "農委會", "原民會", "新北市青年局"],
    "對應組別": ["E", "DE", "A", "B", "C", "C", "C", "D"]
}

tab3, tab4, tab5 = st.tabs(["主持團隊", "專家教練", "相關單位"])

with tab3:
    st.subheader("主持團隊")
    with st.expander("點擊展開查看主持團隊名單"): 
        st.dataframe(pd.DataFrame(data_host), use_container_width=True, hide_index=True, unsafe_allow_html=True)

with tab4:
    st.subheader("專家教練")
    with st.expander("點擊展開查看專家教練名單"):
        st.dataframe(pd.DataFrame(data_coach), use_container_width=True, hide_index=True, unsafe_allow_html=True)

with tab5:
    st.subheader("相關單位")
    with st.expander("感謝相關部會局處出席及參與"):
        st.dataframe(pd.DataFrame(data_department), use_container_width=True, hide_index=True)

st.markdown("---")

# --- 參考資料 ---
st.header("📚 核心參考資料")
st.caption("請點擊下方按鈕，查閱與本次活動相關的背景資料。")
reference_links = [
    {
        "label": "👉 青年小組彙整的建議與洞見",
        "url": "https://wonderl.ink/@kclt25",
        "help": "跳轉至外部資料彙整平台"
    },
    {
        "label": "📝 初步書面回應",
        "url": "https://youthhub.yda.gov.tw/",
        "help": "到青年好政網站查閱初步書面回應資料"
    },
    {
        "label": "💻 大場簡報",
        "url": "https://docs.google.com/presentation/d/14ELmqJNLsI_4lvEqoXxfbk1ojJZPVq1mig0nKZ1G9AY/edit?usp=sharing",
        "help": "查看大場簡報"
    },
    {
        "label": "🧪 (beta)Gemini洞見檢核助手",
        "url": "https://gemini.google.com/gem/5e3aa78bcbf8?usp=sharing",
        "help": "使用Gemini輔助思考洞見深化與資訊對齊方向"
    },
    {
        "label": "💬 其他補充內容",
        "url": "https://docs.google.com/document/d/1H0RU-Glp-s3gJJcFZadaOeUe4rieOUiThFr-jl8ewuI/edit?usp=sharing",
        "help": "活動常見問題與解答"
    }
]

cols = []
for i in range(0, len(reference_links), 2):
    cols.append(st.columns(2))
    
    # 處理第一欄 (cols[i//2][0])
    with cols[i//2][0]:
        link_data = reference_links[i]
        st.link_button(link_data['label'], link_data['url'], help=link_data['help'])
        
    # 處理第二欄
    if i + 1 < len(reference_links):
        with cols[i//2][1]:
            link_data = reference_links[i+1]
            st.link_button(link_data['label'], link_data['url'], help=link_data['help'])

st.markdown("---")
