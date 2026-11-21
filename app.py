import json
import time
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="BhashaSetu AI Translator", layout="centered")
st.title("BhashaSetu AI: Multilingual Language Translator")
st.caption("1BAI103 CCA Case Study | Localized UI + Voice Auto-Detect + Tone Control")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

UI_TEXT = {
    "English": {
        "tgt_label": "Target Language",
        "tone_label": "Choose Translation Style",
        "tones": {"Formal": "Formal (Polite)", "Colloquial": "Everyday Spoken", "Code-Mixed": "Code-Mixed (Native + English)"},
        "mic_toggle": "Enable Microphone (Auto-Detect Spoken Language)",
        "mic_label": "Tap the mic and speak in any language:",
        "input_label": "Enter your message:",
        "btn": "Translate",
        "output_hdr": "Translated Output",
        "sample": "Hey bro, don't worry about the exam, it's going to be super easy.",
    },
    "Kannada": {
        "tgt_label": "ಯಾವ ಭಾಷೆಗೆ ಅನುವಾದಿಸಬೇಕು? (Target Language)",
        "tone_label": "ಅನುವಾದದ ಶೈಲಿ ಆಯ್ಕೆಮಾಡಿ",
        "tones": {"Formal": "ಔಪಚಾರಿಕ (ಶುದ್ಧ)", "Colloquial": "ಸಾಮಾನ್ಯ (ಮಾತನಾಡುವ ಶೈಲಿ)", "Code-Mixed": "ಮಿಶ್ರ ಭಾಷೆ (ಕಂಗ್ಲಿಷ್)"},
        "mic_toggle": "ಮೈಕ್ರೊಫೋನ್ ಆನ್ ಮಾಡಿ (ಭಾಷೆಯನ್ನು ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಗುರುತಿಸುತ್ತದೆ)",
        "mic_label": "ಮೈಕ್ ಒತ್ತಿ ಯಾವುದೇ ಭಾಷೆಯಲ್ಲಿ ಮಾತನಾಡಿ:",
        "input_label": "ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ:",
        "btn": "ಅನುವಾದಿಸಿ",
        "output_hdr": "ಅನುವಾದಿತ ಫಲಿತಾಂಶ",
        "sample": "ನಮಸ್ಕಾರ, ನಾನು ಕಂಪ್ಯೂಟರ್ ಸೈನ್ಸ್ ವಿದ್ಯಾರ್ಥಿ.",
    },
    "Hindi": {
        "tgt_label": "किस भाषा में अनुवाद करें? (Target Language)",
        "tone_label": "अनुवाद की शैली चुनें",
        "tones": {"Formal": "औपचारिक (शुद्ध)", "Colloquial": "बोलचाल की भाषा", "Code-Mixed": "मिश्रित भाषा (हिंग्लिश)"},
        "mic_toggle": "माइक्रोफ़ोन चालू करें (बोली गई भाषा अपने आप पहचानेगा)",
        "mic_label": "माइक दबाएँ और किसी भी भाषा में बोलें:",
        "input_label": "अपना संदेश यहाँ लिखें:",
        "btn": "अनुवाद करें",
        "output_hdr": "अनुवादित परिणाम",
        "sample": "नमस्ते, मैं कंप्यूटर साइंस का छात्र हूँ।",
    },
    "Tamil": {
        "tgt_label": "எந்த மொழியில் மொழிபெயர்க்க வேண்டும்? (Target Language)",
        "tone_label": "மொழிபெயர்ப்பு நடையைத் தேர்ந்தெடுக்கவும்",
        "tones": {"Formal": "முறையான (தூய தமிழ்)", "Colloquial": "பேச்சு வழக்கு", "Code-Mixed": "கலப்பு மொழி (தங்கிலிஷ்)"},
        "mic_toggle": "மைக்ரோஃபோனை இயக்கு (பேசும் மொழியை தானாகக் கண்டறியும்)",
        "mic_label": "மைக்கை அழுத்தி எந்த மொழியிலும் பேசுங்கள்:",
        "input_label": "உங்கள் செய்தியை இங்கே எழுதுங்கள்:",
        "btn": "மொழிபெயர்க்கவும்",
        "output_hdr": "மொழிபெயர்க்கப்பட்ட வெளியீடு",
        "sample": "வணக்கம், நான் கணினி அறிவியல் மாணவன்.",
    },
    "Telugu": {
        "tgt_label": "ఏ భాషలోకి అనువదించాలి? (Target Language)",
        "tone_label": "అనువాద శైలిని ఎంచుకోండి",
        "tones": {"Formal": "అధికారిక (స్వచ్ఛమైన)", "Colloquial": "వాడుక భాష", "Code-Mixed": "మిశ్రమ భాష (తెలుగు + ఇంగ్లీష్)"},
        "mic_toggle": "మైక్రోఫోన్ ఆన్ చేయండి (మాట్లాడే భాషను ఆటోమేటిక్‌గా గుర్తిస్తుంది)",
        "mic_label": "మైక్ నొక్కి ఏ భాషలోనైనా మాట్లాడండి:",
        "input_label": "మీ సందేశాన్ని ఇక్కడ రాయండి:",
        "btn": "అనువదించండి",
        "output_hdr": "అనువదించిన ఫలితం",
        "sample": "నమస్కారం, నేను కంప్యూటర్ సైన్స్ విద్యార్థిని.",
    },
    "Malayalam": {
        "tgt_label": "ഏത് ഭാഷയിലേക്ക് വിവർത്തനം ചെയ്യണം? (Target Language)",
        "tone_label": "വിവർത്തന ശൈലി തിരഞ്ഞെടുക്കുക",
        "tones": {"Formal": "ഔപചാരികം (ശുദ്ധമായ)", "Colloquial": "സംസാരഭാഷ", "Code-Mixed": "മിശ്രഭാഷ (മംഗ്ലീഷ്)"},
        "mic_toggle": "മൈക്രോഫോൺ ഓൺ ചെയ്യുക (ഭാഷ സ്വയം തിരിച്ചറിയും)",
        "mic_label": "മൈക്ക് അമർത്തി ഏത് ഭാഷയിലും സംസാരിക്കുക:",
        "input_label": "നിങ്ങളുടെ സന്ദേശം ഇവിടെ എഴുതുക:",
        "btn": "വിവർത്തനം ചെയ്യുക",
        "output_hdr": "വിവർത്തനം ചെയ്ത ഫലം",
        "sample": "നമസ്കാരം, ഞാൻ കമ്പ്യൂട്ടർ സയൻസ് വിദ്യാർത്ഥിയാണ്.",
    },
    "Marathi": {
        "tgt_label": "कोणत्या भाषेत भाषांतर करायचे? (Target Language)",
        "tone_label": "भाषांतर शैली निवडा",
        "tones": {"Formal": "औपचारिक (शुद्ध)", "Colloquial": "बोलभाषा", "Code-Mixed": "मिश्र भाषा (मराठी + इंग्लिश)"},
        "mic_toggle": "मायक्रोफोन सुरू करा (बोललेली भाषा आपोआप ओळखेल)",
        "mic_label": "माइक दाबा आणि कोणत्याही भाषेत बोला:",
        "input_label": "तुमचा संदेश येथे लिहा:",
        "btn": "भाषांतर करा",
        "output_hdr": "भाषांतरित निकाल",
        "sample": "नमस्कार, मी संगणक शास्त्राचा विद्यार्थी आहे.",
    },
}

LANGUAGES = list(UI_TEXT.keys())

# Step 1: User selects their preferred UI / Input language
src_lang = st.selectbox("Select Your Language / ನಿಮ್ಮ ಭಾಷೆ / अपनी भाषा चुनें", LANGUAGES, index=0)
ui = UI_TEXT[src_lang]

# Step 2: Target language
default_tgt_idx = 1 if src_lang == "English" else 0
tgt_lang = st.selectbox(ui["tgt_label"], LANGUAGES, index=default_tgt_idx)

# Step 3: Localized tone selector
tone_keys = list(ui["tones"].keys())
selected_tone_key = st.radio(
    ui["tone_label"],
    options=tone_keys,
    format_func=lambda k: ui["tones"][k],
    horizontal=True,
)

tone_rules = {
    "Formal": f"Translate into pure, polite, formal {tgt_lang}. Every single word MUST be in {tgt_lang} script only.",
    "Colloquial": f"Translate into natural, casual, everyday spoken {tgt_lang}. Every single word MUST be in {tgt_lang} script only.",
    "Code-Mixed": f"Translate into natural urban {tgt_lang}-English code-mixing written in {tgt_lang} script. Mix ONLY {tgt_lang} and English—never use any third language.",
}

# Step 4: Microphone toggle
use_mic = st.toggle(ui["mic_toggle"], value=False)

if use_mic:
    audio_file = st.audio_input(ui["mic_label"])
    if st.button(ui["btn"], type="primary"):
        if audio_file is None:
            st.warning("Please record your voice first.")
        else:
            audio_bytes = audio_file.getvalue()
            mime_type = audio_file.type or "audio/wav"

            prompt = (
                f"Listen to the audio. Identify the spoken language, transcribe it accurately, "
                f"and translate it into {tgt_lang}.\n"
                f"Style rule: {tone_rules[selected_tone_key]}\n"
                f"Return ONLY a JSON object with exact keys: "
                f'"detected_language", "transcript", and "translation".'
            )

            t0 = time.perf_counter()
            try:
                with st.spinner("Detecting language & translating..."):
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            prompt,
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    )
                latency_ms = (time.perf_counter() - t0) * 1000
                data = json.loads(response.text)

                st.info(f"**Detected Language:** {data.get('detected_language', 'Unknown')}")
                st.write(f"**Transcript:** {data.get('transcript', '')}")
                st.subheader(f"{ui['output_hdr']} ({tgt_lang})")
                st.success(data.get("translation", ""))
                st.metric("Response Latency", f"{latency_ms:.0f} ms")
            except Exception as e:
                st.error(f"API Error: {e}")
else:
    text = st.text_area(ui["input_label"], value=ui["sample"], height=130)
    if st.button(ui["btn"], type="primary"):
        if not text.strip():
            st.warning("Please enter some text first.")
        elif src_lang == tgt_lang:
            st.info("Source and Target languages are the same. Please choose a different target language.")
        else:
            system_msg = (
                f"You are an expert native {tgt_lang} translator. "
                f"Never leak unrelated languages into {tgt_lang} output. "
                f"Return ONLY the final translation with zero explanation."
            )
            prompt = f"Style: {tone_rules[selected_tone_key]}\n\nTranslate from {src_lang} to {tgt_lang}:\n{text}"

            t0 = time.perf_counter()
            try:
                with st.spinner("Translating..."):
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_msg,
                            temperature=0.2,
                        ),
                    )
                latency_ms = (time.perf_counter() - t0) * 1000

                st.subheader(f"{ui['output_hdr']} ({tgt_lang})")
                st.success(response.text.strip())

                m1, m2 = st.columns(2)
                m1.metric("Input Characters", len(text))
                m2.metric("Response Latency", f"{latency_ms:.0f} ms")
            except Exception as e:
                st.error(f"API Error: {e}")
