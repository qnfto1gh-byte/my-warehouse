import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="부대 창고", layout="wide")
st.title("📋 창고 현황판")

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"])

today = datetime.now().date()

# 1. 임박 알림 (D-Day)
if not st.session_state.inventory.empty:
    df = st.session_state.inventory.copy()
    df['dt'] = pd.to_datetime(df['유통기한']).dt.date
    urgent = df[df['dt'] <= today + timedelta(days=7)].sort_values('dt')
    if not urgent.empty:
        st.error("🚨 유통기한 임박!")
        for _, r in urgent.iterrows():
            d = (r['dt'] - today).days
            txt = f"D-{d}" if d > 0 else ("오늘" if d == 0 else f"만료 D+{-d}")
            st.write(f"⚠️ {r['물품명']} ({int(r['개수'])}{r['단위
