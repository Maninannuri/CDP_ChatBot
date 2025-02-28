# CDP Assistant Chatbot

An AI-powered chatbot that provides assistance with Customer Data Platforms (CDPs) like Segment, mParticle, Lytics, and Zeotap.

## 🌟 Features

- **Real-time CDP Assistance**
  - Step-by-step implementation guides
  - Best practices and troubleshooting
  - Technical documentation lookups

- **Supported CDPs**
  - Segment
  - mParticle
  - Lytics
  - Zeotap

- **Modern UI/UX**
  - Dark/Light theme
  - Mobile responsive design
  - Interactive chat interface
  - Suggestion chips
  - Typing indicators

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/Maninannuri/CDP_ChatBot.git
cd CDP_Chatbot
```

2. Create virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize documentation:
```bash
python -m app.init_chatbot
```

5. Run the application:
```bash
python -m uvicorn app.main:app --reload
```

6. Visit http://localhost:8000 in your browser

## 💻 Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: HTML5, CSS3, JavaScript
- **NLP**: SentenceTransformers, scikit-learn
- **Documentation**: BeautifulSoup4, Selenium
- **Database**: File-based JSON storage

## 📁 Project Structure
```
Chatbot-for-CDP/
├── app/
│   ├── static/          # Static assets
│   ├── templates/       # HTML templates
│   ├── data/           # Documentation storage
│   ├── config/         # Configuration files
│   ├── utils/          # Utility functions
│   ├── main.py         # FastAPI application
│   ├── chatbot.py      # Chatbot logic
│   ├── scraper.py      # Documentation scraper
│   └── knowledge_base.py # Knowledge management
├── requirements.txt
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch:
```bash
git checkout -b feature/my-feature
```
3. Commit your changes:
```bash
git commit -m 'Add my feature'
```
4. Push to the branch:
```bash
git push origin feature/my-feature
```
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- CDP Documentation:
  - [Segment Docs](https://segment.com/docs/)
  - [mParticle Docs](https://docs.mparticle.com/)
  - [Lytics Docs](https://docs.lytics.com/)
  - [Zeotap Docs](https://docs.zeotap.com/)

## 📝 Notes

- Requires Python 3.8 or higher
- Chrome/Chromium for documentation scraping
- Internet connection for initial setup
