import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="부대 창고", layout="wide")

# 1. 강화된 스크립트: 다음 칸 이동 + 숫자 키패드 강제 활성화
components.html(
    """
    <script>
    const doc = window.parent.document;
    
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

    // 천지인 숫자패드 강제 전환 로직
    setInterval(() => {
        const inputs = doc.querySelectorAll('input');
        inputs.forEach(input => {
            const label = input.getAttribute('aria-label');
            if (label && (label.includes('유통기한') || label.includes('무게') || label.includes('개수'))) {
                input.setAttribute('type', 'number'); // 유형을 숫자로 강제
                input.setAttribute('inputmode', 'numeric');
            }
        });
    }, 500);
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

# 2. 물자 등록 창
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("input_form", clear_on_submit=True): # 등록 후 칸 비우기 활성화
        name = st.text_input("1. 물품명", key="m_name")
        qty = st.number_input("2. 입고 개수", min_value=1, value=1, step=1, key="m_qty")
        d6 = st.text_input("3. 유통기한 6자리 (YYMMDD)", key="m_date", help="예: 270914")
        wgt = st.number_input("4. 단위당 무게/부피", min_value=0, value=0, step=1, key="m_wgt")
        unit = st.selectbox("5. 단위", ["g", "mL", "kg", "L"], key="m_unit")
        
        submit = st.form_submit_button("🚀 창고에 등록하기", use_container_width=True)
        
        if submit:
            if not name or not d6:
                st.warning("⚠️ 모든 칸을 채워주세요.")
            elif len(d6) != 6:
                st.error("❌ 날짜는 6자리여야 합니다.")
            else:
                try:
                    # 날짜 판독 로직 단순화 (YY-MM-DD)
                    yy = int(d6[:2])
                    mm = int(d6[2:4])
                    dd = int(d6[4:])
                    
                    # 2000년대 날짜로 고정 처리
                    target_dt = datetime(2000 + yy, mm, dd).date()
                    f_dt_str = target_dt.strftime("%Y-%m-%d")
                    
                    # 데이터 추가
                    new_row = pd.DataFrame([[name, int(qty), f_dt_str, int(wgt*qty), unit]], 
                                       columns=st.session_state.inventory.columns)
                    st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
                    
                    # 확실한 1초 알림
                    st.success("✅ 등록되었습니다!")
                    time.sleep(1.0)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 날짜 입력 오류: {d6} (월/일을 확인하세요)")

st.divider()

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

# 4. 현황 리스트 (검색 및 불출)
search = st.text_input("🔍 검색", placeholder="물품명 입력...")

if not st.session_state.inventory.empty:
    df_m = st.session_state.inventory.copy()
    df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
    items = [i for i in df_m['물품명'].unique() if search.lower() in i.lower()]

    for item in items:
        i_df = df_m[df_m['물품명'] == item].sort_values('dt')
        t_qty = int(i_df['개수'].sum())
        min_d = i_df['dt'].min()
        total_str = get_total_display(i_df)
        d_v = (min_d - today).days
        d_l = f"D-{d_v}" if d_v > 0 else ("오늘" if d_v == 0 else f"만료 D+{-d_v}")
        
        with st.expander(f"📦 {item} | {t_qty}개 | {min_d}({d_l}) | {total_str}"):
            st.table(i_df[["개수", "유통기한", "총 무게", "단위"]])
            
            c1, c2 = st.columns([2, 1])
            rem_qty = c1.number_input(f"불출 수량", min_value=1, max_value=t_qty, step=1, key="del_q_"+item)
            if c2.button(f"불출", key="del_b_"+item, use_container_width=True):
                to_rem = rem_qty
                temp_inv = st.session_state.inventory.copy()
                for idx in i_df.index:
                    if to_rem <= 0: break
                    curr = temp_inv.at[idx, '개수']
                    u_w = temp_inv.at[idx, '총 무게'] / curr
                    if curr <= to_rem:
                        to_rem -= curr
                        temp_inv = temp_inv.drop(idx)
                    else:
                        temp_inv.at[idx, '개수'] -= to_rem
                        temp_inv.at[idx, '총 무게'] = int(temp_inv.at[idx, '개수'] * u_w)
                        to_rem = 0
                st.session_state.inventory = temp_inv.reset_index(drop=True)
                st.rerun()
else:
    st.info("창고가 비어있습니다.")
