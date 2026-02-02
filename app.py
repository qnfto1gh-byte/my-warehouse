import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

# 앱 설정 및 이름
st.set_page_config(page_title="창고관리", layout="wide")

# 1. 포커스 이동 및 숫자패드 (유지)
components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const active = doc.activeElement;
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(active);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault(); inputs[index + 1].focus();
            }
        }
    }, true);
    </script>
""", height=0)

# 세션 데이터 초기화 (로그가 안 읽히는 문제 방지용)
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["일시", "물품명", "유형", "수량", "상태"])

today = datetime.now().date()
now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.title("📦 창고관리 시스템")

# --- [1. 작업로그] ---
# 로그가 안 보인다면 데이터가 DataFrame 형태인지 강제 확인
st.subheader("🔍 작업로그")
if not st.session_state.history.empty:
    st.dataframe(st.session_state.history.sort_values("일시", ascending=False), use_container_width=True)
else:
    st.info("현재 기록된 로그가 없습니다. 물자를 등록하거나 불출해 보세요.")

st.divider()

# --- [2. 유통기한 7일 이내 모아보기] ---
st.subheader("⚠️ 유통기한 임박 리스트 (7일 이내)")
if not st.session_state.inventory.empty:
    df_alert = st.session_state.inventory.copy()
    # 날짜 변환 시 에러 방지를 위해 에러 무시 옵션 추가
    df_alert['dt'] = pd.to_datetime(df_alert['유통기한'], errors='coerce').dt.date
    df_alert = df_alert.dropna(subset=['dt']) # 변환 실패한 날짜 제거
    
    urg_items = df_alert[df_alert['dt'] <= today + timedelta(days=7)].sort_values('dt')
    if not urg_items.empty:
        for _, r in urg_items.iterrows():
            d_day = (r['dt'] - today).days
            st.error(f"**[D-{d_day if d_day >=0 else '만료'}]** {r['물품명']} | {r['개수']}개 | 기한: {r['유통기한']}")
    else:
        st.success("✅ 임박 물자 없음")

st.divider()

# --- [3. 기간별 정산 및 카톡 보고] ---
with st.expander("📅 기간별 정산 보고 (설정하기)"):
    date_range = st.date_input("정산 기간", value=(today - timedelta(days=7), today))
    if len(date_range) == 2:
        start_d, end_d = date_range
        if st.button("📊 결과 생성"):
            df_h = st.session_state.history.copy()
            if not df_h.empty:
                df_h['날짜'] = pd.to_datetime(df_h['일시']).dt.date
                period_data = df_h[(df_h['날짜'] >= start_d) & (df_h['날짜'] <= end_d)]
                if not period_data.empty:
                    stats = period_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                    for col in ['입고', '불출']: 
                        if col not in stats: stats[col] = 0
                    st.table(stats[['입고', '불출']])
                    # 카톡 양식
                    txt = f"📦 [창고관리 정산]\n📅 {start_d}~{end_d}\n"
                    for i in stats.index:
                        txt += f"🔹 {i}: +{stats.loc[i, '입고']} / -{stats.loc[i, '불출']}\n"
                    st.code(txt)

st.divider()

# --- [4. 신규 등록: 날짜 오류 집중 수정] ---
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("물품명")
        qty = c2.number_input("입고 수량", min_value=1)
        
        c3, c4 = st.columns(2)
        d6 = c3.text_input("유통기한 6자리 (YYMMDD)")
        wgt = c4.number_input("단위당 무게/부피", min_value=0)
        
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])
        
        if st.form_submit_button("🚀 등록하기"):
            if name and len(d6) == 6:
                try:
                    # 날짜 변환 검증 로직 강화
                    year = int("20" + d6[:2])
                    month = int(d6[2:4])
                    day = int(d6[4:])
                    formatted_date = f"{year}-{month:02d}-{day:02d}"
                    # 실제 유효한 날짜인지 체크
                    datetime.strptime(formatted_date, "%Y-%m-%d")
                    
                    # 데이터 저장
                    new_inv = pd.DataFrame([[name, int(qty), formatted_date, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                    st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
                    
                    new_log = pd.DataFrame([[now_time, name, "입고", int(qty), "정상"]], columns=st.session_state.history.columns)
                    st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                    
                    st.success(f"✅ {name} 등록 완료!")
                    time.sleep(0.5)
                    st.rerun()
                except ValueError:
                    st.error("❌ 잘못된 날짜입니다! (예: 260231은 존재하지 않음)")
                except Exception as e:
                    st.error(f"❌ 오류 발생: {e}")
            else:
                st.warning("⚠️ 물품명과 유통기한 6자리를 모두 입력하세요.")
