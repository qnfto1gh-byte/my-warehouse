import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# --- 사이드바 고정 ---
with st.sidebar:
    st.header("➕ 신규 물자 등록")
    name = st.text_input("물품명", key="n")
    qty = st.number_input("개수", min_value=1, step=1, key="q")
    
    # 1. 날짜 입력칸 (여기서는 안내 문구만 표시)
    d6 = st.text_input("유통기한 6자리", placeholder="예: 270917", key="d", max_chars=6)
    
    st.markdown("---") # 구분선으로 공간 분리
    
    # 2. 무게 및 단위
    wgt = st.number_input("단위당 무게", min_value=0, key="w")
    unit = st.selectbox("단위", ["g", "kg", "L", "mL"], key="u")

    # 3. 미리보기 및 등록 버튼 (입력창과 거리 두기)
    f_dt = ""
    if len(d6) == 6:
        try:
            f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
            datetime.strptime(f_dt, "%Y-%m-%d")
            # 입력창 바로 아래가 아닌 버튼 위에 작게 표시
            st.caption(f"✅ 확인된 날짜: {f_dt}")
        except:
            st.caption("❌ 유효하지 않은 날짜")
            f_dt = "error"

    if st.button("🚀 창고에 등록하기", use_container_width=True):
        if name and len(d6) == 6 and f_dt != "error":
            row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], 
                               columns=st.session_state.inventory.columns)
            st.session_state.inventory = pd.concat([st.session_state.inventory, row], ignore_index=True)
            st.rerun()
        else:
            st.error("입력값을 확인하세요.")

# --- 메인 화면 ---
st.title("📋 창고 현황판")

if not st.session_state.inventory.empty:
    df = st.session_state.inventory.
