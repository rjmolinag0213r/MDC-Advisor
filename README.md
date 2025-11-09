<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# 🎓 MDC Career Path Advisor

A full-stack academic advisor application for Miami Dade College students. This intelligent chatbot uses Gemini 2.0 via OpenRouter to provide personalized academic guidance based on MDC's curriculum documents.

## 🌟 Features

- **AI-Powered Academic Advisor**: Uses Gemini 2.0 to analyze curriculum documents and provide accurate course guidance
- **Document-Based Knowledge**: Processes PDF curriculum documents for Applied AI, Data Analytics, Cybersecurity, Software Engineering, Networking, and Electrical Engineering programs
- **Interactive Chat Interface**: Beautiful React-based UI with real-time chat
- **Progress Tracking**: Visual progress indicators for degree completion
- **Transfer University Recommendations**: Suggests relevant transfer options (FIU, UM, etc.)
- **Course Status Management**: Track completed, in-progress, and pending courses

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: Python Flask API
- **AI Model**: Google Gemini 2.0 (via OpenRouter)
- **Document Processing**: PyPDF2 for extracting curriculum information

## 📋 Prerequisites

### Backend Requirements
- Python 3.8 or higher
- pip (Python package manager)

### Frontend Requirements
- Node.js 16 or higher
- npm or yarn

## 🚀 Quick Start

### 1. Backend Setup

#### Navigate to backend directory
```powershell
cd backend
```

#### Create virtual environment (recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Install dependencies
```powershell
pip install -r requirements.txt
```

#### Configure environment
The `.env` file is already configured with:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `PDF_DIRECTORY`: Path to your PDF documents (`C:\Users\Ricar\Downloads\PDF-Info`)

**Important**: Make sure your PDF documents are in the `C:\Users\Ricar\Downloads\PDF-Info` directory.

#### Start the backend server
```powershell
python app.py
```

The backend will start on `http://localhost:5000`

You should see output confirming:
- ✓ API Key configured
- ✓ PDF Directory found
- ✓ Documents loaded successfully

### 2. Frontend Setup

Open a **new terminal** and navigate to the project root:

```powershell
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor
```

#### Install dependencies
```powershell
npm install
```

#### Start the development server
```powershell
npm run dev
```

The frontend will start on `http://localhost:5173`

### 3. Open the Application

Open your browser and navigate to `http://localhost:5173`

## 📁 Project Structure

```
mdc-career-path-advisor/
├── backend/
│   ├── app.py                  # Flask API server
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Backend environment config
├── components/                 # React components
│   ├── CareerJourneyPanel.tsx  # Progress tracking panel
│   ├── ChatPanel.tsx           # Chat interface
│   ├── ChatBubble.tsx          # Message bubbles
│   └── ProgressCircle.tsx      # Visual progress indicator
├── services/
│   ├── geminiService.ts        # API communication
│   └── backendService.ts       # Backend integration
├── App.tsx                     # Main React component
├── types.ts                    # TypeScript definitions
├── constants.ts                # App constants
├── .env.local                  # Frontend environment config
└── package.json               # Node dependencies
```

## 🔧 Configuration

### Backend Configuration (`backend/.env`)
```
OPENROUTER_API_KEY=your-api-key-here
PDF_DIRECTORY=C:\Users\Ricar\Downloads\PDF-Info
```

### Frontend Configuration (`.env.local`)
```
VITE_BACKEND_URL=http://localhost:5000
```

## 📚 PDF Documents Required

Place these curriculum PDFs in `C:\Users\Ricar\Downloads\PDF-Info`:
- AI course.pdf (Applied Artificial Intelligence S9520)
- Data Analytics.pdf (Data Analytics S9510)
- CyberSecurity.pdf (Cybersecurity S9515)
- Sotfware Engienner.pdf (IST-Software Engineering S9501)
- Networking.pdf (IST-Networking S9500)
- Electrical Engennier.pdf (Electrical & Computer Engineering S9100)
- AA_FIU_Business.pdf (FIU Connect4Success MOU)
- UM Articulation Agreement.pdf

## 🎯 How to Use

1. **Start a Conversation**: The chatbot will greet you and ask about your program interest
2. **Ask Questions**: 
   - "What courses do I need for the AI program?"
   - "What are the prerequisites for Data Structures?"
   - "Can you compare Cybersecurity and Software Engineering?"
   - "I've completed ENC 1101, what's next?"
3. **Track Progress**: The right panel shows your degree progress and transfer options
4. **Update Course Status**: Click courses to mark them as completed or in-progress

## 🛠️ Development

### Run Frontend in Development Mode
```powershell
npm run dev
```

### Build Frontend for Production
```powershell
npm run build
```

### Preview Production Build
```powershell
npm run preview
```

### Run Backend with Debug Mode
```powershell
python app.py
```

## 🔍 API Endpoints

### Health Check
```
GET http://localhost:5000/health
```

### Chat Endpoint
```
POST http://localhost:5000/api/chat
Content-Type: application/json

{
  "chatHistory": [
    {
      "sender": "user",
      "text": "I'm interested in Computer Science",
      "role": "user"
    }
  ]
}
```

## 🐛 Troubleshooting

### Backend won't start
- Verify Python 3.8+ is installed: `python --version`
- Check if virtual environment is activated
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify API key in `backend/.env`

### Frontend won't connect to backend
- Ensure backend is running on port 5000
- Check `VITE_BACKEND_URL` in `.env.local`
- Look for CORS errors in browser console

### PDFs not loading
- Verify PDF directory path in `backend/.env`
- Ensure PDF files exist in the specified directory
- Check file permissions
- Look for error messages in backend console

### API errors
- Verify OpenRouter API key is valid
- Check API rate limits
- Ensure internet connection is working

## 📝 License

This project is for educational purposes as part of Miami Dade College's academic support system.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review console logs (both frontend and backend)
3. Verify all configuration files are correct

## 🎓 About

Built to help MDC students navigate their academic journey with AI-powered guidance based on official curriculum documents.

