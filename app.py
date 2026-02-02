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
        with st.container():
            st.error("🚨 **유통기한 임박 물자 발생! (7일 이내)**")
            for _, row in urgent_items.iterrows():
                st.write(f"⚠️ **{row['물품명']}** ({int(row['개수'])}{row['단위']}) - 유통기한: **{row['유통기한']}**")
            st.divider()

# --- 2. 물자 입력 칸 (소수점 제거 및 정수 설정) ---
with st.expander("➕ 신규 물자 등록 (클릭해서 열기/닫기)", expanded=False):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        name = st.text_input("물품명", key="input_name")
    with c2:
        # step=1로 설정하여 정수 입력 유도
        qty = st.number_input("입고 개수", min_value=1, step=1, value=1, key="input_qty")
    with c3:
        exp_date = st.date_input("유통기한", datetime.now(), key="input_date")
    
    c4, c5 = st.columns([1, 1])
    with c4:
        # value=0, step=1로 설정하여 기본 소수점 제거
        weight = st.number_input("단위당 무게 (숫자만)", min_value=0, step=1, value=0, key="input_weight")
    with c5:
        unit = st.selectbox("단위", ["g", "kg", "L", "mL"], key="input_unit")
    
    if st.button("🚀 창고에 등록하기", use_container_width=True):
        if name:
            # 계산 결과도 정수로 변환하여 저장
            total_w = int(weight * qty)
            new_row = pd.DataFrame([[name, int(qty), exp_date.strftime('%Y-%m-%d'), total_w, unit]], 
                                   columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.success(f"✅ {name} 등록 완료!")
            st.rerun()
        else:
            st.warning("물품명을 입력해주세요.")

st.divider()

# --- 3. 품목별 개별 총량 요약 ---
if not st.session_state.inventory.empty:
    st.subheader("📍 [1단계] 품목별 합계")
    df_main = st.session_state.inventory.copy()
    # 숫자 데이터 정수형으로 변환
    df_main['개수'] = df_main['개수'].astype(int)
    df_main['총 무게'] = df_main['총 무게'].astype(int)
    
    item_summary = df_main.groupby(['물품명', '단위'])['총 무게'].sum().reset_index()
    
    summary_cols = st.columns(4)
    for idx, row in item_summary.iterrows():
        with summary_cols[idx % 4]:
            st.metric(label=f"{row['물품명']} 총량", value=f"{int(row['총 무게'])}{row['단위']}")
    
    st.divider()

    # --- 4. 검색 및 상세 리스트 ---
    st.subheader("🔍 물자 검색 및 상세현황")
    search_term = st.text_input("찾으시는 물품명을 입력하세요", "")

    df_main['유통기한_dt'] = pd.to_datetime(df_main['유통기한'])
    df_main = df_main.sort_values(by='유통기한_dt').drop(columns=['유통기한_dt'])
    
    if search_term:
        df_main = df_main[df_main['물품명'].str.contains(search_term, case=False, na=False)]
    
    df_main.index = range(1, len(df_main) + 1)
    # 표 출력 시 소수점 없이 정수로 표시
    st.table(df_main.style.format({"개수": "{:.0f}", "총 무게": "{:.0f}"}))

    # --- 5. 개수 지정 삭제 기능 ---
    with st.expander("🗑️ 물자 불출 (개수 지정 삭제)"):
        df_del = st.session_state.inventory.copy()
        df_del['display'] = df_del['물품명'] + " [" + df_del['유통기한'] + "]"
