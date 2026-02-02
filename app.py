import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# 1. 앱 설정
st.set_page_config(page_title="부식 관리 통합 시스템", layout="wide")

# 데이터 초기화 (재고와 기록을 따로 관리하지만 서로 연동됨)
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["날짜", "물품명", "유형", "수량"])

today = datetime.now().date()

# -------------------------------------------
# [섹션 1] 신규 부식 등록 (월/수/금 수령 시)
# -------------------------------------------
with st.expander("➕ 1. 부식 등록 (여기서 넣으면 창고+달력 동시 반영)", expanded=True):
    with st.form("input_form", clear_on_submit=True):
        name = st.text_input("물품명")
        qty = st.number_input("수량", min_value=1, value=1)
        d6 = st.text_input("유통기한 6자리")
        if st.form_submit_button("등록하기"):
            f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
            # 창고에 플러스
            new_inv = pd.DataFrame([[name, int(qty), f_dt]], columns=st.session_state.inventory.columns)
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
            # 달력에 플러스 기록
            new_log = pd.DataFrame([[today, name, "입고", int(qty)]], columns=st.session_state.history.columns)
            st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
            st.success("등록 완료!")
            time.sleep(1)
            st.rerun()

# -------------------------------------------
# [섹션 2] 일별 수지 타산 (달력 확인)
# -------------------------------------------
st.subheader("📅 2. 일별 기록 (달력)")
selected_date = st.date_input("날짜를 선택해 보세요", value=today)

day_data = st.session_state.history[pd.to_datetime(st.session_state.history['날짜']).dt.date == selected_date]

if not day_data.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.write("📈 **입고 (+)**")
        for _, r in day_data[day_data['유형']=="입고"].iterrows():
            st.write(f"- {r['물품명']} : +{r['수량']}")
    with col2:
        st.write("📉 **불출 (-)**")
        for _, r in day_data[day_data['유형']=="불출"].iterrows():
            st.write(f"- {r['물품명']} : -{r['수량']}")
else:
    st.info("해당 날짜에 기록이 없습니다.")

# -------------------------------------------
# [섹션 3] 현재 창고 재고 현황
# -------------------------------------------
st.subheader("📦 3. 현재 창고 재고")
if not st.session_state.inventory.empty:
    st.dataframe(st.session_state.inventory, use_container_width=True)
    # 여기서 불출 버튼을 만들면 자동으로 '달력'에 마이너스 기록이 남게 됩니다.
