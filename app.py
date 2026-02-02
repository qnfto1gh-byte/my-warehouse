import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="부식 관리 마스터", layout="wide")

# (생략: 기존 천지인 최적화 스크립트)
components.html("""<script>...</script>""", height=0)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["날짜", "물품명", "유형", "수량"])

today = datetime.now().date()

st.title("🚛 일별 부식 수지 타산")

# --- 📅 여기에 달력창이 바로 보이게 수정했습니다 ---
st.subheader("🗓️ 날짜별 입고(+) 및 불출(-) 현황")
# 달력을 누르면 날짜를 바꿀 수 있습니다.
selected_date = st.date_input("날짜 선택", value=today)

if not st.session_state.history.empty:
    df_h = st.session_state.history.copy()
    df_h['날짜'] = pd.to_datetime(df_h['날짜']).dt.date
    day_data = df_h[df_h['날짜'] == selected_date]
    
    if not day_data.empty:
        # 일별 리스트 시각화
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"➕ {selected_date} 입고 내역")
            in_data = day_data[day_data['유형'] == "입고"]
            if not in_data.empty:
                for _, r in in_data.iterrows():
                    st.write(f"✅ {r['물품명']} : +{r['수량']}개")
            else: st.write("없음")
            
        with c2:
            st.error(f"➖ {selected_date} 불출 내역")
            out_data = day_data[day_data['유형'] == "불출"]
            if not out_data.empty:
                for _, r in out_data.iterrows():
                    st.write(f"❌ {r['물품명']} : -{r['수량']}개")
            else: st.write("없음")
    else:
        st.warning(f"💡 {selected_date}에는 기록이 없습니다.")
else:
    st.info("데이터를 먼저 입력해 주세요!")

st.divider()

# --- 이하 등록 및 재고 관리 로직 동일 ---
# ... (생략)
