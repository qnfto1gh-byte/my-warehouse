Streamlit Warehouse Management App (Big / Small Warehouse)

All users equal, no admin, correction("정정") only, full logs

import streamlit as st import pandas as pd from datetime import datetime, date

st.set_page_config(page_title="물류 현황판", layout="wide")

------------------ Session State Init ------------------

if "big" not in st.session_state: st.session_state.big = pd.DataFrame(columns=["품목", "수량", "유통기한"])

if "small" not in st.session_state: st.session_state.small = pd.DataFrame(columns=["품목", "수량", "유통기한"])

if "logs" not in st.session_state: st.session_state.logs = pd.DataFrame(columns=[ "시간", "사용자", "창고", "행동", "품목", "수량", "유통기한", "비고" ])

------------------ Helpers ------------------

def log(user, wh, action, item, qty, exp, note=""): st.session_state.logs.loc[len(st.session_state.logs)] = [ datetime.now(), user, wh, action, item, qty, exp, note ]

def expiry_color(d): if pd.isna(d): return "" days = (d - date.today()).days if days <= 3: return "background-color:#ffb3b3"  # red elif days <= 7: return "background-color:#ffd699"  # orange return ""

------------------ Header ------------------

st.title("📦 물류 관리 시스템")

user = st.text_input("사용자 이름", value="") mode = st.toggle("📊 현황판 모드")

warehouse_tab = st.radio("창고 선택", ["큰창고", "작은창고"], horizontal=True)

------------------ Big Warehouse ------------------

if warehouse_tab == "큰창고": st.subheader("🏢 큰 창고")

if not mode:
    with st.expander("➕ 입고"):
        item = st.text_input("품목명", key="b_in_item")
        qty = st.number_input("수량", min_value=1, step=1, key="b_in_qty")
        exp = st.date_input("유통기한", key="b_in_exp")
        if st.button("입고 실행"):
            st.session_state.big.loc[len(st.session_state.big)] = [item, qty, exp]
            log(user, "큰창고", "입고", item, qty, exp)
            st.success("입고 완료")

    with st.expander("📤 불출 → 작은창고"):
        idx = st.selectbox("불출 품목", st.session_state.big.index,
                           format_func=lambda x: st.session_state.big.loc[x, "품목"])
        out_qty = st.number_input("불출 수량", min_value=1, step=1)
        if st.button("불출"):
            row = st.session_state.big.loc[idx]
            st.session_state.big.at[idx, "수량"] -= out_qty
            st.session_state.small.loc[len(st.session_state.small)] = [
                row["품목"], out_qty, row["유통기한"]
            ]
            log(user, "큰창고", "불출", row["품목"], out_qty, row["유통기한"], "작은창고 이동")
            st.success("불출 완료")

styled = st.session_state.big.style.applymap(expiry_color, subset=["유통기한"])
st.dataframe(styled, use_container_width=True)

------------------ Small Warehouse ------------------

else: st.subheader("🧺 작은 창고")

if not mode:
    with st.expander("➕ 물류 추가"):
        item = st.text_input("품목명", key="s_in_item")
        qty = st.number_input("수량", min_value=1, step=1, key="s_in_qty")
        exp = st.date_input("유통기한", key="s_in_exp")
        if st.button("추가"):
            st.session_state.small.loc[len(st.session_state.small)] = [item, qty, exp]
            log(user, "작은창고", "추가", item, qty, exp)
            st.success("추가 완료")

    with st.expander("📉 소비"):
        idx = st.selectbox("소비 품목", st.session_state.small.index,
                           format_func=lambda x: st.session_state.small.loc[x, "품목"])
        use_qty = st.number_input("소비 수량", min_value=1, step=1)
        if st.button("소비"):
            row = st.session_state.small.loc[idx]
            st.session_state.small.at[idx, "수량"] -= use_qty
            log(user, "작은창고", "소비", row["품목"], use_qty, row["유통기한"])
            st.success("소비 완료")

styled = st.session_state.small.style.applymap(expiry_color, subset=["유통기한"])
st.dataframe(styled, use_container_width=True)

------------------ Logs ------------------

st.divider() st.subheader("📜 기록 조회")

start = st.date_input("시작 날짜", value=date.today()) end = st.date_input("종료 날짜", value=date.today())

mask = (st.session_state.logs["시간"].dt.date >= start) & (st.session_state.logs["시간"].dt.date <= end) st.dataframe(st.session_state.logs[mask], use_container_width=True)
