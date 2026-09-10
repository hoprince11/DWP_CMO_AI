import streamlit as st
import pandas as pd
from datetime import datetime
from google import genai

# 페이지 설정
st.set_page_config(
    page_title="동화약품 수탁팀 AI 자동화 시스템", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------
# 🎨 [UI] 토글 버튼 보존 및 우측 요소 정밀 제거
# ------------------------------------------
st.markdown("""
    <style>
    header[data-testid="stHeader"] { background-color: transparent !important; z-index: 99990 !important; }
    [data-testid*="stSidebar"], button[aria-label*="sidebar"] { display: flex !important; visibility: visible !important; opacity: 1 !important; z-index: 99999 !important; }
    [data-testid="stHeaderActionElements"], [data-testid="stToolbarActions"], button[title="View app in GitHub"], button[title="Share this app"],
    div[data-testid="stStatusWidget"], button[title="Manage app"], #MainMenu, footer, div[data-testid="stViewerBadge"] {
        display: none !important; visibility: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 [보안 & 사용자 관리] 세션 DB 초기화
# ==========================================
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "master": {"pw": "3019", "name": "최고관리자", "position": "관리자", "approved": True, "created_at": "2026-01-01 00:00:00"},
        "dh_teamleader": {"pw": "dongwha2026!", "name": "홍길동", "position": "팀장", "approved": True, "created_at": "2026-01-01 00:00:00"}
    }

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def auth_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔒 동화약품 수탁팀 AI 자동화 시스템")
        st.caption("인가된 동화약품 팀원만 접속 가능한 내부 보안 시스템입니다.")
        st.markdown("---")
        
        tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])
        
        with tab_login:
            with st.form("login_form"):
                user_id = st.text_input("사번 (ID)", key="login_id")
                user_pw = st.text_input("비밀번호 (Password)", type="password", key="login_pw")
                if st.form_submit_button("로그인", type="primary"):
                    user_info = st.session_state["user_db"].get(user_id)
                    if user_info and user_info["pw"] == user_pw:
                        if not user_info.get("approved", False):
                            st.warning("⏳ 관리자 승인 대기 중인 계정입니다.")
                        else:
                            st.session_state.update({
                                "authenticated": True, "user_id": user_id,
                                "user_name": user_info.get("name", ""),
                                "user_position": user_info.get("position", "")
                            })
                            st.success("로그인 성공!")
                            st.rerun()
                    else:
                        st.error("❌ 사번(ID) 또는 비밀번호가 올바르지 않습니다.")

        with tab_signup:
            with st.form("signup_form"):
                new_id = st.text_input("사번 (ID)", key="signup_id", placeholder="예: 20260101")
                new_name = st.text_input("이름", key="signup_name", placeholder="예: 홍길동")
                new_pos = st.text_input("직급", key="signup_position", placeholder="예: 팀장, 과장")
                new_pw = st.text_input("비밀번호", type="password", key="signup_pw")
                new_pw_confirm = st.text_input("비밀번호 확인", type="password", key="signup_pw_confirm")
                
                if st.form_submit_button("회원가입 신청"):
                    if not all([new_id, new_name, new_pos, new_pw]):
                        st.warning("모든 필드를 입력해 주세요.")
                    elif new_id in st.session_state["user_db"]:
                        st.error("이미 존재하는 사번입니다.")
                    elif new_pw != new_pw_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        st.session_state["user_db"][new_id] = {
                            "pw": new_pw, "name": new_name, "position": new_pos,
                            "approved": False, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.success("🎉 회원가입 신청 완료! 관리자 승인 후 로그인 가능합니다.")

if not st.session_state["authenticated"]:
    st.sidebar.info("🔒 로그인 후 시스템 이용이 가능합니다.")
    auth_screen()
    st.stop()

# ==========================================
# 📌 [사이드바] 접속자 정보 / 관리자 메뉴
# ==========================================
st.sidebar.title("💊 동화약품 수탁 AI")

curr_user_id = st.session_state['user_id']
curr_user_name = st.session_state.get('user_name', '')
curr_user_pos = st.session_state.get('user_position', '')

st.sidebar.markdown(f"👤 접속자: **`{curr_user_name} {curr_user_pos}`** (`{curr_user_id}`)")
if st.sidebar.button("🔓 로그아웃", key="logout_btn"):
    st.session_state["authenticated"] = False
    st.rerun()

st.sidebar.markdown("---")

if curr_user_id == "master":
    st.sidebar.subheader("👑 관리자 메뉴")
    with st.sidebar.expander("🙋‍♂️ 회원가입 승인 관리", expanded=True):
        pending_users = {uid: uinfo for uid, uinfo in st.session_state["user_db"].items() if not uinfo.get("approved", False)}
        if not pending_users:
            st.caption("승인 대기 건이 없습니다.")
        else:
            st.write(f"**대기건수: {len(pending_users)}건**")
            for p_id, p_info in list(pending_users.items()):
                st.markdown(f"**- {p_info['name']} {p_info['position']}** (`{p_id}`)")
                col_app, col_rej = st.columns(2)
                if col_app.button("승인", key=f"app_{p_id}", type="primary"):
                    st.session_state["user_db"][p_id]["approved"] = True
                    st.rerun()
                if col_rej.button("거절", key=f"rej_{p_id}"):
                    del st.session_state["user_db"][p_id]
                    st.rerun()

api_key = st.secrets.get("GEMINI_API_KEY", "")

st.sidebar.markdown("---")
st.sidebar.subheader("👤 작성자 정보")
st.sidebar.text_input("수탁사명", value="동화약품", disabled=True)
user_position = st.sidebar.text_input("직책", value=curr_user_pos)
user_name = st.sidebar.text_input("작성자 성명", value=curr_user_name)

st.sidebar.markdown("---")
menu_choice = st.sidebar.radio(
    "📌 메뉴 이동",
    [
        "📊 수탁공급가 분석 & AI 제안",
        "💰 CSO 수수료율 / 약가 인하 시뮬레이터 (예정)",
        "📁 수탁 품목 계약 및 이력 관리 (예정)",
        "📄 거래처 맞춤형 제안서 PDF (예정)"
    ]
)

st.title("💊 동화약품 수탁 AI 자동화 시스템")

# API 호출 공통 헬퍼
def generate_ai_response(prompt):
    if not api_key:
        st.error("Gemini API Key가 설정되지 않았습니다.")
        return None
    try:
        client = genai.Client(api_key=api_key.strip())
        response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
        return response.text
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        return None

# ==========================================
# 🟢 [메뉴 1] 수탁공급가 분석 & AI 제안
# ==========================================
if menu_choice == "📊 수탁공급가 분석 & AI 제안":
    st.write("제품 기반 포장규격·Batch·포장타입·CSO 자동 시뮬레이션 및 공급단가 분석 시스템")
    st.markdown("---")
    
    st.subheader("📝 Step 0. 수탁 품목 기본 정보 입력")
    c1, c2, c3 = st.columns([2, 1, 1])
    item_name = c1.text_input("제품명", placeholder="예: 대웅바이오암로디핀정5밀리그램")
    form_type = c2.selectbox("제형 구분", ["정제 (T)", "캡슐 (C)"], index=0)
    unit_symbol, unit_kor = ("T", "정") if "정제" in form_type else ("C", "캡슐")
    insurance_price = c3.number_input(f"보험약가 (원/{unit_kor})", min_value=0, value=312, step=1, format="%d")

    c4, c5, c6 = st.columns([2, 1, 1])
    batch_size_num = c4.number_input(f"기준 배치 사이즈 ({unit_kor})", min_value=0, value=1000000, step=10000, format="%d")
    is_cso = c5.checkbox("CSO 대상 품목 여부", value=True)
    cso_fee_rate = c6.number_input("CSO 수수료율 (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.5)

    st.markdown("---")
    st.subheader(f"📦 포장단위별(SKU) 1{unit_kor}당 원가 및 단가 비교 입력")
    use_sku3 = st.checkbox("☑️ 규격 3 추가 입력 (3번째 포장 규격이 있는 경우 체크)", value=False)

    # SKU 입력 모듈화 헬퍼
    def render_sku_input(num, default_type_idx, default_size, default_cost, default_supply, default_ratio):
        st.markdown(f"#### 🔹 규격 {num} 정보")
        p_type = st.selectbox("포장 타입", ["PTP", "Bottle (병)"], index=default_type_idx, key=f"sku{num}_type")
        p_size = st.number_input(f"포장 규격 수치 ({unit_kor}/포장)", min_value=1, value=default_size, step=1, format="%d", key=f"sku{num}_size")
        name = f"{p_size}{unit_symbol}({p_type.split()[0]})"
        
        cost = st.number_input(f"{name} 원가 (원/{unit_kor})", min_value=0, value=default_cost, step=1, format="%d", key=f"sku{num}_cost")
        supply = st.number_input(f"{name} 공급단가 (원/{unit_kor})", min_value=0, value=default_supply, step=1, format="%d", key=f"sku{num}_supply")
        ratio = st.number_input(f"{name} 생산 비율 (%)", min_value=0, max_value=100, value=default_ratio, step=5, format="%d", key=f"sku{num}_ratio")
        
        prod_qty = int(batch_size_num * (ratio / 100.0))
        st.metric(f"{name} 생산실적 ({unit_kor})", f"{prod_qty:,} {unit_kor}")
        return p_type, p_size, name, cost, supply, ratio

    cols = st.columns(3 if use_sku3 else 2)
    with cols[0]:
        sku1_type, sku1_size, sku1_name, cost_sku1, supply_sku1, ratio_sku1 = render_sku_input(1, 0, 30, 65, 65, 20 if use_sku3 else 30)
    with cols[1]:
        sku2_type, sku2_size, sku2_name, cost_sku2, supply_sku2, ratio_sku2 = render_sku_input(2, 0, 300, 29, 35, 50 if use_sku3 else 70)
    
    if use_sku3:
        with cols[2]:
            sku3_type, sku3_size, sku3_name, cost_sku3, supply_sku3, ratio_sku3 = render_sku_input(3, 0, 90, 42, 46, 30)
    else:
        cost_sku3 = supply_sku3 = ratio_sku3 = sku3_size = 0
        sku3_name = ""

    total_ratio = ratio_sku1 + ratio_sku2 + ratio_sku3
    if total_ratio != 100:
        st.warning(f"⚠️ 현재 생산 비율 합계가 **{total_ratio}%** 입니다. (100%가 되도록 조정해 주세요)")

    # 가중평균 산출
    r1_f, r2_f, r3_f = ratio_sku1 / 100.0, ratio_sku2 / 100.0, ratio_sku3 / 100.0
    weighted_avg_cost_per_unit = int(round((cost_sku1 * r1_f) + (cost_sku2 * r2_f) + (cost_sku3 * r3_f)))
    weighted_avg_supply_per_unit = int(round((supply_sku1 * r1_f) + (supply_sku2 * r2_f) + (supply_sku3 * r3_f)))

    cmo_profit_per_unit = weighted_avg_supply_per_unit - weighted_avg_cost_per_unit
    cmo_profit_margin_rate = round((cmo_profit_per_unit / weighted_avg_supply_per_unit) * 100, 1) if weighted_avg_supply_per_unit > 0 else 0.0

    st.info(f"⚖️ **[생산량 가중평균 통합 1{unit_kor}당 단가 및 수탁사 이익]**\n- **가중평균 1{unit_kor}당 원가**: `{weighted_avg_cost_per_unit:,} 원` | **공급단가**: `{weighted_avg_supply_per_unit:,} 원`  \n- 💰 **동화약품 매출이익**: `{cmo_profit_per_unit:,} 원/정` | 📈 **매출이익률**: **`{cmo_profit_margin_rate:.1f}%`**")

    st.markdown("---")
    st.subheader("📐 기준 Batch Size 기반 포장 공정 및 단가 절감 시뮬레이션")

    opt_ratio_sku1, opt_ratio_sku2 = max(0, ratio_sku1 - 10), min(100, ratio_sku2 + 10)
    opt_ratio_sku3 = ratio_sku3 if use_sku3 else 0

    curr_b1 = int(round((batch_size_num * r1_f) / sku1_size)) if sku1_size > 0 else 0
    curr_b2 = int(round((batch_size_num * r2_f) / sku2_size)) if sku2_size > 0 else 0
    curr_b3 = int(round((batch_size_num * r3_f) / sku3_size)) if (use_sku3 and sku3_size > 0) else 0
    total_curr_bottles = curr_b1 + curr_b2 + curr_b3

    opt_r1_f, opt_r2_f, opt_r3_f = opt_ratio_sku1 / 100.0, opt_ratio_sku2 / 100.0, opt_ratio_sku3 / 100.0
    opt_b1 = int(round((batch_size_num * opt_r1_f) / sku1_size)) if sku1_size > 0 else 0
    opt_b2 = int(round((batch_size_num * opt_r2_f) / sku2_size)) if sku2_size > 0 else 0
    opt_b3 = int(round((batch_size_num * opt_r3_f) / sku3_size)) if (use_sku3 and sku3_size > 0) else 0
    total_opt_bottles = opt_b1 + opt_b2 + opt_b3

    saved_bottles = total_curr_bottles - total_opt_bottles
    opt_weighted_supply = int(round((supply_sku1 * opt_r1_f) + (supply_sku2 * opt_r2_f) + (supply_sku3 * opt_r3_f)))
    opt_weighted_cost = int(round((cost_sku1 * opt_r1_f) + (cost_sku2 * opt_r2_f) + (cost_sku3 * opt_r3_f)))
    saved_per_unit = weighted_avg_supply_per_unit - opt_weighted_supply

    col_ratio_a, col_ratio_b = st.columns(2)
    sku_ratio_label_curr = f"{ratio_sku1}% : {ratio_sku2}%" if not use_sku3 else f"{ratio_sku1}% : {ratio_sku2}% : {ratio_sku3}%"
    sku_ratio_label_opt = f"{opt_ratio_sku1}% : {opt_ratio_sku2}%" if not use_sku3 else f"{opt_ratio_sku1}% : {opt_ratio_sku2}% : {opt_ratio_sku3}%"
    sku_names_label = f"{sku1_name} : {sku2_name}" if not use_sku3 else f"{sku1_name} : {sku2_name} : {sku3_name}"

    with col_ratio_a:
        st.markdown(f"##### 📌 **1 Batch({batch_size_num:,}{unit_kor}) 생산 시 포장 단위 수량 비교**")
        sku3_curr_txt = f" / `{sku3_name}`: `{curr_b3:,} 개`" if use_sku3 else ""
        sku3_opt_txt = f" / `{sku3_name}`: `{opt_b3:,} 개`" if use_sku3 else ""
        st.markdown(f"""
        - **현행 비율 ({sku_ratio_label_curr}) 기준**:
          - `{sku1_name}`: `{curr_b1:,} 개` / `{sku2_name}`: `{curr_b2:,} 개`{sku3_curr_txt}
          - **총 포장 단위 수**: **`{total_curr_bottles:,} 개`**
        - **추천 비율 ({sku_ratio_label_opt}) 적용 시**:
          - `{sku1_name}`: `{opt_b1:,} 개` / `{sku2_name}`: `{opt_b2:,} 개`{sku3_opt_txt}
          - **총 포장 단위 수**: **`{total_opt_bottles:,} 개`** (총 **`{saved_bottles:,} 개`** 포장 공정 감소!)
        """)

    with col_ratio_b:
        st.markdown("##### 📌 **비율 최적화 시 단가 절감 시뮬레이션**")
        st.markdown(f"""
        | 구분 | 현재 비율 | 추천 최적 비율 | 비고 |
        | :--- | :---: | :---: | :--- |
        | **생산 비율 ({sku_names_label})** | `{sku_ratio_label_curr}` | **`{sku_ratio_label_opt}`** | 소포장 10%↓ / 대용량 10%↑ |
        | **1 Batch 총 포장 단위** | `{total_curr_bottles:,} 개` | **`{total_opt_bottles:,} 개`** | **`{saved_bottles:,} 개`** 공정 절감 |
        | **가중평균 원가** | `{weighted_avg_cost_per_unit:,}원` | **`{opt_weighted_cost:,}원`** | 원가 **`{weighted_avg_cost_per_unit - opt_weighted_cost:,}원`** 절감 |
        | **가중평균 공급단가** | `{weighted_avg_supply_per_unit:,}원` | **`{opt_weighted_supply:,}원`** | 1정당 **`{saved_per_unit:,}원`** 인하 효과 |
        """)

    st.markdown("---")
    st.subheader(f"📊 위탁사 매출이익 분석 (현재 기준, 1{unit_kor}당)")

    vat_ex_price = int(round(insurance_price / 1.1)) if insurance_price > 0 else 0
    wholesale_price_ex_vat = int(round(vat_ex_price * 0.89)) if insurance_price > 0 else 0
    cso_fee_ex_vat = int(round((insurance_price * (cso_fee_rate / 100.0)) / 1.1)) if is_cso and insurance_price > 0 else 0

    margin_current = wholesale_price_ex_vat - cso_fee_ex_vat - weighted_avg_supply_per_unit
    margin_rate_current = round((margin_current / wholesale_price_ex_vat) * 100, 1) if wholesale_price_ex_vat > 0 else 0.0

    if insurance_price > 0:
        col_sim1, col_sim2 = st.columns(2)
        col_sim1.markdown(f"""
        ##### 📌 **CSO 구조 분석 요약**
        | 항목 | 금액 | 비고 |
        | :--- | :---: | :--- |
        | **보험약가** | `{insurance_price:,}원` | 기준 약가 |
        | **-VAT 제외가** | `{vat_ex_price:,}원` | 1.1 환산 |
        | **전산매출 (89%)** | `{wholesale_price_ex_vat:,}원` | 도매할인 11% 적용 |
        | **CSO 수수료 ({cso_fee_rate:.0f}%)** | `{cso_fee_ex_vat:,}원` | VAT 제외 |
        """)
        col_sim2.markdown(f"""
        ##### 📌 **위탁사 공헌이익 (현재 입력값 기준)**
        | 구분 | 현재 (Current) |
        | :--- | :---: |
        | **공급단가** | `{weighted_avg_supply_per_unit:,}원` |
        | **공헌이익** | `{margin_current:,}원` |
        | **공헌이익률** | **`{margin_rate_current:.1f}%`** |
        """)

    st.markdown("---")
    st.subheader("💡 Step 1. AI 인상 전략 옵션 제안 생성")

    if st.button("🤖 AI 인상 전략 옵션 3가지 도출하기", type="primary"):
        if not item_name:
            st.warning("제품명을 입력해 주세요!")
        else:
            sku_details_prompt = f"- 규격 1({sku1_name}): 원가 {cost_sku1:,}원 / 현공급가 {supply_sku1:,}원 (생산비율 {ratio_sku1}%)\n- 규격 2({sku2_name}): 원가 {cost_sku2:,}원 / 현공급가 {supply_sku2:,}원 (생산비율 {ratio_sku2}%)"
            if use_sku3:
                sku_details_prompt += f"\n- 규격 3({sku3_name}): 원가 {cost_sku3:,}원 / 현공급가 {supply_sku3:,}원 (생산비율 {ratio_sku3}%)"

            prompt_options = f"""
            당신은 동화약품 수탁(CMO)영업팀의 최고의 수석 전략 컨설턴트입니다.
            포장 규격({3 if use_sku3 else 2}개 SKU)의 원가 및 단가 현황과 기준 배치 사이즈({batch_size_num:,}{unit_kor}) 기반 생산 비율 조절 근거를 종합 분석하여 전략적 인상 옵션 안 3가지를 작성해 주세요.

            [제품 및 포장 현황]
            - 제품명: {item_name} ({form_type})
            - 기준 배치 사이즈: {batch_size_num:,}{unit_kor}
            - 약가: {insurance_price:,}원 (VAT제외 전산매출: {wholesale_price_ex_vat:,}원)
            - CSO 수수료: {cso_fee_rate:.0f}% ({cso_fee_ex_vat:,}원)
            {sku_details_prompt}
            - 가중평균 현황: 원가 {weighted_avg_cost_per_unit:,}원 / 현공급가 {weighted_avg_supply_per_unit:,}원
            - 동화약품 이익 현황: 매출이익 {cmo_profit_per_unit:,}원 (이익률 {cmo_profit_margin_rate:.1f}%)

            [작성 형식]
            ■ 옵션 A [대용량/주력규격 전환 및 비율 조절 유도안]
            ■ 옵션 B [가중평균 원가 보전안]
            ■ 옵션 C [상호 타협/슬라이딩 단계 적용안]
            """
            with st.spinner("AI가 최적의 인상 전략 옵션 3가지를 도출 중입니다..."):
                res_text = generate_ai_response(prompt_options)
                if res_text:
                    st.session_state['ai_options_text'] = res_text

    if 'ai_options_text' in st.session_state:
        st.markdown("### 📋 도출된 AI 제안 옵션 분석")
        st.info(st.session_state['ai_options_text'])
        st.markdown("### 📊 옵션별 Before vs After 비교표")
        
        # 옵션별 스펙 계산
        s1_a, s2_a, s3_a = int(round(supply_sku1 * 1.10)), supply_sku2, (supply_sku3 if use_sku3 else 0)
        avg_s_a = int(round((s1_a * opt_r1_f) + (s2_a * opt_r2_f) + (s3_a * opt_r3_f)))
        margin_a = round(((avg_s_a - opt_weighted_cost) / avg_s_a) * 100, 1) if avg_s_a > 0 else 0
        client_margin_a = round(((wholesale_price_ex_vat - cso_fee_ex_vat - avg_s_a) / wholesale_price_ex_vat) * 100, 1) if wholesale_price_ex_vat > 0 else 0

        avg_s_b = int(round(weighted_avg_cost_per_unit * 1.12))
        margin_b = round(((avg_s_b - weighted_avg_cost_per_unit) / avg_s_b) * 100, 1) if avg_s_b > 0 else 0
        client_margin_b = round(((wholesale_price_ex_vat - cso_fee_ex_vat - avg_s_b) / wholesale_price_ex_vat) * 100, 1) if wholesale_price_ex_vat > 0 else 0

        avg_s_c = int(round(weighted_avg_supply_per_unit + ((avg_s_b - weighted_avg_supply_per_unit) * 0.5)))
        margin_c = round(((avg_s_c - weighted_avg_cost_per_unit) / avg_s_c) * 100, 1) if avg_s_c > 0 else 0
        client_margin_c = round(((wholesale_price_ex_vat - cso_fee_ex_vat - avg_s_c) / wholesale_price_ex_vat) * 100, 1) if wholesale_price_ex_vat > 0 else 0

        df_comp = pd.DataFrame({
            "구분": ["생산 비율 Mix", "1 Batch 포장 단위", "가중평균 공급단가", "가중평균 원가", "동화약품 매출이익률", "위탁사 공헌이익률"],
            "현행 (Before)": [sku_ratio_label_curr, f"{total_curr_bottles:,}개", f"{weighted_avg_supply_per_unit:,}원", f"{weighted_avg_cost_per_unit:,}원", f"{cmo_profit_margin_rate:.1f}%", f"{margin_rate_current:.1f}%"],
            "옵션 A (비율전환)": [sku_ratio_label_opt, f"{total_opt_bottles:,}개 ({saved_bottles:-,}개)", f"{avg_s_a:,}원 ({avg_s_a - weighted_avg_supply_per_unit:+}원)", f"{opt_weighted_cost:,}원", f"{margin_a:.1f}% ({round(margin_a - cmo_profit_margin_rate, 1):+}%p)", f"{client_margin_a:.1f}% ({round(client_margin_a - margin_rate_current, 1):+}%p)"],
            "옵션 B (원가보전)": [sku_ratio_label_curr, f"{total_curr_bottles:,}개", f"{avg_s_b:,}원 ({avg_s_b - weighted_avg_supply_per_unit:+}원)", f"{weighted_avg_cost_per_unit:,}원", f"{margin_b:.1f}% ({round(margin_b - cmo_profit_margin_rate, 1):+}%p)", f"{client_margin_b:.1f}% ({round(client_margin_b - margin_rate_current, 1):+}%p)"],
            "옵션 C (슬라이딩)": [sku_ratio_label_curr, f"{total_curr_bottles:,}개", f"{avg_s_c:,}원 ({avg_s_c - weighted_avg_supply_per_unit:+}원)", f"{weighted_avg_cost_per_unit:,}원", f"{margin_c:.1f}% ({round(margin_c - cmo_profit_margin_rate, 1):+}%p)", f"{client_margin_c:.1f}% ({round(client_margin_c - margin_rate_current, 1):+}%p)"]
        })
        st.table(df_comp)

        st.markdown("---")
        st.subheader("✉️ Step 2. 전략 옵션 선택 및 메일 제안서 작성")
        selected_option = st.radio("거래처에 제안할 최종 옵션을 선택하세요:", ["옵션 A (대용량/주력규격 비율 전환 유도안)", "옵션 B (가중평균 원가 보전안)", "옵션 C (상호 타협/슬라이딩 단계 적용안)"])

        if st.button("📧 선택된 옵션으로 메일 제안서 생성하기"):
            sku_summary_txt = f"{sku1_name} {supply_sku1:,}원 / {sku2_name} {supply_sku2:,}원" + (f" / {sku3_name} {supply_sku3:,}원" if use_sku3 else "")
            prompt_email = f"""
            당신은 동화약품 수탁팀 담당자입니다. 위탁사 담당자에게 보낼 메일 제안서를 작성해 주세요.
            선택된 옵션: [{selected_option}]
            
            [기본 정보]
            - 수탁사: 동화약품 수탁팀 {user_position} {user_name}
            - 품목명: {item_name}
            - 약가: {insurance_price:,}원
            - 배치 사이즈: {batch_size_num:,}{unit_kor} (현행 포장 단위 수량: {total_curr_bottles:,}개)
            - 현행 단가: {sku_summary_txt} (가중평균 {weighted_avg_supply_per_unit:,}원)
            - 가중평균 원가: {weighted_avg_cost_per_unit:,}원
            - AI 분석 옵션 전문:
            {st.session_state['ai_options_text']}
            """
            with st.spinner("거래처 제출용 메일 Draft 생성 중..."):
                email_text = generate_ai_response(prompt_email)
                if email_text:
                    st.markdown("---")
                    st.markdown(f"### ✉️ [{selected_option}] 기반 거래처 제안 메일 Draft")
                    st.write(email_text)

# ==========================================
# 🟡 [메뉴 2~4] (예정 기능)
# ==========================================
else:
    st.subheader(menu_choice)
    st.info("🚧 **업데이트 예정 기능입니다.**")
