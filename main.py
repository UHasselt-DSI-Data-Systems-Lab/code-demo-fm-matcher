import streamlit as st

from utils.screen_load import create_load_screen
from utils.screen_visualize import create_visualize_screen

from utils.request import Request

st.title("Schema Matching for Health Data using Foundation Models")
st.write("This will be an actual demo some day.")

with st.expander("Load Data"):
    create_load_screen()

with st.expander("Results"):
    create_visualize_screen()
    