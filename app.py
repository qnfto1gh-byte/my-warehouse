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
            st.write(f"⚠️ **{row['물품명']}** ({int(row['개수'])}{row['단위']}) - 유통기한: **{row['유통기한']}**")
        st.divider()

# --- 2. 신규 물자 등록 칸 ---
with st.expander("➕ 신규 물자 등록", expanded=False):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: name = st.text_input("물품명", key="input_name")
    with c2: qty = st.number_input("입고 개수", min_value=1, step=1, value=1, key="input_qty")
    with c3: exp_date = st.date_input("유통기한", datetime.now(), key="input_date")
    
    c4, c5 = st.columns([1, 1])
    with c4: weight = st.number_input("단위당 무게 (숫자만)", min_value=0, step=1, value=0, key="input_weight")
    with c5: unit = st.selectbox("단위", ["g", "kg", "L", "mL"], key="input_unit")
    
    if st.button("🚀 창고에 등록하기", use_container_width=True):
        if name:
            new_row = pd.DataFrame([[name, int(qty), exp_date.strftime('%Y-%m-%d'), int(weight * qty), unit]], 
                                   columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
            st.success(f"✅ {name} 등록 완료!")
            st.rerun()

st.divider()

# --- 3. 품목별 요약 및 상세 리스트 (접기/펴기) ---
st.subheader("🔍 품목별 현황 (클릭 시 상세 유통기한 확인)")

if st.session_state.inventory.empty:
    st.info("현재 등록된 물자가 없습니다.")
else:
    df_main = st.session_state.inventory.copy()
    df_main['유통기한_dt'] = pd.to_datetime(df_main['유통기한'])
    
    # 검색 기능
    search_term = st.text_input("물품명 검색", "")
    if search_term:
        df_main = df_main[df_main['물품명'].str.contains(search_term, case=False)]

    # 품목 리스트 추출
    unique_items = df_main['물품명'].unique()

    for item in unique_items:
        item_data = df_main[df_main['물품명'] == item].sort_values('유통기한_dt')
        
        # 요약 정보 계산
        total_qty = item_data['개수'].sum()
        total_weight = item_data['총 무게'].sum()
        earliest_exp = item_data['유통기한'].min()
        unit_type = item_data['단위'].iloc[0]

        # 아코디언 형태로 한 줄 요약 표시
        with st.expander(f"📦 **{item}** | 총 {int(total_qty)}개 | 가장 빠른 유통기한: {earliest_exp} | 총 {int(total_weight)}{unit_type}"):
            # 펼쳤을 때 보여줄 상세 표
            display_data = item_data[["개수", "유통기한", "총 무게", "단위"]].copy()
            display_data.index = range(1, len(display_data) + 1)
            st.table(display_data.style.format({"개수": "{:.0f}", "총 무게": "{:.0f}"}))
            
            # 해당 품목 내 특정 유통기한 삭제 기능
            st.markdown("---")
            st.caption(f"📍 {item} 불출 관리")
            del_target = st.selectbox(f"불출할 {item}의 유통기한 선택", item_data['유통기한'].unique(), key=f"del_select_{item}")
            minus_qty = st.number_input("불출 개수", min_value=1, step=1, key=f"minus_qty_{item}")
            
            if st.button(f"{item} 불출 실행", key=f"del_btn_{item}"):
                # 선택한 품목 + 선택한 유통기한의 인덱스 찾기
                target_idx = item_data[item_data['유통기한'] == del_target].index[0]
                current_val = st.session_state.inventory.at[target_idx, '개수']
                u_weight = st.session_state.inventory.at[target_idx, '총 무게'] / current_val
                
                if minus_qty >= current_val:
                    st.session_state.inventory = st.session_state.inventory.drop(target_idx).reset_index(drop=True)
                else:
                    st.session_state.inventory.at[target_idx, '개수'] -= minus_qty
                    st.session_state.inventory.at[target_idx, '총 무게'] = int(st.session_state.inventory.at[target_idx, '개수'] * u_weight)
                st.rerun()

