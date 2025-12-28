import streamlit as st
import re
from engine import get_query_engine

st.set_page_config(page_title="Latvenergo AI Insights", layout="wide", page_icon="⚡")

# Custom CSS to match Latvenergo-style professionalism
st.markdown("""
    <style>
    .reportview-container { background: #f5f5f5; }
    .stChatMessage { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Latvenergo Stratēģiskās Izpētes Bots")
st.caption("AI-powered analysis of 9M 2025 Financials & Strategy")

if "query_engine" not in st.session_state:
    with st.spinner("Inicializēju RAG (Docling + DeepSeek-R1)..."):
        st.session_state.query_engine = get_query_engine()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about EBITDA, AER, or 2025 targets..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        response = st.session_state.query_engine.query(prompt)
        
        for chunk in response.response_gen:
            full_response += chunk
            # Optional: Real-time parsing of <think> tags could be added here
            response_placeholder.markdown(full_response + "▌")
        
        # Post-processing: If DeepSeek uses <think> tags, we can format them
        if "<think>" in full_response:
            parts = re.split(r'</think>', full_response.replace("<think>", ""), maxsplit=1)
            if len(parts) > 1:
                with st.expander("Skatīt domāšanas gaitu (Reasoning Chain)"):
                    st.info(parts[0].strip())
                final_answer = parts[1].strip()
            else:
                final_answer = full_response
        else:
            final_answer = full_response

        response_placeholder.markdown(final_answer)
    
    st.session_state.messages.append({"role": "assistant", "content": final_answer})