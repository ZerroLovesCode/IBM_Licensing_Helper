import streamlit as st
import os
from oracle import get_oracle_response
from dotenv import load_dotenv

load_dotenv()

st.title("IBM Licensing Assistant")

st.caption("IBM Licensing Expertise at your fingertips")
st.markdown("""

*Get queries relating to IBM software products and licensing policies answered along with **citations to official documentations***
""")

st.divider()

is_submitted = False
password = os.getenv("PASSWORD") 

form_data = {
    "query": None,
    "query_category": None,
    "response_length": None,
}

with st.form(key="get_query", enter_to_submit=False):
    form_data['query'] = st.text_area(label="**Query**", placeholder="Write your query here", )
    form_data['query_category'] = st.selectbox(label="**Category**", options=["Product information", "Licensing Scenario", "General"])
    form_data['response_length'] = st.selectbox(label="**Answer length**", options=['Summarized', 'Medium', 'Long'])
    password_entered = st.text_input(label="**Password**", placeholder="Please enter the password to access the system", type="password")
    is_submitted =  st.form_submit_button("Submit")

    if(is_submitted):
        if not form_data["query"] or (form_data["query"].strip() == ""):
            st.warning("Please enter your query.")
        

if password == password_entered and is_submitted and form_data['query'] and form_data['query'].strip() != '':
    with st.spinner("Retreiving information..."):
        response, sources = get_oracle_response(query=form_data["query"], response_length=form_data['response_length'], category=form_data['query_category'])

    with st.container(border=True):
        st.markdown(response)
elif is_submitted and password != password_entered:
    st.warning("Password entered is incorrect!")