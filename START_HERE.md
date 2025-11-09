# 🎯 READY TO RUN - Copy & Paste These Commands

## ✅ Everything is set up and ready!

Your MDC Career Path Advisor is fully implemented with:
- ✅ Python Flask backend with PDF processing
- ✅ React frontend with beautiful UI
- ✅ OpenRouter API integration (Gemini 2.0)
- ✅ All 8 curriculum PDFs configured
- ✅ API key configured

---

## 🚀 COMMANDS TO RUN (Copy these exactly)

### Step 1: Open PowerShell Terminal #1 (Backend)

```powershell
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor\backend
python -m pip install flask flask-cors python-dotenv requests PyPDF2
python app.py
```

**Wait for this output**:
```
============================================================
🎓 MDC Academic Advisor Backend Server
============================================================
API Key configured: True
PDF Directory: C:\Users\Ricar\Downloads\PDF-Info
Documents loaded: 81001 characters
============================================================
 * Running on http://127.0.0.1:5000
```

✅ **Backend is ready when you see the above!**

---

### Step 2: Open PowerShell Terminal #2 (Frontend)

```powershell
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor
npm install
npm run dev
```

**Wait for this output**:
```
  VITE v6.2.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

✅ **Frontend is ready when you see the above!**

---

### Step 3: Open Your Browser

Navigate to: **http://localhost:5173**

You should see the MDC Career Path Advisor interface!

---

## 🧪 TEST THE APPLICATION

Try these queries in the chat:

1. "Hi, what programs are available?"
2. "Tell me about the Applied Artificial Intelligence program"
3. "What courses do I need for Software Engineering?"
4. "I've completed ENC 1101 and MAC 1105"
5. "What are the prerequisites for Data Structures?"

---

## 🛑 TO STOP THE APPLICATION

1. **Backend Terminal**: Press `Ctrl+C`
2. **Frontend Terminal**: Press `Ctrl+C`

---

## 🔍 IF SOMETHING GOES WRONG

### Backend not starting?
```powershell
# Check Python version (need 3.8+)
python --version

# Verify PDFs exist
Test-Path "C:\Users\Ricar\Downloads\PDF-Info"
Get-ChildItem "C:\Users\Ricar\Downloads\PDF-Info" -Filter *.pdf
```

### Frontend not starting?
```powershell
# Check Node.js version (need 16+)
node --version

# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules
npm install
```

### Application loads but chat doesn't work?
1. Check backend terminal - should show "Running on http://127.0.0.1:5000"
2. Check frontend terminal - should show "Local: http://localhost:5173/"
3. Open browser DevTools (F12) and check Console for errors
4. Refresh the page (F5)

---

## 📁 FILE LOCATIONS

All files are in: `c:\Users\Ricar\Downloads\mdc-career-path-advisor\`

**Backend files**:
- `backend/app.py` - Main Flask server
- `backend/.env` - Configuration (API key, PDF path)
- `backend/requirements.txt` - Python dependencies

**Frontend files**:
- `App.tsx` - Main React application
- `services/geminiService.ts` - Backend communication
- `.env.local` - Frontend configuration

**PDF Documents** (must exist here):
- `C:\Users\Ricar\Downloads\PDF-Info\*.pdf`

---

## 📊 WHAT YOU'LL SEE

### Backend Terminal Output:
```
Loading 8 PDF files from C:\Users\Ricar\Downloads\PDF-Info...
  ✓ Loaded AA_FIU_Business.pdf
  ✓ Loaded AI course.pdf
  ✓ Loaded CyberSecurity.pdf
  ✓ Loaded Data Analytics.pdf
  ✓ Loaded Electrical Engennier.pdf
  ✓ Loaded Networking.pdf
  ✓ Loaded Sotfware Engienner.pdf
  ✓ Loaded UM Articulation Agreement.pdf

============================================================
🎓 MDC Academic Advisor Backend Server
============================================================
API Key configured: True
PDF Directory: C:\Users\Ricar\Downloads\PDF-Info
Documents loaded: 81001 characters
============================================================

 * Running on http://127.0.0.1:5000
```

### Frontend Terminal Output:
```
  VITE v6.2.0  ready in 523 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### Browser Interface:
- Left side: Chat interface with messages
- Right side: Career journey panel with progress tracker
- Top: Program name and progress percentage
- Bottom: Required courses and transfer universities

---

## 💡 QUICK TIPS

1. **Always start backend first**, then frontend
2. **Keep both terminals open** while using the app
3. **Backend processes PDFs on startup** - takes a few seconds
4. **First API call may be slow** - Gemini model is loading
5. **Chat history is maintained** during your session

---

## 🎉 YOU'RE ALL SET!

Your complete academic advisor application is ready to use!

**Just run the two command blocks above in separate terminals and open the browser.**

Need help? Check:
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick start guide with troubleshooting
- `IMPLEMENTATION.md` - Technical details

**Enjoy your MDC Academic Advisor! 🎓**
