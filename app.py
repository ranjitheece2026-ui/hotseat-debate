import streamlit as st
import random
from google import genai

# Page Configuration for an immersive, arcade-style look
st.set_page_config(page_title="⚔️ The Hot Seat! AI Debate Arena", page_icon="⚔️", layout="centered")

# Custom CSS for gaming/arena styling (arcade red and dark mode vibes)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .title { text-align: center; color: #ff4b4b; font-family: 'Courier New', Courier, monospace; font-size: 2.2rem; font-weight: bold; }
    .score-label { font-size: 1.1rem; font-weight: bold; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>⚔️ THE HOT SEAT ⚔️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Can you out-debate an AI in front of a relentless judge and crowd?</p>", unsafe_allow_html=True)

# API setup
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")
st.sidebar.markdown("[Get a free key at Google AI Studio](https://aistudio.google.com/)")

# Game Setup State
if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "player_score" not in st.session_state:
    st.session_state.player_score = 50  # Out of 100
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
                st.error("Please provide your API key in the sidebar to start!")
            else:
                st.session_state.game_started = True
                st.session_state.topic = topic
                st.session_state.player_stance = player_stance
                st.session_state.ai_persona = ai_persona
                
                # Kick off the first AI attack to make user "react" in the hot seat
                client = genai.Client(api_key=api_key)
                with st.spinner("Your opponent is preparing their opening roast..."):
                    first_prompt = (
                        f"You are debating a human on: '{topic}'. You are advocating for the opposite of "
                        f"the human's stance: '{player_stance}'. Your persona is: '{ai_persona}'. "
                        f"Deliver a sharp, punchy, 3-sentence opening argument/roast directly attacking "
                        f"their point of view. Keep it under 80 words."
                    )
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=first_prompt)
                    st.session_state.conversation_history.append({"role": "AI Opponent", "text": response.text})
                st.rerun()

# Play Active Game
else:
    # Score indicators
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<p class='score-label'>Round: {st.session_state.round_num} / 3</p>", unsafe_allow_html=True)
    with c2:
        score = st.session_state.player_score
        color = "🔴" if score < 40 else "🟡" if score < 70 else "🟢"
        st.markdown(f"<p class='score-label'>Crowd Approval: {color} {score}%</p>", unsafe_allow_html=True)
        st.progress(score / 100.0)

    st.markdown("---")

    # Show debate history
    for message in st.session_state.conversation_history:
        if message["role"] == "AI Opponent":
            st.chat_message("assistant", avatar="🤖").markdown(f"**Opponent ({st.session_state.ai_persona.split('(')[0].strip()}):**\n{message['text']}")
        elif message["role"] == "Player":
            st.chat_message("user", avatar="🤠").markdown(f"**You:**\n{message['text']}")
        elif message["role"] == "Judge":
            st.chat_message("system", avatar="⚖️").markdown(f"*🎬 {message['text']}*")

    # Check if game is over (3 rounds)
    if st.session_state.round_num > 3:
        st.balloons() if st.session_state.player_score >= 50 else st.snow()
        st.markdown("### 🏆 Final Assessment")
        
        client = genai.Client(api_key=api_key)
        history_text = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.conversation_history])
        final_prompt = (
            f"Review this debate history:\n{history_text}\n"
            f"The final player approval rating is {st.session_state.player_score}%. Give a dramatic, "
            f"hilarious final match critique and declare a winner in 3 sentences."
        )
        with st.spinner("The media judge is calculating the definitive winner..."):
            final_verdict = client.models.generate_content(model="gemini-2.5-flash", contents=final_prompt).text
        st.write(final_verdict)
        
        if st.button("Play Again"):
            st.session_state.clear()
            st.rerun()
    else:
        # Player Input
        with st.form("player_turn"):
            user_response = st.text_area("Your Counter-Argument:", placeholder="Type your punchiest comeback here...", max_chars=350)
            submit_turn = st.form_submit_button("LAUNCH COUNTER")
            
            if submit_turn and user_response:
                st.session_state.conversation_history.append({"role": "Player", "text": user_response})
                
                client = genai.Client(api_key=api_key)
                
                # Step 1: Media Judge evaluates user response and adjusts crowd rating
                with st.spinner("Analyzing your response..."):
                    judge_prompt = (
                        f"Topic: '{st.session_state.topic}'. Opponent made an argument, and user countered with: '{user_response}'. "
                        f"Give a 1-sentence dramatic media reaction/scorecard evaluation, followed by an appraisal "
                        f"integer point swing for the user (positive if witty/logical, negative if weak/defensive) "
                        f"formatted EXACTLY as '[SCORE_CHANGE: <int>]'. Example: 'The crowd loved that burn! [SCORE_CHANGE: 12]'"
                    )
                    j_response = client.models.generate_content(model="gemini-2.5-flash", contents=judge_prompt).text
                    
                    try:
                        score_delta = int(j_response.split("[SCORE_CHANGE:")[1].split("]")[0].strip())
                    except Exception:
                        score_delta = random.randint(-8, 8)
                    
                    st.session_state.player_score = max(0, min(100, st.session_state.player_score + score_delta))
                    st.session_state.conversation_history.append({"role": "Judge", "text": j_response.split("[SCORE_CHANGE:")[0].strip()})
                
                # Step 2: AI Counter Attack
                if st.session_state.round_num < 3:
                    with st.spinner("Your opponent is preparing their counter-argument..."):
                        ai_prompt = (
                            f"You are {st.session_state.ai_persona} debating on '{st.session_state.topic}'. "
                            f"React directly to their latest point: '{user_response}'. Provide a 3-sentence "
                            f"scathing rebuttal maintaining your personality. Under 80 words."
                        )
                        ai_response = client.models.generate_content(model="gemini-2.5-flash", contents=ai_prompt).text
                        st.session_state.conversation_history.append({"role": "AI Opponent", "text": ai_response})
                
                st.session_state.round_num += 1
                st.rerun()
