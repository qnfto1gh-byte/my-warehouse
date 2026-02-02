import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="부대 창고 현황판", layout="wide")

st.markdown("# 📋 창고 현황판 (기록용)")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["물품명", "개수", "유통기한", "총 무게", "단위"]
    )

if not st.session_state.inventory.empty:
    df = st.session_state.inventory.copy()
    
    # --- 1. 품목별 개별 총량 요약 (현황판 하단 기록용) ---
    st.subheader("📍 [1단계] 품목별 합계 (따로 보기)")
    # 품목명과 단위별로 그룹화하여 합계 계산
    item_summary = df.groupby(['물품명', '단위'])['총 무게'].sum().reset_index()
    
    summary_cols = st.columns(4) # 4열로 나누어 출력
    for idx, row in item_summary.iterrows():
        with summary_cols[idx % 4]:
            st.metric(label=f"{row['물품명']} 총량", value=f"{row['총 무게']} {row['단위']}")
    
    st.divider()

    # --- 2. 유통기한 순 물품 리스트 ---
    st.subheader("📅 [2단계] 물품별 상세 (유통기한 빠른 순)")
    df['유통기한_dt'] = pd.to_datetime(df['유통기한'])
    df = df.sort_values(by='유통기한_dt').drop(columns=['유통기한_dt'])
    
    # 인덱스를 1부터 시작하는 번호로 변경 (따라 적기 쉽게)
    df.index = range(1, len(df) + 1)
    st.table(df)

else:
    st.info("현재 등록된 물자가 없습니다.")

# --- 3. 사이드바: 입력창 ---
with st.sidebar:
    st.header("➕ 물자 입력")
    name = st.text_input("물품명 (예: 물, 간장)")
    qty = st.number_input("개수", min_value=1, step=1)
    exp_date = st.date_input("유통기한")
    weight = st.number_input("단위당 무게 (숫자만)", min_value=0.0)
    unit = st.selectbox("단위", ["kg", "g", "L", "mL"])
    
    if st.button("등록"):
        if name:
            new_row = pd.DataFrame([[name, qty, exp_date.strftime('%Y-%m-%d'), weight * qty, unit]], 
                                   columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.rerun()

# --- 4. 정교한 삭제 기능 (이름 + 유통기한 조합) ---
if not st.session_state.inventory.empty:
    with st.expander("🗑️ 물자 삭제 (유통기한 확인 후 삭제)"):
        # 삭제를 위해 '이름 (유통기한)' 형태의 리스트 생성
        df_for_del = st.session_state.inventory.copy()
        df_for_del['삭제옵션'] = df_for_del['물품명'] + " [" + df_for_del['유통기한'] + "]"
        
        selected_targets = st.multiselect("삭제할 항목을 선택하세요", df_for_del['삭제옵션'].unique())
        
        if st.button("선택 항목 삭제 실행"):
            # 선택된 옵션에 해당하지 않는 데이터만 남기기
            st.session_state.inventory = df_for_del[~df_for_del['삭제옵션'].isin(selected_targets)].drop(columns=['삭제옵션'])
            st.success("해당 물자가 삭제되었습니다.")
            st.rerun()
