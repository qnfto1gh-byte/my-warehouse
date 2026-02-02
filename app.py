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

# --- 2. 신규 물자 등록 칸 (중앙 배치) ---
with st.expander("➕ 신규 물자 등록", expanded=False):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: 
        name = st.text_input("물품명", key="input_name")
    with c2: 
        qty = st.number_input("입고 개수", min_value=1, step=1, value=1, key="input_qty")
    with c3: 
        exp_date = st.date_input("유통기한", datetime.now(), key="input_date")
    
    c4, c5 = st.columns([1, 1])
    with c4: 
        weight = st.number_input("단위당 무게 (숫자만)", min_value=0, step=1, value=0, key="input_weight")
    with c5: 
        unit = st.selectbox("단위", ["g", "kg", "L", "mL"], key="input_unit")
    
    if st.button("🚀 창고에 등록하기", use_container_width=True):
        if name:
            new_row = pd.DataFrame([[name, int(qty), exp_date.strftime('%Y-%m-%d'), int(weight * qty), unit]], 
                                   columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.success(f"✅ {name} 등록 완료!")
            st.rerun()
        else:
            st.warning("물품명을 입력해주세요.")

st.divider()

# --- 3. 품목별 요약 및 상세 리스트 (접기/펴기) ---
st.subheader("🔍 품목별 현황 (클릭 시 상세 유통기한 확인)")

if st.session_state.inventory.empty:
    st.info("현재 등록된 물자가 없습니다.")
else:
    df_main = st.session_state.inventory.copy()
    df_main['유통기한_dt'] = pd.to_datetime(df_main['유통기한']).dt.date
    
    search_term = st.text_input("물품명 검색", "")
    if search_term:
        df_main = df_main[df_main['물품명'].str.contains(search_term, case=False)]

    unique_items = df_main['물품명'].unique()

    for item in unique_items:
        item_data = df_main[df_main['물품명'] == item].sort_values('유통기한_dt')
        
        total_qty = item_data['개수'].sum()
        total_weight = item_data['총 무게'].sum()
        earliest_date = item_data['유통기한_dt'].min()
        unit_type = item_data['단위'].iloc[0]
        
        # D-Day 계산
        d_day_val = (earliest_date - today).days
        if d_day_val > 0:
            d_day_label = f" (D-{d_day_val})"
        elif d_day_val == 0:
            d_day_label = " (오늘 만료!)"
        else:
            d_day_label =
