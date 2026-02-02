import streamlit as st
import pandas as pd
# [수정] datetime에서 timedelta를 명시적으로 가져와야 에러가 안 납니다.
from datetime import datetime, timedelta
import urllib.parse
import time

# 앱 이름 변경
st.set_page_config(page_title="창고관리", layout="wide")

# 세션 데이터 초기화
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["일시", "물품명", "유형", "수량", "상태"])

today = datetime.now().date()
now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 메인 타이틀 변경
st.title("📦 창고관리 시스템")

# --- [로그 기능: 누가 찐빠냈나 확인용] ---
with st.expander("🔍 작업 로그 (오류 추적)", expanded=False):
    if not st.session_state.history.empty:
        st.dataframe(st.session_state.history.sort_values("일시", ascending=False), use_container_width=True)
    else:
        st.info("기록된 로그가 없습니다.")

st.divider()

# --- [주간 결산 및 카톡 보고 기능] ---
st.subheader("📢 주간 결산 보고 (카톡)")
with st.container(border=True):
    # 이번 주 월요일과 금요일 계산 (이제 에러 안 남!)
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    
    if st.button(f"🗓️ 이번 주 ({monday} ~ {friday}) 요약 생성"):
        df_h = st.session_state.history.copy()
        if not df_h.empty:
            df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
            week_data = df_h[(df_h['날짜'] >= monday) & (df_h['날짜'] <= friday)]
            
            if not week_data.empty:
                stats = week_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                if '입고' not in stats: stats['입고'] = 0
                if '불출' not in stats: stats['불출'] = 0
                
                report_msg = f"📦 [창고관리 주간 정산]\n📅 기간: {monday} ~ {friday}\n"
                report_msg += "--------------------------\n"
                for item in stats.index:
                    report_msg += f"🔹 {item}: 입고 {stats.loc[item, '입고']} / 불출 {stats.loc[item, '불출']}\n"
                report_msg += "--------------------------\n✅ 이상 무."
                
                st.code(report_msg, language="text")
                
                # 카톡 공유 링크 (모바일용 가짜 링크 지양, 인코딩 메시지 제공)
                encoded_msg = urllib.parse.quote(report_msg)
                st.markdown(f"**[카톡 공유는 위 박스 내용을 복사해서 붙여넣어 주세요]**")
            else:
                st.warning("이번 주 데이터가 없습니다.")
        else:
            st.warning("로그 데이터가 없습니다.")

# --- [재고 현황 및 등록 기능 생략된 부분 유지] ---
# 사용자님, 나머지 등록/불출 로직은 기존 코드와 동일하게 하단에 붙여넣으시면 됩니다.
