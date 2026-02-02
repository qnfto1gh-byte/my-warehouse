import streamlit as st
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="우리집 창고 매니저", layout="wide")
st.title("📦 스마트 창고 관리 시스템")

# 데이터 저장용 세션 스테이트 초기화 (데이터베이스 역할)
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(
        columns=["물품명", "개수", "유통기한", "총 무게", "단위"]
    )

# 사이드바: 물건 등록
with st.sidebar:
    st.header("➕ 새 물구 등록")
    name = st.text_input("물품명")
    qty = st.number_input("개수", min_value=1, value=1)
    exp_date = st.date_input("유통기한", datetime.now())
    weight = st.number_input("무게(숫자만)", min_value=0.0)
    unit = st.selectbox("단위", ["kg", "g", "L", "mL"])
    
    if st.button("창고에 넣기"):
        new_data = pd.DataFrame([[name, qty, exp_date, weight * qty, unit]], 
                                columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
        st.session_state.inventory = pd.concat([st.session_state.inventory, new_data], ignore_index=True)
        st.success(f"{name} 등록 완료!")

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
