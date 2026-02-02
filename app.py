import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import time

# 앱 설정
st.set_page_config(page_title="창고관리", layout="wide")

# [기능 4, 5, 7, 9] 엔터 이동 시 0 삭제 스크립트
components.html("""
    <script>
    const doc = window.parent.document;
    doc.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT' && (e.target.type === 'number' || e.target.inputMode === 'numeric')) {
            if (e.target.value === "0" || e.target.value === 0) { e.target.value = ""; }
            setTimeout(() => { e.target.select(); }, 30);
        }
    });
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            const inputs = Array.from(doc.querySelectorAll('input'));
            const index = inputs.indexOf(doc.activeElement);
            if (index > -1 && index < inputs.length - 1) {
                e.preventDefault(); inputs[index + 1].focus();
            }
        }
    }, true);
    </script>
""", height=0)

# --- 구글 시트 주소 ---
SHEET_URL = "여기에_본인의_구글_시트_주소를_복사해서_넣으세요"

# [수정] 보안 에러 방지를 위한 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # 읽기 권한을 위해 구문 수정
        inv = conn.read(spreadsheet=SHEET_URL, worksheet="Inventory", ttl=0)
        hist = conn.read(spreadsheet=SHEET_URL, worksheet="History", ttl=0)
        return inv.dropna(how='all'), hist.dropna(how='all')
    except Exception as e:
        st.error(f"데이터 로딩 실패: {e}")
        return pd.DataFrame(columns=["물품명", "개수", "유통기한", "총 무게", "단위"]), pd.DataFrame(columns=["일시", "물품명", "유형", "수량", "상태"])

inventory, history = load_data()
today = datetime.now().date()

# [기능 1] 총 무게 표시
def get_total_display(df_item):
    total_val = 0
    unit_type = "" 
    for _, row in df_item.iterrows():
        val, u = row['총 무게'], row['단위']
        total_val += val * 1000 if u in ["L", "kg"] else val
        unit_type = "L" if u in ["L", "mL"] else "kg"
    if total_val >= 1000: return f"{total_val/1000:.2f}{unit_type}".replace(".00", "")
    return f"{int(total_val)}{'mL' if unit_type == 'L' else 'g'}"

st.title("📦 창고관리 시스템")

# --- 이후 모든 8가지 기능(로그, 등록, 검색, 불출, 주간보고) 코드는 동일하게 유지 ---
# (지면상 생략하지만 이전의 9가지 통합 코드를 그대로 사용하세요!)

# [중요] 만약 위 코드로도 'Service Account' 에러가 계속 뜬다면 
# 아래와 같이 안내창을 띄워드립니다.
if "cannot be written to" in str(st.session_state.get('last_error', '')):
    st.error("⚠️ 구글 시트 보안 설정이 강화되었습니다. PC에서 구글 시트의 [공유] 설정이 [편집자]로 되어있는지 다시 확인해주세요.")
