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
    df_main = st.session_state.inventory.copy()
    item_summary = df_main.groupby(['물품명', '단위'])['총 무게'].sum().reset_index()
    
    summary_cols = st.columns(4)
    for idx, row in item_summary.iterrows():
        with summary_cols[idx % 4]:
            st.metric(label=f"{row['물품명']} 총량", value=f"{row['총 무게']} {row['단위']}")
    
    st.divider()

    # --- 3. 검색 및 상세 리스트 ---
    st.subheader("🔍 물자 검색 및 상세현황")
    search_term = st.text_input("찾으시는 물품명을 입력하세요", "")

    df_main['유통기한_dt'] = pd.to_datetime(df_main['유통기한'])
    df_main = df_main.sort_values(by='유통기한_dt').drop(columns=['유통기한_dt'])
    
    if search_term:
        df_main = df_main[df_main['물품명'].str.contains(search_term, case=False, na=False)]
    
    df_main.index = range(1, len(df_main) + 1)
    st.table(df_main)
else:
    st.info("현재 등록된 물자가 없습니다. 왼쪽 [➕ 물자 입력] 메뉴를 이용하세요.")

# --- 4. 사이드바: 입력창 ---
with st.sidebar:
    st.header("➕ 물자 입력")
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
            st.success(f"✅ {name} 등록 완료!")
            st.rerun()
        else:
            st.warning("물품명을 입력해주세요.")

# --- 5. 개수 지정 삭제 기능 ---
if not st.session_state.inventory.empty:
    with st.expander("🗑️ 물자 불출 (개수 지정 삭제)"):
        df_del = st.session_state.inventory.copy()
        df_del['display'] = df_del['물품명'] + " [" + df_del['유통기한'] + "]"
        target = st.selectbox("불출할 물자를 선택하세요", df_del['display'].unique())
        
        selected_info = df_del[df_del['display'] == target].iloc[0]
        curr_qty = selected_info['개수']
        u_weight = selected_info['총 무게'] / curr_qty
        
        st.write(f"현재 수량: **{curr_qty}개**")
        minus_qty = st.number_input("불출할 개수", min_value=1, max_value=int(curr_qty), step=1)
        
        if st.button("불출 실행"):
            idx = df_del[df_del['display'] == target].index[0]
            if minus_qty >= curr_qty:
                st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
            else:
                st.session_state.inventory.at[idx, '개수'] -= minus_qty
                st.session_state.inventory.at[idx, '총 무게'] = st.session_state.inventory.at[idx, '개수'] * u_weight
            st.rerun()
