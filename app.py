import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="부대 창고 마스터", layout="wide")

# 포커스 및 숫자패드 스크립트
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

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["날짜", "물품명", "유형", "수량"])

today = datetime.now().date()

# 무게 표시 함수
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

st.title("📋 부대 창고 관리 (최종)")

# 1. 물자 등록
with st.expander("➕ 신규 물자 등록", expanded=False):
    with st.form("input_form", clear_on_submit=True):
        name = st.text_input("물품명")
        qty = st.number_input("입고 수량", min_value=1, value=1)
        d6 = st.text_input("유통기한 (YYMMDD)")
        col3, col4 = st.columns(2)
        wgt = col3.number_input("단위당 무게", min_value=0)
        unit = col4.selectbox("단위", ["g", "mL", "kg", "L"])
        if st.form_submit_button("창고 등록", use_container_width=True):
            if name and len(d6) == 6:
                f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                new_inv = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_inv], ignore_index=True)
                new_log = pd.DataFrame([[today, name, "입고", int(qty)]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                st.success("✅ 등록 완료!")
                time.sleep(1)
                st.rerun()

st.divider()

# 2. 메인 탭
tab_stock, tab_report = st.tabs(["📦 현재고 및 불출", "📅 기간별 정산"])

with tab_stock:
    # 🔴 [복구] 유통기한 임박 알림 (7일 이내)
    if not st.session_state.inventory.empty:
        df_alert = st.session_state.inventory.copy()
        df_alert['dt'] = pd.to_datetime(df_alert['유통기한']).dt.date
        urg = df_alert[df_alert['dt'] <= today + timedelta(days=7)].sort_values('dt')
        if not urg.empty:
            st.error("🚨 유통기한 위험 (7일 이내)")
            for _, r in urg.iterrows():
                d_v = (r['dt'] - today).days
                st.write(f"⚠️ **{r['물품명']}** ({r['유통기한']}) | **D-{d_v if d_v > 0 else 'Day'}**")
            st.divider()

    search = st.text_input("🔍 재고 검색")
    if not st.session_state.inventory.empty:
        df_m = st.session_state.inventory.copy()
        df_m['dt'] = pd.to_datetime(df_m['유통기한']).dt.date
        items = [i for i in df_m['물품명'].unique() if search.lower() in i.lower()]
        
        for item in items:
            i_df = df_m[df_m['물품명'] == item].sort_values('dt')
            t_qty = int(i_df['개수'].sum())
            min_d = i_df['dt'].min()
            d_v = (min_d - today).days
            
            with st.expander(f"📦 {item} | 총 {t_qty}개 | {min_d} (D-{d_v}) | {get_total_display(i_df)}"):
                st.table(i_df[["개수", "유통기한", "총 무게", "단위"]])
                
                # 🔵 [복구] 불출 개수 입력 및 버튼
                c1, c2 = st.columns([2, 1])
                del_qty = c1.number_input(f"불출할 개수", min_value=1, max_value=t_qty, key=f"q_{item}")
                if c2.button("불출 확정", key=f"b_{item}", use_container_width=True):
                    # 이력 남기기
                    new_log = pd.DataFrame([[today, item, "불출", int(del_qty)]], columns=st.session_state.history.columns)
                    st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                    # 재고 차감 (선입선출)
                    rem = del_qty
                    temp_inv = st.session_state.inventory.copy()
                    for idx in i_df.index:
                        if rem <= 0: break
                        curr = temp_inv.at[idx, '개수']
                        u_w = temp_inv.at[idx, '총 무게'] / curr
                        if curr <= rem:
                            rem -= curr
                            temp_inv = temp_inv.drop(idx)
                        else:
                            temp_inv.at[idx, '개수'] -= rem
                            temp_inv.at[idx, '총 무게'] = int(temp_inv.at[idx, '개수'] * u_w)
                            rem = 0
                    st.session_state.inventory = temp_inv.reset_index(drop=True)
                    st.rerun()
    else:
        st.info("재고가 없습니다.")

with tab_report:
    st.subheader("🗓️ 기간별 맞춤 정산")
    date_range = st.date_input("정산 기간 선택", value=(today - timedelta(days=7), today))
    if len(date_range) == 2:
        start, end = date_range
        if not st.session_state.history.empty:
            df_h = st.session_state.history.copy()
            df_h['날짜'] = pd.to_datetime(df_h['날짜']).dt.date
            period_data = df_h[(df_h['날짜'] >= start) & (df_h['날짜'] <= end)]
            if not period_data.empty:
                stats = period_data.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
                if '입고' not in stats: stats['입고'] = 0
                if '불출' not in stats: stats['불출'] = 0
                st.table(stats[['입고', '불출']])
                # 복사용 텍스트
                txt = f"[{start} ~ {end} 정산]\n"
                for i in stats.index:
                    txt += f"- {i}: 입고 {stats.loc[i, '입고']} / 불출 {stats.loc[i, '불출']}\n"
                st.text_area("장부 복사용", value=txt, height=150)
