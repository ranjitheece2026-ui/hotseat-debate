import streamlit as st
import random
import time
from google import genai
from google.genai import errors

# Page Configuration
st.set_page_config(page_title="⚔️ The Hot Seat! AI Debate Arena", page_icon="⚔️", layout="centered")

# Custom CSS for gaming/arena styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .title { text-align: center; color: #ff4b4b; font-family: 'Courier New', Courier, monospace; font-size: 2.2rem; font-weight: bold; }
    .score-label { font-size: 1.1rem; font-weight: bold; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>⚔️ THE HOT SEAT ⚔️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Can you out-debate an AI in front of a relentless judge and crowd?</p>", unsafe_allow_html=True)

MODEL_NAME = "gemini-3.8-flash"

# Helper function with rate-limit retry logic
def generate_safe_content(client, prompt):
    for attempt in range(3):
        try:
            res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            return res.text
        except errors.ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                time.sleep(3)  # Wait for quota window to reset
                continue
            raise e
        except Exception as e:
            if "429" in str(e):
                time.sleep(3)
                continue
            raise e
    raise Exception("Rate limit hit. Please wait a few seconds and try again.")

# Sidebar API setup
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")
st.sidebar.markdown("[Get a free key at Google AI Studio](https://aistudio.google.com/)")

# Game State Setup
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "player_score" not in st.session_state:
    st.session_state.player_score = 50
if "round_num" not in st.session_state:
    st.session_state.round_num = 1

# Setup Form
if not st.session_state.game_started:
    with st.form("setup_form"):
        topic = st.text_input("Debate Topic:", value="AI will completely replace human software engineers by 2030")
        player_stance = st.selectbox("Your Stance:", ["AGAINST (No, humans are essential)", "FOR (Yes, AI is taking over)"])
        ai_persona = st.selectbox("Choose Your Opponent:", [
            "Sarcastic Tech Bro (Dismissive, uses 'bro', heavily biased toward hyper-scalability)",
            "The Pedantic Academic (Uses overly complex jargon, cites fake 'studies', extremely condescending)",
            "Aggressive Startup Founder (Everything is about hustle, speed, and disruption)"
        ])
        start_btn = st.form_submit_button("ENTER THE ARENA")
        
        if start_btn:
            if not api_key:
                st.error("Please enter your Gemini API key in the sidebar first!")
            else:
                try:
                    client = genai.Client(api_key=api_key)
                    with st.spinner("Your opponent is preparing their opening roast..."):
                        first_prompt = (
                            f"You are debating a human on: '{topic}'. You are advocating for the opposite of "
                            f"the human's stance: '{player_stance}'. Your persona is: '{ai_persona}'. "
                            f"Deliver a sharp, punchy, 3-sentence opening argument directly attacking "
                            f"their point of view. Keep it under 80 words."
                        )
                        text = generate_safe_content(client, first_prompt)
                        st.session_state.conversation_history.append({"role": "AI Opponent", "text": text})
                        st.session_state.topic = topic
                        st.session_state.player_stance = player_stance
                        st.session_state.ai_persona = ai_persona
                        st.session_state.game_started = True
                        st.rerun()
                except Exception as e:
                    st.error(f"API Connection Error: {str(e)}")

# Active Game Loop
else:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<p class='score-label'>Round: {st.session_state.round_num} / 3</p>", unsafe_allow_html=True)
    with c2:
        score = st.session_state.player_score
        color = "🔴" if score < 40 else "🟡" if score < 70 else "🟢"
        st.markdown(f"<p class='score-label'>Crowd Approval: {color} {score}%</p>", unsafe_allow_html=True)
        st.progress(score / 100.0)

    st.markdown("---")

    # Display dialogue history
    for message in st.session_state.conversation_history:
        if message["role"] == "AI Opponent":
            st.chat_message("assistant", avatar="🤖").markdown(f"**Opponent ({st.session_state.ai_persona.split('(')[0].strip()}):**\n{message['text']}")
        elif message["role"] == "Player":
            st.chat_message("user", avatar="🤠").markdown(f"**You:**\n{message['text']}")
        elif message["role"] == "Judge":
            st.chat_message("system", avatar="⚖️").markdown(f"*🎬 {message['text']}*")

    # Final Verdict Assessment after 3 rounds
    if st.session_state.round_num > 3:
        st.balloons() if st.session_state.player_score >= 50 else st.snow()
        st.markdown("### 🏆 Final Assessment")
        
        try:
            client = genai.Client(api_key=api_key)
            history_text = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.conversation_history])
            final_prompt = (
                f"Review this debate history:\n{history_text}\n"
                f"The final player approval rating is {st.session_state.player_score}%. Give a dramatic, "
                f"entertaining final match critique and declare a winner in 3 sentences."
            )
            with st.spinner("The media judge is calculating the definitive winner..."):
                final_verdict = generate_safe_content(client, final_prompt)
            st.write(final_verdict)
        except Exception as e:
            st.error(f"Could not load final critique: {str(e)}")
        
        if st.button("Play Again"):
            st.session_state.clear()
            st.rerun()
    else:
        # Player Input Turn
        with st.form("player_turn"):
            user_response = st.text_area("Your Counter-Argument:", placeholder="Type your punchiest comeback here...", max_chars=350)
            submit_turn = st.form_submit_button("LAUNCH COUNTER")
            
            if submit_turn and user_response:
                st.session_state.conversation_history.append({"role": "Player", "text": user_response})
                client = genai.Client(api_key=api_key)
                
                try:
                    # Step 1: Judge scoring
                    with st.spinner("Analyzing your response..."):
                        judge_prompt = (
                            f"Topic: '{st.session_state.topic}'. Opponent made an argument, and user countered with: '{user_response}'. "
                            f"Give a 1-sentence dramatic media reaction/scorecard evaluation, followed by an appraisal "
                            f"integer point swing for the user (positive if witty/logical, negative if weak/defensive) "
                            f"formatted EXACTLY as '[SCORE_CHANGE: <int>]'. Example: 'The crowd loved that burn! [SCORE_CHANGE: 12]'"
                        )
                        j_text = generate_safe_content(client, judge_prompt)
                        
                        try:
                            score_delta = int(j_text.split("[SCORE_CHANGE:")[1].split("]")[0].strip())
                        except Exception:
                            score_delta = random.randint(-8, 8)
                        
                        st.session_state.player_score = max(0, min(100, st.session_state.player_score + score_delta))
                        st.session_state.conversation_history.append({"role": "Judge", "text": j_text.split("[SCORE_CHANGE:")[0].strip()})
                    
                    # 1.5s delay to keep within 5 RPM rate limit
                    time.sleep(1.5)

                    # Step 2: AI Opponent Counter
                    if st.session_state.round_num < 3:
                        with st.spinner("Your opponent is preparing their counter-argument..."):
                            ai_prompt = (
                                f"You are {st.session_state.ai_persona} debating on '{st.session_state.topic}'. "
                                f"React directly to their latest point: '{user_response}'. Provide a 3-sentence "
                                f"scathing rebuttal maintaining your personality. Under 80 words."
                            )
                            ai_text = generate_safe_content(client, ai_prompt)
                            st.session_state.conversation_history.append({"role": "AI Opponent", "text": ai_text})
                    
                    st.session_state.round_num += 1
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {str(e)}")
