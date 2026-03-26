import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import random
import json
import time
import threading
import uuid
from streamlit.runtime.scriptrunner import add_script_run_ctx
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Google API Key is missing. Please add it to your .env file.")
    st.stop()

genai.configure(api_key=api_key)

# Page configuration
st.set_page_config(page_title="Thirukkural Competitive Exam", page_icon="valluvar.png", layout="wide")

# Add the custom sidebar logo
st.logo("valluvar.png", size="large")

# Load Custom Extracted CSS
with open("style.css", "r", encoding="utf-8") as f:
    css_content = f.read()
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# Define UI Text Dictionary for Bilingual Support
ui_text = {
    "English": {
        "title": "Thirukkural Competitive Exam",
        "sidebar_title": "Navigation Modes",
        "modes": ["Study 1330 Kurals", "Meaning MCQ", "Classification", "Fill in the Blanks", "Dashboard & Analysis"],
        "lang_toggle": "Language / மொழி",
        
        "mcq_header": "🧠 Meaning MCQ",
        "mcq_desc": "Match the Kural with its correct explanation.",
        "mcq_prompt": "Select the correct meaning:",
        
        "porul_header": "🏛️ Porul Classification",
        "porul_desc": "Identify the category (Iyal) of the Kural.",
        "porul_categories": ["Virtue", "Wealth", "Love"],
        "porul_prompt": "Which category?",
        "porul_meaning_hint": "Meaning:",
        "porul_why": "**Why?**",
        
        "fitb_header": "✍️ Fill in the Blanks",
        "fitb_desc": "Complete the missing Tamil word in the Kural.",
        "fitb_hint": "Hint:",
        "fitb_blank1": "Missing Word",
        
        "hint_label": "💡 Hint",
        
        "btn_submit": "Submit Answer",
        "btn_check": "Check Answer",
        "btn_next": "Next Question",
        
        "msg_correct": "✅ Correct! Well done.",
        "msg_correct_porul": "✅ Correct! It belongs to {}.",
        "msg_wrong": "❌ Incorrect. The right answer is: {}",
        "msg_wrong_porul": "❌ Incorrect. It belongs to {}.",
        
        "dashboard_header": "📊 Dashboard & Analytics",
        "study_header": "📚 Study 1330 Kurals"
    },
    "தமிழ்": {
        "title": "திருக்குறள் போட்டித் தேர்வு",
        "sidebar_title": "📜 தேர்வு முறைகள்",
        "modes": ["1330 குறள்களைப் படி", "பொருள் பலவுள் தெரிக", "பொருட்பால் வகைப்பாடு", "கோடிட்ட இடங்களை நிரப்புக", "செயல்திறன் பலகை"],
        "lang_toggle": "மொழி / Language",
        
        "mcq_header": "🧠 பொருள் பலவுள் தெரிக",
        "mcq_desc": "குறளுக்கான சரியான பொருளைத் தேர்ந்தெடுக்கவும்.",
        "mcq_prompt": "சரியான பொருளைத் தேர்ந்தெடுக்கவும்:",
        
        "porul_header": "🏛️ பொருட்பால் வகைப்பாடு",
        "porul_desc": "குறள் எந்தப் பிரிவை (இயல்) சார்ந்தது என அடையாளம் காண்க.",
        "porul_categories": ["அறத்துப்பால்", "பொருட்பால்", "காமத்துப்பால்"],
        "porul_prompt": "எந்தப் பிரிவு?",
        "porul_meaning_hint": "பொருள்:",
        "porul_why": "**ஏன்?**",
        
        "fitb_header": "✍️ கோடிட்ட இடங்களை நிரப்புக",
        "fitb_desc": "குறளில் விடுபட்ட சொல்லை நிரப்புக.",
        "fitb_hint": "குறிப்பு:",
        "fitb_blank1": "விடுபட்ட சொல்",
        
        "hint_label": "💡 குறிப்பு",
        
        "btn_submit": "விடையைச் சமர்ப்பி",
        "btn_check": "விடையைச் சரிபார்",
        "btn_next": "அடுத்த கேள்வி",
        
        "msg_correct": "✅ சரி! மிக நன்று.",
        "msg_correct_porul": "✅ சரி! இது {} பிரிவைச் சார்ந்தது.",
        "msg_wrong": "❌ தவறு. சரியான விடை: {}",
        "msg_wrong_porul": "❌ தவறு. இது {} பிரிவைச் சார்ந்தது.",
        
        "dashboard_header": "📊 செயல்திறன் பலகை",
        "study_header": "📚 1330 குறள்களைப் படி"
    }
}

# --- Sidebar Navigation & Language ---
st.sidebar.image("valluvar.png", use_container_width=True)
st.sidebar.title("🌐 Language / மொழி")
lang = st.sidebar.radio(
    "Language",
    ["English", "தமிழ்"],
    index=0,
    label_visibility="collapsed"
)

# Text dictionary shortcut for the active language
t = ui_text[lang]

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("Thirukkural.csv")
        # Combine Verse
        df['Verse'] = df['Kural_line1'] + " " + df['Kural_line2']
        return df
    except Exception as e:
        st.error(f"Error loading required dataset: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# Map internal mode states to Language specific translations
mode_map_eng_to_internal = {
    "Study 1330 Kurals": "Study", 
    "Meaning MCQ": "Meaning MCQ",
    "Classification": "Porul Classification",
    "Fill in the Blanks": "Fill in the Blanks",
    "Dashboard & Analysis": "Dashboard"
}
mode_map_tam_to_internal = {
    "1330 குறள்களைப் படி": "Study",
    "பொருள் பலவுள் தெரிக": "Meaning MCQ",
    "பொருட்பால் வகைப்பாடு": "Porul Classification",
    "கோடிட்ட இடங்களை நிரப்புக": "Fill in the Blanks",
    "செயல்திறன் பலகை": "Dashboard"
}
mode_map_internal_to_eng = {v: k for k, v in mode_map_eng_to_internal.items()}
mode_map_internal_to_tam = {v: k for k, v in mode_map_tam_to_internal.items()}

# --- GLOBAL ASYNC PRELOAD REGISTRY ---
@st.cache_resource
def get_preload_store():
    return {}

preload_store = get_preload_store()

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    preload_store[st.session_state.session_id] = {
        "mcq": None,
        "porul": None,
        "fitb": None,
        "mcq_loading": False,
        "porul_loading": False,
        "fitb_loading": False
    }

user_preload = preload_store[st.session_state.session_id]

def raw_call_gemini(prompt, is_json=False):
    """Thread-safe Gemini call that doesn't trigger UI updates."""
    models = ['gemini-2.5-flash', 'gemini-3-flash-preview', 'gemini-3.1-flash-lite-preview']
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if is_json:
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                return json.loads(text.strip())
            return response.text.strip()
        except Exception:
            continue
    return None

def trigger_preload(mode_id, target_func, *args):
    """Fires a background thread to preload the next question zero-latency style."""
    t = threading.Thread(target=target_func, args=args)
    add_script_run_ctx(t)
    t.start()

def preload_mcq_task(session_id, lang, df):
    store = get_preload_store()
    if store[session_id]["mcq_loading"] or store[session_id]["mcq"] is not None:
        return
    store[session_id]["mcq_loading"] = True
    try:
        next_kural = df.sample(1).iloc[0]
        real_explanation = next_kural['English_explanation'] if lang == "English" else next_kural['Explanation1']
        if lang == "English":
            prompt = f'''
            I have a valid English explanation for a Tamil Thirukkural: "{real_explanation}".
            Generate 3 plausible but incorrect distractor explanations that sound similar but are wrong.
            They MUST be in English.
            Return ONLY valid JSON in this exact format:
            [
                "Distractor 1",
                "Distractor 2",
                "Distractor 3"
            ]
            '''
        else:
            prompt = f'''
            இத்திருக்குறளின் சரியான விளக்கம்: "{real_explanation}".
            வாசிப்பதற்குச் சரி போலத் தோன்றும், ஆனால் முற்றிலும் தவறான 3 வேறு விளக்கங்களை (distractors) தமிழில் மட்டும் உருவாக்கவும்.
            இதை மட்டுமே JSON வடிவத்தில் தரவும், வேறு எந்த வார்த்தையும் வேண்டாம்:
            [
                "தவறான பொருள் 1",
                "தவறான பொருள் 2",
                "தவறான பொருள் 3"
            ]
            '''
        distractors = raw_call_gemini(prompt, is_json=True)
        if distractors and isinstance(distractors, list) and len(distractors) >= 3:
            options = distractors[:3] + [real_explanation]
            random.shuffle(options)
        else:
            options = [real_explanation, "Plausible but incorrect generic meaning 1", "Plausible but incorrect generic meaning 2", "Plausible but incorrect generic meaning 3"] if lang == "English" else [real_explanation, "இது ஒரு போலியான தவறான பொருள் 1", "இது ஒரு போலியான தவறான பொருள் 2", "இது ஒரு போலியான தவறான பொருள் 3"]
            random.shuffle(options)
        store[session_id]["mcq"] = {"kural": next_kural, "options": options, "answer": real_explanation}
    except Exception:
        pass
    finally:
        store[session_id]["mcq_loading"] = False

def preload_fitb_task(session_id, df):
    store = get_preload_store()
    if store[session_id]["fitb_loading"] or store[session_id]["fitb"] is not None:
        return
    store[session_id]["fitb_loading"] = True
    try:
        next_kural = df.sample(1).iloc[0]
        verse = next_kural['Verse']
        kural_words = verse.split()
        prompt = f'''
        I have a Tamil Thirukkural: "{verse}"
        Pick exactly ONE prominent word from it to be missing.
        Return ONLY valid JSON in this exact format:
        {{
            "missing_word": "word",
            "modified_verse": "the verse with the word replaced by _____"
        }}
        Make sure the missing_word exactly matches a word from the Verse.
        '''
        response_json = raw_call_gemini(prompt, is_json=True)
        if response_json and "missing_word" in response_json and "modified_verse" in response_json:
            missing = response_json["missing_word"]
            mod_verse = response_json["modified_verse"]
        else:
            if kural_words:
                missing = kural_words[0]
                mod_verse = verse.replace(missing, "_____", 1)
            else:
                missing = "_____"; mod_verse = "_____"
        store[session_id]["fitb"] = {"kural": next_kural, "blanks": missing, "modified": mod_verse}
    except Exception:
        pass
    finally:
        store[session_id]["fitb_loading"] = False

# Initialize session state variables for logic & analytics
if 'internal_mode' not in st.session_state:
    st.session_state.internal_mode = "Study"
if 'total_answered' not in st.session_state:
    st.session_state.total_answered = 0
if 'correct_answers' not in st.session_state:
    st.session_state.correct_answers = 0
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = []
if 'test_stats' not in st.session_state:
    st.session_state.test_stats = {
        "Meaning MCQ": {"answered": 0, "correct": 0, "mistakes": []},
        "Porul Classification": {"answered": 0, "correct": 0, "mistakes": []},
        "Fill in the Blanks": {"answered": 0, "correct": 0, "mistakes": []}
    }

def change_mode(new_internal_mode):
    if st.session_state.internal_mode != new_internal_mode:
        st.session_state.internal_mode = new_internal_mode
        # Reset mode-specific states when mode changes
        for key in ['mcq_kural', 'mcq_options', 'mcq_answer', 'mcq_checked', 
                    'porul_kural', 'porul_checked', 'porul_answer', 'porul_explanation',
                   'fitb_kural', 'fitb_blanks', 'fitb_modified_verse', 'fitb_checked']:
            if key in st.session_state:
                del st.session_state[key]

# Display Modes in sidebar
st.sidebar.title(t["sidebar_title"])

# Get index for Radio button based on correct language mapping
current_display_mode = mode_map_internal_to_eng[st.session_state.internal_mode] if lang == "English" else mode_map_internal_to_tam[st.session_state.internal_mode]

selected_display_mode = st.sidebar.radio(
    t["lang_toggle"] + " Modes",
    t["modes"],
    index=t["modes"].index(current_display_mode),
    label_visibility="hidden"
)

# Figure out internal mode from display mode
if lang == "English":
    new_internal_mode = mode_map_eng_to_internal[selected_display_mode]
else:
    new_internal_mode = mode_map_tam_to_internal[selected_display_mode]

# Handle mode change logic avoiding callback loops
if new_internal_mode != st.session_state.internal_mode:
    change_mode(new_internal_mode)

# V6: Layout Column Setup for Right-Side Scoreboard
st.markdown(f"<h1 class='main-title'>{t['title']}</h1>", unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])

# Helper function to call Gemini safely
@st.cache_data(show_spinner=False)
def call_gemini(prompt, is_json=False):
    models = ['gemini-2.5-flash', 'gemini-3-flash-preview', 'gemini-3.1-flash-lite-preview']
    last_err = None
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if is_json:
                text = response.text
                # Simple extraction in case it's wrapped in markdown backticks
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]
                return json.loads(text.strip())
            return response.text.strip()
        except ValueError as e: # JSON decode error usually
            last_err = e
            # JSON parsing failed, let's break and try the next model
            continue
        except Exception as e:
            last_err = e
            continue
            
    # If we get here, all 3 models failed
    err_msg = f"Gemini API Limit reached across all backup models: {last_err}. Please wait or try again later." if lang == "English" else f"Gemini API பயன்பாட்டு எல்லை மீறப்பட்டது அல்லது பிழை ஏற்பட்டது: {last_err}. தயவுசெய்து சிறிது நேரம் காத்திருக்கவும்."
    st.warning(err_msg)
    return None

# ================================
# TIMER & LOADER HELPERS
# ================================
def show_custom_spinner(msg):
    loader = st.empty()
    html = f"""
    <style>
    @keyframes writing {{
        0% {{ transform: translateX(-5px) rotate(-5deg); }}
        50% {{ transform: translateX(5px) rotate(5deg); }}
        100% {{ transform: translateX(-5px) rotate(-5deg); }}
    }}
    </style>
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px; color: #D4C594; font-family: 'Cinzel', serif;">
        <div style="font-size: 55px; animation: writing 1.5s infinite ease-in-out;">🪶📜</div>
        <div style="font-size: 22px; margin-top: 15px; font-weight: bold; text-shadow: 1px 1px 2px #000000;">{msg}</div>
    </div>
    """
    loader.markdown(html, unsafe_allow_html=True)
    return loader
def render_timer(key_suffix, auto_btn_text):
    if 'question_start_time' not in st.session_state:
        st.session_state.question_start_time = time.time()
    
    elapsed = time.time() - st.session_state.question_start_time
    time_left = max(0, int(30 - elapsed))
    timer_id = f"timer_{st.session_state.question_start_time}_{key_suffix}".replace(".", "_")
    
    html_code = f"""
    <div style="color: #D4C594; font-size: 20px; font-family: 'Cinzel', serif; text-align: right; margin-bottom: 0px; padding-right: 15px;">
        ⏳ Time Left: <span id="{timer_id}" style="font-weight: bold; font-size: 28px;">{time_left}</span>s
    </div>
    <script>
        const parent = window.parent.document;
        const buttons = Array.from(parent.querySelectorAll('button'));
        const autoBtn = buttons.find(b => b.innerText.includes('{auto_btn_text}'));
        if(autoBtn) {{
            autoBtn.parentNode.style.display = 'none'; // hide the auto-advance wrapper
        }}

        let t = {time_left};
        const el = document.getElementById('{timer_id}');
        if (el) {{
            const interval = setInterval(() => {{
                t--;
                if(t >= 0) el.innerText = t;
                if(t <= 10) el.style.color = "#FF4B4B";
                if(t <= 0) {{
                    clearInterval(interval);
                    if(autoBtn) autoBtn.click();
                }}
            }}, 1000);
        }}
    </script>
    """
    components.html(html_code, height=50)

# ================================
# MAIN CONTENT AREA (Left Column)
# ================================
with col1:
    
    # --- Mode: Study 1330 Kurals ---
    if st.session_state.internal_mode == "Study":
        st.header(t["study_header"])
        st.write("Browse and learn Kurals grouped by chapters." if lang == "English" else "அதிகாரங்கள் அடிப்படையில் குறள்களைப் படிக்கவும்.")
        
        # Group by Section (Iyal) and Adikaram (Chapter)
        iyals = df['Iyal_eng_trans'].unique() if lang == "English" else df['Iyal'].unique()
        
        for iyal in iyals:
            st.markdown(f"### {iyal}")
            sec_df = df[df['Iyal_eng_trans'] == iyal] if lang == "English" else df[df['Iyal'] == iyal]
            
            adikarams = sec_df['Adikaram_eng_trans'].unique() if lang == "English" else sec_df['Adikaram'].unique()
            for adikaram in adikarams:
                adi_df = sec_df[sec_df['Adikaram_eng_trans'] == adikaram] if lang == "English" else sec_df[sec_df['Adikaram'] == adikaram]
                count = len(adi_df)
                with st.expander(f"📖 {adikaram} ({count} Kurals)"):
                    for _, row in adi_df.iterrows():
                        st.markdown(f"**{row['Verse']}**")
                        st.write(row['English_explanation'] if lang == "English" else row['Explanation1'])
                        st.divider()

    # --- Mode: Meaning MCQ ---
    elif st.session_state.internal_mode == "Meaning MCQ":
        st.header(t["mcq_header"])
        stats = st.session_state.test_stats["Meaning MCQ"]
        
        if stats["answered"] >= 25:
            st.subheader("🎉 Test Complete!" if lang == "English" else "🎉 தேர்வு முடிந்தது!")
            st.write(f"Your Score: {stats['correct']} / 25" if lang == "English" else f"உங்கள் மதிப்பெண்: {stats['correct']} / 25")
            if stats["mistakes"]:
                st.error("Mistakes to Review:" if lang == "English" else "கவனிக்க வேண்டிய தவறுகள்:")
                for i, m in enumerate(stats["mistakes"]):
                    st.write(f"**Q{i+1}:** {m['verse']}  \n**Your Answer:** `{m['guess']}`  \n**Correct:** `{m['correct']}`")
                    st.divider()
            if st.button("Start New Test" if lang == "English" else "புதிய தேர்வு தொடங்கு", type="primary"):
                st.session_state.test_stats["Meaning MCQ"] = {"answered": 0, "correct": 0, "mistakes": []}
                st.rerun()
        else:
            st.write(t["mcq_desc"])
            st.write(f"**Question {stats['answered'] + 1} of 25**" if lang == "English" else f"**கேள்வி {stats['answered'] + 1} / 25**")

            if st.button("`\u200C`", key="auto_adv_mcq"):
                st.session_state.test_stats["Meaning MCQ"]['answered'] += 1
                st.session_state.total_answered += 1
                mistake = {
                    "verse": st.session_state.mcq_kural['Verse'],
                    "guess": "Timeout",
                    "correct": st.session_state.mcq_answer
                }
                st.session_state.test_stats["Meaning MCQ"]['mistakes'].append(mistake)
                st.session_state.mistakes.append(mistake)
                del st.session_state['mcq_kural']
                if 'question_start_time' in st.session_state:
                    del st.session_state['question_start_time']
                st.rerun()
            
            if 'mcq_kural' not in st.session_state:
                if user_preload["mcq"] is not None:
                    # ---------------------------------------------
                    # CONSUME ZERO-LATENCY PRELOADED DATA
                    # ---------------------------------------------
                    st.session_state.mcq_kural = user_preload["mcq"]["kural"]
                    st.session_state.mcq_options = user_preload["mcq"]["options"]
                    st.session_state.mcq_answer = user_preload["mcq"]["answer"]
                    st.session_state.mcq_checked = False
                    user_preload["mcq"] = None
                else:
                    # ---------------------------------------------
                    # SYNCHRONOUS FALLBACK LOAD (Usually only Question 1)
                    # ---------------------------------------------
                    st.session_state.mcq_kural = df.sample(1).iloc[0]
                    st.session_state.mcq_checked = False
                    
                    # Generate distractors using Gemini based on selected language
                    if lang == "English":
                        real_explanation = st.session_state.mcq_kural['English_explanation']
                        prompt = f'''
                        I have a valid English explanation for a Tamil Thirukkural: "{real_explanation}".
                        Generate 3 plausible but incorrect distractor explanations that sound similar but are wrong.
                        They MUST be in English.
                        Return ONLY valid JSON in this exact format:
                        [
                            "Distractor 1",
                            "Distractor 2",
                            "Distractor 3"
                        ]
                        '''
                    else:
                        real_explanation = st.session_state.mcq_kural['Explanation1']
                        prompt = f'''
                        இத்திருக்குறளின் சரியான விளக்கம்: "{real_explanation}".
                        வாசிப்பதற்குச் சரி போலத் தோன்றும், ஆனால் முற்றிலும் தவறான 3 வேறு விளக்கங்களை (distractors) தமிழில் மட்டும் உருவாக்கவும்.
                        இதை மட்டுமே JSON வடிவத்தில் தரவும், வேறு எந்த வார்த்தையும் வேண்டாம்:
                        [
                            "தவறான பொருள் 1",
                            "தவறான பொருள் 2",
                            "தவறான பொருள் 3"
                        ]
                        '''
    
                    loading_msg = "Etching distractors on palm leaves..." if lang == "English" else "விடைகளை ஓலைச்சுவடியில் எழுதுகிறோம்..."
                    loader = show_custom_spinner(loading_msg)
                    distractors = call_gemini(prompt, is_json=True)
                    loader.empty()
                    if distractors and isinstance(distractors, list) and len(distractors) >= 3:
                        options = distractors[:3] + [real_explanation]
                        random.shuffle(options)
                        st.session_state.mcq_options = options
                        st.session_state.mcq_answer = real_explanation
                    else:
                        fallback_options = [real_explanation, "Plausible but incorrect generic meaning 1", "Plausible but incorrect generic meaning 2", "Plausible but incorrect generic meaning 3"] if lang == "English" else [real_explanation, "இது ஒரு போலியான தவறான பொருள் 1", "இது ஒரு போலியான தவறான பொருள் 2", "இது ஒரு போலியான தவறான பொருள் 3"]
                        st.session_state.mcq_options = fallback_options
                        random.shuffle(st.session_state.mcq_options)
                        st.session_state.mcq_answer = real_explanation
                        
                # ---------------------------------------------
                # START TIMER & TRIGGER BACKGROUND NEXT-QUESTION PRELOAD
                # ---------------------------------------------
                st.session_state.question_start_time = time.time()
                trigger_preload("mcq", preload_mcq_task, st.session_state.session_id, lang, df)

            if not st.session_state.mcq_checked:
                render_timer("mcq", "\u200C")
                
            st.markdown(f"<div class='kural-box'><div class='verse-text'>{st.session_state.mcq_kural['Verse']}</div></div>", unsafe_allow_html=True)
            
            with st.expander(t["hint_label"]):
                hint_str = f"**Chapter:** {st.session_state.mcq_kural['Iyal_eng_trans']}  \n**Section:** {st.session_state.mcq_kural['Adikaram_eng_trans']}" if lang == "English" else f"**இயல்:** {st.session_state.mcq_kural['Iyal']}  \n**அதிகாரம்:** {st.session_state.mcq_kural['Adikaram']}"
                st.info(hint_str)

            user_choice = st.radio(t["mcq_prompt"], st.session_state.mcq_options, key=f"mcq_radio_choice_{stats['answered']}")
            
            if st.button(t["btn_submit"], type="primary", key=f"mcq_btn_submit_{stats['answered']}") and not st.session_state.mcq_checked:
                st.session_state.mcq_checked = True
                st.session_state.total_answered += 1
                st.session_state.test_stats["Meaning MCQ"]['answered'] += 1
                
                st.session_state.mcq_timeout = False
                if user_choice == st.session_state.mcq_answer:
                    st.session_state.correct_answers += 1
                    st.session_state.test_stats["Meaning MCQ"]['correct'] += 1
                else:
                    mistake = {
                        "verse": st.session_state.mcq_kural['Verse'],
                        "guess": user_choice,
                        "correct": st.session_state.mcq_answer
                    }
                    st.session_state.mistakes.append(mistake)
                    st.session_state.test_stats["Meaning MCQ"]['mistakes'].append(mistake)
                
            if st.session_state.mcq_checked:
                if user_choice == st.session_state.mcq_answer:
                    st.success(t["msg_correct"])
                else:
                    st.error(t["msg_wrong"].format(st.session_state.mcq_answer))
                    
                if st.button(t["btn_next"], key=f"mcq_btn_next_{stats['answered']}"):
                    del st.session_state['mcq_kural']
                    if 'question_start_time' in st.session_state:
                        del st.session_state['question_start_time']
                    st.rerun()

    # --- Mode: Porul Classification ---
    elif st.session_state.internal_mode == "Porul Classification":
        st.header(t["porul_header"])
        stats = st.session_state.test_stats["Porul Classification"]
        
        if stats["answered"] >= 25:
            st.subheader("🎉 Test Complete!" if lang == "English" else "🎉 தேர்வு முடிந்தது!")
            st.write(f"Your Score: {stats['correct']} / 25" if lang == "English" else f"உங்கள் மதிப்பெண்: {stats['correct']} / 25")
            if stats["mistakes"]:
                st.error("Mistakes to Review:" if lang == "English" else "கவனிக்க வேண்டிய தவறுகள்:")
                for i, m in enumerate(stats["mistakes"]):
                    st.write(f"**Q{i+1}:** {m['verse']}  \n**Your Answer:** `{m['guess']}`  \n**Correct:** `{m['correct']}`")
                    st.divider()
            if st.button("Start New Test" if lang == "English" else "புதிய தேர்வு தொடங்கு", type="primary"):
                st.session_state.test_stats["Porul Classification"] = {"answered": 0, "correct": 0, "mistakes": []}
                st.rerun()
        else:
            st.write(t["porul_desc"])
            st.write(f"**Question {stats['answered'] + 1} of 25**" if lang == "English" else f"**கேள்வி {stats['answered'] + 1} / 25**")
            
            porul_map_to_eng = {"அறத்துப்பால்": "Virtue", "பொருட்பால்": "Wealth", "காமத்துப்பால்": "Love"}
            porul_map_to_tam = {"Virtue": "அறத்துப்பால்", "Wealth": "பொருட்பால்", "Love": "காமத்துப்பால்"}

            if st.button("`\u200C`", key="auto_adv_porul"):
                st.session_state.test_stats["Porul Classification"]['answered'] += 1
                st.session_state.total_answered += 1
                mistake = {
                    "verse": st.session_state.porul_kural['Verse'],
                    "guess": "Timeout",
                    "correct": st.session_state.porul_answer_eng if lang == "English" else porul_map_to_tam.get(st.session_state.porul_answer_eng, "")
                }
                st.session_state.test_stats["Porul Classification"]['mistakes'].append(mistake)
                st.session_state.mistakes.append(mistake)
                del st.session_state['porul_kural']
                if 'porul_explanation' in st.session_state:
                    del st.session_state['porul_explanation']
                if 'question_start_time' in st.session_state:
                    del st.session_state['question_start_time']
                st.rerun()

            if 'porul_kural' not in st.session_state:
                st.session_state.porul_kural = df.sample(1).iloc[0]
                st.session_state.porul_checked = False
                st.session_state.porul_answer_eng = st.session_state.porul_kural['Iyal_eng_trans']
                st.session_state.question_start_time = time.time()
            
            if not st.session_state.porul_checked:
                render_timer("porul", "\u200C")
                
            box_meaning = st.session_state.porul_kural['English_explanation'] if lang == "English" else st.session_state.porul_kural['Explanation1']
            st.markdown(f"<div class='kural-box'><div class='verse-text'>{st.session_state.porul_kural['Verse']}<br><br><small>{t['porul_meaning_hint']} {box_meaning}</small></div></div>", unsafe_allow_html=True)
            
            with st.expander(t["hint_label"]):
                hint_str = f"**Section:** {st.session_state.porul_kural['Adikaram_eng_trans']}" if lang == "English" else f"**அதிகாரம்:** {st.session_state.porul_kural['Adikaram']}"
                st.info(hint_str)
            
            categories = t["porul_categories"]
            
            user_guess_localized = st.radio(t["porul_prompt"], categories, key=f"porul_radio_choice_{stats['answered']}")
            user_guess_eng = user_guess_localized if lang == "English" else porul_map_to_eng.get(user_guess_localized, "")

            if st.button(t["btn_check"], type="primary", key=f"porul_btn_check_{stats['answered']}") and not st.session_state.porul_checked:
                st.session_state.porul_checked = True
                st.session_state.total_answered += 1
                st.session_state.test_stats["Porul Classification"]['answered'] += 1
                
                st.session_state.porul_timeout = False
                if user_guess_eng == st.session_state.porul_answer_eng:
                    st.session_state.correct_answers += 1
                    st.session_state.test_stats["Porul Classification"]['correct'] += 1
                else:
                    mistake = {
                        "verse": st.session_state.porul_kural['Verse'],
                        "guess": user_guess_localized,
                        "correct": st.session_state.porul_answer_eng if lang == "English" else porul_map_to_tam.get(st.session_state.porul_answer_eng, "")
                    }
                    st.session_state.mistakes.append(mistake)
                    st.session_state.test_stats["Porul Classification"]['mistakes'].append(mistake)
                
                # Fetch explanation
                if 'porul_explanation' not in st.session_state:
                    if lang == "English":
                        prompt = f"The Thirukkural '{st.session_state.porul_kural['Verse']}' belongs to the category '{st.session_state.porul_answer_eng}'. In exactly 1 simple sentence, explain why it belongs to this category based on its meaning: '{st.session_state.porul_kural['English_explanation']}'."
                        loading_msg = "Consulting the sage..."
                    else:
                        tam_cat = porul_map_to_tam.get(st.session_state.porul_answer_eng, "")
                        prompt = f"இந்தத் திருக்குறள் '{st.session_state.porul_kural['Verse']}' ஆனது '{tam_cat}' அதிகாரத்தை/பிரிவைச் சேர்ந்தது. இந்தப் குறளின் பொருளை அடிப்படையாகக் கொண்டு '{st.session_state.porul_kural['Explanation1']}', ஏன் இது இந்தப் பிரிவில் இடம்பெற்றுள்ளது என சரியாக 1 வாக்கியத்தில் தமிழ் மொழியில் விளக்கவும்."
                        loading_msg = "சுவடியை ஆராய்கிறோம்..."

                    loader = show_custom_spinner(loading_msg)
                    error_fb = "Explanation could not be generated due to an API error." if lang == "English" else "விளக்கத்தை உருவாக்க முடியவில்லை."
                    st.session_state.porul_explanation = call_gemini(prompt) or error_fb
                    loader.empty()
                        
            if st.session_state.porul_checked:
                correct_answer_localized = st.session_state.porul_answer_eng if lang == "English" else porul_map_to_tam.get(st.session_state.porul_answer_eng, "")

                if user_guess_eng == st.session_state.porul_answer_eng:
                    st.success(t["msg_correct_porul"].format(correct_answer_localized))
                else:
                    st.error(t["msg_wrong_porul"].format(correct_answer_localized))
                    
                st.info(f"{t['porul_why']} {st.session_state.porul_explanation}")
                
                if st.button(t["btn_next"], key=f"porul_btn_next_{stats['answered']}"):
                    del st.session_state['porul_kural']
                    if 'porul_explanation' in st.session_state:
                        del st.session_state['porul_explanation']
                    if 'question_start_time' in st.session_state:
                        del st.session_state['question_start_time']
                    st.rerun()

    # --- Mode: Fill in the Blanks ---
    elif st.session_state.internal_mode == "Fill in the Blanks":
        st.header(t["fitb_header"])
        stats = st.session_state.test_stats["Fill in the Blanks"]
        
        if stats["answered"] >= 25:
            st.subheader("🎉 Test Complete!" if lang == "English" else "🎉 தேர்வு முடிந்தது!")
            st.write(f"Your Score: {stats['correct']} / 25" if lang == "English" else f"உங்கள் மதிப்பெண்: {stats['correct']} / 25")
            if stats["mistakes"]:
                st.error("Mistakes to Review:" if lang == "English" else "கவனிக்க வேண்டிய தவறுகள்:")
                for i, m in enumerate(stats["mistakes"]):
                    st.write(f"**Q{i+1}:** {m['verse']}  \n**Your Answer:** `{m['guess']}`  \n**Correct:** `{m['correct']}`")
                    st.divider()
            if st.button("Start New Test" if lang == "English" else "புதிய தேர்வு தொடங்கு", type="primary"):
                st.session_state.test_stats["Fill in the Blanks"] = {"answered": 0, "correct": 0, "mistakes": []}
                st.rerun()
        else:
            st.write(t["fitb_desc"])
            st.write(f"**Question {stats['answered'] + 1} of 25**" if lang == "English" else f"**கேள்வி {stats['answered'] + 1} / 25**")

            if st.button("`\u200C`", key="auto_adv_fitb"):
                st.session_state.test_stats["Fill in the Blanks"]['answered'] += 1
                st.session_state.total_answered += 1
                mistake = {
                    "verse": st.session_state.fitb_modified_verse,
                    "guess": "Timeout",
                    "correct": st.session_state.fitb_blanks
                }
                st.session_state.test_stats["Fill in the Blanks"]['mistakes'].append(mistake)
                st.session_state.mistakes.append(mistake)
                del st.session_state['fitb_kural']
                if 'question_start_time' in st.session_state:
                    del st.session_state['question_start_time']
                st.rerun()
            
            if 'fitb_kural' not in st.session_state:
                if user_preload["fitb"] is not None:
                    # ---------------------------------------------
                    # CONSUME ZERO-LATENCY PRELOADED DATA
                    # ---------------------------------------------
                    st.session_state.fitb_kural = user_preload["fitb"]["kural"]
                    st.session_state.fitb_blanks = user_preload["fitb"]["blanks"]
                    st.session_state.fitb_modified_verse = user_preload["fitb"]["modified"]
                    st.session_state.fitb_checked = False
                    user_preload["fitb"] = None
                else:
                    # ---------------------------------------------
                    # SYNCHRONOUS FALLBACK LOAD
                    # ---------------------------------------------
                    st.session_state.fitb_kural = df.sample(1).iloc[0]
                    st.session_state.fitb_checked = False
                    
                    # Call Gemini to blank ONE word
                    verse = st.session_state.fitb_kural['Verse']
                    prompt = f'''
                    Here is a Tamil verse: "{verse}".
                    Pick exactly ONE meaningful word from this verse to blank out and replace it with "____" (four underscores).
                    Return ONLY valid JSON in this exact format:
                    {{
                        "modified_verse": "word1 ____ word3 word4 ...",
                        "blank1": "The true single word you replaced"
                    }}
                    '''
                    loading_msg = "Preparing manuscript question..." if lang == "English" else "கேள்வியைத் தயார் செய்கிறோம்..."
                    loader = show_custom_spinner(loading_msg)
                    result = call_gemini(prompt, is_json=True)
                    loader.empty()
                    if result and "modified_verse" in result and "blank1" in result:
                        st.session_state.fitb_modified_verse = result["modified_verse"]
                        st.session_state.fitb_blanks = result["blank1"].strip()
                    else:
                        # Fallback block
                        words = verse.split()
                        if len(words) >= 4:
                            b1_idx = random.randint(1, len(words)-1)
                            st.session_state.fitb_blanks = words[b1_idx]
                            words[b1_idx] = "____"
                            st.session_state.fitb_modified_verse = " ".join(words)
                        else:
                            st.session_state.fitb_modified_verse = "____ " + " ".join(words[1:])
                            st.session_state.fitb_blanks = words[0]
                
                # ---------------------------------------------
                # START TIMER & TRIGGER BACKGROUND NEXT-QUESTION PRELOAD
                # ---------------------------------------------
                st.session_state.question_start_time = time.time()
                trigger_preload("fitb", preload_fitb_task, st.session_state.session_id, df)
            
            if not st.session_state.fitb_checked:
                render_timer("fitb", "\u200C")

            hint_text = st.session_state.fitb_kural['English_explanation'] if lang == "English" else st.session_state.fitb_kural['Explanation1']
            st.markdown(f"<div class='kural-box'><div class='verse-text'>{st.session_state.fitb_modified_verse}</div></div>", unsafe_allow_html=True)
            
            with st.expander(t["hint_label"]):
                st.info(f"{t['fitb_hint']} {hint_text}")
            
            ans1 = st.text_input(t["fitb_blank1"], key=f"fitb_ans1_{stats['answered']}")
                
            if st.button(t["btn_check"], type="primary", key=f"fitb_btn_check_{stats['answered']}") and not st.session_state.fitb_checked:
                st.session_state.fitb_checked = True
                st.session_state.total_answered += 1
                st.session_state.test_stats["Fill in the Blanks"]['answered'] += 1
                
                st.session_state.fitb_timeout = False
                if ans1.strip() == st.session_state.fitb_blanks:
                    st.session_state.correct_answers += 1
                    st.session_state.test_stats["Fill in the Blanks"]['correct'] += 1
                else:
                    mistake = {
                        "verse": st.session_state.fitb_modified_verse,
                        "guess": ans1.strip(),
                        "correct": st.session_state.fitb_blanks
                    }
                    st.session_state.mistakes.append(mistake)
                    st.session_state.test_stats["Fill in the Blanks"]['mistakes'].append(mistake)
                
            if st.session_state.fitb_checked:
                if ans1.strip() == st.session_state.fitb_blanks:
                    st.success(t["msg_correct"])
                else:
                    st.error(t["msg_wrong"].format(st.session_state.fitb_blanks))
                    
                if st.button(t["btn_next"]):
                    del st.session_state['fitb_kural']
                    if 'question_start_time' in st.session_state:
                        del st.session_state['question_start_time']
                    st.rerun()

    # --- Mode: Dashboard ---
    elif st.session_state.internal_mode == "Dashboard":
        st.header(t["dashboard_header"])
        total = st.session_state.total_answered
        correct = st.session_state.correct_answers
        accuracy = (correct / total * 100) if total > 0 else 0
        
        score_html = f"""
        <div style="background-color: #251d15; padding: 2rem; border-radius: 8px; border: 1px solid #8B5A2B; margin-bottom: 2rem;">
            <h2 style="text-align: center; color: #FFFFFF; margin:0;">Score Overview</h2>
            <hr style="border-top: 1px solid #8B5A2B; margin: 10px 0;">
            <div style="display:flex; justify-content:space-around;">
                <div style="text-align:center;"><h2 style="color:#FFFFFF;">{total}</h2><p style="color:#FFFFFF;">Attempted</p></div>
                <div style="text-align:center;"><h2 style="color:#FFFFFF;">{correct}</h2><p style="color:#FFFFFF;">Correct</p></div>
                <div style="text-align:center;"><h2 style="color:#FFFFFF;">{accuracy:.1f}%</h2><p style="color:#FFFFFF;">Accuracy</p></div>
            </div>
        </div>
        """
        st.markdown(score_html, unsafe_allow_html=True)
        
        if st.session_state.mistakes:
            st.subheader("Mistakes Analysis" if lang == "English" else "தவறுகளின் பகுப்பாய்வு")
            for i, m in enumerate(reversed(st.session_state.mistakes)):
                with st.expander(f"Mistake #{len(st.session_state.mistakes) - i}"):
                    st.write(f"**Kural Context:** {m['verse']}")
                    st.write(f"**Your Guess:** `{m['guess']}`")
                    st.write(f"**Correct Answer:** `{m['correct']}`")
        else:
            st.info("No mistakes recorded yet!" if lang == "English" else "இதுவரை தவறுகள் இல்லை!")

# ================================
# RIGHT COLUMN: SCOREBOARD
# ================================
with col2:
    st.markdown("<h3 style='color: #D4C594; text-align: center;'>Scoreboard 🏆</h3>", unsafe_allow_html=True)
    
    score_metric_html = f"""
    <div style="background-color: #271b18; border: 2px solid #8B5A2B; border-radius: 8px; padding: 1.5rem 1rem; text-align: center; box-shadow: 2px 2px 0px rgba(0,0,0,0.5);">
        <h4 style="color: #D4C594; margin-bottom: 0;">✨ Total Answered</h4>
        <h1 style="color: #FFFFFF; margin-top: 0; font-size: 3rem;">{st.session_state.total_answered}</h1>
        <h4 style="color: #D4C594; margin-bottom: 0;">🎯 Correct</h1>
        <h2 style="color: #4CAF50; margin-top: 0;">{st.session_state.correct_answers}</h2>
    </div>
    """
    st.markdown(score_metric_html, unsafe_allow_html=True)

    st.markdown("<br><p style='text-align:center; font-size: 0.9em;'>Learn from your mistakes in the Dashboard Tab. 📈</p>", unsafe_allow_html=True)
