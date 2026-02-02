import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="부대 창고", layout="wide")

# 포커스 자동 이동 및 숫자 키패드 최적화 스크립트
components.html(
    """
    <script>
    const doc = window.parent.document;
    
    // 1. 엔터 키 누르면 다음 칸으로 이동
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

    // 2. 유통기한(3번), 무게(4번) 칸에 숫자 키패드 강제 활성화 (천지인용)
    // Streamlit의 input 태그가 생성된 후 속성을 부여합니다.
    setInterval(() => {
        const inputs = doc.querySelectorAll('input');
        inputs.forEach(input => {
            const label = input.getAttribute('aria-label');
            if (label && (label.includes('유통기한') || label.includes('무게'))) {
                input.setAttribute('inputmode', 'numeric');
                input.setAttribute('pattern', '[0-9]*');
            }
        });
    }, 1000);
    </script>
    """,
    height=0,
)

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

def get_total_display(df_item):
    total_raw_ml_g = 0
    base_unit_type = "" 
    for i, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        if u == "L": total_raw_ml_g += val * 1000; base_unit_type = "L"
        elif u == "kg": total_raw_ml_g += val * 1000; base_unit_type = "kg"
        elif u == "mL": total_raw_ml_g += val; base_unit_type = "L"
        elif u == "g": total_raw_ml_g += val; base_unit_type = "kg"
    
    if total_raw_ml_g >= 1000:
        res = total_raw_ml_g / 1000
        final_unit = "L" if base_unit_type == "L" else "kg"
        return f"{res:.2f}{final_unit}".replace(".00", "")
    else:
        final_unit = "mL" if base_unit_type == "L" else "g"
        return f"{int(total_raw_ml_g)}{final_unit}"

st.title("📋 창고 현황판")

# 1. 물자 등록 창
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("input_form", clear_on_submit=False):
        name = st.text_input("1. 물품명", key="m_name")
        qty = st.number_input("2. 입고 개수", min_value=1, step=1, key="m_qty")
        
        # 유통기한: 텍스트 입력이지만 숫자 키패드가 뜨도록 스크립트가 보조
        d6 = st.text_input("3. 유통기한 6자리 (YYMMDD)", max_chars=6, key="m_date")
        
        # 무게: number_input은 기본적으로 숫자를 유도하지만, 
        # 천지인에서는 text_input에 inputmode를 주는 것이 더 확실할 때가 많아 위 스크립트로 보강
        wgt = st.number_input("4. 단위당 무게/부피", min_value=0, step=1, key="m_wgt")
        
        unit = st.selectbox("5. 단위", ["g", "mL", "kg", "L"], key="m_unit")
        
        submit = st.form_submit_button("🚀 창고에 등록하기", use_container_width=True)
        
        if submit:
            if not name:
                st.warning("⚠️ 물품명을 입력해주세요.")
            elif len(d6) != 6:
                st.error("❌ 날짜 6자리를 입력해주세요.")
            else:
                try:
                    yy = "20" + d6[:2] if int(d6[:2]) < 80 else "19" + d6[:2]
                    f_dt = f"{yy}-{d6[2:4]}-{d6[4:]}"
                    datetime.strptime(f_dt, "%Y-%m-%d")
                    
                    new_row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], 
                                       columns=st.session_state.inventory.columns)
                    st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
                    
                    st.success(f"✅ 등록 완료!") 
                    time.sleep(1.0)
                    st.rerun()
                except ValueError:
                    st.error("❌ 유효하지 않은 날짜입니다.")

st.divider()

# 2. 검색창
search = st.text_input("🔍 검색", placeholder="물품명 입력...")

# 3. 유통기한 임박 알림 (7일 이내)
if not st.session_state.inventory.empty:
    df_alert = st.session_state.inventory.copy()
    df_alert['dt'] = pd.to_datetime(df_alert['유통기한']).dt.date
    urg = df_alert[df_alert['dt'] <= today + timedelta(days=7)].sort_values('dt')
    
    if not urg.empty:
        st.error("🚨 유통기한 임박 (7일 이내)")
        for i, r in urg.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ **{r['물품명']}** - {txt} ({r['유통기한']})")
        st.divider()

# 4. 리스트 현황 (생략 - 이전과 동일)
# ... [이후 리스트 코드는 동일하게 유지]
