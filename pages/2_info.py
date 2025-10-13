import streamlit as st
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="參考資料")

st.title("🔗 相關補充資訊與數據概覽")
st.markdown("---")

# 超連結
st.header("🌐 相關政策參考資訊")
st.caption("歡迎點擊下方按鈕查看相關政策數據或報告。")
reference_links = [
    {
        "label": "數發部｜人工智慧應用服務產業2025-2027專業人才需求推估調查",
        "url": "https://ws.ndc.gov.tw/001/administrator/18/relfile/6037/9877/3c064d79-1bf7-46ba-b781-81a358ca423d.pdf",
        "help": "查看完整報告"
    },
    {
        "label": "客委會｜臺灣客語語料庫",
        "url": "https://corpus.hakka.gov.tw/",
        "help": "查看臺灣客語語料庫"
    },
    {
        "label": "行政院｜人工智慧基本法草案",
        "url": "https://www.ey.gov.tw/File/E3D2460979E0685?A=C",
        "help": "查看行政院核轉立院審議版草案"
    },
    {
        "label": "數發部｜AI 產業實戰應用人才淬煉計畫報告",
        "url": "https://aigo.org.tw/download/113%20%E5%B9%B4%E8%87%BA%E7%81%A3%20AI%20%E5%89%8D%E7%9E%BB%E4%BA%BA%E6%89%8D%E7%99%BC%E5%B1%95%E5%8F%8A%E5%9F%B9%E8%82%B2%E5%A0%B1%E5%91%8A(%E7%B2%BE).pdf",
        "help": "點擊查看報告"
    },
    {
        "label": "數發部｜促進資料創新利用發展條例草案",
        "url": "https://www-api.moda.gov.tw/File/Get/moda/zh-tw/kTu4o05SWXtGxfl",
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


# 數據統計分析視覺化成果
# 檔案名稱定義
FILE_HOTSPOTS = "iTaiwan_spots.csv"
FILE_TALENT = "AI_Talent.csv"
FILE_COURSES = "AIGO_OnlineCourse.csv"
FILE_GRANT = "AI_Grant.csv"
FILE_CORPUS = "corpus_collect.csv"

# --- 1. 資料清洗工具與快取 ---

def minguo_to_gregorian(minguo_year):
    """將民國年轉換為西元年 (民國年 + 1911)"""
    return minguo_year + 1911

@st.cache_data
def load_and_prepare_data():
    """載入所有數據並執行清洗和格式化。"""
    
    try:
        df_hotspots = pd.read_csv(FILE_HOTSPOTS)
        df_talent = pd.read_csv(FILE_TALENT)
        df_courses = pd.read_csv(FILE_COURSES)
        df_grant = pd.read_csv(FILE_GRANT)
        df_corpus = pd.read_csv(FILE_CORPUS)
    except FileNotFoundError:
        return None, None, None, None, None, None 

    # --- A. Hotspots (iTaiwan_spots.csv) ---
    # 融化數據以繪製區域趨勢圖 
    year_cols = [col for col in df_hotspots.columns if '熱點數量' in col]
    regional_aggregates = df_hotspots[
        df_hotspots['地區'].isin(['北部區域', '中部區域', '南部區域', '東部區域', '離島區域'])
    ].copy()
    
    df_hotspots_melt = regional_aggregates.melt(
        id_vars='地區', 
        value_vars=year_cols, 
        var_name='年度', 
        value_name='熱點數量'
    )
    df_hotspots_melt['年度'] = df_hotspots_melt['年度'].str.replace('年(熱點數量)', '', regex=False).astype(int)
    
    # --- B. Talent (AI_Talent.csv) ---
    # 融化數據以繪製多情境趨勢圖 
    df_talent_melt = df_talent.melt(
        id_vars='年度', 
        value_vars=['樂觀推估新增專才人數', '持平推估新增專才人數', '保守推估新增專才人數'],
        var_name='推估情境', 
        value_name='新增專才人數'
    )
    
    # --- C. Courses (AIGO_OnlineCourse.csv) ---
    # 年份轉換 
    df_courses['年度_西元'] = df_courses['年度'].apply(minguo_to_gregorian)
    # 時數清洗: 移除 'hr' 並轉換為數值
    df_courses['時數_num'] = df_courses['時數'].astype(str).str.replace('hr', '', regex=False)
    df_courses['時數_num'] = pd.to_numeric(df_courses['時數_num'], errors='coerce').fillna(0)
    
    # --- D. Grant (AI_Grant.csv) ---
    # 發布日期年份轉換 
    df_grant['發布年份_西元'] = df_grant['發布日期'].astype(str).str[:3].astype(int).apply(minguo_to_gregorian)

    # --- E. Corpus (corpus_collect.csv) ---
    # 年份轉換
    df_corpus['年度_西元'] = df_corpus['年度'].apply(minguo_to_gregorian)
    # 聚合採集數
    df_corpus_agg = df_corpus.groupby('年度_西元')['採集數'].sum().reset_index()

    return df_hotspots, df_hotspots_melt, df_talent_melt, df_courses, df_grant, df_corpus_agg

# 載入所有數據
df_hotspots, df_hotspots_melt, df_talent_melt, df_courses, df_grant, df_corpus_agg = load_and_prepare_data()

# 檢查數據是否成功載入
if df_hotspots is None:
    st.title("📊 相關補充資訊與統計分析")
    st.error("無法載入數據：請確認所有 CSV 檔案已正確放置。")
    st.stop()


# --- 2. 視覺化繪圖函式 (Plotly) ---

def plot_hotspots_trend(df):
    """iTaiwan 熱點數量分區域趨勢圖"""
    fig = px.line(
        df, x='年度', y='熱點數量', color='地區',
        title='iTaiwan 熱點數量分區域趨勢',
        markers=True
    )
    fig.update_layout(xaxis_title="年度 (西元)", yaxis_title="熱點數量")
    st.plotly_chart(fig, use_container_width=True)

def plot_talent_projection(df):
    """AI 專才新增人數情境推估趨勢圖"""
    fig = px.line(
        df, x='年度', y='新增專才人數', color='推估情境',
        title='AI 專才新增人數推估趨勢',
        markers=True
    )
    fig.update_layout(xaxis_title="年度 ", yaxis_title="新增專才人數")
    st.plotly_chart(fig, use_container_width=True)

def plot_course_hours(df):
    """AIGO 課程總時數趨勢圖"""
    df_agg = df.groupby('年度_西元')['時數_num'].sum().reset_index()
    fig = px.bar(
        df_agg, x='年度_西元', y='時數_num', color='年度_西元',
        title='AIGO 自製線上課程總時數',
        text_auto=True
    )
    fig.update_layout(xaxis_title="年度", yaxis_title="總時數 (小時)")
    st.plotly_chart(fig, use_container_width=True)

def plot_corpus_trend(df):
    """語料庫採集數趨勢圖"""
    fig = px.line(
        df, x='年度_西元', y='採集數',
        title='語料庫採集數年度趨勢',
        markers=True
    )
    fig.update_layout(xaxis_title="年度", yaxis_title="總採集數")
    st.plotly_chart(fig, use_container_width=True)

# --- 3. Streamlit 頁面內容 ---

st.title("📊 相關補充資訊與統計分析")
st.markdown("---")


# --- 3.1 資訊與社會防護 I：iTaiwan 熱點覆蓋趨勢 (iTaiwan_spots.csv) ---
st.header("數位基礎建設：iTaiwan 熱點覆蓋趨勢")
st.caption("數據來源：iTaiwan熱點數。圖表顯示五大區域熱點數量逐年變化。")
plot_hotspots_trend(df_hotspots_melt)

with st.expander("查看原始數據：iTaiwan 熱點數"):
    df_display = df_hotspots[
        ~df_hotspots['地區'].isin(['臺閩地區', '臺灣地區'])
    ].copy()
    st.dataframe(df_display, use_container_width=True, hide_index=True)

st.markdown("---")


# --- 3.2 勞動產業：AI 專才新增人數推估 (AI_Talent.csv) ---
st.header("勞動及產業轉型：AI 專才新增人數推估")
st.caption("數據來源：AI專才推估。圖表呈現三種不同情境下，AI 專才新增人數隨西元年的推估趨勢。")
plot_talent_projection(df_talent_melt)

with st.expander("查看原始數據：專才推估"):
    st.dataframe(df_talent, use_container_width=True, hide_index=True)

st.markdown("---")


# --- 3.3 教育：AIGO 自製線上課程總覽 (AIGO_OnlineCourse.csv) ---
st.header("全民AI識能與教育：AIGO 自製線上課程總覽")
st.caption("資料來源：政府開放資料平台，最新資訊請看AIGO網站。圖表顯示各年課程總時數。")
plot_course_hours(df_courses)

st.subheader("完整課程列表 (含連結)")

# 顯示關鍵欄位，並將年度換成西元
df_course_list = df_courses[['年度_西元', '合作單位', '課程名稱', '時數', '網址']].copy()
df_course_list.rename(columns={'年度_西元': '年度 (西元)'}, inplace=True)
st.dataframe(df_course_list, use_container_width=True, hide_index=True)


st.markdown("---")


# --- 3.4 數位平權與共融治理：補助計畫 (AI_Grant.csv) ---
st.header("補助計畫列表")
st.caption("資料來源：行政院智慧國家2.0推動小組。")

# 顯示美化後的表格，並突出關鍵資訊
df_grant_display = df_grant[['補助計畫', '發布日期', '主辦單位', '補助對象', '簡介與補助範疇']].copy()
df_grant_display.rename(columns={'發布日期': '發布日期'}, inplace=True)
st.dataframe(df_grant_display, use_container_width=True, hide_index=True)

st.markdown("---")

# --- 3.5 資訊與社會防護 II：語料庫採集趨勢 (corpus_collect.csv) ---
st.header("文化：全國語言推廣人員工作成果語料採集與紀錄則數統計")
st.caption("資料來源：原民會開放資料")
plot_corpus_trend(df_corpus_agg)

with st.expander("查看原始數據：語料庫採集數"):
    df_corpus_display = df_corpus.copy()
    df_corpus_display.rename(columns={'年度_西元': '年度 (西元)'}, inplace=True)
    st.dataframe(df_corpus_display, use_container_width=True, hide_index=True)
