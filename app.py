import streamlit as st
import pandas as pd

st.set_page_config(page_title="TDS Portal", layout="centered")

@st.cache_data
def load_data():
    try:
        # This 'sep=None' tells Python to guess if you used commas or tabs
        df = pd.read_csv("tds_data.csv", sep=None, engine='python')
        
        # Standardize columns
        df.columns = [c.strip() for c in df.columns]
        for col in ['Section', 'Payee Type']:
            df[col] = df[col].astype(str).str.strip()
            
        # Date Handling
        df['Effective From'] = pd.to_datetime(df['Effective From'], dayfirst=True, errors='coerce').fillna(pd.Timestamp('1900-01-01'))
        df['Effective To'] = pd.to_datetime(df['Effective To'], dayfirst=True, errors='coerce').fillna(pd.Timestamp('2099-12-31'))
        
        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🏛️ TDS Calculation Portal")
    
    col1, col2 = st.columns(2)
    with col1:
        section = st.selectbox("1. Section", options=sorted(df['Section'].unique()))
        amount = st.number_input("2. Amount (INR)", min_value=0.0)
        pay_date = st.date_input("3. Date")
    with col2:
        pan_status = st.radio("4. PAN Available?", ["Yes", "No"])
        payee_options = sorted(df[df['Section'] == section]['Payee Type'].unique())
        payee_type = st.selectbox("5. Category", options=payee_options)

    if st.button("Calculate"):
        target = pd.to_datetime(pay_date)
        pot = df[(df['Section'] == section) & (df['Payee Type'] == payee_type)]
        rule = pot[(pot['Effective From'] <= target) & (pot['Effective To'] >= target)]
        
        if rule.empty and not pot.empty:
            rule = pot.sort_values(by='Effective From', ascending=False).head(1)

        if not rule.empty:
            sel = rule.iloc[0]
            rate_raw = str(sel['Rate of TDS (%)']).strip()
            if rate_raw.lower() == 'avg':
                st.info(f"Note: {sel['Notes']}")
            else:
                base = float(rate_raw)
                final = 20.0 if pan_status == "No" else base
                thresh = float(sel['Threshold Amount (Rs)'])
                if amount > thresh:
                    st.success(f"Deduct: ₹{(amount * final / 100):,.2f}")
                else:
                    st.warning(f"Below Threshold (₹{thresh})")
