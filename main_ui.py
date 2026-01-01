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
        thought_container = st.container()
        answer_placeholder = st.empty()
        
        # 1. STREAMING PHASE (Better UX)
        response = st.session_state.query_engine.query(prompt)
        full_raw_text = ""
        for chunk in response.response_gen:
            full_raw_text += chunk
            # Show the user the raw stream so they see it's "thinking"
            answer_placeholder.markdown(full_raw_text + "▌")
        
        # 2. POST-PROCESSING PHASE (Cleanup)
        # Identify the thinking block regardless of tag name
        think_match = re.search(r"<(think|reasoning|tags)>(.*?)</\1>", full_raw_text, re.DOTALL | re.IGNORECASE)
        
        if think_match:
            thought_process = think_match.group(2).strip()
            # Remove all tags and thinking content from the final visible answer
            clean_answer = re.sub(r"<(think|reasoning|tags)>.*?</\1>", "", full_raw_text, flags=re.DOTALL | re.IGNORECASE).strip()
            
            # Update UI with the clean structure
            with thought_container.expander("🔍 Analītiskais pamatojums (Reasoning Chain)", expanded=True):
                st.info(thought_process)
            answer_placeholder.success(clean_answer)
        else:
            clean_answer = full_raw_text.strip()
            answer_placeholder.markdown(clean_answer)
        
        # 3. SOURCE AUDIT (Always at the bottom)
        with st.expander("📚 Izmantotie datu avoti un citāti"):
            for i, node in enumerate(response.source_nodes):
                meta = node.node.metadata
                f_name = meta.get("file_name", "Dokuments")
                page_no = meta.get("page_no", "N/A")
                score = f"{node.score:.3f}" if node.score else "N/A"
                
                st.markdown(f"**Avots {i+1}:** `{f_name}` | **Lpp:** `{page_no}` | **Score:** `{score}`")
                st.caption(node.node.get_content()[:500] + "...")
                st.divider()

    # Save ONLY the clean answer to chat history
    st.session_state.messages.append({"role": "assistant", "content": clean_answer})