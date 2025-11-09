# Hugging Face Fallback Setup

## Overview

Your MDC Academic Advisor now has **3 layers of AI responses**:

1. **Primary**: OpenRouter API (Llama 3.2) - Fastest, most reliable when working
2. **Fallback #1**: Hugging Face Llama (if OpenRouter fails)
3. **Fallback #2**: Smart Static Responses (if both APIs fail)

## Current Status

✅ **OpenRouter**: Configured (both conversation & PDF keys)
⚠️ **Hugging Face**: Not configured yet (optional fallback)
✅ **Static Fallback**: Active and working

## How to Enable Hugging Face Fallback

### Step 1: Get a Hugging Face API Token

1. Go to: https://huggingface.co/settings/tokens
2. Sign up or log in
3. Click "New token"
4. Name it: "MDC Advisor"
5. Type: Select "Read" (free tier is fine)
6. Copy your token (starts with `hf_...`)

### Step 2: Add Token to .env File

Open `backend\.env` and replace:

```
HUGGINGFACE_API_KEY=your_huggingface_token_here
```

With your actual token:

```
HUGGINGFACE_API_KEY=hf_YourActualTokenHere
```

### Step 3: Restart Backend

Stop the backend (Ctrl+C) and run:

```powershell
cd c:\Users\Ricar\Downloads\mdc-career-path-advisor\backend
python app.py
```

You should see:
```
Hugging Face API configured: True
```

## How It Works

### When You Ask a Question:

1. **Try OpenRouter first**
   - If successful → Returns AI-powered response
   - If fails (401, timeout, etc.) → Goes to step 2

2. **Try Hugging Face Llama**
   - Uses `meta-llama/Llama-3.2-3B-Instruct` model
   - Free tier available
   - If successful → Returns AI response
   - If fails → Goes to step 3

3. **Use Smart Static Fallback**
   - Detects program interest from keywords
   - Provides detailed info from loaded PDFs
   - Always works, no API needed

## Benefits

- **Redundancy**: If one API has issues, another takes over
- **Free Option**: Hugging Face has a generous free tier
- **No Downtime**: Static fallback ensures the chatbot always works
- **Cost Savings**: Can use Hugging Face free tier if OpenRouter credits run out

## Testing

To see the fallback in action:

1. Open: http://localhost:3002
2. Ask: "What programs are available?"
3. Check backend terminal to see which system responded:
   - `[DEBUG] Sending request to OpenRouter` = Primary working
   - `[INFO] Trying Hugging Face Llama fallback` = Fallback #1 active
   - `[INFO] Using static fallback` = Fallback #2 active

## Troubleshooting

**Q: Hugging Face says "Rate limit exceeded"?**
A: Free tier has limits. Wait a few minutes or upgrade to Pro ($9/month)

**Q: Both APIs fail?**
A: No problem! The static fallback will still provide helpful responses

**Q: Want to test Hugging Face directly?**
A: Temporarily remove/comment out the OpenRouter API key in `.env`

## Model Information

- **OpenRouter Model**: `meta-llama/llama-3.2-3b-instruct:free`
- **Hugging Face Model**: `meta-llama/Llama-3.2-3B-Instruct`
- Both use the same Llama 3.2 architecture for consistency!

## Cost Comparison

| Service | Model | Cost |
|---------|-------|------|
| OpenRouter | Llama 3.2 3B | $0.06 per 1M tokens (input) |
| Hugging Face | Llama 3.2 3B | 1,000 requests/day free |
| Static Fallback | N/A | Always free |

---

**Current Setup**: You're using OpenRouter (which has a 401 error) + Static Fallback.
**Recommended**: Add Hugging Face token for the middle fallback layer!
