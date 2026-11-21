import csv
import io
import json
import re
import time
import streamlit as st
from gtts import gTTS
from pypdf import PdfReader
from google import genai
from google.genai import types

st.set_page_config(page_title="BhashaSetu AI Translator", layout="wide")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL_NAME = "gemini-3.5-flash-lite"

# --- CONSTANTS & LOCALIZED UI ---
TTS_CODES = {
    "English": "en",
    "Kannada": "kn",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Malayalam": "ml",
    "Marathi": "mr",
}

UI_TEXT = {
    "English": {
        "tgt_label": "Target Language",
        "tone_label": "Translation Style",
        "tones": {"Formal": "Formal (Polite)", "Colloquial": "Everyday Spoken", "Code-Mixed": "Code-Mixed (Native + English)"},
        "input_label": "Enter your message:",
        "btn": "Translate",
        "output_hdr": "Translated Output",
        "sample": "Hey bro, don't worry about the exam, it's going to be super easy.",
    },
    "Kannada": {
        "tgt_label": "ಯಾವ ಭಾಷೆಗೆ ಅನುವಾದಿಸಬೇಕು?",
        "tone_label": "ಅನುವಾದದ ಶೈಲಿ ಆಯ್ಕೆಮಾಡಿ",
        "tones": {"Formal": "ಔಪಚಾರಿಕ (ಶುದ್ಧ)", "Colloquial": "ಸಾಮಾನ್ಯ (ಮಾತನಾಡುವ ಶೈಲಿ)", "Code-Mixed": "ಮಿಶ್ರ ಭಾಷೆ (ಕಂಗ್ಲಿಷ್)"},
        "input_label": "ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ:",
        "btn": "ಅನುವಾದಿಸಿ",
        "output_hdr": "ಅನುವಾದಿತ ಫಲಿತಾಂಶ",
        "sample": "ನಮಸ್ಕಾರ, ನಾನು ಕಂಪ್ಯೂಟರ್ ಸೈನ್ಸ್ ವಿದ್ಯಾರ್ಥಿ.",
    },
    "Hindi": {
        "tgt_label": "किस भाषा में अनुवाद करें?",
        "tone_label": "अनुवाद की शैली चुनें",
        "tones": {"Formal": "औपचारिक (शुद्ध)", "Colloquial": "बोलचाल की भाषा", "Code-Mixed": "मिश्रित भाषा (हिंग्लिश)"},
        "input_label": "अपना संदेश यहाँ लिखें:",
        "btn": "अनुवाद करें",
        "output_hdr": "अनुवादित परिणाम",
        "sample": "नमस्ते, मैं कंप्यूटर साइंस का छात्र हूँ।",
    },
    "Tamil": {
        "tgt_label": "எந்த மொழியில் மொழிபெயர்க்க வேண்டும்?",
        "tone_label": "மொழிபெயர்ப்பு நடையைத் தேர்ந்தெடுக்கவும்",
        "tones": {"Formal": "முறையான (தூய தமிழ்)", "Colloquial": "பேச்சு வழக்கு", "Code-Mixed": "கலப்பு மொழி (தங்கிலிஷ்)"},
        "input_label": "உங்கள் செய்தியை இங்கே எழுதுங்கள்:",
        "btn": "மொழிபெயர்க்கவும்",
        "output_hdr": "மொழிபெயர்க்கப்பட்ட வெளியீடு",
        "sample": "வணக்கம், நான் கணினி அறிவியல் மாணவன்.",
    },
    "Telugu": {
        "tgt_label": "ఏ భాషలోకి అనువదించాలి?",
        "tone_label": "అనువాద శైలిని ఎంచుకోండి",
        "tones": {"Formal": "అధికారిక (స్వచ్ఛమైన)", "Colloquial": "వాడుక భాష", "Code-Mixed": "మిశ్రమ భాష"},
        "input_label": "మీ సందేశాన్ని ఇక్కడ రాయండి:",
        "btn": "అనువదించండి",
        "output_hdr": "అనువదించిన ఫలితం",
        "sample": "నమస్కారం, నేను కంప్యూటర్ సైన్స్ విద్యార్థిని.",
    },
    "Malayalam": {
        "tgt_label": "ഏത് ഭാഷയിലേക്ക് വിവർത്തനം ചെയ്യണം?",
        "tone_label": "വിവർത്തന ശൈലി തിരഞ്ഞെടുക്കുക",
        "tones": {"Formal": "ഔപചാരികം (ശുദ്ധമായ)", "Colloquial": "സംസാരഭാഷ", "Code-Mixed": "മിശ്രഭാഷ (മംഗ്ലീഷ്)"},
        "input_label": "നിങ്ങളുടെ സന്ദേശം ഇവിടെ എഴുതുക:",
        "btn": "വിവർത്തനം ചെയ്യുക",
        "output_hdr": "വിവർത്തനം ചെയ്ത ഫലം",
        "sample": "നമസ്കാരം, ഞാൻ കമ്പ്യൂട്ടർ സയൻസ് വിദ്യാർത്ഥിയാണ്.",
    },
    "Marathi": {
        "tgt_label": "कोणत्या भाषेत भाषांतर करायचे?",
        "tone_label": "भाषांतर शैली निवडा",
        "tones": {"Formal": "औपचारिक (शुद्ध)", "Colloquial": "बोलभाषा", "Code-Mixed": "मिश्र भाषा"},
        "input_label": "तुमचा संदेश येथे लिहा:",
        "btn": "भाषांतर करा",
        "output_hdr": "भाषांतरित निकाल",
        "sample": "नमस्कार, मी संगणक शास्त्राचा विद्यार्थी आहे.",
    },
}

LANGUAGES = list(UI_TEXT.keys())

# --- SESSION STATE ---
for key, default in [
    ("src_lang", "English"),
    ("tgt_lang", "Kannada"),
    ("history", []),
    ("last_result", None),
    ("voice_result", None),
    ("img_result", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def swap_languages():
    st.session_state.src_lang, st.session_state.tgt_lang = (
        st.session_state.tgt_lang,
        st.session_state.src_lang,
    )


def fast_config(json_mode: bool = True, max_tokens: int | None = 400):
    """Low-latency Gemini config with thinking disabled."""
    kwargs = {
        "temperature": 0.2,
        "thinking_config": types.ThinkingConfig(thinking_budget=0),
    }
    if json_mode:
        kwargs["response_mime_type"] = "application/json"
    if max_tokens is not None:
        kwargs["max_output_tokens"] = max_tokens
    return types.GenerateContentConfig(**kwargs)


def mask_pii(text: str) -> tuple[str, int]:
    """Masks emails, 12-digit Aadhaar-style IDs, and 10-digit phone numbers (DPDP Act 2023)."""
    count = 0
    patterns = [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",                     # 12-digit ID / Aadhaar
        r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b",                       # Indian mobile number
    ]
    masked = text
    for pat in patterns:
        masked, n = re.subn(pat, "[REDACTED]", masked)
        count += n
    return masked, count


def generate_tts_bytes(text: str, lang_name: str):
    """Generates MP3 audio bytes on demand using gTTS."""
    try:
        tts = gTTS(text=text, lang=TTS_CODES.get(lang_name, "en"))
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def get_tone_rule(tone_key: str, tgt_lang: str) -> str:
    rules = {
        "Formal": f"Use pure, polite, formal {tgt_lang}. Every word MUST be in {tgt_lang} script only.",
        "Colloquial": f"Use natural, casual, everyday spoken {tgt_lang}. Every word MUST be in {tgt_lang} script only.",
        "Code-Mixed": f"Use natural urban {tgt_lang}-English code-mixing in {tgt_lang} script. Mix ONLY {tgt_lang} and English—never any third language.",
    }
    return rules[tone_key]


def save_history(mode: str, src: str, tgt: str, inp: str, out: str):
    st.session_state.history.insert(
        0,
        {"Mode": mode, "Source": src, "Target": tgt, "Input": inp[:120], "Output": out[:120]},
    )
    st.session_state.history = st.session_state.history[:20]


def render_output_block(translation: str, translit: str, tgt_lang: str, key_prefix: str):
    st.success(translation)
    if translit and tgt_lang != "English":
        st.caption(f"**Pronunciation (Romanized):** {translit}")
    with st.expander("Copyable Text"):
        st.code(translation, language=None)
    if st.button("Listen (Audio)", key=f"tts_{key_prefix}"):
        with st.spinner("Generating audio..."):
            audio_bytes = generate_tts_bytes(translation, tgt_lang)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.warning("Audio temporarily unavailable.")


# --- SIDEBAR: PRIVACY, DOMAIN & HISTORY ---
with st.sidebar:
    st.header("Settings & Governance")
    pii_enabled = st.toggle("DPDP Privacy Mode (Mask PII)", value=True)
    st.caption("Redacts phone numbers, emails & 12-digit IDs before sending to AI.")

    domain = st.selectbox(
        "Domain Glossary Context",
        ["General", "Engineering / STEM", "Medical / Clinical", "Legal / Official"],
    )

    st.divider()
    st.subheader("Recent Translations")
    if st.session_state.history:
        csv_buf = io.StringIO()
        writer = csv.DictWriter(csv_buf, fieldnames=["Mode", "Source", "Target", "Input", "Output"])
        writer.writeheader()
        writer.writerows(st.session_state.history)
        st.download_button(
            "Download History (CSV)",
            data=csv_buf.getvalue(),
            file_name="bhashasetu_history.csv",
            mime="text/csv",
        )
        for item in st.session_state.history[:5]:
            st.markdown(f"**{item['Source']} → {item['Target']}** ({item['Mode']})\n> {item['Output']}")
    else:
        st.caption("No translations yet in this session.")


# --- HEADER & LANGUAGE SELECTORS WITH SWAP ---
st.title("BhashaSetu AI: Multilingual Language Translator")
st.caption("1BAI103 CCA Case Study | Localized UI • Voice • Camera OCR • PDF • DPDP Privacy • TTS")

c1, c2, c3 = st.columns([5, 1, 5])
with c1:
    src_lang = st.selectbox("Select Your Language / ನಿಮ್ಮ ಭಾಷೆ / अपनी भाषा", LANGUAGES, key="src_lang")
ui = UI_TEXT[src_lang]
with c2:
    st.write("")
    st.write("")
    st.button("⇄", on_click=swap_languages, help="Swap Source & Target Languages", use_container_width=True)
with c3:
    tgt_lang = st.selectbox(ui["tgt_label"], LANGUAGES, key="tgt_lang")

tone_keys = list(ui["tones"].keys())
selected_tone_key = st.radio(
    ui["tone_label"],
    options=tone_keys,
    format_func=lambda k: ui["tones"][k],
    horizontal=True,
)

# --- 4 MULTIMODAL TABS ---
tab_text, tab_voice, tab_camera, tab_doc = st.tabs(
    ["Text & 3-Tone Compare", "Voice Auto-Detect", "Camera / Photo", "Document / PDF"]
)

# ==============================================================================
# TAB 1: TEXT, 3-TONE COMPARISON & BACK-TRANSLATION VERIFY
# ==============================================================================
with tab_text:
    compare_all = st.checkbox("Compare all 3 tones side-by-side (Formal vs. Colloquial vs. Code-Mixed)")
    text_in = st.text_area(ui["input_label"], value=ui["sample"], height=120)

    if st.button(ui["btn"], type="primary", key="btn_text"):
        if not text_in.strip():
            st.warning("Please enter some text first.")
        elif src_lang == tgt_lang:
            st.info("Source and Target languages are the same.")
        else:
            clean_text, pii_count = mask_pii(text_in) if pii_enabled else (text_in, 0)
            if pii_count > 0:
                st.warning(f"DPDP Privacy Mode masked {pii_count} sensitive item(s): `{clean_text}`")

            t0 = time.perf_counter()
            try:
                if compare_all:
                    prompt = (
                        f"Translate the following {domain} text from {src_lang} to {tgt_lang} in THREE styles.\n"
                        f"1. formal: {get_tone_rule('Formal', tgt_lang)}\n"
                        f"2. colloquial: {get_tone_rule('Colloquial', tgt_lang)}\n"
                        f"3. code_mixed: {get_tone_rule('Code-Mixed', tgt_lang)}\n"
                        f'Return ONLY JSON with keys "formal", "colloquial", "code_mixed".\n\nText: {clean_text}'
                    )
                    with st.spinner("Generating 3-tone comparison..."):
                        resp = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=prompt,
                            config=fast_config(json_mode=True, max_tokens=500),
                        )
                    data = json.loads(resp.text)
                    latency_ms = (time.perf_counter() - t0) * 1000
                    st.subheader(f"3-Tone Comparison ({tgt_lang})")
                    k1, k2, k3 = st.columns(3)
                    k1.info(f"**Formal**\n\n{data.get('formal', '')}")
                    k2.success(f"**Colloquial**\n\n{data.get('colloquial', '')}")
                    k3.warning(f"**Code-Mixed**\n\n{data.get('code_mixed', '')}")
                    st.metric("Response Latency", f"{latency_ms:.0f} ms")
                    save_history("3-Tone", src_lang, tgt_lang, clean_text, data.get("colloquial", ""))
                else:
                    prompt = (
                        f"You are an expert native {tgt_lang} translator specializing in {domain} terminology.\n"
                        f"Style: {get_tone_rule(selected_tone_key, tgt_lang)}\n"
                        f"Never leak unrelated languages into {tgt_lang}.\n"
                        f"Translate from {src_lang} to {tgt_lang} and provide a Romanized pronunciation guide.\n"
                        f'Return ONLY JSON with exact keys: "translation" and "transliteration".\n\nText: {clean_text}'
                    )
                    with st.spinner("Translating..."):
                        resp = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=prompt,
                            config=fast_config(json_mode=True, max_tokens=300),
                        )
                    data = json.loads(resp.text)
                    latency_ms = (time.perf_counter() - t0) * 1000
                    st.session_state.last_result = {
                        "src_lang": src_lang,
                        "tgt_lang": tgt_lang,
                        "translation": data.get("translation", ""),
                        "transliteration": data.get("transliteration", ""),
                        "latency_ms": latency_ms,
                        "chars": len(clean_text),
                    }
                    save_history(selected_tone_key, src_lang, tgt_lang, clean_text, data.get("translation", ""))
            except Exception as e:
                st.error(f"API Error: {e}")

    if st.session_state.last_result and not compare_all:
        res = st.session_state.last_result
        st.subheader(f"{ui['output_hdr']} ({res['tgt_lang']})")
        render_output_block(res["translation"], res["transliteration"], res["tgt_lang"], "text")

        m1, m2 = st.columns(2)
        m1.metric("Input Characters", res["chars"])
        m2.metric("Response Latency", f"{res['latency_ms']:.0f} ms")

        if st.button("Verify Meaning (Back-Translate to Source Language)"):
            try:
                with st.spinner("Back-translating to check accuracy..."):
                    bt = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=f"Translate literally from {res['tgt_lang']} back into {res['src_lang']} to verify meaning. Return ONLY the text:\n{res['translation']}",
                        config=fast_config(json_mode=False, max_tokens=200),
                    )
                st.info(f"**Back-Translation Check ({res['src_lang']}):** {bt.text.strip()}")
            except Exception as e:
                st.error(f"Verification Error: {e}")

# ==============================================================================
# TAB 2: VOICE AUTO-DETECT
# ==============================================================================
with tab_voice:
    st.write("Tap the microphone and speak in **any language**—the app will detect it, transcribe it, and translate it.")
    audio_file = st.audio_input("Record your voice:")
    if st.button("Detect Language & Translate Voice", type="primary", key="btn_voice"):
        if audio_file is None:
            st.warning("Please record your voice first.")
        else:
            t0 = time.perf_counter()
            try:
                prompt = (
                    f"Listen to the audio. Detect the spoken language, transcribe it accurately, "
                    f"and translate it into {tgt_lang} ({domain} domain).\n"
                    f"Style: {get_tone_rule(selected_tone_key, tgt_lang)}\n"
                    f'Return ONLY JSON with keys: "detected_language", "transcript", "translation", "transliteration".'
                )
                with st.spinner("Detecting language & translating..."):
                    resp = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[
                            types.Part.from_bytes(data=audio_file.getvalue(), mime_type=audio_file.type or "audio/wav"),
                            prompt,
                        ],
                        config=fast_config(json_mode=True, max_tokens=400),
                    )
                data = json.loads(resp.text)
                latency_ms = (time.perf_counter() - t0) * 1000
                st.session_state.voice_result = {
                    "detected_language": data.get("detected_language", "Unknown"),
                    "transcript": data.get("transcript", ""),
                    "translation": data.get("translation", ""),
                    "transliteration": data.get("transliteration", ""),
                    "tgt_lang": tgt_lang,
                    "latency_ms": latency_ms,
                }
                save_history("Voice", data.get("detected_language", "Auto"), tgt_lang, data.get("transcript", ""), data.get("translation", ""))
            except Exception as e:
                st.error(f"Voice Error: {e}")

    if st.session_state.voice_result:
        vres = st.session_state.voice_result
        st.info(f"**Detected Language:** {vres['detected_language']}")
        st.write(f"**Transcript:** {vres['transcript']}")
        render_output_block(vres["translation"], vres["transliteration"], vres["tgt_lang"], "voice")
        st.metric("Response Latency", f"{vres['latency_ms']:.0f} ms")

# ==============================================================================
# TAB 3: CAMERA / PHOTO SIGNBOARD TRANSLATION
# ==============================================================================
with tab_camera:
    img_mode = st.radio("Image Source", ["Upload Photo", "Use Camera"], horizontal=True)
    img_file = (
        st.file_uploader("Upload a signboard, menu, or textbook photo", type=["png", "jpg", "jpeg"])
        if img_mode == "Upload Photo"
        else st.camera_input("Take a photo of text to translate")
    )
    if img_file is not None:
        st.image(img_file, width=320)
        if st.button("Extract & Translate Image", type="primary", key="btn_img"):
            t0 = time.perf_counter()
            try:
                prompt = (
                    f"Read all visible text in this image and translate it into {tgt_lang} ({domain} domain).\n"
                    f"Style: {get_tone_rule(selected_tone_key, tgt_lang)}\n"
                    f'Return ONLY JSON with keys: "extracted_text", "translation", "transliteration".'
                )
                with st.spinner("Reading image & translating..."):
                    resp = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[
                            types.Part.from_bytes(data=img_file.getvalue(), mime_type=img_file.type or "image/jpeg"),
                            prompt,
                        ],
                        config=fast_config(json_mode=True, max_tokens=500),
                    )
                data = json.loads(resp.text)
                latency_ms = (time.perf_counter() - t0) * 1000
                st.session_state.img_result = {
                    "extracted_text": data.get("extracted_text", ""),
                    "translation": data.get("translation", ""),
                    "transliteration": data.get("transliteration", ""),
                    "tgt_lang": tgt_lang,
                    "latency_ms": latency_ms,
                }
                save_history("Image", "Image OCR", tgt_lang, data.get("extracted_text", ""), data.get("translation", ""))
            except Exception as e:
                st.error(f"Image Error: {e}")

    if st.session_state.img_result:
        ires = st.session_state.img_result
        st.write(f"**Extracted Text:** {ires['extracted_text']}")
        render_output_block(ires["translation"], ires["transliteration"], ires["tgt_lang"], "img")
        st.metric("Response Latency", f"{ires['latency_ms']:.0f} ms")

# ==============================================================================
# TAB 4: DOCUMENT / PDF TRANSLATOR
# ==============================================================================
with tab_doc:
    doc_file = st.file_uploader("Upload a PDF or TXT file (e.g., notice, notes)", type=["pdf", "txt"])
    if doc_file is not None:
        if doc_file.name.lower().endswith(".pdf"):
            reader = PdfReader(doc_file)
            raw_doc = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            raw_doc = doc_file.read().decode("utf-8", errors="ignore")

        st.text_area("Extracted Document Preview (first 3,000 chars):", value=raw_doc[:3000], height=140)
        if st.button("Translate Document", type="primary", key="btn_doc"):
            doc_chunk = raw_doc[:6000].strip()
            if not doc_chunk:
                st.warning("No readable text found in the uploaded file.")
            else:
                clean_doc, pii_count = mask_pii(doc_chunk) if pii_enabled else (doc_chunk, 0)
                if pii_count > 0:
                    st.warning(f"DPDP Privacy Mode masked {pii_count} sensitive item(s) in the document.")
                try:
                    with st.spinner("Translating document..."):
                        resp = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=(
                                f"Translate this {domain} document into {tgt_lang}.\n"
                                f"Style: {get_tone_rule(selected_tone_key, tgt_lang)}\n"
                                f"Return ONLY the translated document text.\n\n{clean_doc}"
                            ),
                            config=fast_config(json_mode=False, max_tokens=None),
                        )
                    translated_doc = resp.text.strip()
                    st.subheader(f"Translated Document ({tgt_lang})")
                    st.write(translated_doc)
                    st.download_button(
                        "Download Translated File (.txt)",
                        data=translated_doc,
                        file_name=f"translated_{tgt_lang.lower()}.txt",
                        mime="text/plain",
                    )
                    save_history("Document", src_lang, tgt_lang, doc_file.name, translated_doc)
                except Exception as e:
                    st.error(f"Document Error: {e}")
