import math
from typing import Dict, Optional, Tuple, List

import streamlit as st

st.set_page_config(
    page_title="Complementary 5-Year CVD Risk Assessment",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================
# Parameters from thesis / current app package
# =========================

WHO_EAST_ASIA = {
    "Female": {
        "chd": {
            "age": 0.1049,
            "bmi": 0.0258,
            "sbp": 0.0167,
            "smk": 1.0931,
            "age_bmi": -0.0007,
            "age_sbp": -0.0002,
            "age_smk": -0.0344,
            "s0_10y": 0.9887,
        },
        "stroke": {
            "age": 0.1046,
            "bmi": 0.0036,
            "sbp": 0.0217,
            "smk": 0.7399,
            "age_bmi": -0.00001,
            "age_sbp": -0.0005,
            "age_smk": -0.0204,
            "s0_10y": 0.9886,
        },
    },
    "Male": {
        "chd": {
            "age": 0.0736,
            "bmi": 0.0337,
            "sbp": 0.0134,
            "smk": 0.5955,
            "age_bmi": -0.0010,
            "age_sbp": -0.0002,
            "age_smk": -0.0201,
            "s0_10y": 0.9544,
        },
        "stroke": {
            "age": 0.0977,
            "bmi": 0.0160,
            "sbp": 0.0227,
            "smk": 0.5000,
            "age_bmi": -0.0004,
            "age_sbp": -0.0004,
            "age_smk": -0.0154,
            "s0_10y": 0.9848,
        },
    },
}

WHO_RECAL = {
    "Female": {"alpha": 1.2174, "beta": 1.0409},
    "Male": {"alpha": 0.9976, "beta": 1.3730},
}

# Model 2 exact coefficients + baseline survival from thesis.
# WBC and HRR mean/SD are temporary approximations: mean ~= median, sd ~= IQR/1.349.
MODEL2 = {
    "Female": {
        "s0_5y": 0.978,
        "beta": {"age": 1.1177, "hrr": -0.1511, "rbc": -0.0280, "wbc": 0.1182},
        "mu": {"age": 55.59, "hrr": 10.31, "rbc": 4.32, "wbc": 6.10},
        "sd": {"age": 10.10, "hrr": 1.201, "rbc": 0.44, "wbc": 2.001},
    },
    "Male": {
        "s0_5y": 0.972,
        "beta": {"age": 0.9886, "hrr": -0.0811, "rbc": -0.0501, "wbc": 0.1331},
        "mu": {"age": 56.39, "hrr": 11.61, "rbc": 4.72, "wbc": 6.80},
        "sd": {"age": 10.41, "hrr": 1.364, "rbc": 0.55, "wbc": 2.298},
    },
}

# Model 3 coefficients from thesis.
# IMPORTANT: exact 5-year baseline survival for Model 3 is NOT in the uploaded thesis tables.
# Leave as None until the exact female/male S0(5) is supplied from the saved Cox model.
MODEL3 = {
    "Female": {
        "s0_5y": 0.978,
        "beta": {
            "age": 1.0988,
            "smoking": -0.2586,
            "bmi": 0.0711,
            "sbp": 0.0949,
            "hrr": -0.1543,
            "rbc": -0.0394,
            "wbc": 0.1136,
        },
        "mu": {"age": 55.59, "bmi": 23.12, "sbp": 129.90, "hrr": 10.31, "rbc": 4.32, "wbc": 6.10},
        "sd": {"age": 10.10, "bmi": 2.99, "sbp": 15.90, "hrr": 1.201, "rbc": 0.44, "wbc": 2.001},
    },
    "Male": {
        "s0_5y": 0.972,
        "beta": {
            "age": 0.9658,
            "smoking": -0.0197,
            "bmi": -0.0079,
            "sbp": 0.1057,
            "hrr": -0.0807,
            "rbc": -0.0525,
            "wbc": 0.1313,
        },
        "mu": {"age": 56.39, "bmi": 23.32, "sbp": 130.57, "hrr": 11.61, "rbc": 4.72, "wbc": 6.80},
        "sd": {"age": 10.41, "bmi": 2.76, "sbp": 15.27, "hrr": 1.364, "rbc": 0.55, "wbc": 2.298},
    },
}

RANGES = {
    "age": (40.0, 79.0),
    "rbc_female": (3.0, 6.0),
    "rbc_male": (3.0, 6.5),
    "wbc": (2.0, 15.0),
    "hrr": (7.0, 16.0),
    "bmi": (10.0, 60.0),
    "sbp": (60.0, 260.0),
}

DEFAULT_CASES = {
    "Female": {"age": 56.0, "rbc": 4.32, "wbc": 6.10, "hrr": 10.31, "bmi": 23.1, "sbp": 130.0, "smoking": "No"},
    "Male": {"age": 58.0, "rbc": 4.72, "wbc": 6.80, "hrr": 11.61, "bmi": 23.3, "sbp": 131.0, "smoking": "No"},
}

TECH_NOTE = "Model 2 uses exact thesis coefficients and baseline survival. WBC/HRR mean and SD are temporary approximations inherited from the current deployment package. Model 3 coefficients are ready, but exact 5-year baseline survival still needs to be filled in from the saved Cox output before absolute risk can be shown."

# =========================
# Helpers
# =========================


def css() -> None:
    st.markdown(
        """
<style>
.block-container {
    max-width: 1320px;
    padding-top: 1.1rem;
    padding-bottom: 2rem;
}
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 1rem 1.1rem;
    box-shadow: 0 8px 26px rgba(15,23,42,0.05);
}
.card-soft {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 0.95rem 1rem;
}
.smallcap {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #64748b;
}
.big-number {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
}
.result-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    padding: 1rem 1rem 1.1rem 1rem;
    box-shadow: 0 10px 30px rgba(15,23,42,0.05);
    min-height: 215px;
}
.tag {
    display: inline-block;
    border-radius: 999px;
    padding: 0.22rem 0.68rem;
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid #e2e8f0;
    background: #ffffff;
}
.tag-low { color: #166534; background: #dcfce7; border-color: #bbf7d0; }
.tag-borderline { color: #92400e; background: #fef3c7; border-color: #fde68a; }
.tag-high { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
.tag-na { color: #475569; background: #f1f5f9; border-color: #cbd5e1; }
.note {
    font-size: 0.92rem;
    color: #475569;
    line-height: 1.7;
}
hr { margin-top: 0.8rem; margin-bottom: 0.8rem; }
</style>
""",
        unsafe_allow_html=True,
    )


def safe_num(x: Optional[float]) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def logit(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return math.log(p / (1 - p))


def expit(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def classify_risk(p: Optional[float]) -> Tuple[str, str]:
    if p is None:
        return ("N/A", "tag-na")
    pct = p * 100
    if pct < 2.5:
        return ("Low", "tag-low")
    if pct < 5.0:
        return ("Borderline", "tag-borderline")
    return ("High", "tag-high")


def consensus_label(model_labels: List[str]) -> str:
    usable = [x for x in model_labels if x in {"Low", "Borderline", "High"}]
    if not usable:
        return "No result"
    high_n = sum(x == "High" for x in usable)
    borderline_n = sum(x == "Borderline" for x in usable)
    if high_n >= 2 or (high_n == 1 and len(usable) == 1):
        return "High"
    if borderline_n == len(usable):
        return "Borderline"
    if borderline_n >= 1:
        return "Borderline"
    return "Low"


def smoking_value(smoking: str) -> Optional[int]:
    if smoking == "Yes":
        return 1
    if smoking == "No":
        return 0
    return None


def num_input(label: str, key: str, value: float, min_v: float, max_v: float, step: float, unit: str, digits: int = 2) -> float:
    st.markdown(f'<div class="smallcap">{label}</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1.0, 0.72])
    with col1:
        val = st.number_input(
            key,
            min_value=float(min_v),
            max_value=float(max_v),
            value=float(value),
            step=float(step),
            label_visibility="collapsed",
        )
    with col2:
        st.markdown(f"<div style='padding-top:0.55rem;color:#64748b;font-size:0.88rem'>{unit}</div>", unsafe_allow_html=True)
    return round(float(val), digits)


# =========================
# Risk calculation
# =========================


def who_raw_10y(sex: str, age: float, bmi: float, sbp: float, smoking: int) -> float:
    p = WHO_EAST_ASIA[sex]
    age_c = age - 60.0
    bmi_c = bmi - 25.0
    sbp_c = sbp - 120.0

    def one_outcome(name: str) -> float:
        q = p[name]
        lp = (
            q["age"] * age_c
            + q["bmi"] * bmi_c
            + q["sbp"] * sbp_c
            + q["smk"] * smoking
            + q["age_bmi"] * age_c * bmi_c
            + q["age_sbp"] * age_c * sbp_c
            + q["age_smk"] * age_c * smoking
        )
        return 1.0 - (q["s0_10y"] ** math.exp(lp))

    r_chd = one_outcome("chd")
    r_stroke = one_outcome("stroke")
    return 1.0 - (1.0 - r_chd) * (1.0 - r_stroke)


def who_recalibrated_5y(sex: str, age: Optional[float], bmi: Optional[float], sbp: Optional[float], smoking: Optional[str]) -> Tuple[Optional[float], str]:
    if age is None or bmi is None or sbp is None or smoking is None:
        return None, "Missing required inputs"
    smk = smoking_value(smoking)
    if smk is None:
        return None, "Smoking is unknown"
    raw10 = who_raw_10y(sex, age, bmi, sbp, smk)
    raw5 = 1.0 - ((1.0 - raw10) ** 0.5)
    alpha = WHO_RECAL[sex]["alpha"]
    beta = WHO_RECAL[sex]["beta"]
    recal = expit(alpha + beta * logit(raw5))
    return recal, "Available"


def cox_risk_from_standardized_model(values: Dict[str, Optional[float]], cfg: Dict, required: List[str], smoking_key: bool = False) -> Tuple[Optional[float], str]:
    if cfg.get("s0_5y") is None:
        return None, "Exact baseline survival not configured"

    beta = cfg["beta"]
    mu = cfg["mu"]
    sd = cfg["sd"]
    lp = 0.0

    for key in required:
        if values.get(key) is None:
            return None, f"Missing {key.upper()}"
        z = (float(values[key]) - mu[key]) / sd[key]
        lp += beta[key] * z

    if smoking_key:
        smk = smoking_value(values.get("smoking"))
        if smk is None:
            return None, "Smoking is unknown"
        lp += beta["smoking"] * smk

    risk = 1.0 - (cfg["s0_5y"] ** math.exp(lp))
    return risk, "Available"


# =========================
# UI
# =========================

css()

if "sex" not in st.session_state:
    st.session_state.sex = "Female"
if "case" not in st.session_state:
    st.session_state.case = DEFAULT_CASES[st.session_state.sex].copy()


def load_case(sex: str) -> None:
    st.session_state.sex = sex
    st.session_state.case = DEFAULT_CASES[sex].copy()


st.title("Complementary 5-Year Cardiovascular Risk Assessment")
st.caption("WHO + CBC-based Cox models for an EHR-oriented, complementary screening workflow")

left, right = st.columns([1.0, 1.65], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Current case")
    st.markdown('<div class="smallcap">Patient profile</div>', unsafe_allow_html=True)

    sex = st.selectbox("Sex", ["Female", "Male"], index=0 if st.session_state.sex == "Female" else 1)
    if sex != st.session_state.sex:
        load_case(sex)
        st.rerun()

    case = st.session_state.case.copy()

    c1, c2 = st.columns(2)
    with c1:
        case["age"] = num_input("Age", "age_input", case["age"], *RANGES["age"], 1.0, "years", digits=0)
        case["rbc"] = num_input(
            "RBC",
            "rbc_input",
            case["rbc"],
            *(RANGES["rbc_female"] if sex == "Female" else RANGES["rbc_male"]),
            0.01,
            "×10¹²/L",
        )
        case["bmi"] = num_input("BMI", "bmi_input", case["bmi"], *RANGES["bmi"], 0.1, "kg/m²")
    with c2:
        case["wbc"] = num_input("WBC", "wbc_input", case["wbc"], *RANGES["wbc"], 0.01, "×10⁹/L")
        case["hrr"] = num_input("HRR", "hrr_input", case["hrr"], *RANGES["hrr"], 0.01, "ratio")
        case["sbp"] = num_input("SBP", "sbp_input", case["sbp"], *RANGES["sbp"], 1.0, "mmHg", digits=0)

    case["smoking"] = st.selectbox(
        "Smoking",
        ["No", "Yes", "Unknown"],
        index=["No", "Yes", "Unknown"].index(case.get("smoking", "No")),
        help="WHO and Model 3 require smoking status. Model 2 does not.",
    )

    m1, m2, m3 = st.columns(3)
    with m1:
        if st.button("Female example", use_container_width=True):
            load_case("Female")
            st.rerun()
    with m2:
        if st.button("Male example", use_container_width=True):
            load_case("Male")
            st.rerun()
    with m3:
        if st.button("Reset", type="primary", use_container_width=True):
            load_case(st.session_state.sex)
            st.rerun()

    st.session_state.case = case

    smoking_txt = "current smoking" if case["smoking"] == "Yes" else ("non-smoking" if case["smoking"] == "No" else "smoking status unavailable")
    st.markdown(
        f'''
        <div class="card-soft" style="margin-top:0.9rem">
          <div class="smallcap">Case summary</div>
          <div class="note">
            {sex}, {int(case['age'])} years; RBC {case['rbc']:.2f} ×10¹²/L; WBC {case['wbc']:.2f} ×10⁹/L; HRR {case['hrr']:.2f}; BMI {case['bmi']:.1f} kg/m²; SBP {case['sbp']:.0f} mmHg; {smoking_txt}.
          </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# calculations
values = {
    "age": clamp(case["age"], *RANGES["age"]),
    "rbc": clamp(case["rbc"], *(RANGES["rbc_female"] if sex == "Female" else RANGES["rbc_male"])),
    "wbc": clamp(case["wbc"], *RANGES["wbc"]),
    "hrr": clamp(case["hrr"], *RANGES["hrr"]),
    "bmi": clamp(case["bmi"], *RANGES["bmi"]),
    "sbp": clamp(case["sbp"], *RANGES["sbp"]),
    "smoking": case["smoking"],
}

who_risk, who_status = who_recalibrated_5y(sex, values["age"], values["bmi"], values["sbp"], values["smoking"])
model2_risk, model2_status = cox_risk_from_standardized_model(values, MODEL2[sex], ["age", "hrr", "rbc", "wbc"])
model3_risk, model3_status = cox_risk_from_standardized_model(values, MODEL3[sex], ["age", "bmi", "sbp", "hrr", "rbc", "wbc"], smoking_key=True)

results = [
    {
        "title": "WHO",
        "subtitle": "Recalibrated WHO East Asia, 5-year risk",
        "risk": who_risk,
        "status": who_status,
        "inputs": "Age, smoking, BMI, SBP",
    },
    {
        "title": "Model 2 (Cox)",
        "subtitle": "Primary CBC model",
        "risk": model2_risk,
        "status": model2_status,
        "inputs": "Age, WBC, RBC, HRR",
    },
    {
        "title": "Model 3 (Cox)",
        "subtitle": "Integrated model",
        "risk": model3_risk,
        "status": model3_status,
        "inputs": "Age, smoking, BMI, SBP, WBC, RBC, HRR",
    },
]

labels = [classify_risk(r["risk"])[0] for r in results]
final_label = consensus_label(labels)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Risk results")
    st.markdown('<div class="smallcap">Three-model comparison</div>', unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    for col, item in zip([r1, r2, r3], results):
        label, tag_cls = classify_risk(item["risk"])
        risk_text = f"{item['risk']*100:.2f}%" if item["risk"] is not None else "—"
        with col:
            st.markdown(
                f'''
                <div class="result-card">
                  <div class="smallcap">{item['title']}</div>
                  <div style="font-size:1rem;font-weight:700;color:#0f172a;margin-top:0.2rem">{item['subtitle']}</div>
                  <div class="big-number" style="margin-top:0.85rem">{risk_text}</div>
                  <div style="margin-top:0.4rem"><span class="tag {tag_cls}">{label}</span></div>
                  <hr>
                  <div class="note"><b>Inputs:</b> {item['inputs']}</div>
                  <div class="note" style="margin-top:0.45rem"><b>Status:</b> {item['status']}</div>
                </div>
                ''',
                unsafe_allow_html=True,
            )

    overall_tag_cls = {"Low": "tag-low", "Borderline": "tag-borderline", "High": "tag-high", "No result": "tag-na"}.get(final_label, "tag-na")
    st.markdown(
        f'''
        <div class="card-soft" style="margin-top:1rem">
          <div class="smallcap">Suggested reading</div>
          <div style="margin-top:0.35rem"><span class="tag {overall_tag_cls}">Consensus: {final_label}</span></div>
          <div class="note" style="margin-top:0.55rem">
            This summary is designed for complementary use in structured EHR workflows. It does not replace clinician judgement. When multiple models are available, the combined pattern is more informative than any single score alone.
          </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)

    a, b = st.columns([1.05, 0.95], gap="large")
    with a:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### How to use this page")
        st.markdown(
            """
1. Enter the currently available examination data.
2. Review all model outputs side by side rather than selecting only one model.
3. If BMI, SBP, or smoking status is unavailable, WHO and Model 3 may be unavailable, but Model 2 can still be used.
4. Use the result as a complementary screening signal for follow-up assessment inside the EHR workflow.
"""
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Technical note")
        st.markdown(TECH_NOTE)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card" style="margin-top:1rem">', unsafe_allow_html=True)
    st.markdown("### Design rationale")
    st.markdown(
        """
- The page shows WHO, Model 2, and Model 3 together.
- Coefficients, intermediate linear predictors, and variable-contribution panels are intentionally removed from the main interface.
- The emphasis is on risk output, availability of each model, and a workflow-compatible comparison that can later be embedded into an EHR system.
"""
    )
    st.markdown('</div>', unsafe_allow_html=True)
