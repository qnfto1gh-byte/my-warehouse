부대 창고관리 시스템 (Streamlit 단일 파일)

⚠️ 주의: Python 코드 외 텍스트/이모지는 주석(#)으로만 사용

import streamlit as st import pandas as pd from datetime import datetime, timedelta import streamlit.components.v1 as components import time

---------------- 앱 설정 ----------------

st.set_page_config(page_title="부대 창고관리", layout="wide")

---------------- 숫자 입력 UX ----------------

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

def load_data(): try: inv = conn.read(spreadsheet=RAW_URL, worksheet="Inventory", ttl=0) hist = conn.read(spreadsheet=RAW_URL, worksheet="History", ttl=0) except Exception: inv = pd.DataFrame(columns=["창고","물품명","개수","유통기한","총 무게","단위"]) hist = pd.DataFrame(columns=["일시","창고","물품명","유형","개수","유통기한"]) return inv.dropna(how='all'), hist.dropna(how='all')

inventory, history = load_data() today = datetime.now().date()

---------------- 유틸 함수 ----------------

def total_display(df): total = 0 unit_type = None for _, r in df.iterrows(): v, u = r['총 무게'], r['단위'] if u in ['L','kg']: total += v * 1000 unit_type = 'L' if u == 'L' else 'kg' else: total += v unit_type = 'L' if u == 'mL' else 'kg' if unit_type == 'L': return f"{total/1000:.1f}L" if total >= 1000 else f"{int(total)}mL" return f"{total/1000:.1f}kg" if total >= 1000 else f"{int(total)}g"

---------------- 상태 ----------------

if 'warehouse' not in st.session_state: st.session_state.warehouse = '큰창고' if 'board_mode' not in st.session_state: st.session_state.board_mode = False

---------------- 상단 UI ----------------

st.title("부대 창고관리 시스템") col1, col2, col3 = st.columns([1,1,2]) with col1: if st.button("큰창고"): st.session_state.warehouse = '큰창고' with col2: if st.button("작은창고"): st.session_state.warehouse = '작은창고' with col3: st.session_state.board_mode = st.toggle("현황판 모드", value=st.session_state.board_mode)

---------------- 유통기한 임박 알림 ----------------

if not inventory.empty: inv_dates = pd.to_datetime(inventory['유통기한'], errors='coerce').dt.date if (inv_dates <= today + timedelta(days=7)).any(): st.error("유통기한 7일 이내 물품이 있습니다")

---------------- 검색 ----------------

search = st.text_input("물품 검색")

---------------- 신규 입고 ----------------

if not st.session_state.board_mode: with st.expander("신규 물류 추가"): with st.form("add_form", clear_on_submit=True): name = st.text_input("물품명") qty = st.number_input("개수", min_value=1, step=1) exp_raw = st.text_input("유통기한 (YYMMDD)", max_chars=6) weight = st.number_input("단위당 무게", min_value=1) unit = st.selectbox("단위", ['g','kg','mL','L']) if st.form_submit_button("등록"): d = ''.join(filter(str.isdigit, exp_raw)) if len(d) != 6: st.error("날짜 형식 오류") else: exp = f"20{d[:2]}-{d[2:4]}-{d[4:]}" new_row = pd.DataFrame([[st.session_state.warehouse, name, qty, exp, qty*weight, unit]], columns=inventory.columns) log = pd.DataFrame([[datetime.now(), st.session_state.warehouse, name, '입고', qty, exp]], columns=history.columns) conn.update(spreadsheet=RAW_URL, worksheet="Inventory", data=pd.concat([inventory, new_row], ignore_index=True)) conn.update(spreadsheet=RAW_URL, worksheet="History", data=pd.concat([history, log], ignore_index=True)) st.success("등록 완료") time.sleep(0.3) st.rerun()

---------------- 재고 표시 ----------------

st.subheader(f"{st.session_state.warehouse} 재고") df = inventory[inventory['창고'] == st.session_state.warehouse]

items = [i for i in df['물품명'].unique() if search.lower() in str(i).lower()]

for item in items: dfi = df[df['물품명'] == item] exp_min = pd.to_datetime(dfi['유통기한']).min().date() danger = exp_min <= today + timedelta(days=7) title = f"{item} | {total_display(dfi)} | {exp_min}"

with st.expander(title):
    st.table(dfi[['개수','유통기한']])

    if not st.session_state.board_mode:
        if st.session_state.warehouse == '큰창고':
            out_qty = st.number_input("불출 개수", min_value=1, max_value=int(dfi['개수'].sum()), key=f"out_{item}")
            if st.button("작은창고로 이동", key=f"move_{item}"):
                fifo = dfi.sort_values('유통기한')
                move = fifo.head(out_qty).copy()
                move['창고'] = '작은창고'
                remain = fifo.iloc[out_qty:]
                new_inv = pd.concat([
                    inventory.drop(dfi.index),
                    remain,
                    move
                ], ignore_index=True)
                log = pd.DataFrame([[datetime.now(), '큰→작은', item, '불출', out_qty, exp_min]],
                    columns=history.columns)
                conn.update(spreadsheet=RAW_URL, worksheet="Inventory", data=new_inv)
                conn.update(spreadsheet=RAW_URL, worksheet="History",
                            data=pd.concat([history, log], ignore_index=True))
                st.rerun()

        if st.session_state.warehouse == '작은창고':
            if st.button("소진", key=f"del_{item}"):
                new_inv = inventory.drop(dfi.index)
                log = pd.DataFrame([[datetime.now(), '작은창고', item, '소진', int(dfi['개수'].sum()), exp_min]],
                    columns=history.columns)
                conn.update(spreadsheet=RAW_URL, worksheet="Inventory", data=new_inv)
                conn.update(spreadsheet=RAW_URL, worksheet="History",
                            data=pd.concat([history, log], ignore_index=True))
                st.rerun()

---------------- 작업 로그 ----------------

with st.expander("입출고 기록"): if not history.empty: h = history.copy() h['주차'] = pd.to_datetime(h['일시']).dt.to_period('W').astype(str) week = st.selectbox("주차 선택", sorted(h['주차'].unique(), reverse=True)) st.table(h[h['주차'] == week].sort_values('일시', ascending=False))