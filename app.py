import streamlit as st
import pandas as pd

# 1. SETUP
st.set_page_config(page_title="TDS Tool", layout="centered")

@st.cache_data
def load_data():
    try:
        # Load the CSV
        df = pd.read_csv("tds_data.csv")
        # Clean text to prevent "Not Found" errors
        df['Section'] = df['Section'].astype(str).str.strip()
        df['Payee Type'] = df['Payee Type'].astype(str).str.strip()
        # Clean dates so 2026 works
        df['Effective From'] = pd.to_datetime(df['Effective From'], dayfirst=True, errors='coerce').fillna(pd.Timestamp('1900-01-01'))
        df['Effective To'] = pd.to_datetime(df['Effective To'], dayfirst=True, errors='coerce').fillna(pd.Timestamp('2099-12-31'))
        return df
    except Exception as e:
        st.error(f"Cannot load data: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🏛️ TDS Calculation Portal")
    
    # 2. INPUTS
    col1, col2 = st.columns(2)
    with col1:
        section = st.selectbox("1. Select Section", options=sorted(df['Section'].unique()))
        amount = st.number_input("2. Amount (INR)", min_value=0.0)
        pay_date = st.date_input("3. Payment Date")

    with col2:
        pan_status = st.radio("4. PAN Available?", ["Yes", "No"])
        # Filters payee options based on Section
        payee_options = sorted(df[df['Section'] == section]['Payee Type'].unique())
        payee_type = st.selectbox("5. Payee Category", options=payee_options)

    # 3. LOGIC
    if st.button("Calculate TDS Now"):
        target_date = pd.to_datetime(pay_date)
        potential = df[(df['Section'] == section) & (df['Payee Type'] == payee_type)]
        
        # Match date range
        rule = potential[(potential['Effective From'] <= target_date) & 
                         (potential['Effective To'] >= target_date)]
        
        # Fallback for future dates
        if rule.empty and not potential.empty:
            rule = potential.sort_values(by='Effective From', ascending=False).head(1)

        if not rule.empty:
            sel = rule.iloc[0]
            rate_raw = str(sel['Rate of TDS (%)']).strip()
            
            # Handle Section 192 "Avg" rate
            if rate_raw.lower() == 'avg':
                st.info(f"ℹ️ {sel['Notes']}")
            else:
                base_rate = float(rate_raw)
                final_rate = 20.0 if pan_status == "No" else base_rate
                threshold = float(sel['Threshold Amount (Rs)'])
                
                if amount > threshold:
                    tax = (amount * final_rate) / 100
                    st.success(f"✅ Deduct TDS: ₹{tax:,.2f}")
                    st.write(f"Applied Rate: {final_rate}%")
                else:
                    st.warning(f"Below Threshold (₹{threshold})")
