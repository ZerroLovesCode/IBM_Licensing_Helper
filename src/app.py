import streamlit as st
from oracle import get_oracle_response

st.title("IBM Licensing Assistant")

st.subheader("IBM Licensing Expertise at your fingertips")
st.markdown("""

*Get queries relating to IBM software products and licensing policies answered along with **citations to official documentations***
""")

st.divider()

is_submitted = False

form_data = {
    "query": None,
    "query_category": None
}

with st.form(key="get_query", enter_to_submit=False):
    form_data['query'] = st.text_area(label="**Query**", placeholder="Write your query here", )
    form_data['query_category'] = st.selectbox(label="Category", options=["Product information", "Licensing Scenario", "Other"])
    is_submitted =  st.form_submit_button("Submit")

    if(is_submitted):
        if not form_data["query"] or (form_data["query"].strip() == ""):
            st.warning("Please enter your query.")

if is_submitted and form_data['query'] and form_data['query'].strip() != '':
    response, sources = get_oracle_response(form_data["query"])
    
    st.text(response)
    st.text(sources)