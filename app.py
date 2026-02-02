import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

# 앱 설정
st.set_page_config(page_title="부대 창고관리", layout="wide")

# [기능 4, 5, 7, 9] 엔터 이동 + 0 자동삭제 + 전체 선택 스크립트
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

# --- 구글 시트 설정 (사용자님의 시트 주소를 꼭 넣어주세요) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lKMH5BjjXWaqib_pqeqp_5UXpbc3M1PSDb4nEAoxw-A/edit?usp=drivesdk"

from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        inv = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
        hist = conn.read(spreadsheet=SHEET_URL, worksheet="History", ttl=0)
        return inv.dropna(how='all'), hist.dropna(how='all')
    except Exception as e:
        st.error(f"데이터 로딩 실패: 시트 주소와 '편집자' 권한을 확인하세요.")
        return pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"]), pd.DataFrame(columns=["일시", "물품명", "유형", "수량"])

inventory, history = load_data()
today = datetime.now().date()

# [기능 1] 총 무게 표시 (L/kg 단위 자동 변환)
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
with st.expander("🔍 작업로그 보기", expanded=False):
    if not history.empty:
        df_h = history.copy()
        df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
        for d in sorted(df_h['날짜'].unique(), reverse=True):
            st.markdown(f"**📅 {d}**")
            st.table(df_h[df_h['날짜'] == d].sort_values("일시", ascending=False)[["일시", "물품명", "유형", "수량"]])

# [기능 8] 주간 입출 정산 보고
with st.expander("📅 주간 입출 정산 보고", expanded=False):
    d_range = st.date_input("정산 기간 선택", value=(today - timedelta(days=7), today))
    if len(d_range) == 2:
        if st.button("📊 보고서 생성"):
            df_rep = history.copy()
            df_rep['날짜'] = pd.to_datetime(df_rep['일시']).dt.date
            filtered = df_rep[(df_rep['날짜'] >= d_range[0]) & (df_rep['날짜'] <= d_range[1])]
            if not filtered.empty:
                stats = filtered.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                st.table(stats)
            else: st.warning("해당 기간에 기록이 없습니다.")

st.divider()

# [기능 6, 9] 신규 등록 (날짜 보정 기능 포함)
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
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=pd.concat([inventory, new_inv], ignore_index=True))
                    conn.update(spreadsheet=SHEET_URL, worksheet="History", data=pd.concat([history, new_log], ignore_index=True))
                    st.success("✅ 등록 완료!"); time.sleep(0.5); st.rerun()
                except: st.error("❌ 날짜를 확인하세요 (예: 260917)")
            else: st.warning("⚠️ 물품명과 유통기한 6자리를 확인하세요.")

st.divider()

# [기능 2] 검색 기능 (물품명 필터링)
st.subheader("📦 현재 창고 재고 현황")
search = st.text_input("🔍 물품 검색 (검색어를 입력하면 아래 리스트가 필터링됩니다)")

if not inventory.empty:
    df_m = inventory.copy()
    # 검색어에 맞는 물품만 리스트업
    items = [i for i in df_m['물품명'].unique() if search.lower() in str(i).lower()]
    
    if not items:
        st.info("검색 결과가 없습니다.")
    else:
        for item in items:
            i_df = df_m[df_m['물품명'] == item].copy()
            i_df['dt'] = pd.to_datetime(i_df['유통기한']).dt.date
            i_df = i_df.sort_values('dt')
            t_qty = int(i_df['개수'].sum())
            
            # 메인 화면 표시 (품명 | 총수량 | 가장 빠른 유통기한 | 총 무게)
            with st.expander(f"📦 {item} | 총 {t_qty}개 | 가장 빠른 기한: {i_df['dt'].min()} | 총량: {get_total_display(i_df)}"):
                st.table(i_df[["개수", "유통기한"]])
                c1, c2 = st.columns([2, 1])
                rem_qty = c1.number_input(f"불출 수량", min_value=1, max_value=t_qty, key=f"del_{item}", value=1)
                if c2.button("불출 확정", key=f"btn_{item}"):
                    # FIFO(선입선출) 기반 자동 차감 로직
                    rem = rem_qty
                    temp_inv = inventory.copy()
                    for idx in i_df.index:
                        if rem <= 0: break
                        curr = temp_inv.at[idx, '개수']
                        u_w = temp_inv.at[idx, '총 무게'] / curr
                        if curr <= rem: rem -= curr; temp_inv = temp_inv.drop(idx)
                        else:
                            temp_inv.at[idx, '개수'] -= rem
                            temp_inv.at[idx, '총 무게'] = int(temp_inv.at[idx, '개수'] * u_w)
                            rem = 0
                    new_log = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item, "불출", int(rem_qty)]], columns=history.columns)
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=temp_inv.reset_index(drop=True))
                    conn.update(spreadsheet=SHEET_URL, worksheet="History", data=pd.concat([history, new_log], ignore_index=True))
                    st.success(f"✅ {item} 불출 완료!"); time.sleep(0.5); st.rerun()
