import time
import streamlit as st
from google import genai

st.set_page_config(page_title="BhashaSetu AI Translator", layout="centered")
st.title("BhashaSetu AI: Multilingual Language Translator")
st.caption("1BAI103 CCA Case Study | English ↔ Kannada, Hindi, Tamil & Telugu")

# Load API key securely from Streamlit Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

LANGUAGES = ["English", "Kannada", "Hindi", "Tamil", "Telugu", "Malayalam", "Marathi"]
col1, col2 = st.columns(2)
with col1:
    src_lang = st.selectbox("Source Language", LANGUAGES, index=0)
with col2:
    tgt_lang = st.selectbox("Target Language", LANGUAGES, index=1)

tone = st.radio("Translation Tone", ["Formal", "Colloquial (Everyday)", "Code-Mixed"], horizontal=True)

text = st.text_area(
    "Enter text to translate:",
    value="Artificial intelligence is changing the world.",
    height=130,
)

if st.button("Translate", type="primary"):
    if not text.strip():
        st.warning("Please enter some text first.")
    else:
        prompt = (
            f"Translate the following text from {src_lang} to {tgt_lang} in a {tone} tone. "
            f"Return ONLY the translated text without any explanation.\n\nText: {text}"
        )
        t0 = time.perf_counter()
        with st.spinner("Translating..."):
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
            )
        latency_ms = (time.perf_counter() - t0) * 1000

        st.subheader(f"Translated Output ({tgt_lang})")
        st.success(response.text.strip())

        m1, m2 = st.columns(2)
        m1.metric("Input Characters", len(text))
        m2.metric("Response Latency", f"{latency_ms:.0f} ms")
