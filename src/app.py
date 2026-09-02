import streamlit as st
import os
from oracle import workflow
from dotenv import load_dotenv

load_dotenv()
password = os.getenv("PASSWORD") 

st.title("IBM Licensing Assistant")

st.caption("IBM Licensing Expertise at your fingertips")
st.markdown("""

*Get queries relating to IBM software products and licensing policies answered along with **citations to official documentation***
""")

st.divider()

if "entered_password" not in st.session_state:
    st.session_state["entered_password"] = False

if not st.session_state["entered_password"]:
    with st.form(key="auth"):
        pw = st.text_input(label="**Password**", placeholder="Please enter the password", type="password")
        st.form_submit_button()
        # print("submitted")
        if pw == password:
            st.session_state['entered_password'] = True
            st.rerun()
        elif pw:
            st.warning("The entered password is incorrect")
else:
    if 'message_history' not in st.session_state:
        st.session_state['message_history'] = []


    for message in st.session_state['message_history']:
        with st.chat_message(message['role']):
            st.text(message['content'])


    query = st.chat_input(placeholder="Ask a query about IBM licensing")

    if query:
        st.session_state["message_history"].append(
            {
                'role': "user",
                'content': query
            }
        )

        with st.chat_message('user'):
            st.text(st.session_state['message_history'][-1]['content'])
        
        response = workflow(query=query, message_history=st.session_state["message_history"])
        
        with st.chat_message('ai'):
            ai_message = st.write_stream(
                message_chunk.content[0]["text"] for message_chunk, metadata in response if message_chunk.content
            )
        
        st.session_state['message_history'].append(
            {
                "role": "ai",
                "content": ai_message
            }
        )
          
