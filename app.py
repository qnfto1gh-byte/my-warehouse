import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="부대 창고 관리", layout="wide")

# 포커스 이동 및 숫자패드 (천지인 최적화)
components.html("""
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
    setInterval(() => {
        doc.querySelectorAll('input').forEach(input => {
            const label = input.getAttribute('aria-label');
            if (label && (label.includes('유통기한') || label.includes('무게') || label.includes('개수'))) {
                input.setAttribute('inputmode', 'numeric');
            }
        });
    }, 500);
    </script>
""", height=0)

# 데이터 초기화
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["날짜", "물품명", "유형", "수량"])

today = datetime.now().date()

st.title("📋 창고 현황 및 주간 통계")

# 1. 신규 물자 등록
with st.expander("➕ 신규 물자 등록", expanded=True):
    with st.form("input_form", clear_on_submit=True):
        name = st.text_input("1. 물품명")
        qty = st.number_input("2. 입고 개수", min_value=1, value=1)
        d6 = st.text_input("3. 유통기한 6자리 (YYMMDD)")
        wgt = st.number_input("4. 단위당 무게/부피", min_value=0, value=0)
        unit = st.selectbox("5. 단위", ["g", "mL", "kg", "L"])
        submit = st.form_submit_button("🚀 창고에 등록하기", use_container_width=True)
        
        if submit and name and len(d6) == 6:
            try:
                f_dt = f"20{d6[:2]}-{d6[2:4]}-{d6[4:]}"
                # 재고 추가
                new_row = pd.DataFrame([[name, int(qty), f_dt, int(wgt*qty), unit]], columns=st.session_state.inventory.columns)
                st.session_state.inventory = pd.concat([st.session_state.inventory, new_row], ignore_index=True)
                # 통계용 이력 추가
                new_log = pd.DataFrame([[today, name, "입고", int(qty)]], columns=st.session_state.history.columns)
                st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                
                st.success("✅ 등록 완료!")
                time.sleep(1.0)
                st.rerun()
            except: st.error("❌ 날짜 형식을 확인해주세요.")

st.divider()

# 2. 메인 탭 구성 (현황 vs 통계)
tab_stock, tab_stats = st.tabs(["📦 현재 재고 현황", "📊 주간 통계 (보고용)"])

with tab_stock:
    search = st.text_input("🔍 검색", placeholder="물품명 입력...")
    
    # 유통기한 임박 알림 (7일 이내)
    if not st.session_state.inventory.empty:
        df_alert = st.session_state.inventory.copy()
        df_alert['dt'] = pd.to_datetime(df_alert['유통기한']).dt.date
        urg = df_alert[df_alert['dt'] <= today + timedelta(days=7)].sort_values('dt')
        if not urg.empty:
            st.error("🚨 유통기한 임박 물자 발생!")
            for _, r in urg.iterrows():
                d = (r['dt'] - today).days
                st.write(f"⚠️ **{r['물품명']}** ({r['유통기한']}) - D-{d if d > 0 else 'Day'}")
            st.divider()

    # 재고 리스트 및 불출
    if not st.session_state.inventory.empty:
        df_m = st.session_state.inventory.copy()
        items = [i for i in df_m['물품명'].unique() if search.lower() in i.lower()]
        for item in items:
            i_df = df_m[df_m['물품명'] == item]
            t_qty = int(i_df['개수'].sum())
            with st.expander(f"{item} | 현재 {t_qty}개"):
                st.table(i_df[["개수", "유통기한"]])
                c1, c2 = st.columns([2, 1])
                rem_q = c1.number_input("불출 수량", min_value=1, max_value=t_qty, key=f"del_{item}")
                if c2.button("불출", key=f"btn_{item}", use_container_width=True):
                    # 통계용 이력 추가 (불출)
                    new_log = pd.DataFrame([[today, item, "불출", int(rem_q)]], columns=st.session_state.history.columns)
                    st.session_state.history = pd.concat([st.session_state.history, new_log], ignore_index=True)
                    
                    # 재고 차감 로직
                    to_rem = rem_q
                    temp_inv = st.session_state.inventory.copy()
                    for idx in i_df.index:
                        if to_rem <= 0: break
                        curr = temp_inv.at[idx, '개수']
                        if curr <= to_rem:
                            to_rem -= curr
                            temp_inv = temp_inv.drop(idx)
                        else:
                            temp_inv.at[idx, '개수'] -= to_rem
                            to_rem = 0
                    st.session_state.inventory = temp_inv.reset_index(drop=True)
                    st.rerun()
    else:
        st.info("창고가 비어있습니다.")

with tab_stats:
    if not st.session_state.history.empty:
        # 이번 주 월요일 계산
        monday = today - timedelta(days=today.weekday())
        df_h = st.session_state.history.copy()
        df_h['날짜'] = pd.to_datetime(df_h['날짜']).dt.date
        this_week = df_h[df_h['날짜'] >= monday]
        
        if not this_week.empty:
            st.write(f"📅 **이번 주 ({monday} ~ {today}) 집계**")
            # 피벗 테이블로 입고/불출 한눈에 보기
            stats = this_week.groupby(['물품명', '유형'])['수량'].sum().unstack(fill_value=0)
            if '입고' not in stats: stats['입고'] = 0
            if '불출' not in stats: stats['불출'] = 0
            st.table(stats[['입고', '불출']])
            
            # 수기 장부 작성용 텍스트
            summary_txt = f"[{monday} 주간 보고]\n"
            for item in stats.index:
                summary_txt += f"- {item}: 입고 {stats.loc[item, '입고']} / 불출 {stats.loc[item, '불출']}\n"
            st.text_area("장부 작성용 텍스트", value=summary_txt, height=150)
        else:
            st.info("이번 주에는 입고/불출 내역이 없습니다.")
    else:
        st.info("기록된 데이터가 없습니다.")
