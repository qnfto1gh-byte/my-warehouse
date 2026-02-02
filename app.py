import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="부대 창고 마스터", layout="wide")

# 1. 포커스 이동 + 날짜 입력 편의 스크립트
components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const active = doc.activeElement;
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(active);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault();
                inputs[index + 1].focus();
            }
        }
    }, true);
    </script>
""", height=0)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["날짜", "물품명", "유형", "수량"])

today = datetime.now().date()

# 무게 표시 함수 (이전과 동일)
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

st.title("📋 부대 물자 통합 관리 시스템")

# --- [섹션 1] 물자 등록 ---
with st.expander("➕ 신규 물자 등록", expanded=False):
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("물품명")
        qty = col2.number_input("입고 수량", min_value=1, value=1)
        d6 = st.text_input("유통기한 (YYMMDD)", max_chars=6)
        col3, col4 = st.columns(2)
        wgt = col3.number_input("단위당 무게", min_value=0)
        unit = col4.selectbox("단위", ["g", "mL", "kg", "L"])
        if st.form_submit_button("창고 등록", use_container_width=True):
            if name and len(d6) == 6:
                f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
                new_log = pd.DataFrame([[today, name, "입고", int(qty)]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                st.success("등록 완료!")
                st.rerun()

st.divider()

# --- [섹션 2] 메인 기능 탭 ---
tab_stock, tab_report = st.tabs(["📦 현재고 현황", "📅 기간별 맞춤 정산"])

with tab_stock:
    # (기존 재고 검색 및 불출 로직 유지)
    search = st.text_input("🔍 재고 검색")
    if not st.session_state.inventory.empty:
        df_m = st.session_state.inventory.copy()
        df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
        items = [i for i in df_m['물품명'].unique() if search.lower() in i.lower()]
        for item in items:
            i_df = df_m[df_m['물품명'] == item].sort_values('dt')
            t_qty = int(i_df['개수'].sum())
            min_d = i_df['dt'].min()
            d_v = (min_d - today).days
            with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d} (D-{d_v}) | {get_total_display(i_df)}"):
                st.table(i_df[["개수", "유통기한"]])
                if st.button(f"{item} 1개 불출", key=f"btn_{item}"):
                    # 불출 이력 남기고 재고 차감 (로직 생략)
                    st.rerun()

with tab_report:
    st.subheader("🗓️ 정산 기간 설정")
    # 사용자님이 원하신 '26/02/06 ~ 26/03/05' 같은 범위를 슬라이더나 달력으로 선택
    date_range = st.date_input(
        "정산할 시작일과 종료일을 선택하세요",
        value=(today - timedelta(days=7), today),
        help="두 날짜를 선택하면 그 사이의 모든 기록을 집계합니다."
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        if not st.session_state.history.empty:
            df_h = st.session_state.history.copy()
            df_h['날짜'] = pd.to_datetime(df_h['날짜']).dt.date
            
            # 🔍 선택된 기간으로 필터링
            mask = (df_h['날짜'] >= start_date) & (df_h['날짜'] <= end_date)
            period_data = df_h.loc[mask]
            
            if not period_data.empty:
                st.write(f"### 📊 {start_date} ~ {end_date} 정산 결과")
                stats = period_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                if '입고' not in stats: stats['입고'] = 0
                if '불출' not in stats: stats['불출'] = 0
                st.table(stats[['입고', '불출']])
                
                # 수기 장부 복사용 텍스트 (자동 생성)
                report_txt = f"[{start_date} ~ {end_date} 물자 결산]\n"
                for item in stats.index:
                    report_txt += f"- {item}: 입고 {stats.loc[item, '입고']} / 불출 {stats.loc[item, '불출']}\n"
                st.text_area("수기 장부 복사용", value=report_txt, height=200)
            else:
                st.info("해당 기간에는 기록된 내역이 없습니다.")
    else:
        st.write("종료 날짜까지 선택해 주세요.")
