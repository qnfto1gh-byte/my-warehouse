import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

# 앱 설정
st.set_page_config(page_title="창고관리", layout="wide")

# [기능 4, 5, 7, 9] 엔터 이동 + 0 자동삭제 + 전체 선택
components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT' && (e.target.type === 'number' || e.target.inputMode === 'numeric')) {
            if (e.target.value === "0" || e.target.value === 0) { e.target.value = ""; }
            setTimeout(() => { e.target.select(); }, 50);
        }
    });
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(doc.activeElement);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault(); inputs[index + 1].focus();
            }
        }
    }, true);
    </script>
""", height=0)

# --- 구글 시트 주소 설정 ---
# 사진 2번의 시트 브라우저 주소를 통째로 따옴표 안에 넣으세요.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lKMH5BjjXWaqib_pqeqp_5UXpbc3M1PSDb4nEAoxw-A/edit?usp=drivesdk"

from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # [우회] 데이터 로딩 (보안 에러 방지를 위해 ttl=0 설정)
        inv = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
        hist = conn.read(spreadsheet=SHEET_URL, worksheet="History", ttl=0)
        return inv.dropna(how='all'), hist.dropna(how='all')
    except:
        return pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"]), pd.DataFrame(columns=["일시", "물품명", "유형", "수량"])

inventory, history = load_data()
today = datetime.now().date()

# [기능 1] 총 무게 표시
def get_total_display(df_item):
    total_val = 0
    unit_type = "" 
    for _, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        total_val += val * 1000 if u in ["L", "kg"] else val
        unit_type = "L" if u in ["L", "mL"] else "kg"
    if total_val >= 1000: return f"{total_val/1000:.2f}{unit_type}".replace(".00", "")
    return f"{int(total_val)}{'mL' if unit_type == 'L' else 'g'}"

st.title("📦 창고관리 시스템")

# [기능 3] 작업로그 (접이식)
with st.expander("🔍 작업로그 보기"):
    if not history.empty:
        df_h = history.copy()
        df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
        for d in sorted(df_h['날짜'].unique(), reverse=True):
            st.markdown(f"**📅 {d}**")
            st.table(df_h[df_h['날짜'] == d].sort_values("일시", ascending=False)[["일시", "물품명", "유형", "수량"]])

# [기능 8] 주간 정산 보고
with st.expander("📅 주간 정산 보고"):
    d_range = st.date_input("정산 기간", value=(today - timedelta(days=7), today))
    if len(d_range) == 2 and st.button("📊 보고서 생성"):
        df_rep = history.copy()
        df_rep['날짜'] = pd.to_datetime(df_rep['일시']).dt.date
        filtered = df_rep[(df_rep['날짜'] >= d_range[0]) & (df_rep['날짜'] <= d_range[1])]
        if not filtered.empty:
            st.table(filtered.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0))

st.divider()

# [기능 6, 9] 신규 등록 (날짜 보정)
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("물품명")
        qty = c2.number_input("입고 수량", min_value=0, value=0)
        c3, c4 = st.columns(2)
        d_raw = c3.text_input("유통기한 (YYMMDD)", max_chars=6)
        wgt = c4.number_input("단위당 무게/부피", min_value=0, value=0)
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])
        
        if st.form_submit_button("🚀 등록하기", use_container_width=True):
            d_clean = "".join(filter(str.isdigit, d_raw))
            if name and len(d_clean) == 6:
                try:
                    f_dt = f"20{d_clean[:2]}-{d_clean[2:4]}-{d_clean[4:]}"
                    datetime.strptime(f_dt, "%Y-%m-%d")
                    new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=inventory.columns)
                    new_log = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, "입고", int(qty)]], columns=history.columns)
                    
                    # [핵심] 수동 주소 업데이트로 보안 우회
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=pd.concat([inventory, new_inv], ignore_index=True))
                    conn.update(spreadsheet=SHEET_URL, worksheet="History", data=pd.concat([history, new_log], ignore_index=True))
                    st.success("✅ 등록 완료!"); time.sleep(0.5); st.rerun()
                except: st.error("❌ 날짜 확인요망 (예: 260917)")

# [기능 2] 검색 및 현황 (이하 생략 - 이전 동일 로직 적용)
