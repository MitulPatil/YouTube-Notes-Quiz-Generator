"""
YouTube Quiz Generator - Main Streamlit Application
A gamified learning tool that converts YouTube videos into interactive quizzes
"""

import streamlit as st
import time
from utils.transcript import get_transcript, get_video_metadata
from utils.llm import generate_notes, format_notes_for_display
from utils.quiz import (
    generate_questions, 
    select_quiz_questions, 
    check_answer,
    calculate_topic_performance,
    get_weak_topics
)
from utils.storage import SessionStorage
from utils.pdf_generator import generate_pdf

# Page configuration
st.set_page_config(
    page_title="YouTube Quiz Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        padding: 20px 0;
        font-size: 2.5em;
    }
    .quiz-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .correct-answer {
        background-color: #d4edda;
        border: 3px solid #28a745;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        color: #155724;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.2);
    }
    .correct-answer strong {
        color: #0d4520;
        font-size: 1.1em;
    }
    .wrong-answer {
        background-color: #f8d7da;
        border: 3px solid #dc3545;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        color: #721c24;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(220, 53, 69, 0.2);
    }
    .wrong-answer strong {
        color: #4a0e14;
        font-size: 1.1em;
    }
    .score-display {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'page' not in st.session_state:
        st.session_state.page = 'input'
    if 'video_data' not in st.session_state:
        st.session_state.video_data = {}
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = {}
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'answers' not in st.session_state:
        st.session_state.answers = []
    if 'show_feedback' not in st.session_state:
        st.session_state.show_feedback = False

init_session_state()

# Storage instance
storage = SessionStorage()


def show_input_page():
    """Page 1: URL Input and Processing"""
    st.markdown("<h1 class='main-header'>🎓 YouTube Quiz Generator</h1>", unsafe_allow_html=True)
    st.markdown("### Transform any YouTube lecture into an interactive quiz!")
    
    st.write("")
    st.write("**How it works:**")
    st.write("1. 📺 Paste a YouTube video URL")
    st.write("2. 📝 We'll generate comprehensive notes")
    st.write("3. 🎮 Take an interactive quiz and earn points")
    st.write("4. 📊 See your performance and weak areas")
    
    st.write("")
    st.write("---")
    
    # URL Input
    youtube_url = st.text_input(
        "Enter YouTube Video URL:",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste the URL of any YouTube video with captions/transcript"
    )
    
    if st.button("🚀 Generate Notes & Quiz", type="primary"):
        if not youtube_url:
            st.error("Please enter a YouTube URL")
            return
        
        with st.spinner("🔍 Processing video..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Get transcript
            status_text.text("📥 Fetching transcript...")
            progress_bar.progress(20)
            transcript_result = get_transcript(youtube_url)
            
            if not transcript_result['success']:
                st.error(f"❌ {transcript_result['error']}")
                return
            
            video_id = transcript_result['video_id']
            transcript = transcript_result['transcript']
            
            # Check if we have cached data
            if storage.session_exists(video_id):
                status_text.text("💾 Loading cached data...")
                progress_bar.progress(100)
                cached_data = storage.load_session(video_id)
                
                st.session_state.video_data = {
                    'video_id': video_id,
                    'url': youtube_url,
                    'transcript': cached_data['transcript'],
                    'notes': cached_data['notes'],
                    'metadata': get_video_metadata(video_id)
                }
                st.session_state.quiz_data = {
                    'all_questions': cached_data['questions'],
                    'current_questions': []
                }
                
                time.sleep(0.5)
                st.success("✅ Loaded from cache!")
                time.sleep(1)
                st.session_state.page = 'notes'
                st.rerun()
                return
            
            # Step 2: Generate notes
            status_text.text("📝 Generating structured notes...")
            progress_bar.progress(50)
            notes_result = generate_notes(transcript, video_id)
            
            if not notes_result['success']:
                st.error(f"❌ {notes_result['error']}")
                return
            
            # Step 3: Generate questions
            status_text.text("🎯 Creating quiz questions...")
            progress_bar.progress(75)
            questions_result = generate_questions(notes_result['notes'], num_questions=50)
            
            if not questions_result['success']:
                st.error(f"❌ {questions_result['error']}")
                return
            
            # Save to cache
            status_text.text("💾 Saving data...")
            progress_bar.progress(90)
            storage.save_session(
                video_id,
                transcript,
                notes_result['notes'],
                questions_result['questions']
            )
            
            # Store in session
            st.session_state.video_data = {
                'video_id': video_id,
                'url': youtube_url,
                'transcript': transcript,
                'notes': notes_result['notes'],
                'metadata': get_video_metadata(video_id)
            }
            
            st.session_state.quiz_data = {
                'all_questions': questions_result['questions'],
                'current_questions': []
            }
            
            progress_bar.progress(100)
            status_text.text("✅ All done!")
            
            time.sleep(1)
            st.success("🎉 Ready! Proceed to view your notes.")
            time.sleep(1)
            st.session_state.page = 'notes'
            st.rerun()


def show_notes_page():
    """Page 2: Display Generated Notes"""
    st.markdown("<h1 class='main-header'>📚 Lecture Notes</h1>", unsafe_allow_html=True)
    
    notes = st.session_state.video_data['notes']
    metadata = st.session_state.video_data['metadata']
    
    # Video info
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(metadata['thumbnail'], use_container_width=True)
    with col2:
        st.markdown(f"**Video ID:** {metadata['video_id']}")
        st.markdown(f"[🔗 Watch on YouTube]({metadata['url']})")
    
    st.write("---")
    
    # Display notes
    formatted_notes = format_notes_for_display(notes)
    st.markdown(formatted_notes)
    
    st.write("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎮 Start Quiz", type="primary"):
            st.session_state.page = 'mode_selection'
            st.rerun()
    
    with col2:
        if st.button("📥 Download Notes as PDF"):
            # Generate PDF
            video_title = metadata.get('title', 'YouTube Lecture Notes')
            pdf_bytes = generate_pdf(notes, video_title)
            
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"notes_{st.session_state.video_data['video_id']}.pdf",
                mime="application/pdf",
                type="primary"
            )
    
    with col3:
        if st.button("🔄 New Video"):
            # Reset session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def show_mode_selection():
    """Page 3: Quiz Mode Selection"""
    st.markdown("<h1 class='main-header'>🎮 Select Quiz Mode</h1>", unsafe_allow_html=True)
    
    st.write("")
    st.markdown("### Choose how many questions you want to answer:")
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; text-align: center; color: white;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);'>
            <h2 style='margin:0; font-size: 2.5em;'>🎮</h2>
            <h3 style='margin: 10px 0;'>Quick Play</h3>
            <p style='margin: 5px 0; font-size: 1.1em;'>5 questions</p>
            <p style='margin: 5px 0;'>⏱️ ~5 minutes</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Start Quick Play", key="quick", use_container_width=True):
            start_quiz(5)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 20px; border-radius: 10px; text-align: center; color: white;
                    box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);'>
            <h2 style='margin:0; font-size: 2.5em;'>📚</h2>
            <h3 style='margin: 10px 0;'>Standard</h3>
            <p style='margin: 5px 0; font-size: 1.1em;'>15 questions</p>
            <p style='margin: 5px 0;'>⏱️ ~15 minutes</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Start Standard", key="standard", type="primary", use_container_width=True):
            start_quiz(15)
    
    with col3:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 20px; border-radius: 10px; text-align: center; color: white;
                    box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);'>
            <h2 style='margin:0; font-size: 2.5em;'>🏆</h2>
            <h3 style='margin: 10px 0;'>Challenge</h3>
            <p style='margin: 5px 0; font-size: 1.1em;'>30 questions</p>
            <p style='margin: 5px 0;'>⏱️ ~30 minutes</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Start Challenge", key="challenge", use_container_width=True):
            start_quiz(30)
    
    st.write("")
    st.write("---")
    
    if st.button("⬅️ Back to Notes"):
        st.session_state.page = 'notes'
        st.rerun()


def start_quiz(num_questions):
    """Initialize quiz with selected number of questions"""
    all_questions = st.session_state.quiz_data['all_questions']
    selected = select_quiz_questions(all_questions, num_questions)
    
    st.session_state.quiz_data['current_questions'] = selected
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.answers = []
    st.session_state.show_feedback = False
    st.session_state.page = 'quiz'
    st.rerun()


def show_quiz_page():
    """Page 4: Quiz Interface"""
    questions = st.session_state.quiz_data['current_questions']
    current_idx = st.session_state.current_question
    current_q = questions[current_idx]
    
    # Header with progress
    st.markdown("<h1 class='main-header'>🎯 Quiz Time!</h1>", unsafe_allow_html=True)
    
    # Progress bar
    progress = (current_idx + 1) / len(questions)
    st.progress(progress)
    
    # Score and question counter
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.markdown(f"**Question:** {current_idx + 1}/{len(questions)}")
    with col2:
        st.markdown(f"<div class='score-display'>Points: {st.session_state.score}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"**Topic:** {current_q['topic']}")
    
    st.write("---")
    
    # Question
    st.markdown(f"### {current_q['question']}")
    st.write("")
    
    # Show feedback if answer submitted
    if st.session_state.show_feedback:
        last_answer = st.session_state.answers[-1]
        
        if last_answer['is_correct']:
            st.markdown(f"""
            <div class='correct-answer'>
                <p style='font-size: 1.3em; margin: 0 0 10px 0;'>✅ <strong>Correct! +1 Point</strong></p>
                <p style='margin: 5px 0;'><strong>Answer:</strong> {last_answer['result']['correct_option']}</p>
                <p style='margin: 5px 0;'><strong>Explanation:</strong> {last_answer['result']['explanation']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='wrong-answer'>
                <p style='font-size: 1.3em; margin: 0 0 10px 0;'>❌ <strong>Incorrect</strong></p>
                <p style='margin: 5px 0;'><strong>Your answer:</strong> {last_answer['result']['user_option']}</p>
                <p style='margin: 5px 0;'><strong>Correct answer:</strong> {last_answer['result']['correct_option']}</p>
                <p style='margin: 5px 0;'><strong>Explanation:</strong> {last_answer['result']['explanation']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        
        if current_idx < len(questions) - 1:
            if st.button("➡️ Next Question", type="primary"):
                st.session_state.current_question += 1
                st.session_state.show_feedback = False
                st.rerun()
        else:
            if st.button("🏁 See Results", type="primary"):
                st.session_state.page = 'results'
                st.rerun()
    
    else:
        # Show options
        user_answer = st.radio(
            "Select your answer:",
            range(len(current_q['options'])),
            format_func=lambda x: f"{chr(65+x)}. {current_q['options'][x]}",
            key=f"q_{current_idx}"
        )
        
        st.write("")
        
        if st.button("Submit Answer", type="primary"):
            # Check answer
            result = check_answer(current_q, user_answer)
            
            # Update score
            if result['correct']:
                st.session_state.score += 1
            
            # Store answer
            st.session_state.answers.append({
                'question': current_q,
                'user_answer': user_answer,
                'is_correct': result['correct'],
                'result': result
            })
            
            st.session_state.show_feedback = True
            st.rerun()


def show_results_page():
    """Page 5: Results and Performance Analysis"""
    st.markdown("<h1 class='main-header'>🎊 Quiz Complete!</h1>", unsafe_allow_html=True)
    
    answers = st.session_state.answers
    total_questions = len(answers)
    correct_answers = sum(1 for a in answers if a['is_correct'])
    percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Overall score
    st.markdown(f"""
    <div class='score-display'>
        Final Score: {correct_answers}/{total_questions} ({percentage:.1f}%)
        <br>
        Total Points: {st.session_state.score}
    </div>
    """, unsafe_allow_html=True)
    
    # Performance message
    if percentage >= 80:
        st.success("🌟 Excellent! You have a strong understanding of the material!")
    elif percentage >= 60:
        st.info("👍 Good job! Review the weak areas to master the content.")
    else:
        st.warning("📚 Keep studying! Focus on the topics that need improvement.")
    
    st.write("---")
    
    # Topic performance
    st.markdown("### 📊 Performance by Topic")
    topic_performance = calculate_topic_performance(answers)
    
    for topic, stats in topic_performance.items():
        emoji = "✅" if stats['percentage'] >= 80 else "⚠️" if stats['percentage'] >= 60 else "❌"
        st.markdown(f"{emoji} **{topic}**: {stats['correct']}/{stats['total']} ({stats['percentage']:.0f}%) - {stats['status']}")
    
    # Weak topics
    weak_topics = get_weak_topics(topic_performance, threshold=60)
    
    if weak_topics:
        st.write("")
        st.write("---")
        st.markdown("### 🎯 Topics to Review")
        
        for topic_info in weak_topics:
            st.warning(f"**{topic_info['topic']}**: {topic_info['score']} ({topic_info['percentage']:.0f}%)")
            st.markdown(f"📺 [Re-watch this topic]({st.session_state.video_data['metadata']['url']})")
    
    st.write("")
    st.write("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Play Again", type="primary"):
            st.session_state.page = 'mode_selection'
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.answers = []
            st.session_state.show_feedback = False
            st.rerun()
    
    with col2:
        if st.button("📚 Review Notes"):
            st.session_state.page = 'notes'
            st.rerun()
    
    with col3:
        if st.button("🆕 New Video"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# Main app routing
def main():
    page = st.session_state.page
    
    if page == 'input':
        show_input_page()
    elif page == 'notes':
        show_notes_page()
    elif page == 'mode_selection':
        show_mode_selection()
    elif page == 'quiz':
        show_quiz_page()
    elif page == 'results':
        show_results_page()


if __name__ == "__main__":
    main()
