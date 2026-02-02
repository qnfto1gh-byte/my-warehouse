import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고 현황판", layout="wide")

st.markdown("# 📋 창고 현황판 (기록용)")

# 데이터 저장 구조
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["물품명", "개수", "유통기한", "총 무게", "단위"]
    )

# --- 1. 유통기한 임박 알림창 ---
if not st.session_state.inventory.empty:
    df_alert = st.session_state.inventory.copy()
    df_alert['유통기한_dt'] = pd.to_datetime(df_alert['유통기한'])
    limit_date = datetime.now() + timedelta(days=7)
    urgent_items = df_alert[df_alert['유통기한_dt'] <= limit_date].sort_values(by='유통기한_dt')
    
    if not urgent_items.empty:
        st.error("🚨 **유통기한 임박 물자 발생! (7일 이내)**")
        for _, row in urgent_items.iterrows():
            st.write(f"⚠️ **{row['물품명']}** ({row['개수']}{row['단위']}) - 유통기한: **{row['유통기한']}**")
        st.divider()

# --- 2. 품목별 개별 총량 요약 ---
if not st.session_state.inventory.empty:
    st.subheader("📍 [1단계] 품목별 합계")
    df = st.session_state.inventory.copy()
    item_summary = df.groupby(['물품명', '단위'])['총 무게'].sum().reset_index()
    
    summary_cols = st.columns(4)
    for idx, row in item_summary.iterrows():
        with summary_cols[idx % 4]:
            st.metric(label=f"{row['물품명']} 총량", value=f"{row['총 무게']} {row['단위']}")
    
    st.divider()

    # --- 3. 검색 및 상세 리스트 ---
    st.subheader("🔍 물자 검색 및 상세현황")
    search_term = st.text_input("찾으시는 물품명을 입력하세요", "")

    df['유통기한_dt'] = pd.to_datetime(df['유통기한'])
    df = df.sort_values(by='유통기한_dt').drop(columns=['유통기한_dt'])
    
    if search_term:
        df = df[df['물품명'].str.contains(search_term, case=False, na=False)]
    
    df.index = range(1, len(df) + 1)
    st.table(df)
else:
    st.info("현재 등록된 물자가 없습니다. 왼쪽 [➕ 물자 입력] 메뉴를 이용하세요.")

# --- 4. 사이드바: 입력창 (등록 후 초기화 기능 추가) ---
with st.sidebar:
    st.header("➕ 물자 입력")
    # key를 사용하여 등록 후 값을 초기화할 수 있게 설정
    name = st.text_input("물품명", key="input_name")
    qty = st.number_input("입고 개수", min_value=1, step=1, key="input_qty")
    exp_date = st.date_input("유통기한", datetime.now(), key="input_date")
    weight = st.number_input("단위당 무게", min_value=0.0, key="input_weight")
    unit = st.selectbox("단위", ["kg", "g", "L", "mL"], key="input_unit")
    
    if st.button("창고에 등록하기"):
        if name:
            new_row = pd.DataFrame([[name, qty, exp_date.strftime('%Y-%m-%d'), weight * qty, unit]], 
                                   columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            
            # 중앙 화면에 성공 메시지를 띄우기 위해 세션 스테이트에 저장
            st.toast(f"✅ {name} 등록 완료!", icon="📦")
            st.success(f"'{name}'이(가) 현황판에 추가되었습니다.")
            
            # 입력 칸을 비우기 위해 페이지 재실행
            st.rerun()
        else:
            st.warning("물품명을 입력해야 등록이 가능합니다.")

# --- 5. 개수 지정 삭제 기능 ---
if not st.session_state.inventory.empty:
