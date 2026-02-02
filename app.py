import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="우리집 창고 매니저", layout="wide")
st.title("📦 스마트 창고 관리 시스템")

# 데이터 저장용 세션 스테이트
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["물품명", "개수", "유통기한", "총 무게", "단위"]
    )

# --- 유통기한 임박 알림 기능 ---
if not st.session_state.inventory.empty:
    df = st.session_state.inventory.copy()
    # 날짜 형식으로 변환
    df['유통기한'] = pd.to_datetime(df['유통기한'])
    today = datetime.now()
    
    # 오늘로부터 7일 뒤 날짜 계산
    next_week = today + timedelta(days=7)
    
    # 7일 이내 남은 물건 필터링 (이미 지난 것도 포함)
    urgent_items = df[df['유통기한'] <= next_week]
    
    if not urgent_items.empty:
        st.error(f"⚠️ 유통기한 임박 주의! (7일 이내)")
        # 보기 좋게 날짜만 출력하도록 수정 후 표시
        urgent_display = urgent_items.copy()
        urgent_display['유통기한'] = urgent_display['유통기한'].dt.strftime('%Y-%m-%d')
        st.dataframe(urgent_display, use_container_width=True)
        st.divider()

# 사이드바: 물건 등록 (동일)
with st.sidebar:
    st.header("➕ 새 물건 등록")
    name = st.text_input("물품명")
    qty = st.number_input("개수", min_value=1, value=1)
    exp_date = st.date_input("유통기한", datetime.now())
    weight = st.number_input("무게(숫자만)", min_value=0.0)
    unit = st.selectbox("단위", ["kg", "g", "L", "mL"])
    
    if st.button("창고에 넣기"):
        new_data = pd.DataFrame([[name, qty, exp_date.strftime('%Y-%m-%d'), weight * qty, unit]], 
                                columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
        st.session_state.inventory = pd.concat([st.session_state.inventory, new_data], ignore_index=True)
        st.success(f"{name} 등록 완료!")
        st.rerun() # 화면 즉시 새로고침

# 메인 화면: 검색 및 현황
st.subheader("🔍 물건 찾기")
search_q = st.text_input("찾으시는 물건 이름을 입력하세요")

if search_q:
    result = st.session_state.inventory[st.session_state.inventory["물품명"].str.contains(search_q)]
    if not result.empty:
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("찾으시는 물건이 창고에 없습니다.")

st.subheader("📊 전체 재고 현황")
st.table(st.session_state.inventory)
