import streamlit as st
from data import DeeperLifeSurvey



# Set page configuration
st.set_page_config(page_title="DL Schools App", page_icon="🌍", layout="centered")

with st.container(border=True):  
# Header and section selector
    st.image('./media/Final.png')
    
    survey = DeeperLifeSurvey()
    survey.run()
  
       

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}  # Hide the hamburger menu
    footer {visibility: hidden;}  # Hide the footer
    header {visibility: hidden;}  # Hide the header
    </style>
    """,
    unsafe_allow_html=True
)


