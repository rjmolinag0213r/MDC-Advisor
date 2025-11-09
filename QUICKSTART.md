# 🚀 Quick Start Guide - MDC Career Path Advisor

## ⚡ Fast Setup (3 Steps)

### Step 1: Setup (One Time Only)

Open PowerShell and run:

```powershell
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor
.\setup.ps1
```

This will:
- ✓ Check Python and Node.js installation
- ✓ Create Python virtual environment
- ✓ Install all backend dependencies
- ✓ Install all frontend dependencies

### Step 2: Start Backend

In PowerShell terminal #1:

```powershell
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor
.\start-backend.ps1
```

You should see:
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

### Step 3: Start Frontend

In a NEW PowerShell terminal #2:

```powershell
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor
.\start-frontend.ps1
```

You should see:
```
  VITE v6.2.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
```

### Step 4: Open Application

Open your browser and go to: **http://localhost:5173**

---

## 🎯 Testing the Application

Once the app is open, try these queries:

1. **General Program Info**:
   - "What programs are available?"
   - "Tell me about the AI program"

2. **Course Information**:
   - "What courses do I need for Applied Artificial Intelligence?"
   - "What are the prerequisites for Data Structures?"

3. **Transfer Planning**:
   - "What universities can I transfer to?"
   - "Tell me about the FIU articulation agreement"

4. **Progress Tracking**:
   - "I've completed ENC 1101 and MAC 1105"
   - "I'm interested in Software Engineering"

---

## 🛑 Stopping the Application

1. In the **Backend terminal**: Press `Ctrl+C`
2. In the **Frontend terminal**: Press `Ctrl+C`

---

## 🔧 Troubleshooting

### Backend won't start
```powershell
# Check Python version (need 3.8+)
python --version

# Reinstall dependencies
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Frontend won't start
```powershell
# Check Node version (need 16+)
node --version

# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules
npm install
```

### PDFs not loading
```powershell
# Verify PDF directory exists
Test-Path "C:\Users\Ricar\Downloads\PDF-Info"

# Check PDF files
Get-ChildItem "C:\Users\Ricar\Downloads\PDF-Info" -Filter *.pdf
```

### Application won't load in browser
1. Check backend is running (should show "Running on http://127.0.0.1:5000")
2. Check frontend is running (should show "Local: http://localhost:5173")
3. Try refreshing the browser (F5)
4. Clear browser cache (Ctrl+Shift+Delete)

---

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Node.js**: 16 or higher
- **PDF Files**: Must be in `C:\Users\Ricar\Downloads\PDF-Info`
- **Internet**: Required for OpenRouter API calls
- **Browser**: Chrome, Firefox, or Edge (latest versions)

---

## 🔑 Configuration Files

### Backend (.env)
Location: `backend/.env`
```
OPENROUTER_API_KEY=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
PDF_DIRECTORY=C:\Users\Ricar\Downloads\PDF-Info
```

### Frontend (.env.local)
Location: `.env.local`
```
VITE_BACKEND_URL=http://localhost:5000
```

---

## 💡 Tips

1. **Keep both terminals open** while using the application
2. **Backend must start first** before starting frontend
3. **Check console logs** if something isn't working
4. **PDF files must be in the correct directory** before starting backend
5. **Use the setup script only once** - after that, just use start scripts

---

## 🎓 Example Session

```
You: Hi, I'm interested in Artificial Intelligence
Bot: Hello! I'm your MDC Academic Navigator. The Applied Artificial 
     Intelligence program (S9520) is an excellent choice...

You: What courses do I need?
Bot: Here are the required courses for the Applied AI program:
     - COP 1000: Introduction to Programming
     - COP 2210: Computer Programming I
     ...

You: I've completed COP 1000 and ENC 1101
Bot: Great progress! I've marked those as completed. Your next 
     recommended course would be COP 2210...
```

---

## 📞 Need Help?

1. Check the main README.md for detailed documentation
2. Review the troubleshooting section above
3. Check both terminal windows for error messages
4. Verify all configuration files are correct
