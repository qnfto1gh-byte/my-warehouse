import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="부식 관리 마스터", layout="wide")

# 포커스 이동 및 숫자패드 스크립트 (천지인 최적화)
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

st.title("🚛 부식 관리 & 일별 달력 현황")

# 1. 일별 현황 달력 창 (새로 추가된 기능)
with st.expander("📅 일별 입고/불출 확인 (달력)", expanded=False):
    # 날짜 선택기
    selected_date = st.date_input("확인할 날짜를 선택하세요", value=today)
    
    if not st.session_state.history.empty:
        df_h = st.session_state.history.copy()
        df_h['날짜'] = pd.to_datetime(df_h['날짜']).dt.date
        
        # 선택한 날짜의 데이터만 필터링
        day_data = df_h[df_h['날짜'] == selected_date]
        
        if not day_data.empty:
            st.write(f"### 🗓️ {selected_date} 내역")
            
            # 보기 좋게 + / - 표시
            for _, row in day_data.iterrows():
                sign = "➕" if row['유형'] == "입고" else "➖"
                color = "blue" if row['유형'] == "입고" else "red"
                st.markdown(f"**{sign} {row['물품명']} : :{color}[{row['유형']} {row['수량']}개]**")
            
            # 당일 합계 요약
            st.divider()
            summary = day_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
            st.dataframe(summary, use_container_width=True)
        else:
            st.info(f"{selected_date}에는 기록된 내역이 없습니다.")
    else:
        st.info("데이터가 없습니다.")

st.divider()

# 2. 부식 등록 (입고)
with st.expander("➕ 신규 부식 수령", expanded=True):
    with st.form("quick_input", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("물품명")
        qty = col2.number_input("입고 수량", min_value=1, value=1)
        d6 = st.text_input("유통기한 6자리 (YYMMDD)")
        
        submit = st.form_submit_button("부식 등록", use_container_width=True)
        
        if submit and name and len(d6) == 6:
            try:
                f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                # 재고 업데이트
                new_row = pd.DataFrame([[name, int(qty), f_dt, 0, "g"]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
                # 이력(History) 업데이트
                new_log = pd.DataFrame([[today, name, "입고", int(qty)]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                
                st.success("✅ 등록 완료!")
                time.sleep(1)
                st.rerun()
            except: st.error("날짜를 확인해 주세요.")

st.divider()

# 3. 주간 통계 및 재고 관리
tab1, tab2 = st.tabs(["📊 주간 통계", "📦 현재고 및 불출"])

with tab1:
    # (주간 통계 로직 - 이전과 동일)
    st.subheader("이번 주 전체 요약")
    # ... (생략)

with tab2:
    # 재고 리스트 표시 및 불출 버튼
    search = st.text_input("🔍 재고 검색")
    if not st.session_state.inventory.empty:
        df_inv = st.session_state.inventory.copy()
        items = [i for i in df_inv['물품명'].unique() if search.lower() in i.lower()]
        
        for item in items:
            i_df = df_inv[df_inv['물품명'] == item]
            t_qty = i_df['개수'].sum()
            with st.expander(f"{item} (현재 {t_qty}개)"):
                st.table(i_df[["개수", "유통기한"]])
                
                # 불출 수량 입력
                del_q = st.number_input(f"{item} 불출 수량", min_value=1, max_value=int(t_qty), key=f"q_{item}")
                if st.button(f"{item} 불출 확정", key=f"b_{item}"):
                    # 📊 불출 이력 남기기 (통계용)
                    new_log = pd.DataFrame([[today, item, "불출", int(del_q)]], columns=st.session_state.history.columns)
                    st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                    
                    # 실제 재고 차감 로직 (생략된 기존 로직 사용)
                    # ... (재고 차감 후)
                    st.rerun()
