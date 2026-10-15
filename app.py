"""
app.py - Streamlit Chat UI for NED Guide Competition Bot.
Final Restored & Polished Design:
- Background: #FEF9EB (Warm Beige)
- Primary Text Color: #304D6D (Deep Dusk Blue)
- Message Bubbles: Wrapped in clean cylinders colored #A6BED4 with #304D6D text
- Query Input Bar: Solid #304D6D with pure white text
- Header: Centered title "NED ADMISSIONS ASSISTANT" in clean Futura font
- Custom avatars: Student and Bot icons
- Primary Font: Futura / Futura Bk
"""

import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from retrieve import retrieve

load_dotenv()

CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.8-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
SYSTEM_PROMPT_PATH = "systemprompt.txt"
TOP_K = 5

STUDENT_SVG_PATH = os.path.join("assets", "student_icon.svg")
BOT_SVG_PATH = os.path.join("assets", "bot_icon.svg")

st.set_page_config(
    page_title="NED Admissions Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean, restored styling with #304D6D dusk blue text
st.markdown("""
<style>
    @font-face {
        font-family: 'Futura Bk';
        src: local('Futura-Book'), local('Futura Bk BT'), local('Futura'), local('Century Gothic');
    }

    /* Global Uniform Background: #FEF9EB */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #FEF9EB !important;
        font-family: 'Futura Bk', 'Futura', 'Century Gothic', -apple-system, sans-serif !important;
        color: #304D6D !important;
    }

    /* Primary text in Dusk Blue #304D6D */
    p, span, div, label, li, h1, h2, h3, h4, h5, h6 {
        color: #304D6D !important;
    }

    /* Hide top decorative header */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0px !important;
    }

    .main .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 7.5rem !important;
        max-width: 880px !important;
        margin: 0 auto !important;
    }

    /* Centered Clean Title */
    .header-container {
        text-align: center;
        margin-bottom: 1.8rem;
    }

    .header-title {
        font-family: 'Futura Bk', 'Futura', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #304D6D !important;
        margin: 0;
    }

    /* Bottom Dock Area: blends cleanly with #FEF9EB */
    footer {visibility: hidden;}
    [data-testid="stBottom"], [data-testid="stBottom"] > div {
        background-color: #FEF9EB !important;
        border-top: none !important;
    }

    /* Hamburger Menu Toggle (top left) */
    [data-testid="stSidebarCollapsedControl"] {
        color: #304D6D !important;
        background: #FFFFFF !important;
        border: 1.5px solid rgba(48, 77, 109, 0.3) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        margin-top: 0.5rem !important;
        margin-left: 0.5rem !important;
        box-shadow: 0 4px 10px rgba(48, 77, 109, 0.08) !important;
    }

    [data-testid="stSidebarCollapsedControl"]:hover {
        background: #A6BED4 !important;
        color: #FFFFFF !important;
    }

    /* Sidebar Drawer */
    [data-testid="stSidebar"] {
        background-color: #FAF5E8 !important;
        border-right: 1.5px solid rgba(48, 77, 109, 0.18) !important;
        padding: 1.5rem 1rem !important;
        font-family: 'Futura Bk', 'Futura', sans-serif !important;
    }

    /* Chat Messages Outer Layout */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        padding: 0.45rem 0 !important;
    }

    [data-testid="stChatMessageAvatarCustom"], [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        background: transparent !important;
        border: none !important;
        align-self: flex-start !important;
        margin-top: 4px !important;
    }

    /* Messages: Wrapped in Cylinder of color #A6BED4 with Dusk Blue #304D6D Text */
    [data-testid="stChatMessageContent"] {
        background-color: #A6BED4 !important;
        border: 1.5px solid rgba(48, 77, 109, 0.2) !important;
        border-radius: 26px !important;
        padding: 1.1rem 1.6rem !important;
        box-shadow: 0 4px 14px -3px rgba(166, 190, 212, 0.5) !important;
    }

    [data-testid="stChatMessageContent"] * {
        color: #304D6D !important;
        font-family: 'Futura Bk', 'Futura', sans-serif !important;
    }

    [data-testid="stChatMessageContent"] p {
        color: #304D6D !important;
        font-size: 0.98rem !important;
        line-height: 1.62 !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stChatMessageContent"] li {
        color: #304D6D !important;
    }

    [data-testid="stChatMessageContent"] strong, [data-testid="stChatMessageContent"] b {
        color: #1F364D !important;
        font-weight: 700 !important;
    }

    /* Input Query Bar: Solid Dusk Blue #304D6D with Pure White Text */
    [data-testid="stChatInput"] {
        border-radius: 28px !important;
        border: 2px solid #304D6D !important;
        background-color: #304D6D !important;
        box-shadow: 0 8px 24px -4px rgba(48, 77, 109, 0.35) !important;
        padding: 6px 14px !important;
    }

    [data-testid="stChatInput"] textarea {
        color: #FFFFFF !important;
        font-family: 'Futura Bk', 'Futura', sans-serif !important;
        font-size: 0.98rem !important;
        font-weight: 500 !important;
        background-color: transparent !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: rgba(255, 255, 255, 0.75) !important;
        font-family: 'Futura Bk', 'Futura', sans-serif !important;
        font-weight: 400 !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: #A6BED4 !important;
        box-shadow: 0 0 0 4px rgba(166, 190, 212, 0.5) !important;
    }

    /* Send Arrow Button */
    [data-testid="stChatInput"] button {
        background-color: #A6BED4 !important;
        color: #304D6D !important;
        border-radius: 50% !important;
    }

    [data-testid="stChatInput"] button:hover {
        background-color: #FFFFFF !important;
    }

    /* Organic Pulse Loader */
    .organic-loader {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        background: #A6BED4;
        border-radius: 20px;
        color: #304D6D;
        font-size: 0.88rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(166, 190, 212, 0.4);
        margin: 8px 0;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #304D6D;
        border-radius: 50%;
        animation: organicPulse 1.4s infinite ease-in-out;
    }

    .pulse-dot:nth-child(2) { animation-delay: 0.2s; background-color: #FFFFFF; }
    .pulse-dot:nth-child(3) { animation-delay: 0.4s; background-color: #304D6D; }

    @keyframes organicPulse {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1.2); opacity: 1; }
    }

    /* Sidebar Buttons */
    .stButton>button {
        background-color: #FFFFFF !important;
        color: #304D6D !important;
        border: 1.5px solid #A6BED4 !important;
        border-radius: 18px !important;
        padding: 0.65rem 1rem !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-align: left !important;
        width: 100% !important;
        box-shadow: 0 2px 6px rgba(166, 190, 212, 0.2) !important;
        margin-bottom: 0.5rem !important;
        font-family: 'Futura Bk', 'Futura', sans-serif !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button:hover {
        background-color: #A6BED4 !important;
        color: #304D6D !important;
        border-color: #304D6D !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #A6BED4 !important;
        border-radius: 16px !important;
        margin-top: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_genai_client():
    return genai.Client()


@st.cache_data
def load_system_prompt_template() -> str:
    if not os.path.exists(SYSTEM_PROMPT_PATH):
        raise FileNotFoundError(f"Missing prompt: {SYSTEM_PROMPT_PATH}")
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_standalone_query(client, chat_history, current_user_msg: str) -> str:
    if not chat_history:
        return current_user_msg

    recent_turns = chat_history[-4:]
    history_str = "\n".join([f"{turn['role'].capitalize()}: {turn['content']}" for turn in recent_turns])

    prompt = (
        "Rewrite into a single factual query for NED Undergraduate Prospectus 2025. "
        "Carry over previous topics. Output ONLY search string.\n\n"
        f"History:\n{history_str}\n\n"
        f"Current: {current_user_msg}\n\nQuery:"
    )

    try:
        res = client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt,
        )
        rewritten = res.text.strip().replace('"', '').replace("'", "")
        return rewritten if rewritten else current_user_msg
    except Exception:
        return current_user_msg


def call_gemini(client, system_instruction: str, contents) -> str:
    fallback_models = [CHAT_MODEL, "gemini-3.7-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
    seen = set()
    ordered_models = []
    for m in fallback_models:
        if m and m not in seen:
            seen.add(m)
            ordered_models.append(m)

    last_err = None
    for m in ordered_models:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.0,
                }
            )
            return res.text.strip()
        except Exception as e:
            last_err = e
            continue
    return f"Error: {last_err}"


def main():
    # Sidebar Drawer (Opened via ☰ toggle)
    with st.sidebar:
        st.markdown("""
        <div style="font-weight:700; font-size:1.05rem; color:#304D6D; margin-bottom:1.2rem;">
            NED GUIDE // PROSPECTUS 2025
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#FFFFFF; border:1.5px solid #A6BED4; border-radius:18px; padding:1rem; margin-bottom:1.2rem;">
            <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#304D6D; margin-bottom:6px;">Status</div>
            <div style="font-size:0.82rem; color:#304D6D;">● Grounded RAG Active</div>
            <div style="font-size:0.75rem; color:#304D6D; opacity:0.8; margin-top:4px;">122 Pages • Top-5 Dual Citation</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size:0.75rem; font-weight:700; text-transform:uppercase; margin-bottom:8px; color:#304D6D;'>Starter Questions</div>", unsafe_allow_html=True)
        prompts = [
            "What is the fee structure for first year?",
            "What is the semester fees for BCIT?",
            "How many seats are in Regular Scheme R-1(a)?",
            "What is the merit aggregate calculation formula?",
            "What are the eligibility criteria for Computer Systems Engineering?",
            "What is the difference between Regular and Self-Finance?"
        ]
        for p in prompts:
            if st.button(p, key=f"btn_{p}"):
                st.session_state["queued_prompt"] = p

        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        show_sources = st.checkbox("🔍 Inspect Source Chunks", value=False)
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.rerun()

    # Clean Centered Title
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">NED ADMISSIONS ASSISTANT</h1>
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am your NED Admissions Assistant. Ask me anything regarding admissions, fees, seat quotas, or eligibility criteria from the 2025 Undergraduate Prospectus."
            }
        ]

    # Render Chat History
    for msg in st.session_state.messages:
        avatar = BOT_SVG_PATH if msg["role"] == "assistant" else STUDENT_SVG_PATH
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if show_sources and "context" in msg and msg["context"]:
                with st.expander("📄 Source Chunks"):
                    st.code(msg["context"], language="markdown")

    user_input = None
    if "queued_prompt" in st.session_state and st.session_state["queued_prompt"]:
        user_input = st.session_state.pop("queued_prompt")

    chat_input = st.chat_input("Ask about NED admissions, fees, seats, or eligibility...")
    if chat_input:
        user_input = chat_input

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar=STUDENT_SVG_PATH):
            st.markdown(user_input)

        client = get_genai_client()

        # 1. Search Query
        search_query = build_standalone_query(
            client=client,
            chat_history=st.session_state.messages[:-1],
            current_user_msg=user_input
        )

        # 2. Retrieval
        retrieved_context = retrieve(search_query, k=TOP_K)

        # 3. System Prompt
        base_prompt = load_system_prompt_template()
        full_system_instruction = base_prompt.replace("{context}", retrieved_context)

        # 4. Payload
        contents = []
        for past in st.session_state.messages[-4:-1]:
            role = "user" if past["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": past["content"]}]})
        contents.append({"role": "user", "parts": [{"text": user_input}]})

        with st.chat_message("assistant", avatar=BOT_SVG_PATH):
            loader_placeholder = st.empty()
            loader_placeholder.markdown("""
            <div class="organic-loader">
                <div class="pulse-dot"></div>
                <div class="pulse-dot"></div>
                <div class="pulse-dot"></div>
                <span>Reading prospectus...</span>
            </div>
            """, unsafe_allow_html=True)

            answer = call_gemini(client, full_system_instruction, contents)
            loader_placeholder.empty()

            st.markdown(answer)
            if show_sources and retrieved_context:
                with st.expander("📄 Source Chunks"):
                    st.code(retrieved_context, language="markdown")

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "context": retrieved_context
        })


if __name__ == "__main__":
    main()
