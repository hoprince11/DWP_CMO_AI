import streamlit as st
import pandas as pd
from datetime import datetime
from google import genai

st.set_page_config(page_title="동화약품 수탁 AI 자동화 시스템", layout="wide")

# ==========================================
# 🔒 [보안 & 사용자 관리] 세션 DB 초기화
# ==========================================
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        # 관리자 계정 (승인 완료 상태)
        "master": {
            "pw": "3019",
            "name": "최고관리자",
            "position": "관리자",
            "approved": True,
            "created_at": "2026-01-01 00:00:00"
        },
        # 기존 기본 계정 (승인 완료 상태)
        "dh_teamleader": {
            "pw": "dongwha2026!",
            "name": "홍길동",
            "position": "팀장",
            "approved": True,
            "created_at": "2026-01-01 00:00:00"
        }
    }

def auth_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🔒 동화약품 수탁 AI 자동화 시스템")
        st.caption("인가된 동화약품 팀원만 접속 가능한 내부 보안 시스템입니다.")
        st.markdown("---")
        
        tab_login, tab_signup = st.tabs(["🔑 로그인", "📝 회원가입"])
        
        # --- [1. 로그인 탭] ---
        with tab_login:
            with st.form("login_form"):
                user_id = st.text_input("사번 (ID)", key="login_id")
                user_pw = st.text_input("비밀번호 (Password)", type="password", key="login_pw")
                submit = st.form_submit_button("로그인", type="primary")
                
                if submit:
                    user_info = st.session_state["user_db"].get(user_id)
                    if user_info and user_info["pw"] == user_pw:
                        if not user_info.get("approved", False):
                            st.warning("⏳ 관리자 승인 대기 중인 계정입니다. 관리자 승인 후 로그인해 주세요.")
                        else:
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user_id
                            st.session_state["user_name"] = user_info.get("name", "")
                            st.session_state["user_position"] = user_info.get("position", "")
                            st.success("로그인에 성공하였습니다!")
                            st.rerun()
                    else:
                        st.error("❌ 사번(ID) 또는 비밀번호가 올바르지 않습니다.")
        
        # --- [2. 회원가입 탭] ---
        with tab_signup:
            with st.form("signup_form"):
                new_id = st.text_input("사번 (ID)", key="signup_id", placeholder="예: 20260101")
                new_name = st.text_input("이름", key="signup_name", placeholder="예: 홍길동")
                new_position = st.text_input("직급", key="signup_position", placeholder="예: 팀장, 과장, 대리")
                new_pw = st.text_input("비밀번호 (Password)", type="password", key="signup_pw")
                new_pw_confirm = st.text_input("비밀번호 확인", type="password", key="signup_pw_confirm")
                
                signup_submit = st.form_submit_button("회원가입 신청")
                
                if signup_submit:
                    if not new_id or not new_name or not new_position or not new_pw:
                        st.warning("모든 필드(사번, 이름, 직급, 비밀번호)를 입력해 주세요.")
                    elif new_id in st.session_state["user_db"]:
                        st.error("이미 존재하는 사번(ID)입니다.")
                    elif new_pw != new_pw_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        st.session_state["user_db"][new_id] = {
                            "pw": new_pw,
                            "name": new_name,
                            "position": new_position,
                            "approved": False,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.success("🎉 회원가입 신청이 완료되었습니다! 관리자 승인 후 로그인이 가능합니다.")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    auth_screen()
    st.stop()


# ==========================================
# 📌 [사이드바] 접속자 정보 / 설정 & 관리자 메뉴
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

# 👑 [관리자 전용] 회원가입 승인 대시보드
if curr_user_id == "master":
    st.sidebar.subheader("👑 관리자 메뉴")
    with st.sidebar.expander("🙋‍♂️ 회원가입 승인 관리", expanded=True):
        pending_users = {
            uid: uinfo for uid, uinfo in st.session_state["user_db"].items() 
            if not uinfo.get("approved", False)
        }
        
        if not pending_users:
            st.caption("승인 대기 중인 회원가입 신청이 없습니다.")
        else:
            st.write(f"**대기건수: {len(pending_users)}건**")
            for p_id, p_info in list(pending_users.items()):
                st.markdown(f"**- {p_info['name']} {p_info['position']}** (`{p_id}`)")
                st.caption(f"신청일: {p_info.get('created_at', '-')}")
                col_app, col_rej = st.columns(2)
                with col_app:
                    if st.button("승인", key=f"app_{p_id}", type="primary"):
                        st.session_state["user_db"][p_id]["approved"] = True
                        st.success(f"{p_info['name']}님 승인 완료!")
                        st.rerun()
                with col_rej:
                    if st.button("거절", key=f"rej_{p_id}"):
                        del st.session_state["user_db"][p_id]
                        st.info(f"{p_info['name']}님 거절 완료.")
                        st.rerun()

api_key = st.secrets.get("GEMINI_API_KEY", "")

st.sidebar.markdown("---")
st.sidebar.subheader("👤 작성자 정보")
company_name = st.sidebar.text_input("수탁사명", value="동화약품", disabled=True)
user_position = st.sidebar.text_input("직책", value=curr_user_pos)
user_name = st.sidebar.text_input("작성자 성명", value=curr_user_name)


# ==========================================
# 🔝 [상위 메인 헤더 & 상단 버튼형 메뉴]
# ==========================================
st.title("💊 동화약품 수탁 AI 자동화 시스템")

# 📌 왼쪽 사이드바 메뉴 구성
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

# 기존 tab 변수들을 선택된 메뉴 조건과 연결 (들여쓰기 수정 최소화)
tab1 = (menu_choice == "📊 수탁공급가 분석 & AI 제안")
tab2 = (menu_choice == "💰 CSO 수수료율 / 약가 인하 시뮬레이터 (예정)")
tab3 = (menu_choice == "📁 수탁 품목 계약 및 이력 관리 (예정)")
tab4 = (menu_choice == "📄 거래처 맞춤형 제안서 PDF (예정)")

# ==========================================
# 🟢 [메뉴 1] 수탁공급가 분석 & AI 제안
# ==========================================
if tab1:
    
    st.write("제품 기반 포장규격·Batch·포장타입·CSO 자동 시뮬레이션 및 공급단가 분석 시스템 (동화약품 수탁팀 전용)")

    st.markdown("---")
    st.subheader("📝 Step 0. 수탁 품목 기본 정보 입력")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        item_name = st.text_input(
            "제품명 / 성분명 (예: 대웅바이오암로디핀정5밀리그램)", 
            value="대웅바이오암로디핀정5밀리그램"
        )
    with c2:
        form_type = st.selectbox("제형 구분", ["정제 (T)", "캡슐 (C)"], index=0)
        unit_symbol = "T" if "정제" in form_type else "C"
        unit_kor = "정" if "정제" in form_type else "캡슐"
    with c3:
        insurance_price = st.number_input(f"보험약가 (원/{unit_kor})", min_value=0, value=312, step=1, format="%d")

    c4, c5, c6 = st.columns([2, 1, 1])
    with c4:
        batch_size_num = st.number_input(f"기준 배치 사이즈 (Batch Size, {unit_kor})", min_value=0, value=1000000, step=10000, format="%d")
        st.caption(f"💡 현재 배치 사이즈: **{batch_size_num:,}** {unit_kor}")
    with c5:
        is_cso = st.checkbox("CSO 대상 품목 여부", value=True)
    with c6:
        cso_fee_rate = st.number_input("CSO 수수료율 (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.5)

    st.markdown("---")

    # 📦 포장단위별 원가 및 단가 비교 입력
    st.subheader(f"📦 포장단위별(SKU) 1{unit_kor}당 원가 및 단가 비교 입력")

    use_sku3 = st.checkbox("☑️ 규격 3 추가 입력 (3번째 포장 규격이 있는 경우 체크)", value=False)

    if use_sku3:
        col_sku1, col_sku2, col_sku3 = st.columns(3)
    else:
        col_sku1, col_sku2 = st.columns(2)

    # 🔹 규격 1
    with col_sku1:
        st.markdown("#### 🔹 규격 1 정보")
        sku1_type = st.selectbox("포장 타입", ["PTP", "Bottle (병)"], index=0, key="sku1_type")
        sku1_pack_size = st.number_input(f"포장 규격 수치 ({unit_kor}/포장)", min_value=1, value=30, step=1, format="%d", key="sku1_size")
        sku1_name = f"{sku1_pack_size}{unit_symbol}({sku1_type.split()[0]})"
        
        cost_sku1 = st.number_input(f"{sku1_name} 1{unit_kor}당 원가 (원/{unit_kor})", min_value=0, value=65, step=1, format="%d")
        supply_sku1 = st.number_input(f"{sku1_name} 1{unit_kor}당 공급단가 (원/{unit_kor})", min_value=0, value=65, step=1, format="%d")
        
        default_ratio1 = 30 if not use_sku3 else 20
        ratio_sku1 = st.number_input(f"{sku1_name} 생산 비율 (%)", min_value=0, max_value=100, value=default_ratio1, step=5, format="%d")
        prod_sku1_qty = int(batch_size_num * (ratio_sku1 / 100.0))
        st.metric(f"{sku1_name} 생산실적 ({unit_kor})", f"{prod_sku1_qty:,} {unit_kor}")

    # 🔹 규격 2
    with col_sku2:
        st.markdown("#### 🔹 규격 2 정보")
        sku2_type = st.selectbox("포장 타입", ["Bottle (병)", "PTP"], index=0, key="sku2_type")
        sku2_pack_size = st.number_input(f"포장 규격 수치 ({unit_kor}/포장)", min_value=1, value=300, step=1, format="%d", key="sku2_size")
        sku2_name = f"{sku2_pack_size}{unit_symbol}({sku2_type.split()[0]})"
        
        cost_sku2 = st.number_input(f"{sku2_name} 1{unit_kor}당 원가 (원/{unit_kor})", min_value=0, value=29, step=1, format="%d")
        supply_sku2 = st.number_input(f"{sku2_name} 1{unit_kor}당 공급단가 (원/{unit_kor})", min_value=0, value=35, step=1, format="%d")
        
        default_ratio2 = 70 if not use_sku3 else 50
        ratio_sku2 = st.number_input(f"{sku2_name} 생산 비율 (%)", min_value=0, max_value=100, value=default_ratio2, step=5, format="%d")
        prod_sku2_qty = int(batch_size_num * (ratio_sku2 / 100.0))
        st.metric(f"{sku2_name} 생산실적 ({unit_kor})", f"{prod_sku2_qty:,} {unit_kor}")

    # 🔹 규격 3
    if use_sku3:
        with col_sku3:
            st.markdown("#### 🔹 규격 3 정보")
            sku3_type = st.selectbox("포장 타입", ["Bottle (병)", "PTP"], index=0, key="sku3_type")
            sku3_pack_size = st.number_input(f"포장 규격 수치 ({unit_kor}/포장)", min_value=1, value=90, step=1, format="%d", key="sku3_size")
            sku3_name = f"{sku3_pack_size}{unit_symbol}({sku3_type.split()[0]})"
            
            cost_sku3 = st.number_input(f"{sku3_name} 1{unit_kor}당 원가 (원/{unit_kor})", min_value=0, value=42, step=1, format="%d")
            supply_sku3 = st.number_input(f"{sku3_name} 1{unit_kor}당 공급단가 (원/{unit_kor})", min_value=0, value=46, step=1, format="%d")
            
            ratio_sku3 = st.number_input(f"{sku3_name} 생산 비율 (%)", min_value=0, max_value=100, value=30, step=5, format="%d")
            prod_sku3_qty = int(batch_size_num * (ratio_sku3 / 100.0))
            st.metric(f"{sku3_name} 생산실적 ({unit_kor})", f"{prod_sku3_qty:,} {unit_kor}")
    else:
        cost_sku3, supply_sku3, ratio_sku3, sku3_pack_size, sku3_name = 0, 0, 0, 0, ""

    total_ratio = ratio_sku1 + ratio_sku2 + ratio_sku3
    if total_ratio != 100:
        st.warning(f"⚠️ 현재 생산 비율 합계가 **{total_ratio}%** 입니다. (100%가 되도록 조정해 주세요)")

    weighted_avg_cost_per_unit = int(round((cost_sku1 * (ratio_sku1 / 100.0)) + (cost_sku2 * (ratio_sku2 / 100.0)) + (cost_sku3 * (ratio_sku3 / 100.0))))
    weighted_avg_supply_per_unit = int(round((supply_sku1 * (ratio_sku1 / 100.0)) + (supply_sku2 * (ratio_sku2 / 100.0)) + (supply_sku3 * (ratio_sku3 / 100.0))))

    cmo_profit_per_unit = weighted_avg_supply_per_unit - weighted_avg_cost_per_unit
    cmo_profit_margin_rate = round((cmo_profit_per_unit / weighted_avg_supply_per_unit) * 100, 1) if weighted_avg_supply_per_unit > 0 else 0.0

    st.info(f"⚖️ **[생산량 가중평균 통합 1{unit_kor}당 단가 및 수탁사 이익]**  \n- **가중평균 1{unit_kor}당 원가**: `{weighted_avg_cost_per_unit:,} 원` &nbsp;&nbsp;|&nbsp;&nbsp; - **가중평균 1{unit_kor}당 공급단가**: `{weighted_avg_supply_per_unit:,} 원`  \n- 💰 **동화약품 매출이익**: `{cmo_profit_per_unit:,} 원/정` &nbsp;&nbsp;|&nbsp;&nbsp; - 📈 **동화약품 매출이익률**: **`{cmo_profit_margin_rate:.1f}%`**")

    st.markdown("---")
    st.subheader("📐 기준 Batch Size 기반 포장 공정 및 단가 절감 시뮬레이션")

    opt_ratio_sku1 = max(0, ratio_sku1 - 10)
    opt_ratio_sku2 = min(100, ratio_sku2 + 10)
    opt_ratio_sku3 = ratio_sku3 if use_sku3 else 0

    curr_bottles_sku1 = int(round((batch_size_num * (ratio_sku1 / 100.0)) / sku1_pack_size)) if sku1_pack_size > 0 else 0
    curr_bottles_sku2 = int(round((batch_size_num * (ratio_sku2 / 100.0)) / sku2_pack_size)) if sku2_pack_size > 0 else 0
    curr_bottles_sku3 = int(round((batch_size_num * (ratio_sku3 / 100.0)) / sku3_pack_size)) if (use_sku3 and sku3_pack_size > 0) else 0
    total_curr_bottles = curr_bottles_sku1 + curr_bottles_sku2 + curr_bottles_sku3

    opt_bottles_sku1 = int(round((batch_size_num * (opt_ratio_sku1 / 100.0)) / sku1_pack_size)) if sku1_pack_size > 0 else 0
    opt_bottles_sku2 = int(round((batch_size_num * (opt_ratio_sku2 / 100.0)) / sku2_pack_size)) if sku2_pack_size > 0 else 0
    opt_bottles_sku3 = int(round((batch_size_num * (opt_ratio_sku3 / 100.0)) / sku3_pack_size)) if (use_sku3 and sku3_pack_size > 0) else 0
    total_opt_bottles = opt_bottles_sku1 + opt_bottles_sku2 + opt_bottles_sku3

    saved_bottles = total_curr_bottles - total_opt_bottles

    opt_weighted_supply = int(round((supply_sku1 * (opt_ratio_sku1 / 100.0)) + (supply_sku2 * (opt_ratio_sku2 / 100.0)) + (supply_sku3 * (opt_ratio_sku3 / 100.0))))
    opt_weighted_cost = int(round((cost_sku1 * (opt_ratio_sku1 / 100.0)) + (cost_sku2 * (opt_ratio_sku2 / 100.0)) + (cost_sku3 * (opt_ratio_sku3 / 100.0))))
    saved_per_unit = weighted_avg_supply_per_unit - opt_weighted_supply

    col_ratio_a, col_ratio_b = st.columns([1, 1])

    sku_ratio_label_curr = f"{ratio_sku1}% : {ratio_sku2}%" if not use_sku3 else f"{ratio_sku1}% : {ratio_sku2}% : {ratio_sku3}%"
    sku_ratio_label_opt = f"{opt_ratio_sku1}% : {opt_ratio_sku2}%" if not use_sku3 else f"{opt_ratio_sku1}% : {opt_ratio_sku2}% : {opt_ratio_sku3}%"
    sku_names_label = f"{sku1_name} : {sku2_name}" if not use_sku3 else f"{sku1_name} : {sku2_name} : {sku3_name}"

    with col_ratio_a:
        st.markdown(f"##### 📌 **1 Batch({batch_size_num:,}{unit_kor}) 생산 시 포장 단위 수량 비교**")
        sku3_curr_txt = f" / `{sku3_name}`: `{curr_bottles_sku3:,} 개`" if use_sku3 else ""
        sku3_opt_txt = f" / `{sku3_name}`: `{opt_bottles_sku3:,} 개`" if use_sku3 else ""
        st.markdown(f"""
        - **현행 비율 ({sku_ratio_label_curr}) 기준**:
          - `{sku1_name}`: `{curr_bottles_sku1:,} 개` / `{sku2_name}`: `{curr_bottles_sku2:,} 개`{sku3_curr_txt}
          - **총 포장 단위 수**: **`{total_curr_bottles:,} 개`**
        - **추천 비율 ({sku_ratio_label_opt}) 적용 시**:
          - `{sku1_name}`: `{opt_bottles_sku1:,} 개` / `{sku2_name}`: `{opt_bottles_sku2:,} 개`{sku3_opt_txt}
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
        with col_sim1:
            st.markdown("##### 📌 **CSO 구조 분석 요약**")
            st.markdown(f"""
            | 항목 | 금액 | 비고 |
            | :--- | :---: | :--- |
            | **보험약가** | `{insurance_price:,}원` | 기준 약가 |
            | **-VAT 제외가** | `{vat_ex_price:,}원` | 1.1 환산 |
            | **전산매출 (89%)** | `{wholesale_price_ex_vat:,}원` | 도매할인 11% 적용 |
            | **CSO 수수료 ({cso_fee_rate:.0f}%)** | `{cso_fee_ex_vat:,}원` | VAT 제외 |
            """)

        with col_sim2:
            st.markdown("##### 📌 **위탁사 공헌이익 (현재 입력값 기준)**")
            st.markdown(f"""
            | 구분 | 현재 (Current) |
            | :--- | :---: |
            | **공급단가** | `{weighted_avg_supply_per_unit:,}원` |
            | **공헌이익** | `{margin_current:,}원` |
            | **공헌이익률** | **`{margin_rate_current:.1f}%`** |
            """)

    st.markdown("---")
    st.subheader("💡 Step 1. AI 인상 전략 옵션 제안 생성")

    if st.button("🤖 AI 인상 전략 옵션 3가지 도출하기", type="primary"):
        if not api_key:
            st.error("좌측 사이드바에 Gemini API Key를 입력해 주세요!")
        elif not item_name:
            st.warning("제품명을 입력해 주세요!")
        else:
            client = genai.Client(api_key=api_key.strip())

            sku_details_prompt = f"""- 규격 1({sku1_name}): 원가 {cost_sku1:,}원 / 현공급가 {supply_sku1:,}원 (생산비율 {ratio_sku1}%)
- 규격 2({sku2_name}): 원가 {cost_sku2:,}원 / 현공급가 {supply_sku2:,}원 (생산비율 {ratio_sku2}%)"""
            if use_sku3:
                sku_details_prompt += f"\n- 규격 3({sku3_name}): 원가 {cost_sku3:,}원 / 현공급가 {supply_sku3:,}원 (생산비율 {ratio_sku3}%)"

            prompt_options = f"""
            당신은 동화약품 수탁(CMO)영업팀의 최고의 수석 전략 컨설턴트입니다.
            아래에 명시된 포장 규격({2 if not use_sku3 else 3}개 SKU)의 원가 및 단가 현황과 기준 배치 사이즈({batch_size_num:,}{unit_kor}) 기반 생산 비율(Mix) 조절 근거를 종합 분석하여 거래처(위탁사)와 협상할 수 있는 **3가지 전략적 인상 옵션 안**을 작성해 주세요.

            ⚠️ **[필수 준수 사항]**
            1. 아래 [제품 및 포장 현황]에 명시된 포장 규격만 사용하여 전략을 제안하세요. 명시되지 않은 포장 규격(예: 존재하지 않는 용량이나 제형)을 절대로 임의로 언급하거나 제안하지 마세요.
            2. 각 제안은 명확한 원가 설정 및 수탁사/위탁사 손익 근거에 기초해야 합니다.

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
                try:
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt_options,
                    )
                    st.session_state['ai_options_text'] = response.text
                except Exception as e:
                    st.error(f"오류가 발생했습니다. API Key를 확인해 주세요: {e}")

    if 'ai_options_text' in st.session_state:
        st.markdown("### 📋 도출된 AI 제안 옵션 분석")
        st.info(st.session_state['ai_options_text'])

        st.markdown("### 📊 옵션별 Before vs After (현행 vs 인상안) 비교표")
        
        s1_a = int(round(supply_sku1 * 1.10))
        s2_a = supply_sku2
        s3_a = supply_sku3 if use_sku3 else 0
        avg_s_a = int(round((s1_a * (opt_ratio_sku1/100)) + (s2_a * (opt_ratio_sku2/100)) + (s3_a * (opt_ratio_sku3/100))))
        profit_a = avg_s_a - opt_weighted_cost
        margin_a = round((profit_a / avg_s_a) * 100, 1) if avg_s_a > 0 else 0
        client_margin_a = round(((wholesale_price_ex_vat - cso_fee_ex_vat - avg_s_a) / wholesale_price_ex_vat) * 100, 1) if wholesale_price_ex_vat > 0 else 0

        avg_s_b = int(round(weighted_avg_cost_per_unit * 1.12))
        profit_b = avg_s_b - weighted_avg_cost_per_unit
        margin_b = round((profit_b / avg_s_b) * 100, 1) if avg_s_b > 0 else 0
        client_margin_b = round(((wholesale_price_ex_vat - cso_fee_ex_vat - avg_s_b) / wholesale_price_ex_vat) * 100, 1) if wholesale_price_ex_vat > 0 else 0

        avg_s_c = int(round(weighted_avg_supply_per_unit + ((avg_s_b - weighted_avg_supply_per_unit) * 0.5)))
        profit_c = avg_s_c - weighted_avg_cost_per_unit
        margin_c = round((profit_c / avg_s_c) * 100, 1) if avg_s_c > 0 else 0
        client_margin_c = round(((wholesale_price_ex_vat - cso_fee_ex_vat - avg_s_c) / wholesale_price_ex_vat) * 100, 1) if wholesale_price_ex_vat > 0 else 0

        comparison_data = {
            "구분": ["생산 비율 Mix", "1 Batch 포장 단위", "가중평균 공급단가", "가중평균 원가", "동화약품 매출이익률", "위탁사 공헌이익률"],
            "현행 (Before)": [
                f"{sku_ratio_label_curr}",
                f"{total_curr_bottles:,}개",
                f"{weighted_avg_supply_per_unit:,}원",
                f"{weighted_avg_cost_per_unit:,}원",
                f"{cmo_profit_margin_rate:.1f}%",
                f"{margin_rate_current:.1f}%"
            ],
            "옵션 A (비율전환 유도안)": [
                f"{sku_ratio_label_opt}",
                f"{total_opt_bottles:,}개 ({saved_bottles:-,}개)",
                f"{avg_s_a:,}원 ({avg_s_a - weighted_avg_supply_per_unit:+}원)",
                f"{opt_weighted_cost:,}원",
                f"{margin_a:.1f}% ({round(margin_a - cmo_profit_margin_rate, 1):+}%p)",
                f"{client_margin_a:.1f}% ({round(client_margin_a - margin_rate_current, 1):+}%p)"
            ],
            "옵션 B (원가 보전안)": [
                f"{sku_ratio_label_curr}",
                f"{total_curr_bottles:,}개",
                f"{avg_s_b:,}원 ({avg_s_b - weighted_avg_supply_per_unit:+}원)",
                f"{weighted_avg_cost_per_unit:,}원",
                f"{margin_b:.1f}% ({round(margin_b - cmo_profit_margin_rate, 1):+}%p)",
                f"{client_margin_b:.1f}% ({round(client_margin_b - margin_rate_current, 1):+}%p)"
            ],
            "옵션 C (슬라이딩 적용안)": [
                f"{sku_ratio_label_curr}",
                f"{total_curr_bottles:,}개",
                f"{avg_s_c:,}원 ({avg_s_c - weighted_avg_supply_per_unit:+}원)",
                f"{weighted_avg_cost_per_unit:,}원",
                f"{margin_c:.1f}% ({round(margin_c - cmo_profit_margin_rate, 1):+}%p)",
                f"{client_margin_c:.1f}% ({round(client_margin_c - margin_rate_current, 1):+}%p)"
            ]
        }

        df_comp = pd.DataFrame(comparison_data)
        st.table(df_comp)

        st.markdown("---")
        st.subheader("✉️ Step 2. 전략 옵션 선택 및 메일 제안서 작성")
        
        selected_option = st.radio(
            "거래처에 제안할 최종 옵션을 선택하세요:",
            ["옵션 A (대용량/주력규격 비율 전환 유도안)", "옵션 B (가중평균 원가 보전안)", "옵션 C (상호 타협/슬라이딩 단계 적용안)"]
        )

        if st.button("📧 선택된 옵션으로 메일 제안서 생성하기"):
            client = genai.Client(api_key=api_key.strip())

            sku_summary_txt = f"{sku1_name} {supply_sku1:,}원 / {sku2_name} {supply_sku2:,}원"
            if use_sku3:
                sku_summary_txt += f" / {sku3_name} {supply_sku3:,}원"

            prompt_email = f"""
            당신은 동화약품 수탁팀 담당자입니다.
            위탁사 담당자에게 보낼 **수탁 공급단가 조정 및 포장 비율 최적화 협의 메일 제안서**를 작성해 주세요.
            
            [작성 조건]
            1. 모든 원화 금액은 소수점 없는 정수(예: 312원, 63원)로 작성하세요.
            2. 담당자가 선택한 **[{selected_option}]**의 핵심 제안 내용이 비중 있게 반영되도록 작성하세요.
            3. 상기 입력된 포장 규격({sku_names_label}) 이외의 미입력 규격은 절대로 본문에 포함하지 마세요.
            4. 비즈니스 예의를 갖추되, 정중하고 논리적인 개조식 워딩을 사용하세요.
            5. 메일 제목, 수신/발신, 본문(1. 배경, 2. 제안 내용 및 비율 조절 효과, 3. Expectation/기대효과) 구조로 작성하세요.

            [기본 정보]
            - 수탁사: 동화약품 수탁팀 {user_position} {user_name}
            - 품목명: {item_name}
            - 약가: {insurance_price:,}원
            - 기준 배치 사이즈: {batch_size_num:,}{unit_kor} (현행 포장 단위 수량: {total_curr_bottles:,}개)
            - 현행 단가: {sku_summary_txt} (가중평균 {weighted_avg_supply_per_unit:,}원)
            - 가중평균 원가: {weighted_avg_cost_per_unit:,}원
            - AI 분석 옵션 전문:
            {st.session_state['ai_options_text']}
            """

            with st.spinner("선택하신 옵션으로 거래처 제출용 메일 제안서를 작성 중입니다..."):
                try:
                    response_email = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt_email,
                    )
                    st.markdown("---")
                    st.markdown(f"### ✉️ [{selected_option}] 기반 거래처 제안 메일 Draft")
                    st.write(response_email.text)
                except Exception as e:
                    st.error(f"메일 생성 중 오류가 발생했습니다: {e}")

# ==========================================
# 🟡 [탭 2~4] (업데이트 예정 기능들)
# ==========================================
with tab2:
    st.subheader("💰 CSO 수수료율 및 약가 인하 반응 시뮬레이터")
    st.info("🚧 **업데이트 예정 기능입니다.**")

with tab3:
    st.subheader("📁 수탁 품목 계약 및 협상 이력 대시보드")
    st.info("🚧 **업데이트 예정 기능입니다.**")

with tab4:
    st.subheader("📄 AI 거래처 맞춤형 제안서 PDF 추출")
    st.info("🚧 **업데이트 예정 기능입니다.**")
