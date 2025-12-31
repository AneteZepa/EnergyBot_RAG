import streamlit as st
import re
from engine import get_query_engine

st.set_page_config(page_title="Latvenergo AI Insights", layout="wide", page_icon="⚡")

# Custom CSS to match Latvenergo-style professionalism
st.markdown("""
    <style>
    .reportview-container { background: #f5f5f5; }
    .stChatMessage { border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 10px; }
    .stAlert { border-radius: 8px; }
    .stExpander { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Latvenergo Stratēģiskās Izpētes Bots")
st.caption("AI-powered analysis of 9M 2025 Financials & Strategy")

# 1. INITIALIZE ENGINE
if "query_engine" not in st.session_state:
    with st.spinner("Inicializēju RAG (HyDE + Reranking)..."):
        st.session_state.query_engine = get_query_engine()

# 2. CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. CHAT INPUT
if prompt := st.chat_input("Jautājiet par 2025. gada mērķiem, peļņu vai segmentiem (LV or ENG)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Containers for layout
        thought_container = st.container()
        answer_placeholder = st.empty()
        
        # We use streaming for better UX
        response = st.session_state.query_engine.query(prompt)
        
        full_response = ""
        # Handle streaming output
        for chunk in response.response_gen:
            full_response += chunk
            answer_placeholder.markdown(full_response + "▌")
        
        # 4. POST-PROCESSING: Split Thinking from Answer
        final_answer = ""
        if "<think>" in full_response and "</think>" in full_response:
            parts = full_response.split("</think>")
            # Extract thinking and clean up the tags
            thought_process = parts[0].replace("<think>", "").strip()
            final_answer = parts[1].strip()
            
            with thought_container.expander("Analītiskais pamatojums (Reasoning Chain)", expanded=True):
                st.info(thought_process)
            
            # Display the clean final answer
            answer_placeholder.success(final_answer)
        else:
            final_answer = full_response
            answer_placeholder.markdown(final_answer)
        
        # 5. SOURCE AUDIT (Using Metadata from Docling)
        with st.expander("Izmantotie datu avoti un citāti (Sources)"):
            for i, node in enumerate(response.source_nodes):
                # Safely extract metadata
                meta = node.node.metadata
                f_name = meta.get("file_name", "Dokuments")
                page_no = meta.get("page_no", "N/A")
                score = f"{node.score:.3f}" if node.score else "N/A"
                
                st.markdown(f"**Avots {i+1}:** `{f_name}` | **Lpp:** `{page_no}` | **Score:** `{score}`")
                st.caption(node.node.get_content()[:600] + "...")
                st.divider()

    # Save to history
    st.session_state.messages.append({"role": "assistant", "content": final_answer})