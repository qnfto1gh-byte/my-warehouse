import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="부대 창고 현황판", layout="wide")

st.markdown("# 📋 창고 현황판 (기록용)")

# 데이터 저장 구조
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["물품명", "개수", "유통기한", "총 무게", "단위"]
    )

# --- 1. 품목별 개별 총량 요약 ---
if not st.session_state.inventory.empty:
    st.subheader("📍 [1단계] 품목별 합계")
    df = st.session_state.inventory.copy()
    item_summary = df.groupby(['물품명', '단위'])['총 무게'].sum().reset_index()
    
    summary_cols = st.columns(4)
    for idx, row in item_summary.iterrows():
        with summary_cols[idx % 4]:
            st.metric(label=f"{row['물품명']} 총량", value=f"{row['총 무게']} {row['단위']}")
    
    st.divider()

    # --- 2. 유통기한 순 물품 리스트 ---
    st.subheader("📅 [2단계] 물품별 상세 (유통기한 빠른 순)")
    df['유통기한_dt'] = pd.to_datetime(df['유통기한'])
    df = df.sort_values(by='유통기한_dt').drop(columns=['유통기한_dt'])
    df.index = range(1, len(df) + 1)
    st.table(df)
else:
    st.info("현재 등록된 물자가 없습니다.")

# --- 3. 사이드바: 입력창 ---
with st.sidebar:
    st.header("➕ 물자 입력")
    name = st.text_input("물품명")
    qty = st.number_input("입고 개수", min_value=1, step=1)
    exp_date = st.date_input("유통기한")
    weight = st.number_input("단위당 무게", min_value=0.0)
    unit = st.selectbox("단위", ["kg", "g", "L", "mL"])
    
    if st.button("등록"):
        if name:
            new_row = pd.DataFrame([[name, qty, exp_date.strftime('%Y-%m-%d'), weight * qty, unit]], 
                                   columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.rerun()

# --- 4. [수정] 개수 지정 삭제 기능 ---
if not st.session_state.inventory.empty:
    with st.expander("🗑️ 물자 불출 (개수 지정 삭제)"):
        # 삭제 대상 식별을 위해 이름+날짜 조합 생성
        df_del = st.session_state.inventory.copy()
        df_del['display'] = df_del['물품명'] + " [" + df_del['유통기한'] + "]"
        
        target = st.selectbox("불출할 물자를 선택하세요", df_del['display'].unique())
        
        # 선택한 물자의 현재 정보 가져오기
        selected_info = df_del[df_del['display'] == target].iloc[0]
        current_qty = selected_info['개수']
        unit_weight = selected_info['총 무게'] / current_qty # 단위당 무게 역산
        
        st.write(f"현재 수량: **{current_qty}개**")
        minus_qty = st.number_input("불출(삭제)할 개수", min_value=1, max_value=int(current_qty), step=1)
        
        if st.button("불출 실행"):
            idx = df_del[df_del['display'] == target].index[0]
            
            if minus_qty >= current_qty:
                # 전량 삭제
                st.session_state.inventory = st.session_state.inventory.drop(idx).reset_index(drop=True)
                st.success(f"{target} 전량 불출 완료!")
            else:
                # 일부 삭제 (수량 및 총 무게 업데이트)
                st.session_state.inventory.at[idx, '개수'] -= minus_qty
                st.session_state.inventory.at[idx, '총 무게'] = st.session_state.inventory.at[idx, '개수'] * unit_weight
                st.success(f"{target} {minus_qty}개 불출 완료! (남은 수량: {current_qty - minus_qty}개)")
            st.rerun()
