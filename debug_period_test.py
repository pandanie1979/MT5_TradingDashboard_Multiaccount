import streamlit as st
from datetime import date, timedelta

st.title("Test Period Selection - Isolato")

account_id = "TEST"

# Test 1: Widget base senza session state
st.header("Test 1: Widget Puro")
start_date_pure = st.date_input(
    "Start Date (Puro)",
    value=date.today() - timedelta(days=7),
    key="pure_start"
)
end_date_pure = st.date_input(
    "End Date (Puro)", 
    value=date.today(),
    key="pure_end"
)
st.write(f"Pure widgets: {start_date_pure} to {end_date_pure}")

# Test 2: Con session state manuale
st.header("Test 2: Con Session State")
if "manual_start" not in st.session_state:
    st.session_state["manual_start"] = date.today() - timedelta(days=14)
if "manual_end" not in st.session_state:
    st.session_state["manual_end"] = date.today()

start_manual = st.date_input(
    "Start (Manual Session)",
    value=st.session_state["manual_start"],
    key="manual_start"
)
end_manual = st.date_input(
    "End (Manual Session)",
    value=st.session_state["manual_end"], 
    key="manual_end"
)
st.write(f"Manual session: {start_manual} to {end_manual}")

# Test 3: Debug session state
st.header("Debug Session State")
st.write("All session state keys:")
for key, value in st.session_state.items():
    if "date" in key.lower() or account_id in key:
        st.write(f"- {key}: {value}")