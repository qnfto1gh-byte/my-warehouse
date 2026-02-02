import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import time

# 앱 설정
st.set_page_config(page_title="창고관리", layout="wide")

# [기능 4, 5, 7] 엔터 이동 + 숫자패드 + 0 자동삭제 및 전체선택 스크립트
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

# --- [중요] 구글 시트 주소를 꼭 본인 것으로 수정하세요 ---
SHEET_URL = "여기에_구글_시트_주소를_넣으세요"

conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로드 (캐시 없이 실시간 반영)
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
today = datetime.now().date()

# [기능 1] 총 무게 표시 로직
def get_total_display(df_item):
    total_val = 0
    unit_type = "" 
    for _, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        total_val += val * 1000 if u in ["L", "kg"] else val
        unit_type = "L" if u in ["L", "mL"] else "kg"
    if total_val >= 1000:
        return f"{total_val/1000:.2f}{unit_type}".replace(".00", "")
    return f"{int(total_val)}{'mL' if unit_type == 'L' else 'g'}"

st.title("📦 창고관리 시스템")

# [기능 3] 작업로그 (접이식 + 날짜별 그룹화)
with st.expander("🔍 작업로그 보기", expanded=False):
    if not history.empty:
        df_h = history.copy()
        df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
        for d in sorted(df_h['날짜'].unique(), reverse=True):
            st.markdown(f"**📅 {d}**")
            st.table(df_h[df_h['날짜'] == d].sort_values("일시", ascending=False)[["일시", "물품명", "유형", "수량"]])
    else: st.info("기록된 로그가 없습니다.")

st.divider()

# [기능 6] 신규 물자 등록 (날짜 오류 방지 로직)
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("물품명")
        qty = c2.number_input("입고 수량", min_value=0, value=0, step=1)
        c3, c4 = st.columns(2)
        d6 = c3.text_input("유통기한 (YYMMDD)", max_chars=6)
        wgt = c4.number_input("단위당 무게/부피", min_value=0, value=0, step=1)
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])
        
        if st.form_submit_button("🚀 등록하기", use_container_width=True):
            if name and len(d6) == 6:
                try:
                    f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                    new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=inventory.columns)
                    inventory = pd.concat([inventory, new_inv], ignore_index=True)
                    new_log = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, "입고", int(qty), "정상"]], columns=history.columns)
                    history = pd.concat([history, new_log], ignore_index=True)
                    
                    conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=inventory)
                    conn.update(spreadsheet=SHEET_URL, worksheet="History", data=history)
                    st.success(f"✅ {name} {qty}개 등록 완료!")
                    time.sleep(0.5); st.rerun()
                except: st.error("❌ 날짜 형식을 확인해주세요 (예: 260228)")
            else: st.warning("⚠️ 모든 빈칸을 채워주세요.")

st.divider()

# [기능 2] 현재고 현황 및 검색
st.subheader("📦 현재 창고 재고 현황")
search = st.text_input("🔍 물품 검색", placeholder="물품명을 입력하면 아래 목록이 필터링됩니다.")

if not inventory.empty:
    df_m = inventory.copy()
    items = [i for i in df_m['물품명'].unique() if search.lower() in str(i).lower()]
    
    for item in items:
        i_df = df_m[df_m['물품명'] == item].copy()
        i_df['dt'] = pd.to_datetime(i_df['유통기한']).dt.date
        i_df = i_df.sort_values('dt')
        t_qty = int(i_df['개수'].sum())
        min_d = i_df['dt'].min()
        
        # [기능 1] 제목에 총 무게 표시
        with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d} (D-{(min_d-today).days}) | {get_total_display(i_df)}"):
            st.table(i_df[["개수", "유통기한"]])
            c1, c2 = st.columns([2, 1])
            rem_qty = c1.number_input(f"불출 수량", min_value=1, max_value=t_qty, key=f"del_{item}", value=1)
            if c2.button("불출 확정", key=f"btn_{item}"):
                # 선입선출(FIFO) 차감 로직
                rem = rem_qty
                temp_inv = inventory.copy()
                for idx in i_df.index:
                    if rem <= 0: break
                    curr = temp_inv.at[idx, '개수']
                    u_w = temp_inv.at[idx, '총 무게'] / curr
                    if curr <= rem:
                        rem -= curr; temp_inv = temp_inv.drop(idx)
                    else:
                        temp_inv.at[idx, '개수'] -= rem
                        temp_inv.at[idx, '총 무게'] = int(temp_inv.at[idx, '개수'] * u_w)
                        rem = 0
                
                # 로그 기록 및 저장
                new_log = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item, "불출", int(rem_qty), "정상"]], columns=history.columns)
                history = pd.concat([history, new_log], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="Inventory", data=temp_inv.reset_index(drop=True))
                conn.update(spreadsheet=SHEET_URL, worksheet="History", data=history)
                st.rerun()
else:
    st.info("현재 재고가 없습니다. 물품을 등록해주세요.")
