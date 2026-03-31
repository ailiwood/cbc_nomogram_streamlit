
# CBC Cox 5-year CVD Risk Calculator

This is a Streamlit deployment package for the thesis-derived Cox Model 2
(age + HRR + RBC + WBC).

## Exact from thesis
- sex-specific Cox coefficients
- 5-year baseline survival
- age mean/sd
- RBC mean/sd

## Temporary approximations
The thesis tables report WBC and HRR as median (IQR), not mean (SD).
Current code uses:
- mean ~= median
- sd ~= IQR / 1.349

Replace those four values in `app.py` once the original training-set preprocessing
parameters are available.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud deployment
1. Create a GitHub repository
2. Upload all files in this package
3. Open Streamlit Cloud
4. Create a new app and point it to `app.py`
