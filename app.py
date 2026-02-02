import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="부대 창고 현황판", layout="wide")

# 타이틀을 크게 배치
st.markdown("# 📋 창고 현황판 (기록용)")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["물품명", "개수", "유통기한", "총 무게", "단위"]
    )

if not st.session_state.inventory.empty:
    df = st.session_state.inventory.copy()
    
    # --- 1. 받아적기용 요약 (단위별 총합) ---
    st.subheader("📍 [1단계] 단위별 총량 (현황판 하단 기록용)")
    summary = df.groupby('단위')['총 무게'].sum()
    cols = st.columns(len(summary) if len(summary) > 0 else 1)
    for i, (unit, val) in enumerate(summary.items()):
        cols[i].metric(label=f"총 {unit}", value=f"{val} {unit}")
    
    st.divider()

    # --- 2. 유통기한 순 물품 리스트 (현황판 메인 기록용) ---
    st.subheader("📅 [2단계] 물품별 상세 (유통기한 빠른 순)")
    
    # 유통기한 기준으로 정렬 (적을 때 순서대로 적기 위함)
    df['유통기한_dt'] = pd.to_datetime(df['유통기한'])
    df = df.sort_values(by='유통기한_dt').drop(columns=['유통기한_dt'])

    # 표 형식이 받아적기 가장 깔끔하므로 큰 표로 출력
    st.table(df) # 일반 table이 글자가 더 크고 고정되어 있어 적기 편함

else:
    st.info("현재 등록된 물자가 없습니다.")

# --- 3. 사이드바: 입력창 (기존과 동일) ---
with st.sidebar:
    st.header("➕ 물자 입력")
    name = st.text_input("물품명")
    qty = st.number_input("개수", min_value=1)
    exp_date = st.date_input("유통기한")
    weight = st.number_input("단위당 무게", min_value=0.0)
    unit = st.selectbox("단위", ["kg", "g", "L", "mL"])
    
    if st.button("등록"):
        new_row = pd.DataFrame([[name, qty, exp_date.strftime('%Y-%m-%d'), weight * qty, unit]], 
                               columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
        st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
        st.rerun()

# --- 4. 삭제 기능 (하단) ---
if not st.session_state.inventory.empty:
    with st.expander("🗑️ 물자 삭제 (불출 시 사용)"):
        del_target = st.multiselect("삭제할 물자 선택", df["물품명"].unique())
        if st.button("삭제 실행"):
            st.session_state.inventory = st.session_state.inventory[~st.session_state.inventory["물품명"].isin(del_target)]
            st.rerun()
