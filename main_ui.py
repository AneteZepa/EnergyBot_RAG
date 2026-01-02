import streamlit as st
import re
from engine import get_query_engine

st.set_page_config(page_title="Latvenergo AI Insights", layout="wide", page_icon="⚡")

# Professional Styling to match your screenshot preference
st.markdown("""
    <style>
    .stChatMessage { background-color: white; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 10px; }
    .stExpander { border: none !important; box-shadow: none !important; background-color: #f8f9fa; border-radius: 8px; }
    div[data-testid="stExpanderDetails"] { padding-top: 5px; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Latvenergo Stratēģiskās Izpētes Bots")
st.caption("AI-powered analysis of 9M 2025 Financials & Strategy")

# 1. INITIALIZE ENGINE
if "query_engine" not in st.session_state:
    with st.spinner("Inicializēju RAG..."):
        st.session_state.query_engine = get_query_engine()

# 2. CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Restore the 1-2-3 layout for history
        if message["role"] == "assistant":
            # 1. Thinking
            if "thought" in message and message["thought"]:
                with st.expander("Domāšanas gaita (Reasoning)", expanded=False):
                    st.info(message["thought"])
            
            # 2. Sources
            if "sources" in message and message["sources"]:
                with st.expander("Izmantotie datu avoti (Sources)", expanded=False):
                    for src in message["sources"]:
                        st.markdown(f"**{src['Fails']} (Lpp. {src['Lpp']})** - Score: {src['Score']}")
                        st.caption(src['Text'])
                        st.divider()
            
            # 3. Answer
            st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# 3. CHAT INPUT
if prompt := st.chat_input("Jautājiet par Latvenergo 2025. gada mērķiem un sasniegumiem (LV or Eng)..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        # Create a placeholder for the streaming text
        stream_placeholder = st.empty()
        
        # Run Query
        response = st.session_state.query_engine.query(prompt)
        full_raw_text = ""
        
        # STREAMING PHASE
        for chunk in response.response_gen:
            full_raw_text += chunk
            stream_placeholder.markdown(full_raw_text + "▌")
        
        # CLEANUP PHASE (The magic happens here)
        stream_placeholder.empty() # Clear the raw stream to render the nice layout
        
        # A. Logic Extraction (Supports <think>, <logic>, <thinking>)
        think_match = re.search(r"<(think|thinking|logic|reasoning)>(.*?)</\1>", full_raw_text, re.DOTALL | re.IGNORECASE)
        thought_process = ""
        clean_answer = full_raw_text
        
        if think_match:
            thought_process = think_match.group(2).strip()
            # Remove the tag from the answer
            clean_answer = re.sub(r"<(think|thinking|logic|reasoning)>.*?</\1>", "", full_raw_text, flags=re.DOTALL | re.IGNORECASE).strip()
        
        # B. Handle Empty/No Info Responses
        # If the answer is extremely short or looks like an empty string, provide a default
        is_empty = len(clean_answer.strip()) < 5
        is_refusal = "cannot find information" in clean_answer.lower()
        
        if is_empty or (is_refusal and not thought_process):
            clean_answer = "Diemžēl dokumentos neatradu informāciju par šo jautājumu. (No info found in docs)"
            # Force update the placeholder to show the error
            answer_placeholder.error(clean_answer)
        
        # C. RENDER FINAL LAYOUT (1 -> 2 -> 3)
        
        # 1. Thinking (Collapsed)
        if thought_process:
            with st.expander("Domāšanas gaita (Reasoning)", expanded=False):
                st.info(thought_process)

        # 2. Sources (Collapsed)
        source_data = []
        if response.source_nodes:
            with st.expander("Izmantotie datu avoti (Sources)", expanded=False):
                for i, node in enumerate(response.source_nodes):
                    meta = node.node.metadata
                    src_entry = {
                        "Fails": meta.get("file_name", "Unknown"),
                        "Lpp": meta.get("page_no", "N/A"),
                        "Score": f"{node.score:.3f}" if node.score else "N/A",
                        "Text": node.node.get_content()[:300] + "..."
                    }
                    source_data.append(src_entry)
                    
                    st.markdown(f"**{src_entry['Fails']} (Lpp. {src_entry['Lpp']})** - Score: {src_entry['Score']}")
                    st.caption(src_entry['Text'])
                    st.divider()

        # 3. Final Answer (Visible)
        st.markdown(clean_answer)

    # Save structured data to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": clean_answer,
        "thought": thought_process,
        "sources": source_data
    })