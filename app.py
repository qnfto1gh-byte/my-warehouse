📦 부대 창고관리 시스템 (Streamlit 풀코드)

모든 요구사항 통합 버전

import streamlit as st import pandas as pd from datetime import datetime, timedelta import streamlit.components.v1 as components import time

---------------- 기본 설정 ----------------

st.set_page_config(page_title="부대 창고관리", layout="wide")

숫자 입력 UX (엔터 이동 / 0 자동삭제)

components.html("""

<script>
const doc = window.parent.document;
doc.addEventListener('focusin', function(e) {
  if (e.target.tagName === 'INPUT' && e.target.type === 'number') {
    if (e.target.value === '0') e.target.value = '';
    setTimeout(() => e.target.select(), 50);
  }
});
doc.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    const inputs = Array.from(doc.querySelectorAll('input'));
    const idx = inputs.indexOf(doc.activeElement);
    if (idx > -1 && idx < inputs.length - 1) {
      e.preventDefault(); inputs[idx + 1].focus();
    }
  }
}, true);
</script>""", height=0)

---------------- Google Sheets ----------------

from streamlit_gsheets import GSheetsConnection RAW_URL = "https://docs.google.com/spreadsheets/d/1lKMH5BjjXWaqib_pqeqp_5UXpbc3M1PSDb4nEAoxw-A/edit" conn = st.connection("gsheets", type=GSheetsConnection)

---------------- 데이터 로드 ----------------

def load_data(): inv = conn.read(spreadsheet=RAW_URL, worksheet="Inventory", ttl=0) hist = conn.read(spreadsheet=RAW_URL, worksheet="History", ttl=0) return inv.dropna(how='all'), hist.dropna(how='all')

inventory, history = load_data() today = datetime.now().date()

---------------- 유틸 ----------------

def total_display(df): total, unit = 0, "" for _, r in df.iterrows(): v, u = r['총 무게'], r['단위'] total += v * 1000 if u in ['L', 'kg'] else v unit = 'L' if u in ['L', 'mL'] else 'kg' if total >= 1000: return f"{total/1000:.1f}{unit}" return f"{int(total)}{'mL' if unit=='L' else 'g'}"

---------------- 상태 ----------------

if 'mode' not in st.session_state: st.session_state.mode = '큰창고' if 'board' not in st.session_state: st.session_state.board = False

---------------- 상단 컨트롤 ----------------

st.title("📦 부대 창고관리 시스템") col1, col2, col3 = st.columns([1,1,2]) with col1: if st.button("🏬 큰창고"): st.session_state.mode = '큰창고' with col2: if st.button("🏪 작은창고"): st.session_state.mode = '작은창고' with col3: st.session_state.board = st.toggle("📋 현황판 모드", value=st.session_state.board)

---------------- 유통기한 임박 알람 ----------------

alert_items = inventory[pd.to_datetime(inventory['유통기한']).dt.date <= today + timedelta(days=7)] if not alert_items.empty: st.error("⚠️ 유통기한 7일 이내 물품 존재")

---------------- 검색 ----------------

search = st.text_input("🔍 물품 검색")

---------------- 신규 입고 ----------------

if not st.session_state.board: with st.expander("➕ 신규 물류 추가", expanded=False): with st.form("add_form"): name = st.text_input("물품명") qty = st.number_input("개수", min_value=0, value=0) exp = st.text_input("유통기한 (YYMMDD)", max_chars=6) wgt = st.number_input("단위당 무게", min_value=0) unit = st.selectbox("단위", ['g','kg','mL','L']) if st.form_submit_button("등록"): d = ''.join(filter(str.isdigit, exp)) if len(d)==6: date = f"20{d[:2]}-{d[2:4]}-{d[4:]}" new = pd.DataFrame([[st.session_state.mode, name, qty, date, wgt*qty, unit]], columns=['창고','물품명','개수','유통기한','총 무게','단위']) log = pd.DataFrame([[datetime.now(), st.session_state.mode, name, '입고', qty, date]], columns=['일시','창고','물품명','유형','개수','유통기한']) conn.update(spreadsheet=RAW_URL, worksheet="Inventory", data=pd.concat([inventory,new])) conn.update(spreadsheet=RAW_URL, worksheet="History", data=pd.concat([history,log])) st.success("등록 완료") st.rerun()

---------------- 재고 현황 ----------------

st.subheader(f"📦 {st.session_state.mode} 현황")

df = inventory[inventory['창고']==st.session_state.mode] items = [i for i in df['물품명'].unique() if search.lower() in i.lower()]

for item in items: dfi = df[df['물품명']==item] exp_min = pd.to_datetime(dfi['유통기한']).min().date() danger = exp_min <= today + timedelta(days=7)

header = f"{item} | {total_display(dfi)} | {exp_min}"
with st.expander("🚨 "+header if danger else header):
    st.table(dfi[['개수','유통기한']])

    if not st.session_state.board:
        if st.session_state.mode=='큰창고':
            out = st.number_input("불출 개수", min_value=0, key=f"out_{item}")
            if st.button("➡️ 작은창고 이동", key=f"btn_{item}"):
                fifo = dfi.sort_values('유통기한')
                move = fifo.head(out)
                rest = fifo.iloc[out:]
                move['창고'] = '작은창고'
                new_inv = pd.concat([inventory[~inventory.index.isin(move.index)], move, rest])
                log = pd.DataFrame([[datetime.now(),'큰→작은',item,'불출',out,exp_min]],
                    columns=['일시','창고','물품명','유형','개수','유통기한'])
                conn.update(spreadsheet=RAW_URL, worksheet="Inventory", data=new_inv)
                conn.update(spreadsheet=RAW_URL, worksheet="History", data=pd.concat([history,log]))
                st.rerun()

        if st.session_state.mode=='작은창고':
            if st.button("🗑️ 소진"):
                new_inv = inventory.drop(dfi.index)
                log = pd.DataFrame([[datetime.now(),'작은창고',item,'소진',dfi['개수'].sum(),exp_min]],
                    columns=['일시','창고','물품명','유형','개수','유통기한'])
                conn.update(spreadsheet=RAW_URL, worksheet="Inventory", data=new_inv)
                conn.update(spreadsheet=RAW_URL, worksheet="History", data=pd.concat([history,log]))
                st.rerun()

---------------- 작업 로그 ----------------

with st.expander("📜 입출고 기록"): h = history.copy() h['주차'] = pd.to_datetime(h['일시']).dt.to_period('W').astype(str) week = st.selectbox("주 선택", sorted(h['주차'].unique(), reverse=True)) st.table(h[h['주차']==week].sort_values('일시', ascending=False))