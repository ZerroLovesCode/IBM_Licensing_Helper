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


STATUS_NODES = {
    "retrieve_chunks": "Retrieving relevant documentation...",
    "generate_response": "Generating answer..."
}

def text_stream(response):
    # status_set = set()
    # status =  st.status(label="Thinking...", expanded=False)
    # for message_chunk, metadata in response:
    #     node = metadata.get("langgraph_node")
    #     if node and node not in status_set:
    #         status_set.add(node)
    #         label = STATUS_NODES.get(node, f"Working...")
    #         status.update(label=label)
        
    #     if node == "generate_response" and message_chunk.content:
    #         status.update(label="Answer ready...", state="complete")
    #         yield message_chunk.content[0]["text"]

    with st.spinner(text=f"Thinking..."):
        for message_chunk, metadata in response:
            if message_chunk.content and metadata.get("langgraph_node") == "generate_response":
                yield message_chunk.content[0]["text"]
                break
    
    for message_chunk, metadata in response:
        if message_chunk.content and metadata.get("langgraph_node") == "generate_response":
            yield message_chunk.content[0]["text"]


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
            st.markdown(message['content'])


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
                # message_chunk.content[0]["text"] for message_chunk, metadata in response if message_chunk.content if metadata.get("langgraph_node") == "generate_response"
                text_stream(response=response)
            )
        
        st.session_state['message_history'].append(
            {
                "role": "ai",
                "content": ai_message
            }
        )
          
