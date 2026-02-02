import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

# 앱 설정
st.set_page_config(page_title="창고관리", layout="wide")

# 1. [강력 수정] 클릭 시 0 삭제 + 엔터 이동 스크립트
components.html("""
    <script>
    const doc = window.parent.document;
    
    // 0 자동 삭제 기능 (더 강력한 이벤트 리스너)
    doc.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT' && e.target.type === 'number') {
            if (e.target.value === "0") {
                e.target.value = "";
                // Streamlit의 내부 값을 갱신하기 위한 강제 이벤트 발생
                e.target.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });

    // 엔터 키로 다음 칸 이동
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const active = doc.activeElement;
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(active);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault();
                inputs[index + 1].focus();
            }
        }
    }, true);
    </script>
""", height=0)

# 세션 데이터 초기화
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["일시", "물품명", "유형", "수량", "상태"])

today = datetime.now().date()
now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_total_display(df_item):
    total_val = 0
    unit_type = "" 
    for _, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        total_val += val * 1000 if u in ["L", "kg"] else val
        unit_type = "L" if u in ["L", "mL"] else "kg"
    if total_val >= 1000:
        return f"{total_val/1000:.2f}{unit_type}".replace(".00", "")
    return f"{int(total_val)}{'mL' if unit_type == 'L' else 'g'}"

st.title("📦 창고관리 시스템")

# --- [1. 작업로그] ---
with st.expander("🔍 작업로그", expanded=False):
    if not st.session_state.history.empty:
        log_df = st.session_state.history.copy()
        log_df['날짜'] = pd.to_datetime(log_df['일시']).dt.date
        for day in sorted(log_df['날짜'].unique(), reverse=True):
            st.markdown(f"**📅 {day}**")
            st.table(log_df[log_df['날짜'] == day].sort_values("일시", ascending=False)[["일시", "물품명", "유형", "수량"]])

st.divider()

# --- [2. 유통기한 7일 이내 알림] ---
# (기존 로직 유지)

# --- [3. 신규 물자 등록] ---
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("reg_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("물품명")
        qty = c2.number_input("입고 수량", min_value=0, step=1)
        
        c3, c4 = st.columns(2)
        d6 = c3.text_input("유통기한 (YYMMDD)", max_chars=6)
        wgt = c4.number_input("단위당 무게/부피", min_value=0, step=1)
        
        unit = st.selectbox("단위", ["g", "mL", "kg", "L"])
        
        submit = st.form_submit_button("🚀 등록하기", use_container_width=True)
        
        if submit:
            if name and len(d6) == 6:
                # [수정] 오류 방지를 위해 try-except 범위를 최소화하고 성공 시에만 rerun
                f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                
                # 데이터 저장
                new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
                
                new_log = pd.DataFrame([[now_time, name, "입고", int(qty), "정상"]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                
                st.success(f"✅ {name} 등록 완료!")
                time.sleep(0.3)
                st.rerun() # 성공 메시지 후 새로고침
            else:
                st.warning("⚠️ 물품명과 유통기한 6자리를 입력하세요.")

st.divider()

# --- [4. 현재고 현황 및 검색] ---
# (이하 검색 및 불출 로직은 기존과 동일하게 유지)
