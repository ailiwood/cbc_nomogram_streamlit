import math
import streamlit as st

st.set_page_config(
    page_title="CBC-Based CVD Risk Assessment",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 1.2rem; max-width: 1400px;}
[data-testid="stMetricValue"] {font-size: 2rem;}
.smallcap {font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase; color: #64748b;}
.panel-card {
    background: rgba(255,255,255,0.92);
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 1rem 1rem 1.1rem 1rem;
    box-shadow: 0 10px 30px rgba(15,23,42,0.05);
}
.soft-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 1rem;
}
.kpi-card {
    background: white;
    border-radius: 22px;
    padding: 1rem 1rem 1.1rem 1rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 30px rgba(15,23,42,0.05);
}
.kpi-bar {height: 6px; width: 74px; border-radius: 999px; margin-bottom: 0.75rem;}
.profile-bar-bg {
    height: 16px; border-radius: 999px; background: #e2e8f0; overflow: hidden;
}
.profile-bar-fill {
    height: 16px; border-radius: 999px;
    background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 48%, #f43f5e 100%);
}
.badge {
    display:inline-block; border-radius:999px; padding:0.3rem 0.75rem;
    font-size:0.82rem; border:1px solid #e2e8f0; background:white;
}
.summary-row {
    display:flex; justify-content:space-between; align-items:center;
    background:#f8fafc; border-radius:16px; padding:0.95rem 1rem; margin-bottom:0.7rem;
}
</style>
""", unsafe_allow_html=True)

PARAMS = {
    "Female": {
        "label": "Female",
        "S0": 0.978,
        "beta": {"age": 1.1177, "hrr": -0.1511, "rbc": -0.0280, "wbc": 0.1182},
        "mu": {"age": 55.59, "rbc": 4.32, "hrr": 10.31, "wbc": 6.10},
        "sigma": {"age": 10.10, "rbc": 0.44, "hrr": 1.20, "wbc": 2.00},
        "ranges": {"age": (40.0, 79.0), "hrr": (7.0, 16.0), "rbc": (3.0, 6.0), "wbc": (2.0, 15.0)},
        "defaults": {"age": 58.0, "hrr": 10.31, "rbc": 4.42, "wbc": 6.80, "bmi": 24.6, "sbp": 136.0, "smoking": "No"},
    },
    "Male": {
        "label": "Male",
        "S0": 0.972,
        "beta": {"age": 0.9886, "hrr": -0.0811, "rbc": -0.0501, "wbc": 0.1331},
        "mu": {"age": 56.39, "rbc": 4.72, "hrr": 11.61, "wbc": 6.80},
        "sigma": {"age": 10.41, "rbc": 0.55, "hrr": 1.36, "wbc": 2.30},
        "ranges": {"age": (40.0, 79.0), "hrr": (7.0, 16.0), "rbc": (3.0, 6.5), "wbc": (2.0, 15.0)},
        "defaults": {"age": 58.0, "hrr": 11.61, "rbc": 4.92, "wbc": 6.80, "bmi": 25.8, "sbp": 136.0, "smoking": "No"},
    },
}

def z_score(x, mu, sigma):
    return (x - mu) / sigma

def calc(values, p):
    z = {
        "age": z_score(values["age"], p["mu"]["age"], p["sigma"]["age"]),
        "hrr": z_score(values["hrr"], p["mu"]["hrr"], p["sigma"]["hrr"]),
        "rbc": z_score(values["rbc"], p["mu"]["rbc"], p["sigma"]["rbc"]),
        "wbc": z_score(values["wbc"], p["mu"]["wbc"], p["sigma"]["wbc"]),
    }
    contrib = {
        "age": p["beta"]["age"] * z["age"],
        "hrr": p["beta"]["hrr"] * z["hrr"],
        "rbc": p["beta"]["rbc"] * z["rbc"],
        "wbc": p["beta"]["wbc"] * z["wbc"],
    }
    lp = sum(contrib.values())
    relative_hazard = math.exp(lp)
    risk = 1 - (p["S0"] ** relative_hazard)
    risk_index = 100 / (1 + math.exp(-lp))
    return z, contrib, lp, relative_hazard, risk, risk_index

def risk_profile(risk):
    pct = risk * 100
    if pct < 2.5:
        return "Low", "Below 2.5% 5-year risk", "#dcfce7", "#166534"
    elif pct < 5:
        return "Borderline", "2.5%–4.9% 5-year risk", "#fef3c7", "#92400e"
    elif pct < 10:
        return "Intermediate", "5.0%–9.9% 5-year risk", "#ffedd5", "#9a3412"
    return "Elevated", "10% or higher 5-year risk", "#ffe4e6", "#be123c"

def num_input_block(label, unit, value, min_v, max_v, step, digits=2):
    st.markdown(f'<div class="smallcap">{label}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.0, 0.75])
    with c1:
        v = st.number_input(label, min_value=min_v, max_value=max_v, value=float(value), step=float(step), label_visibility="collapsed")
    with c2:
        st.markdown(f"<div style='padding-top:0.55rem;color:#64748b;font-size:0.88rem'>{unit}</div>", unsafe_allow_html=True)
    v = st.slider(f"{label} slider", min_value=float(min_v), max_value=float(max_v), value=float(v), step=float(step), label_visibility="collapsed")
    return round(v, digits)

if "sex" not in st.session_state:
    st.session_state.sex = "Female"
if "values" not in st.session_state:
    st.session_state.values = PARAMS["Female"]["defaults"].copy()

def load_case(sex):
    st.session_state.sex = sex
    st.session_state.values = PARAMS[sex]["defaults"].copy()

sex = st.session_state.sex
p = PARAMS[sex]
vals = st.session_state.values

left, right = st.columns([0.9, 2.1], gap="large")

with left:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown("## Input panel")
    st.caption("Interactive")
    c1, c2 = st.columns(2)
    with c1:
        chosen_sex = st.selectbox("SEX", ["Female", "Male"], index=0 if sex=="Female" else 1)
    with c2:
        model = st.selectbox("MODEL", ["Model 2"], index=0)
    if chosen_sex != st.session_state.sex:
        load_case(chosen_sex)
        st.rerun()

    st.markdown('<div class="smallcap" style="margin-top:0.8rem">Core inputs</div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        vals["age"] = num_input_block("AGE", "years", vals["age"], *p["ranges"]["age"], 1.0, 0)
        vals["rbc"] = num_input_block("RBC", "×10¹²/L", vals["rbc"], *p["ranges"]["rbc"], 0.01, 2)
    with b:
        vals["wbc"] = num_input_block("WBC", "×10⁹/L", vals["wbc"], *p["ranges"]["wbc"], 0.01, 2)
        vals["hrr"] = num_input_block("HRR", "ratio", vals["hrr"], *p["ranges"]["hrr"], 0.01, 2)

    st.markdown('<div class="smallcap" style="margin-top:0.8rem">Additional inputs</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="smallcap">BMI</div>', unsafe_allow_html=True)
        vals["bmi"] = st.number_input("BMI", min_value=10.0, max_value=60.0, value=float(vals["bmi"]), step=0.1, label_visibility="collapsed")
        st.caption("kg/m²")
    with c4:
        st.markdown('<div class="smallcap">SBP</div>', unsafe_allow_html=True)
        vals["sbp"] = st.number_input("SBP", min_value=60.0, max_value=260.0, value=float(vals["sbp"]), step=1.0, label_visibility="collapsed")
        st.caption("mmHg")
    vals["smoking"] = st.selectbox("SMOKING", ["No", "Yes"], index=0 if vals["smoking"]=="No" else 1)

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Female case", use_container_width=True):
            load_case("Female")
            st.rerun()
    with b2:
        if st.button("Male case", use_container_width=True):
            load_case("Male")
            st.rerun()
    with b3:
        if st.button("Reset", use_container_width=True, type="primary"):
            load_case(st.session_state.sex)
            st.rerun()

    st.markdown(
        '''
        <div class="soft-card" style="margin-top:1rem; font-size:0.92rem; line-height:1.8; color:#475569;">
        This interface provides a sex-specific Cox-based complementary cardiovascular risk assessment using age and routine CBC markers available in structured electronic health records.
        </div>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.session_state.values = vals
z, contrib, lp, rh, risk, risk_index = calc(vals, p)
profile, profile_desc, profile_bg, profile_fg = risk_profile(risk)

with right:
    k1, k2, k3, k4 = st.columns(4)
    kpis = [
        (k1, "linear-gradient(90deg,#a855f7,#ec4899)", "Risk index", f"{risk_index:.2f}", "Composite linear score under selected model"),
        (k2, "linear-gradient(90deg,#3b82f6,#06b6d4)", "Relative hazard", f"{rh:.2e}", "Cox-based relative hazard scale"),
        (k3, "linear-gradient(90deg,#10b981,#84cc16)", "5-year risk", f"{risk*100:.2f}%", "Absolute risk estimate"),
        (k4, "linear-gradient(90deg,#f59e0b,#f97316)", "Risk profile", profile, "Output label for interface display"),
    ]
    for col, grad, title, value, desc in kpis:
        with col:
            st.markdown(f'''
            <div class="kpi-card">
              <div class="kpi-bar" style="background:{grad}"></div>
              <div style="font-size:0.95rem;color:#64748b">{title}</div>
              <div style="margin-top:0.35rem;font-size:2.1rem;font-weight:700;color:#020617">{value}</div>
              <div style="margin-top:0.35rem;font-size:0.88rem;color:#64748b">{desc}</div>
            </div>
            ''', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Risk profile", "Variable contribution", "Model explanation", "Workflow"])

    with tab1:
        c1, c2 = st.columns([1.25, 0.85], gap="large")
        with c1:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown(f"### Risk profile &nbsp;&nbsp;<span class='badge'>{sex} · {model}</span>", unsafe_allow_html=True)
            st.markdown('<div class="smallcap" style="margin-top:1rem">Relative hazard scale</div>', unsafe_allow_html=True)
            width_pct = max(2, min(100, risk_index))
            st.markdown(f'''
            <div class="profile-bar-bg"><div class="profile-bar-fill" style="width:{width_pct}%"></div></div>
            <div style="display:flex;justify-content:space-between;margin-top:0.45rem;color:#64748b;font-size:0.88rem"><span>Lower</span><span>Higher</span></div>
            ''', unsafe_allow_html=True)
            st.markdown(
                '''
                <div class="soft-card" style="margin-top:1rem; font-size:1rem; line-height:1.8; color:#475569;">
                This profile summarizes a sex-specific Cox-based complementary assessment using age and routine CBC markers available in structured electronic health records.
                </div>
                ''',
                unsafe_allow_html=True,
            )
            st.markdown("#### Active variables")
            c3, c4 = st.columns(2)
            cards = [
                (c3, "AGE", p["beta"]["age"], vals["age"]),
                (c4, "HRR", p["beta"]["hrr"], vals["hrr"]),
                (c3, "RBC", p["beta"]["rbc"], vals["rbc"]),
                (c4, "WBC", p["beta"]["wbc"], vals["wbc"]),
            ]
            for col, name, beta_v, input_v in cards:
                with col:
                    st.markdown(f'''
                    <div class="soft-card">
                      <div class="smallcap">{name}</div>
                      <div style="font-size:1.2rem;font-weight:700;color:#020617">β = {beta_v:.4f}</div>
                      <div style="margin-top:0.35rem;color:#64748b">Input = {input_v}</div>
                    </div>
                    ''', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### Summary")
            summary_rows = [
                ("Selected sex", sex),
                ("Selected model", model),
                ("Risk index", f"{risk_index:.2f}"),
                ("Relative hazard", f"{rh:.2e}"),
                ("5-year risk", f"{risk*100:.2f}%"),
            ]
            for k, v in summary_rows:
                st.markdown(f'<div class="summary-row"><span style="color:#64748b">{k}</span><span style="font-weight:700;color:#020617">{v}</span></div>', unsafe_allow_html=True)
            st.markdown(f'''
            <div style="border-radius:16px;padding:0.95rem 1rem;background:{profile_bg};color:{profile_fg};border:1px solid #e2e8f0">
              <div style="font-weight:700">{profile}</div>
              <div style="margin-top:0.25rem;font-size:0.92rem">{profile_desc}</div>
            </div>
            ''', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        c1, c2 = st.columns([1.05, 0.95], gap="large")
        with c1:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### Variable contribution")
            st.caption("Current-input contribution to the model linear predictor")
            display = [
                ("Age", contrib["age"], "#3b82f6", "#8b5cf6"),
                ("WBC", contrib["wbc"], "#06b6d4", "#2563eb"),
                ("RBC", contrib["rbc"], "#8b5cf6", "#d946ef"),
                ("HRR", contrib["hrr"], "#ec4899", "#f43f5e"),
            ]
            max_abs = max(abs(x[1]) for x in display) if display else 1.0
            for label, val, c_from, c_to in display:
                width = max(3, abs(val) / max_abs * 100)
                direction = "Upward" if val >= 0 else "Downward"
                st.markdown(f'''
                <div class="soft-card" style="margin-bottom:0.9rem">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                      <div style="font-weight:700;color:#020617">{label}</div>
                      <div style="font-size:0.9rem;color:#64748b">Current contribution = {val:.3f}</div>
                    </div>
                    <div class="badge">{direction}</div>
                  </div>
                  <div style="height:14px;background:#e2e8f0;border-radius:999px;overflow:hidden;margin-top:0.8rem">
                    <div style="height:14px;width:{width}%;background:linear-gradient(90deg,{c_from},{c_to});border-radius:999px"></div>
                  </div>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### How to read variable contribution")
            st.markdown('''
            Variable contribution describes how much the current value of each predictor moves the linear predictor away from the sex-specific reference profile.

            A positive contribution shifts the relative hazard upward, while a negative contribution shifts it downward. Larger absolute values indicate stronger influence under the current input combination.

            These values reflect model contribution rather than causal effect size. They are intended to explain how the current risk estimate is assembled for the selected user inputs.
            ''')
            st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        c1, c2 = st.columns([1.15, 0.85], gap="large")
        with c1:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### Model explanation")
            st.markdown('''
            This interface implements a sex-specific Cox-based complementary cardiovascular risk assessment model.

            **Core predictors**
            - Age
            - White blood cell count (WBC)
            - Red blood cell count (RBC)
            - Haemoglobin-to-red-cell-distribution-width ratio (HRR)

            **Risk scale**
            - The calculator returns a 5-year CVD risk estimate
            - It also displays the Cox-based relative hazard scale and a risk index for interface interpretation

            **Operational role**
            - Designed for complementary risk assessment when routine CBC markers are already available in structured electronic health records
            ''')
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown("### Model coefficients")
            for k, v in [
                ("β(age)", p["beta"]["age"]),
                ("β(HRR)", p["beta"]["hrr"]),
                ("β(RBC)", p["beta"]["rbc"]),
                ("β(WBC)", p["beta"]["wbc"]),
                ("S0(5)", p["S0"]),
            ]:
                st.markdown(f'<div class="summary-row"><span style="color:#64748b">{k}</span><span style="font-weight:700;color:#020617">{v:.4f}</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Suggested workflow")
        w1, w2, w3, w4 = st.columns(4)
        steps = [
            (w1, "1", "Input capture", "Enter or verify sex, age, HRR, RBC, and WBC."),
            (w2, "2", "Model calculation", "The interface standardizes inputs and computes the Cox-based risk estimate."),
            (w3, "3", "Risk interpretation", "Review the 5-year risk, relative hazard scale, and contribution pattern."),
            (w4, "4", "Operational use", "Use the result as a complementary risk signal in routine cardiovascular assessment."),
        ]
        grads = [
            "linear-gradient(90deg,#3b82f6,#06b6d4)",
            "linear-gradient(90deg,#8b5cf6,#d946ef)",
            "linear-gradient(90deg,#10b981,#84cc16)",
            "linear-gradient(90deg,#f59e0b,#f97316)",
        ]
        for (col, n, title, desc), grad in zip(steps, grads):
            with col:
                st.markdown(f'''
                <div class="soft-card" style="height:100%">
                  <div style="width:40px;height:40px;border-radius:14px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;background:{grad};margin-bottom:0.8rem">{n}</div>
                  <div style="font-size:1.08rem;font-weight:700;color:#020617">{title}</div>
                  <div style="margin-top:0.45rem;line-height:1.8;color:#64748b;font-size:0.92rem">{desc}</div>
                </div>
                ''', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
