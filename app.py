
import math
import streamlit as st

st.set_page_config(page_title="CBC Cox Risk Calculator", page_icon="🩺", layout="wide")

PARAMS = {
    "Female": {
        "S0": 0.978,
        "beta": {"age": 1.1177, "hrr": -0.1511, "rbc": -0.0280, "wbc": 0.1182},
        "mu": {
            "age": 55.59,
            "rbc": 4.32,
            "hrr": 10.31,
            "wbc": 6.10,
        },
        "sigma": {
            "age": 10.10,
            "rbc": 0.44,
            "hrr": (11.12 - 9.50) / 1.349,
            "wbc": (7.60 - 4.90) / 1.349,
        },
        "defaults": {"age": 56.0, "hrr": 10.31, "rbc": 4.32, "wbc": 6.10},
        "ranges": {"age": (40.0, 79.0), "hrr": (7.0, 16.0), "rbc": (3.0, 6.0), "wbc": (2.0, 15.0)},
    },
    "Male": {
        "S0": 0.972,
        "beta": {"age": 0.9886, "hrr": -0.0811, "rbc": -0.0501, "wbc": 0.1331},
        "mu": {
            "age": 56.39,
            "rbc": 4.72,
            "hrr": 11.61,
            "wbc": 6.80,
        },
        "sigma": {
            "age": 10.41,
            "rbc": 0.55,
            "hrr": (12.17 - 10.34) / 1.349,
            "wbc": (8.40 - 5.50) / 1.349,
        },
        "defaults": {"age": 56.0, "hrr": 11.61, "rbc": 4.72, "wbc": 6.80},
        "ranges": {"age": (40.0, 79.0), "hrr": (7.0, 16.0), "rbc": (3.0, 6.5), "wbc": (2.0, 15.0)},
    },
}

def z_score(x, mu, sigma):
    return (x - mu) / sigma

def calc_risk(values, p):
    z = {
        "age": z_score(values["age"], p["mu"]["age"], p["sigma"]["age"]),
        "hrr": z_score(values["hrr"], p["mu"]["hrr"], p["sigma"]["hrr"]),
        "rbc": z_score(values["rbc"], p["mu"]["rbc"], p["sigma"]["rbc"]),
        "wbc": z_score(values["wbc"], p["mu"]["wbc"], p["sigma"]["wbc"]),
    }
    lp = (
        p["beta"]["age"] * z["age"]
        + p["beta"]["hrr"] * z["hrr"]
        + p["beta"]["rbc"] * z["rbc"]
        + p["beta"]["wbc"] * z["wbc"]
    )
    risk = 1 - (p["S0"] ** math.exp(lp))
    return z, lp, risk

def risk_label(r):
    pct = r * 100
    if pct < 2.5:
        return "Low", "below 2.5%"
    elif pct < 5:
        return "Borderline", "2.5%-4.9%"
    elif pct < 10:
        return "Intermediate", "5.0%-9.9%"
    else:
        return "High", ">=10%"

st.title("CBC Cox 5-year CVD Risk Calculator")
st.caption("Interactive calculator converted from the thesis Cox Model 2 nomogram")

left, right = st.columns([1.1, 0.9], gap="large")

with left:
    sex = st.radio("Sex", list(PARAMS.keys()), horizontal=True)
    p = PARAMS[sex]

    st.markdown("### Input variables")
    c1, c2 = st.columns(2)
    with c1:
        age = st.slider("Age (years)", p["ranges"]["age"][0], p["ranges"]["age"][1], float(p["defaults"]["age"]), 1.0)
        rbc = st.slider("RBC (x10^12/L)", p["ranges"]["rbc"][0], p["ranges"]["rbc"][1], float(p["defaults"]["rbc"]), 0.01)
    with c2:
        hrr = st.slider("HRR", p["ranges"]["hrr"][0], p["ranges"]["hrr"][1], float(p["defaults"]["hrr"]), 0.01)
        wbc = st.slider("WBC (x10^9/L)", p["ranges"]["wbc"][0], p["ranges"]["wbc"][1], float(p["defaults"]["wbc"]), 0.01)

    values = {"age": age, "hrr": hrr, "rbc": rbc, "wbc": wbc}
    z, lp, risk = calc_risk(values, p)
    label, note = risk_label(risk)

with right:
    st.markdown("### Predicted 5-year risk")
    st.metric("Risk", f"{risk*100:.2f}%")
    st.metric("Risk band", f"{label} ({note})")
    st.metric("Linear predictor", f"{lp:.3f}")
    st.metric("Baseline survival S0(5)", f"{p['S0']:.3f}")

st.divider()

c3, c4 = st.columns([1.0, 1.0], gap="large")

with c3:
    st.markdown("### Standardized values (Z-scores)")
    st.table({
        "Variable": ["Age", "HRR", "RBC", "WBC"],
        "Input": [age, hrr, rbc, wbc],
        "Mean (mu)": [p["mu"]["age"], p["mu"]["hrr"], p["mu"]["rbc"], p["mu"]["wbc"]],
        "SD (sigma)": [p["sigma"]["age"], p["sigma"]["hrr"], p["sigma"]["rbc"], p["sigma"]["wbc"]],
        "Z-score": [z["age"], z["hrr"], z["rbc"], z["wbc"]],
    })

with c4:
    st.markdown("### Variable contributions")
    contrib = {
        "Age": p["beta"]["age"] * z["age"],
        "HRR": p["beta"]["hrr"] * z["hrr"],
        "RBC": p["beta"]["rbc"] * z["rbc"],
        "WBC": p["beta"]["wbc"] * z["wbc"],
    }
    st.bar_chart(contrib)

st.divider()

with st.expander("Model formula"):
    st.latex(r"Risk(5)=1-S_0(5)^{\exp(\eta)}")
    st.latex(r"\eta=\beta_{age}Z_{age}+\beta_{HRR}Z_{HRR}+\beta_{RBC}Z_{RBC}+\beta_{WBC}Z_{WBC}")
    st.latex(r"Z=(X-\mu)/\sigma")

with st.expander("Important note on precision"):
    st.warning(
        "Age and RBC center/scale are exact from the thesis tables. "
        "WBC and HRR center/scale are temporary approximations because the thesis reports median (IQR), "
        "not mean (SD), for these two variables. Replace those four values before formal public deployment."
    )

with st.expander("How to deploy this app"):
    st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")
    st.markdown(
        "For Streamlit Cloud: upload this folder to a GitHub repository, then create a new Streamlit app and select app.py."
    )
