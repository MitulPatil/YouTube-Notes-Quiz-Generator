# 🎓 YouTube Quiz Generator

Transform any YouTube lecture into an interactive, gamified quiz! Learn smarter, not harder.

## ✨ Features

- 📺 **YouTube Integration**: Extract transcripts from any video with captions
- 📝 **Smart Notes Generation**: AI-powered structured notes with key concepts
- 📥 **PDF Download**: Export your notes as professionally formatted PDF documents
- 🎮 **Gamified Quizzes**: Multiple difficulty levels, point system
- 📊 **Performance Tracking**: Detailed analytics by topic
- 🎯 **Weak Area Detection**: Identify topics that need review
- 💾 **Session Caching**: Fast reload for previously processed videos
- 🔄 **Replayability**: Generate new questions from the same video

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd Youtube_quize_generator

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from: https://ai.google.dev/

### 3. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 How to Use

1. **Enter YouTube URL**: Paste any YouTube video link with captions
2. **Wait for Processing**: The app will:
   - Extract the transcript
   - Generate structured notes
   - Create 50 quiz questions
3. **Review Notes**: Read the AI-generated summary and key concepts
4. **Download Notes (Optional)**: Click "📥 Download Notes as PDF" to save professionally formatted notes
5. **Choose Quiz Mode**:
   - 🎮 Quick Play (5 questions)
   - 📚 Standard (15 questions)
   - 🏆 Challenge (30 questions)
6. **Take the Quiz**: Answer questions and earn points
7. **View Results**: See your performance and weak topics

## 🏗️ Project Structure

```
Youtube_quize_generator/
├── app.py                 # Main Streamlit application
├── utils/
│   ├── transcript.py      # YouTube transcript extraction
│   ├── llm.py            # LLM integration for notes
│   ├── quiz.py           # Quiz generation and logic
│   ├── storage.py        # Data caching and persistence
│   └── pdf_generator.py  # PDF export functionality
├── data/                 # Cached sessions and results
├── .env                  # API keys (create this)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🎯 Features in Detail

### Smart Notes Generation
- Executive summary of the lecture
- Key concepts extracted
- Topics with descriptions
- Detailed markdown notes
- **Export to PDF** with professional formatting

### Quiz System
- 50 questions generated per video
- Three difficulty levels: Easy, Medium, Hard
- Multiple choice format
- Explanations for each answer
- Topic categorization

### Performance Analytics
- Overall score and percentage
- Performance by topic
- Weak area identification
- Video timestamp links for review

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini (via LiteLLM)
- **Transcript**: youtube-transcript-api
- **PDF Generation**: ReportLab
- **Storage**: JSON file-based caching

## 📝 Configuration Options

### Change LLM Model

Edit `utils/llm.py` and `utils/quiz.py`:

```python
# Current: Gemini
model="gemini/gemini-1.5-flash-latest"

# Alternatives:
model="openai/gpt-4o-mini"      # OpenAI
model="anthropic/claude-3-haiku" # Anthropic
```

### Adjust Question Count

Edit `app.py`:

```python
# Change default question pool size
questions_result = generate_questions(notes_result['notes'], num_questions=50)
```

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

MIT License - feel free to use this project for learning or commercial purposes.

## 🙏 Acknowledgments

- YouTube Transcript API for caption extraction
- Google Gemini for AI capabilities
- Streamlit for the amazing framework

## 📧 Support

Having issues? Check:
1. Your API keys are correctly set in `.env`
2. The YouTube video has captions enabled
3. You have internet connection
4. Dependencies are installed correctly

---

**Made with ❤️ for learners everywhere**
