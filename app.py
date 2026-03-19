# app.py — WindSense AI Main Entry Point
import streamlit as st

st.set_page_config(
    page_title="WindSense AI",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.switch_page("pages/login.py")
else:
    st.switch_page("pages/1_Realtime.py")