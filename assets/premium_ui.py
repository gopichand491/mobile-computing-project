"""
assets/premium_ui.py – SkillMatch Premium UI & AI Assistant Engine
Provides 3D background particles, gradient orbs, sound effects,
and a global floating AI Career Assistant on every page.
"""

import streamlit as st
import os
import sys

# ═══════════════════════════════════════════════════════════════════
# PARTICLE BACKGROUND & GRADIENT ORBS
# ═══════════════════════════════════════════════════════════════════

PARTICLES_HTML = """
<div id="sm-particles-container" style="position:fixed;top:0;left:0;width:100%;height:100%;
    pointer-events:none;z-index:0;overflow:hidden;">
</div>

<!-- Gradient Orbs -->
<div style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;overflow:hidden;">
    <div style="position:absolute;top:10%;left:15%;width:300px;height:300px;
        background:radial-gradient(circle,rgba(0,212,255,0.06),transparent 70%);
        border-radius:50%;animation:orbFloat1 20s ease-in-out infinite;"></div>
    <div style="position:absolute;bottom:20%;right:10%;width:250px;height:250px;
        background:radial-gradient(circle,rgba(123,47,255,0.05),transparent 70%);
        border-radius:50%;animation:orbFloat2 25s ease-in-out infinite;"></div>
    <div style="position:absolute;top:50%;left:60%;width:200px;height:200px;
        background:radial-gradient(circle,rgba(0,245,212,0.04),transparent 70%);
        border-radius:50%;animation:orbFloat1 18s ease-in-out infinite;"></div>
</div>

<style>
@keyframes orbFloat1 {
    0%,100%{transform:translate(0,0) scale(1);}
    33%{transform:translate(30px,-20px) scale(1.05);}
    66%{transform:translate(-20px,15px) scale(0.95);}
}
@keyframes orbFloat2 {
    0%,100%{transform:translate(0,0) scale(1);}
    33%{transform:translate(-25px,25px) scale(0.95);}
    66%{transform:translate(35px,-10px) scale(1.05);}
}
@keyframes particleDrift {
    0%{transform:translateY(100vh) rotate(0deg);opacity:0;}
    10%{opacity:1;}
    90%{opacity:1;}
    100%{transform:translateY(-10vh) rotate(360deg);opacity:0;}
}
</style>

<script>
(function(){
    if(document.getElementById('sm-particles-init')) return;
    var tag = document.createElement('div');
    tag.id = 'sm-particles-init';
    document.body.appendChild(tag);

    var container = document.getElementById('sm-particles-container');
    if(!container) return;

    for(var i=0; i<22; i++){
        var p = document.createElement('div');
        var size = Math.random()*4 + 1;
        var hue = [190, 260, 170][Math.floor(Math.random()*3)];
        p.style.cssText = 'position:absolute;border-radius:50%;pointer-events:none;'+
            'width:'+size+'px;height:'+size+'px;'+
            'background:hsla('+hue+',100%,70%,'+((Math.random()*0.3+0.1).toFixed(2))+');'+
            'left:'+(Math.random()*100)+'%;'+
            'animation:particleDrift '+(Math.random()*20+15)+'s linear infinite;'+
            'animation-delay:-'+(Math.random()*20)+'s;'+
            'box-shadow:0 0 '+(size*2)+'px hsla('+hue+',100%,70%,0.3);';
        container.appendChild(p);
    }
})();
</script>
"""

# ═══════════════════════════════════════════════════════════════════
# SOUND EFFECTS ENGINE
# ═══════════════════════════════════════════════════════════════════

SOUND_ENGINE_HTML = """
<script>
(function(){
    if(window.skillmatchSound) return;

    var audioCtx = null;
    var enabled = localStorage.getItem('sm_sound') === 'true';

    function getCtx(){
        if(!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        return audioCtx;
    }

    function playTone(freq, dur, type, vol){
        if(!enabled) return;
        try{
            var ctx = getCtx();
            if(ctx.state==='suspended') ctx.resume();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.type = type || 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(vol || 0.08, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + dur);
        } catch(e){}
    }

    window.skillmatchSound = {
        isEnabled: function(){ return enabled; },
        toggle: function(){
            enabled = !enabled;
            localStorage.setItem('sm_sound', enabled);
            if(enabled) playTone(800, 0.08, 'sine', 0.06);
            return enabled;
        },
        play: function(type){
            if(!enabled) return;
            switch(type){
                case 'click':
                    playTone(800, 0.06, 'sine', 0.05);
                    break;
                case 'success':
                    playTone(523, 0.12, 'sine', 0.06);
                    setTimeout(function(){ playTone(659, 0.12, 'sine', 0.06); }, 100);
                    setTimeout(function(){ playTone(784, 0.18, 'sine', 0.06); }, 200);
                    break;
                case 'notification':
                    playTone(880, 0.1, 'sine', 0.05);
                    setTimeout(function(){ playTone(1047, 0.15, 'sine', 0.05); }, 120);
                    break;
                case 'celebration':
                    [523,659,784,1047].forEach(function(f,i){
                        setTimeout(function(){ playTone(f, 0.15, 'sine', 0.05); }, i*80);
                    });
                    break;
                case 'navigate':
                    playTone(600, 0.05, 'sine', 0.04);
                    setTimeout(function(){ playTone(900, 0.05, 'sine', 0.04); }, 50);
                    break;
            }
        }
    };

    // Attach click sounds to buttons
    document.addEventListener('click', function(e){
        if(!enabled) return;
        var btn = e.target.closest('button');
        if(btn) window.skillmatchSound.play('click');
    }, true);
})();
</script>
"""

# ═══════════════════════════════════════════════════════════════════
# FLOATING SOUND TOGGLE
# ═══════════════════════════════════════════════════════════════════

SOUND_TOGGLE_HTML = """
<div id="sm-sound-toggle" onclick="toggleSoundBtn()" style="
    position:fixed; bottom:20px; right:20px; z-index:9999;
    width:42px; height:42px; border-radius:50%;
    background:rgba(10,22,40,0.7); backdrop-filter:blur(10px);
    border:1px solid rgba(0,212,255,0.3);
    display:flex; align-items:center; justify-content:center;
    cursor:pointer; transition:all 0.3s ease;
    box-shadow:0 4px 15px rgba(0,0,0,0.3);
    font-size:18px;" title="Toggle Sound Effects">
    🔇
</div>
<script>
function toggleSoundBtn(){
    if(!window.skillmatchSound) return;
    var on = window.skillmatchSound.toggle();
    document.getElementById('sm-sound-toggle').innerHTML = on ? '🔊' : '🔇';
    document.getElementById('sm-sound-toggle').style.borderColor =
        on ? 'rgba(0,245,212,0.5)' : 'rgba(0,212,255,0.3)';
}
document.addEventListener('DOMContentLoaded', function(){
    setTimeout(function(){
        if(window.skillmatchSound && window.skillmatchSound.isEnabled()){
            var el = document.getElementById('sm-sound-toggle');
            if(el){ el.innerHTML='🔊'; el.style.borderColor='rgba(0,245,212,0.5)'; }
        }
    }, 500);
});
</script>
"""


# ═══════════════════════════════════════════════════════════════════
# AI CAREER ASSISTANT DIALOG COMPONENT
# ═══════════════════════════════════════════════════════════════════

@st.dialog("🤖 SkillMatch AI Career Assistant", width="large")
def show_ai_assistant_dialog():
    """
    Renders the AI Assistant inside a responsive modal dialog.
    Accessible from any page via the floating button or sidebar.
    """
    from modules.ai_chatbot import get_api_credentials, generate_ai_response, stream_text

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    student_name = st.session_state.get("student_name")
    student_id = st.session_state.get("student_id")
    target_career = st.session_state.get("selected_career", "Technology Careers")

    creds = get_api_credentials()

    # Header / Context bar
    context_desc = f"👤 **{student_name}** | 🎯 Target: **{target_career}**" if student_name else "💡 Log in for personalized skill guidance"
    st.markdown(f"""
    <div style="background:rgba(0,212,255,0.06); border:1px solid rgba(0,212,255,0.2);
                border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.8rem; display:flex; justify-content:space-between; align-items:center;">
        <span style="color:#B0C4DE; font-size:0.85rem;">{context_desc}</span>
        <span style="background:rgba(0,245,212,0.15); color:#00F5D4; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:700;">
            {'🟢 AI READY' if creds['is_configured'] else '🔴 KEY NEEDED'}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # API Key Missing Notice
    if not creds["is_configured"]:
        st.warning("⚠️ **AI API Key Not Found**")
        st.markdown("""
        To enable real AI answers, provide a **free Google Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey):
        """)
        user_key = st.text_input("Enter Gemini API Key for this session:", type="password", placeholder="AIzaSy...", key="dlg_quick_key")
        if st.button("💾 Activate AI for Session", key="dlg_save_key"):
            if user_key.strip():
                st.session_state["custom_gemini_key"] = user_key.strip()
                st.success("✅ Gemini Key Activated!")
                st.rerun()
            else:
                st.error("Please enter a valid key.")
        st.caption("Or configure GEMINI_API_KEY permanently in `.streamlit/secrets.toml` or Streamlit Cloud Secrets.")
        return

    # Quick Prompts
    c_q1, c_q2 = st.columns(2)
    selected_quick = None
    with c_q1:
        if st.button("🎯 Best careers for my skills?", key="dlg_q1", use_container_width=True):
            selected_quick = "What career paths best match my current skills and academic profile?"
    with c_q2:
        if st.button(f"📉 Skill gaps for {target_career}?", key="dlg_q2", use_container_width=True):
            selected_quick = f"What specific skill gaps do I have for {target_career}, and how can I start learning them?"

    # Chat history display
    chat_box = st.container(height=350)
    with chat_box:
        if not st.session_state.chat_messages:
            st.info("👋 Hello! Ask me any question about your skills, career options, programming doubts, or interview prep.")
        for msg in st.session_state.chat_messages:
            role = msg["role"]
            with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
                st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Type your question here...", key="dlg_chat_input")
    active_prompt = selected_quick or user_input

    if active_prompt:
        with chat_box:
            with st.chat_message("user", avatar="👤"):
                st.markdown(active_prompt)

        st.session_state.chat_messages.append({"role": "user", "content": active_prompt})

        with chat_box:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    try:
                        reply = generate_ai_response(
                            user_query=active_prompt,
                            chat_history=st.session_state.chat_messages[:-1],
                            student_id=student_id,
                        )
                        st.write_stream(stream_text(reply))
                        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Action footer
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        if st.button("🗑️ Clear Chat", key="dlg_clear_btn", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    with c_f2:
        if st.button("↗️ Full-Screen Assistant", key="dlg_fullscreen_btn", use_container_width=True):
            st.switch_page("pages/13_AI_Career_Assistant.py")


def render_floating_ai_assistant():
    """
    Renders the floating AI trigger on every page.
    Styled with fixed positioning to appear in the bottom-right corner.
    """
    # Sidebar quick launch button
    with st.sidebar:
        st.markdown("""
        <div style="height:1px; background:linear-gradient(90deg, transparent, rgba(0,212,255,0.3), transparent); margin:0.8rem 0;"></div>
        """, unsafe_allow_html=True)
        if st.button("🤖 Ask AI Assistant", key=f"sidebar_ai_btn_{st.session_state.get('_page_id', 'global')}", use_container_width=True):
            show_ai_assistant_dialog()

    # Floating button at viewport bottom-right
    c_anchor, c_btn = st.columns([12, 1])
    with c_btn:
        if st.button("🤖 AI", key=f"floating_ai_action_{st.session_state.get('_page_id', 'global')}", help="Ask AI Career Assistant"):
            show_ai_assistant_dialog()


def inject_premium_ui(page_id: str = "global"):
    """
    Injects full design system, particles, sound effects, and floating AI assistant.
    """
    st.session_state["_page_id"] = page_id

    # Inject Particles & Sounds
    st.components.v1.html(
        PARTICLES_HTML + SOUND_ENGINE_HTML + SOUND_TOGGLE_HTML,
        height=0,
        scrolling=False,
    )

    # Render floating AI button
    render_floating_ai_assistant()


# ═══════════════════════════════════════════════════════════════════
# REUSABLE PRESENTATIONAL HELPERS
# ═══════════════════════════════════════════════════════════════════

def premium_header(title: str, subtitle: str = "", icon: str = "🎯"):
    """Render an animated gradient header."""
    st.markdown(f"""
    <div style="text-align:center; padding:1.8rem 1.5rem 1.2rem 1.5rem; position:relative;">
        <div style="font-size:2.8rem; margin-bottom:0.3rem; animation:float 3s ease-in-out infinite;">{icon}</div>
        <h1 style="
            font-family:'Orbitron','Inter',sans-serif;
            font-size:2.1rem; font-weight:800; margin:0;
            background:linear-gradient(135deg, #00D4FF, #7B2FFF, #00F5D4);
            background-size:200% auto;
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            background-clip:text;
            animation:gradientShift 4s ease infinite;
        ">{title}</h1>
        <p style="color:#7B8FA3; font-size:0.95rem; margin-top:0.4rem; max-width:620px; margin-left:auto; margin-right:auto;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)


def glass_card(content_html: str, border_color: str = "rgba(0,212,255,0.15)", extra_style: str = ""):
    """Render a glassmorphism card."""
    st.markdown(f"""
    <div class="glass-card" style="border-color:{border_color};{extra_style}">
        {content_html}
    </div>
    """, unsafe_allow_html=True)


def neon_divider():
    """Render a neon gradient divider."""
    st.markdown("""
    <div style="height:1px; margin:1.2rem 0;
        background:linear-gradient(90deg, transparent, rgba(0,212,255,0.3), rgba(123,47,255,0.3), transparent);">
    </div>
    """, unsafe_allow_html=True)
