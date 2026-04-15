import math
from typing import Dict, Optional, Tuple, List

import streamlit as st

st.set_page_config(
    page_title="Complementary 5-Year CVD Risk Assessment",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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


def css() -> None:
    st.markdown(
        """
<style>
:root {
    --bg: #f6f8fc;
    --card: #ffffff;
    --soft: #f8fafc;
    --border: #dbe3ef;
    --text: #0f172a;
    --muted: #64748b;
    --shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
}
html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
}
header[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}
.block-container {
    max-width: 1320px;
    padding-top: 1.3rem;
    padding-bottom: 2rem;
}
h1 {
    letter-spacing: -0.02em;
}
.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 1.15rem 1.15rem 1.2rem 1.15rem;
    box-shadow: var(--shadow);
}
.soft-card {
    background: var(--soft);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0.95rem 1rem;
}
.result-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1rem 1rem 1rem 1rem;
    box-shadow: var(--shadow);
    min-height: 210px;
}
.smallcap {
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-size: 0.72rem;
}
.model-name {
    color: var(--text);
    font-size: 1rem;
    font-weight: 700;
    margin-top: 0.2rem;
}
.model-sub {
    color: var(--muted);
    font-size: 0.88rem;
    margin-top: 0.12rem;
}
.big-number {
    color: var(--text);
    font-size: 2.25rem;
    font-weight: 750;
    line-height: 1.05;
    margin-top: 1rem;
}
.badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.24rem 0.7rem;
    font-size: 0.78rem;
    font-weight: 650;
    border: 1px solid transparent;
}
.badge-low { color: #166534; background: #dcfce7; border-color: #bbf7d0; }
.badge-borderline { color: #92400e; background: #fef3c7; border-color: #fde68a; }
.badge-high { color: #991b1b; background: #fee2e2; border-color: #fecaca; }
.badge-na { color: #475569; background: #eef2f7; border-color: #d6dee9; }
.note {
    color: #425466;
    font-size: 0.94rem;
    line-height: 1.68;
}
.note-tight {
    color: #5b6b7f;
    font-size: 0.87rem;
    line-height: 1.55;
}
.divider {
    height: 1px;
    background: #e8edf5;
    margin-top: 0.8rem;
    margin-bottom: 0.8rem;
}
.case-line {
    color: #3b4a5c;
    font-size: 0.93rem;
    line-height: 1.6;
}
.metric-hint {
    color: var(--muted);
    font-size: 0.85rem;
    margin-top: 0.55rem;
}
.stButton > button {
    width: 100%;
    border-radius: 12px;
    border: 1px solid #d4dce8;
    background: #ffffff;
    color: #0f172a;
    font-weight: 650;
    min-height: 44px;
}
.stButton > button:hover {
    border-color: #b7c4d7;
    background: #f8fafc;
}
[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    border-radius: 12px !important;
    border-color: #d8e0ec !important;
    background: #f8fafc !important;
}
[data-baseweb="select"] input,
div[data-baseweb="input"] input {
    color: #0f172a !important;
}
div[data-testid="stNumberInputStepDown"],
div[data-testid="stNumberInputStepUp"] {
    background: transparent !important;
}
div[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-radius: 18px;
    background: #ffffff;
}
</style>
""",
        unsafe_allow_html=True,
    )


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def logit(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return math.log(p / (1 - p))


def expit(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def classify_risk(risk: Optional[float]) -> Tuple[str, str]:
    if risk is None:
        return "Unavailable", "badge-na"
    pct = risk * 100
    if pct < 2.5:
        return "Low", "badge-low"
    if pct < 5.0:
        return "Borderline", "badge-borderline"
    return "High", "badge-high"


def smoking_value(smoking: str) -> Optional[int]:
    if smoking == "Yes":
        return 1
    if smoking == "No":
        return 0
    return None


def num_input(label: str, key: str, value: float, min_v: float, max_v: float, step: float, unit: str, digits: int = 2) -> float:
    st.markdown(f'<div class="smallcap">{label}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.0, 0.66])
    with c1:
        out = st.number_input(
            label,
            min_value=float(min_v),
            max_value=float(max_v),
            value=float(value),
            step=float(step),
            label_visibility="collapsed",
        )
    with c2:
        st.markdown(
            f"<div style='padding-top:0.52rem;color:#64748b;font-size:0.88rem'>{unit}</div>",
            unsafe_allow_html=True,
        )
    return round(float(out), digits)


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
        return None, "Missing required input"
    smk = smoking_value(smoking)
    if smk is None:
        return None, "Smoking status required"
    raw10 = who_raw_10y(sex, age, bmi, sbp, smk)
    raw5 = 1.0 - ((1.0 - raw10) ** 0.5)
    alpha = WHO_RECAL[sex]["alpha"]
    beta = WHO_RECAL[sex]["beta"]
    recal = expit(alpha + beta * logit(raw5))
    return recal, "Available"


def cox_risk(values: Dict[str, Optional[float]], cfg: Dict, required: List[str], smoking_key: bool = False) -> Tuple[Optional[float], str]:
    if cfg.get("s0_5y") is None:
        return None, "Not configured"

    lp = 0.0
    for key in required:
        if values.get(key) is None:
            return None, f"Missing {key.upper()}"
        z = (float(values[key]) - cfg["mu"][key]) / cfg["sd"][key]
        lp += cfg["beta"][key] * z

    if smoking_key:
        smk = smoking_value(values.get("smoking"))
        if smk is None:
            return None, "Smoking status required"
        lp += cfg["beta"]["smoking"] * smk

    risk = 1.0 - (cfg["s0_5y"] ** math.exp(lp))
    return risk, "Available"


def concordance_text(labels: List[str]) -> Tuple[str, str, str]:
    usable = [x for x in labels if x in {"Low", "Borderline", "High"}]
    if not usable:
        return "No model output available", "0/3 available", "Enter all required inputs to generate model output."

    high_n = sum(x == "High" for x in usable)
    border_n = sum(x == "Borderline" for x in usable)
    low_n = sum(x == "Low" for x in usable)
    available_n = len(usable)

    if high_n == available_n:
        return (
            "All available models indicate elevated 5-year risk.",
            f"Concordance: {high_n}/{available_n} high",
            "This pattern supports follow-up risk assessment in a structured EHR workflow.",
        )
    if high_n >= 2:
        return (
            "Most available models indicate elevated 5-year risk.",
            f"Concordance: {high_n}/{available_n} high",
            "The combined pattern is more informative than any single model viewed in isolation.",
        )
    if border_n == available_n:
        return (
            "Available models consistently indicate borderline 5-year risk.",
            f"Concordance: {border_n}/{available_n} borderline",
            "Review in context rather than relying on a single threshold alone.",
        )
    if low_n == available_n:
        return (
            "Available models consistently indicate lower 5-year risk.",
            f"Concordance: {low_n}/{available_n} low",
            "This tool is complementary and should still be interpreted alongside clinical context.",
        )
    return (
        "Model outputs are directionally mixed.",
        f"Concordance: mixed ({available_n}/3 available)",
        "When outputs diverge, use the overall pattern as a complementary signal rather than selecting one model only.",
    )


def result_card(title: str, subtitle: str, descriptor: str, risk: Optional[float], status: str) -> str:
    label, badge_cls = classify_risk(risk)
    if risk is None:
        return f'''
        <div class="result-card">
          <div class="smallcap">{title}</div>
          <div class="model-name">{subtitle}</div>
          <div class="model-sub">{descriptor}</div>
          <div class="big-number" style="font-size:1.65rem">Unavailable</div>
          <div style="margin-top:0.45rem"><span class="badge {badge_cls}">{label}</span></div>
          <div class="divider"></div>
          <div class="note-tight">{status}</div>
        </div>
        '''
    return f'''
    <div class="result-card">
      <div class="smallcap">{title}</div>
      <div class="model-name">{subtitle}</div>
      <div class="model-sub">{descriptor}</div>
      <div class="big-number">{risk*100:.2f}%</div>
      <div style="margin-top:0.45rem"><span class="badge {badge_cls}">{label}</span></div>
    </div>
    '''


css()

if "sex" not in st.session_state:
    st.session_state.sex = "Female"
if "case" not in st.session_state:
    st.session_state.case = DEFAULT_CASES[st.session_state.sex].copy()


def load_case(sex: str) -> None:
    st.session_state.sex = sex
    st.session_state.case = DEFAULT_CASES[sex].copy()


st.title("Complementary 5-Year Cardiovascular Risk Assessment")
st.caption("WHO and CBC-based Cox models for EHR-oriented complementary risk assessment")

left, right = st.columns([1.0, 1.68], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Patient profile")
    st.markdown('<div class="smallcap">Current input</div>', unsafe_allow_html=True)

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
        help="WHO and Model 3 require smoking status. Model 2 can still be used when smoking is unknown.",
    )

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Female demo"):
            load_case("Female")
            st.rerun()
    with b2:
        if st.button("Male demo"):
            load_case("Male")
            st.rerun()
    with b3:
        if st.button("Reset"):
            load_case(st.session_state.sex)
            st.rerun()

    st.session_state.case = case

    smoking_txt = {
        "Yes": "Current smoking",
        "No": "Non-smoking",
        "Unknown": "Smoking unavailable",
    }[case["smoking"]]

    st.markdown(
        f'''
        <div class="soft-card" style="margin-top:0.9rem">
          <div class="smallcap">Case summary</div>
          <div class="case-line"><b>{sex}</b>, {int(case['age'])} y</div>
          <div class="case-line">RBC {case['rbc']:.2f} ×10¹²/L &nbsp;|&nbsp; WBC {case['wbc']:.2f} ×10⁹/L &nbsp;|&nbsp; HRR {case['hrr']:.2f}</div>
          <div class="case-line">BMI {case['bmi']:.1f} kg/m² &nbsp;|&nbsp; SBP {case['sbp']:.0f} mmHg &nbsp;|&nbsp; {smoking_txt}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

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
model2_risk, model2_status = cox_risk(values, MODEL2[sex], ["age", "hrr", "rbc", "wbc"])
model3_risk, model3_status = cox_risk(values, MODEL3[sex], ["age", "bmi", "sbp", "hrr", "rbc", "wbc"], smoking_key=True)

labels = [classify_risk(x)[0] for x in [who_risk, model2_risk, model3_risk]]
interp_title, interp_tag, interp_body = concordance_text(labels)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Three-model risk results")
    st.markdown('<div class="smallcap">5-year absolute risk</div>', unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        st.markdown(
            result_card(
                "WHO",
                "WHO (recalibrated)",
                "Age + smoking + BMI + SBP",
                who_risk,
                who_status,
            ),
            unsafe_allow_html=True,
        )
    with r2:
        st.markdown(
            result_card(
                "Model 2 (Cox)",
                "Primary CBC model",
                "Age + WBC + RBC + HRR",
                model2_risk,
                model2_status,
            ),
            unsafe_allow_html=True,
        )
    with r3:
        st.markdown(
            result_card(
                "Model 3 (Cox)",
                "Integrated model",
                "Age + smoking + BMI + SBP + WBC + RBC + HRR",
                model3_risk,
                model3_status,
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        f'''
        <div class="soft-card" style="margin-top:1rem">
          <div class="smallcap">Clinical interpretation</div>
          <div class="model-name" style="margin-top:0.3rem">{interp_title}</div>
          <div style="margin-top:0.4rem"><span class="badge badge-na">{interp_tag}</span></div>
          <div class="note" style="margin-top:0.6rem">{interp_body}</div>
          <div class="metric-hint">Risk bands used on this page: low &lt; 2.5%, borderline 2.5% to &lt; 5.0%, high ≥ 5.0%.</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("About this tool"):
        st.markdown(
            """
This page is designed for complementary risk assessment in a structured EHR workflow.

- It shows WHO, Model 2, and Model 3 side by side.
- It emphasizes final risk output rather than formulas or intermediate predictors.
- It does not replace clinician judgement or formal diagnostic evaluation.
            """
        )
