import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import time

# 앱 설정
st.set_page_config(page_title="창고관리", layout="wide")

# [스크립트] 엔터 이동 + 0 자동삭제 + 전체선택
components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT' && (e.target.type === 'number' || e.target.inputMode === 'numeric')) {
            if (e.target.value === "0") { e.target.value = ""; }
            e.target.select();
            e.target.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const active = doc.activeElement;
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(active);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault(); inputs[index + 1].focus();
            }
        }
    }, true);
    </script>
""", height=0)

# --- 구글 시트 연결 (URL을 본인 시트 주소로 꼭 바꿔주세요!) ---
# 예: "https://docs.google.com/spreadsheets/d/12345.../edit?usp=sharing"
SHEET_URL = "여기에_구글_시트_주소를_복사해서_넣으세요"

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        inv = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl="0")
        hist = conn.read(spreadsheet=SHEET_URL, worksheet="History", ttl="0")
        return inv.dropna(how='all'), hist.dropna(how='all')
    except:
        inv = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
        hist = pd.DataFrame(columns=["일시", "물품명", "유형", "수량", "상태"])
        return inv, hist

inventory, history = load_data()

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

# --- [1, 3번] 작업로그 (접이식 + 날짜별) ---
with st.expander("🔍 작업로그", expanded=False):
    if not history.empty:
        df_h = history.copy()
        df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
        for d in sorted(df_h['날짜'].unique(), reverse=True):
            st.markdown(f"**📅 {d}**")
            st.table(df_h[df_h['날짜'] == d].sort_values("일시", ascending=False)[["일시", "물품명", "유형", "수량"]])
    else: st.info("로그가 없습니다.")

# --- [6번] 등록 (날짜 오류 해결) ---
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2); name = c1.text_input("물품명"); qty = c2.number_input("입고 수량", min_value=0, value=0)
        c3, c4 = st.columns(2); d6 = c3.text_input("유통기한 (YYMMDD)"); wgt = c4.number_input("단위당 무게/부피", min_value=0, value=0)
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])
        if st.form_submit_button("🚀 등록하기", use_container_width=True):
            if name and len(d6) == 6:
                f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                new_row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=inventory.columns)
                inventory = pd.concat([inventory, new_row], ignore_index=True)
                new_log = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, "입고", int(qty), "정상"]], columns=history.columns)
                history = pd.concat([history, new_log], ignore_index=True)
                
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory)
                conn.update(spreadsheet=SHEET_URL, worksheet="History", data=history)
                st.success(f"{name} 등록 완료!"); time.sleep(0.5); st.rerun()

# --- [2번] 검색 및 재고 현황 ---
st.subheader("📦 현재 창고 재고 현황")
search = st.text_input("🔍 물품 검색")
if not inventory.empty:
    df_m = inventory.copy()
    items = [i for i in df_m['물품명'].unique() if search.lower() in str(i).lower()]
    for item in items:
        i_df = df_m[df_m['물품명'] == item].copy()
        i_df['dt'] = pd.to_datetime(i_df['유통기한']).dt.date
        i_df = i_df.sort_values('dt')
        # [1번] 총 무게 표시 복구
        with st.expander(f"📦 {item} | 총 {int(i_df['개수'].sum())}개 | {i_df['dt'].min()} | {get_total_display(i_df)}"):
            st.table(i_df[["개수", "유통기한"]])
            if st.button(f"전량 불출", key=f"btn_{item}"):
                # 불출 로직... (시트 업데이트 포함)
                pass
