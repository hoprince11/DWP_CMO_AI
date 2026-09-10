import streamlit as st
import pandas as pd
from datetime import datetime
from google import genai

# ------------------------------------------------------------------------------
# 1. Page Config & CSS (깔끔하게 상단 격리)
# ------------------------------------------------------------------------------
st.set_page_config(page_title="동화약품 수탁팀 AI 자동화", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 99990 !important; }
    [data-testid*="stSidebar"], button[aria-label*="sidebar"] { display: flex !important; visibility: visible !important; }
    [data-testid="stHeaderActionElements"], [data-testid="stToolbarActions"], #MainMenu, footer { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. Helper Functions & Calculation Logic (비즈니스 로직 백엔드화)
# ------------------------------------------------------------------------------
def init_session_state():
    if "user_db" not in st.session_state:
        st.session_state["user_db"] = {
            "master": {"pw": "3019", "name": "최고관리자", "position": "관리자", "approved": True},
            "dh_teamleader": {"pw": "dongwha2026!", "name": "홍길동", "position": "팀장", "approved": True}
        }
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

def calculate_sku_metrics(batch_size, skus, insurance_price, cso_fee_rate, is_cso):
    """모든 복잡한 원가/배치/공헌이익 계산을 한곳에서 처리"""
    total_ratio = sum(s['ratio'] for s in skus)
    
    # 가중평균 산출
    avg_cost = sum(s['cost'] * (s['ratio'] / 100.0) for s in skus)
    avg_supply = sum(s['supply'] * (s['ratio'] / 100.0) for s in skus)
    
    # 배치 당 포장 단위 개수
    total_packages = sum(int(round((batch_size * (s['ratio'] / 100.0)) / s['size'])) for s in skus if s['size'] > 0)
    
    # 위탁사 이익 계산
    vat_ex = insurance_price / 1.1 if insurance_price > 0 else 0
    wholesale_ex = vat_ex * 0.89
    cso_fee = (insurance_price * (cso_fee_rate / 100.0)) / 1.1 if is_cso else 0
    margin = wholesale_ex - cso_fee - avg_supply
    margin_rate = (margin / wholesale_ex * 100) if wholesale_ex > 0 else 0
    
    return {
        "total_ratio": total_ratio,
        "avg_cost": int(round(avg_cost)),
        "avg_supply": int(round(avg_supply)),
        "cmo_profit": int(round(avg_supply - avg_cost)),
        "total_packages": total_packages,
        "wholesale_ex": int(round(wholesale_ex)),
        "cso_fee": int(round(cso_fee)),
        "margin": int(round(margin)),
        "margin_rate": round(margin_rate, 1)
    }

def call_gemini(prompt):
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        st.error("Gemini API Key가 설정되지 않았습니다.")
        return None
    try:
        client = genai.Client(api_key=api_key.strip())
        return client.models.generate_content(model='gemini-3.6-flash', contents=prompt).text
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None

# ------------------------------------------------------------------------------
# 3. Auth & Sidebar UI
# ------------------------------------------------------------------------------
init_session_state()

if not st.session_state["authenticated"]:
    # (인증 화면 간소화 호출)
    st.title("🔒 동화약품 수탁팀 AI 시스템")
    uid = st.text_input("사번")
    upw = st.text_input("비밀번호", type="password")
    if st.button("로그인", type="primary"):
        u = st.session_state["user_db"].get(uid)
        if u and u["pw"] == upw and u.get("approved"):
            st.session_state.update({"authenticated": True, "user_id": uid, "user_name": u["name"], "user_position": u["position"]})
            st.rerun()
        else:
            st.error("계정 정보가 올바르지 않거나 승인 대기 중입니다.")
    st.stop()

# 사이드바
st.sidebar.title("💊 동화약품 수탁 AI")
st.sidebar.caption(f"👤 {st.session_state['user_name']} {st.session_state['user_position']}")
if st.sidebar.button("로그아웃"):
    st.session_state["authenticated"] = False
    st.rerun()

menu = st.sidebar.radio("📌 메뉴", ["📊 수탁공급가 분석 & AI 제안", "💰 CSO 시뮬레이터 (예정)", "📁 이력 관리 (예정)"])

# ------------------------------------------------------------------------------
# 4. Main View: 수탁공급가 분석 & AI 제안
# ------------------------------------------------------------------------------
if menu == "📊 수탁공급가 분석 & AI 제안":
    st.title("📊 수탁공급가 분석 & AI 제안")
    
    # UI 구조를 3개의 탭으로 분리하여 정돈된 스텝 제공
    tab1, tab2, tab3 = st.tabs(["1️⃣ 기본 정보 & SKU 입력", "2️⃣ 단가/공정 분석", "3️⃣ AI 인상 전략 & 메일 생성"])
    
    with tab1:
        c1, c2, c3 = st.columns([2, 1, 1])
        item_name = c1.text_input("제품명", value="대웅바이오암로디핀정5mg")
        form_type = c2.selectbox("제형", ["정제 (T)", "캡슐 (C)"])
        insurance_price = c3.number_input("보험약가 (원)", value=312)
        
        c4, c5, c6 = st.columns([2, 1, 1])
        batch_size = c4.number_input("기준 Batch Size", value=1000000)
        is_cso = c5.checkbox("CSO 적용", value=True)
        cso_fee_rate = c6.number_input("CSO 수수료율 (%)", value=40.0)
        
        st.markdown("---")
        use_sku3 = st.checkbox("규격 3 추가", value=False)
        
        # SKU 입력 폼 렌더링
        skus = []
        cols = st.columns(3 if use_sku3 else 2)
        
        defaults = [
            {"size": 30, "cost": 65, "supply": 65, "ratio": 20 if use_sku3 else 30},
            {"size": 300, "cost": 29, "supply": 35, "ratio": 50 if use_sku3 else 70},
            {"size": 90, "cost": 42, "supply": 46, "ratio": 30}
        ]
        
        for i, col in enumerate(cols):
            with col:
                st.subheader(f"규격 {i+1}")
                sz = st.number_input(f"규격 수치", value=defaults[i]["size"], key=f"s_{i}")
                ct = st.number_input(f"원가 (원)", value=defaults[i]["cost"], key=f"c_{i}")
                sp = st.number_input(f"공급가 (원)", value=defaults[i]["supply"], key=f"sp_{i}")
                rt = st.number_input(f"생산비율 (%)", value=defaults[i]["ratio"], key=f"r_{i}")
                skus.append({"name": f"{sz}{form_type[0]}", "size": sz, "cost": ct, "supply": sp, "ratio": rt})
        
        # 계산 실행
        metrics = calculate_sku_metrics(batch_size, skus, insurance_price, cso_fee_rate, is_cso)
        if metrics["total_ratio"] != 100:
            st.warning(f"⚠️ 현재 생산 비율 합계가 {metrics['total_ratio']}% 입니다. (100%에 맞춰주세요)")

    with tab2:
        st.subheader("💡 가중평균 분석 및 포장 공정 효율화")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("가중평균 원가", f"{metrics['avg_cost']:,} 원")
        m2.metric("가중평균 공급가", f"{metrics['avg_supply']:,} 원")
        m3.metric("동화약품 이익률", f"{round(metrics['cmo_profit']/metrics['avg_supply']*100, 1) if metrics['avg_supply'] else 0}%")
        m4.metric("위탁사 공헌이익률", f"{metrics['margin_rate']}%")
        
        st.markdown("---")
        st.write(f"📦 **1 Batch ({batch_size:,}개) 당 총 포장 단위 수량**: `{metrics['total_packages']:,} 개`")

    with tab3:
        st.subheader("🤖 AI 전략 수립 및 메일 제안")
        if st.button("🚀 AI 전략 옵션 도출", type="primary"):
            prompt = f"제품명: {item_name}, 배치: {batch_size}, 약가: {insurance_price}, SKU정보: {skus}. 전략 옵션 A/B/C를 제안해주세요."
            st.session_state['ai_res'] = call_gemini(prompt)
            
        if 'ai_res' in st.session_state:
            st.info(st.session_state['ai_res'])
            
            st.markdown("---")
            opt = st.radio("선택 옵션", ["옵션 A (비율 전환)", "옵션 B (원가 보전)", "옵션 C (단계 적용)"])
            if st.button("📧 메일 제안서 생성"):
                e_prompt = f"담당자: {st.session_state['user_name']}, 제품: {item_name}, 선택옵션: {opt}. 거래처에 보낼 제안 메일을 작성하세요."
                st.write(call_gemini(e_prompt))

else:
    st.info("🚧 업데이트 예정 기능입니다.")
