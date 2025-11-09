# MDC Academic Advisor - Setup Complete! 🎉

## ✅ System Status: WORKING

### Configuration
- **Backend**: http://localhost:5000
- **Frontend**: http://localhost:3002  
- **Model**: Claude 3.5 Sonnet (anthropic/claude-3.5-sonnet)
- **API Provider**: OpenRouter
- **API Key**: Single key for all operations
- **Response Format**: Plain ASCII text only (NO emojis)

### What Was Fixed

1. **API Key Issue**
   - Problem: System environment variable was overriding .env file with old key
   - Solution: Updated system environment variable with new key
   - Location: User environment variable `OPENROUTER_API_KEY`

2. **Request Format Issue**
   - Problem: OpenAI Python client was causing 401 errors
   - Solution: Switched to direct `requests` library for full control

3. **JSON Parsing Issue**
   - Problem: Control characters and emojis breaking JSON parsing
   - Solution: Added regex cleaning to remove control chars and Unicode

4. **Emoji/Unicode Issue**
   - Problem: Emojis causing string communication problems
   - Solution: 
     - Updated system instruction to forbid emojis
     - Added post-processing to strip all non-ASCII characters
     - Responses now contain only plain ASCII text

### How to Start the Backend

**Method 1: Using the batch file (RECOMMENDED)**
```bash
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor\backend
start_backend.bat
```

**Method 2: Manual PowerShell**
```powershell
$env:OPENROUTER_API_KEY='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'
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor\backend
python app.py
```

### Environment Variables

The system checks in this order:
1. System/User environment variables (highest priority)
2. .env file in backend directory

**Current Setup:**
- System variable: `OPENROUTER_API_KEY=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`
- .env file: Same key (backup)

### API Credits
- Your API key has $10 in credits
- Usage: $0 (fresh account)
- No rate limits with paid credits

### Features

**Working:**
- ✅ Real-time chat with Claude 3.5 Sonnet
- ✅ 8 PDF curriculum documents loaded (81,001 characters)
- ✅ Career path recommendations
- ✅ NO static fallbacks (shows real errors)
- ✅ Plain ASCII text responses (no emojis)
- ✅ JSON response format
- ✅ Rate limit retry logic (3 attempts with exponential backoff)

**Models Configured:**
- Primary: `anthropic/claude-3.5-sonnet`
- Fallback: `anthropic/claude-3-haiku`

### Testing

Test the API directly:
```powershell
$body = @{ chatHistory = @(@{ sender='user'; text='Hello!'}) } | ConvertTo-Json -Depth 10
Invoke-RestMethod -Uri 'http://localhost:5000/api/chat' -Method Post -ContentType 'application/json' -Body $body
```

Test the health endpoint:
```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/health'
```

### Troubleshooting

**If you get 401 errors:**
- Check system environment variable is set correctly
- Run: `[System.Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY", "User")`

**If backend won't start:**
- Use `start_backend.bat` which sets the environment variable
- Or set `$env:OPENROUTER_API_KEY` before running `python app.py`

**To update the API key:**
```powershell
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "YOUR_NEW_KEY", "User")
```
Then restart PowerShell and the backend.

### Files Modified
- `backend/app.py` - Main application (emoji removal, request format, JSON cleaning)
- `backend/.env` - API key configuration
- `backend/start_backend.bat` - Easy startup script
- System environment variables - Updated with new API key

---

**Everything is working! 🚀**
- Backend responds with clean ASCII text
- Claude 3.5 Sonnet provides high-quality academic advising
- No fallbacks - shows real errors for debugging
- Single API key for all operations
