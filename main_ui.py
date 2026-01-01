import streamlit as st
import re
from engine import get_query_engine

st.set_page_config(page_title="Latvenergo AI Insights", layout="wide", page_icon="⚡")

# Professional Styling
st.markdown("""
    <style>
    .stChatMessage { border-radius: 12px; border: 1px solid #ddd; margin-bottom: 15px; }
    .source-box { background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-size: 0.85rem; }
    .think-box { font-style: italic; color: #555; border-left: 3px solid #ccc; padding-left: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Latvenergo Stratēģiskās Izpētes Bots")
st.sidebar.button("Clear Conversation", on_click=lambda: st.session_state.clear())

if "query_engine" not in st.session_state:
    with st.spinner("Initializing Analytics Engine..."):
        st.session_state.query_engine = get_query_engine()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History (Cleanly)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("Arhivētie datu avoti"):
                st.json(message["sources"])

# User Input
if prompt := st.chat_input("Jautājiet par Latvenergo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # We separate the thinking expander from the answer container
        thought_placeholder = st.container()
        answer_placeholder = st.empty()
        
        response = st.session_state.query_engine.query(prompt)
        full_raw_text = ""
        
        # 1. STREAMING
        for chunk in response.response_gen:
            full_raw_text += chunk
            answer_placeholder.markdown(full_raw_text + "▌")
        
        # 2. PROCESSING
        if not full_raw_text.strip():
            clean_answer = "I cannot find information about this in the provided Latvenergo reports."
            answer_placeholder.error(clean_answer)
        else:
            # Extract thinking
            think_match = re.search(r"<(think|reasoning|tags)>(.*?)</\1>", full_raw_text, re.DOTALL | re.IGNORECASE)
            if think_match:
                thought_process = think_match.group(2).strip()
                clean_answer = re.sub(r"<(think|reasoning|tags)>.*?</\1>", "", full_raw_text, flags=re.DOTALL | re.IGNORECASE).strip()
                with thought_placeholder.expander("Analītiskais pamatojums", expanded=False):
                    st.markdown(f"<div class='think-box'>{thought_process}</div>", unsafe_allow_html=True)
                answer_placeholder.success(clean_answer)
            else:
                clean_answer = full_raw_text.strip()
                answer_placeholder.markdown(clean_answer)

        # 3. METADATA / SOURCES
        sources_to_save = []
        if response.source_nodes:
            with st.expander("Izmantotie datu avoti un citāti"):
                for i, node in enumerate(response.source_nodes):
                    meta = node.node.metadata
                    source_info = {
                        "Avots": i+1,
                        "Fails": meta.get("file_name"),
                        "Lpp": meta.get("page_no"),
                        "Score": round(node.score, 3) if node.score else "N/A"
                    }
                    sources_to_save.append(source_info)
                    st.markdown(f"**{source_info['Fails']} (Lpp. {source_info['Lpp']})**")
                    st.caption(node.node.get_content()[:300] + "...")
                    st.divider()

    # Save to history including the cleaned answer and the source list
    st.session_state.messages.append({
        "role": "assistant", 
        "content": clean_answer, 
        "sources": sources_to_save
    })