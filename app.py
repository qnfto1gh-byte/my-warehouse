import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="부대 창고 현황판", layout="wide")

st.markdown("# 📋 창고 현황판 (기록용)")

# 데이터 저장 구조 초기화
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["물품명", "개수", "유통기한", "총 무게", "단위"]
    )

# 오늘 날짜
today = datetime.now().date()

# --- 1. 유통기한 임박 알림창 (D-Day 표시) ---
if not st.session_state.inventory.empty:
    df_alert = st.session_state.inventory.copy()
    df_alert['유통기한_dt'] = pd.to_datetime(df_alert['유통기한']).dt.date
    
    # 7일 이내 남은 데이터 필터링
    limit_date = today + timedelta(days=7)
    urgent_items = df_alert[df_alert['유통기한_dt'] <= limit_date].sort_values(by='유통기한_dt')
    
    if not urgent_items.empty:
        st.error("🚨 **유통기한 임박 물자 발생!**")
        for _, row in urgent_items.iterrows():
            d_day = (row['유통기한_dt'] - today).days
            d_day_text = f"D-{d_day}" if d_day > 0 else ("오늘 만료" if d_day == 0 else f"D+{-d_day} (만료)")
            st.write(f"⚠️ **{row['물품명']}** ({int(row['개수'])}{row['단위']}) - **{d_day_text}** ({row['유통기한']})")
        st.divider()

# --- 2. 신규 물자 등록 칸 ---
with st.expander("➕ 신규 물자 등록", expanded=False):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: name = st.text_input("물품명", key="input_name")
    with c2: qty = st.number_input("입고 개수", min_value=1, step=1, value=1, key="input_qty")
    with c3: exp_
