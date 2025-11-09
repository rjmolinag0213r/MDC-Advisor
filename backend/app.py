import os
import json
import requests
import time
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import PyPDF2
from typing import List, Dict
from openai import OpenAI
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_KEY_PDF = os.getenv("OPENROUTER_API_KEY")  # Use same key for everything
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using Claude 3.5 Sonnet (works with your account, excellent quality)
MODEL_NAME = "anthropic/claude-3.5-sonnet"
MODEL_NAME_FALLBACK = "anthropic/claude-3-haiku"  # Cheaper fallback
HUGGINGFACE_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # Hugging Face fallback
PDF_DIRECTORY = os.getenv("PDF_DIRECTORY", r"C:\Users\Ricar\Downloads\PDF-Info")

# System Instruction for the Academic Advisor
SYSTEM_INSTRUCTION = """# Persona and Tone
You are 'MyMDC.NextStop Chat', a friendly and enthusiastic academic advisor helping HIGH SCHOOL STUDENTS explore career paths at Miami Dade College (MDC).

**Remember: You're talking to teenagers who are exploring their future!**

**Your Approach:**
- Be encouraging, positive, and relatable
- Use simple, everyday language (avoid jargon unless explaining it)
- Get excited about their interests and dreams
- Ask questions to understand what they really enjoy doing
- Connect their interests to real careers and programs
- DO NOT use emojis or special Unicode characters - plain text only!

**Your Goal:** Help them discover which MDC technology program matches their interests and personality!

**Available MDC Programs:**
- **Applied Artificial Intelligence (AI)** - Create smart apps, AI assistants, machine learning
- **Data Analytics** - Solve problems with data, help businesses make decisions
- **Cybersecurity** - Be a digital defender, protect against hackers
- **Software Engineering** - Build apps, websites, and software
- **Networking** - Connect computers and build the internet infrastructure
- **Electrical & Computer Engineering** - Work with hardware, electronics, robotics

# How to Talk with High School Students

## Start with Their Interests
Ask questions like:
- "What do you like to do in your free time?"
- "What subjects do you enjoy in school?"
- "Do you like video games? Building things? Solving puzzles?"
- "Have you ever thought about what job sounds cool to you?"

## Connect Interests to Programs

**If they say they like:**
- Video games, apps → Software Engineering or AI
- Math, patterns, puzzles → Data Analytics or AI
- Protecting things, detective work → Cybersecurity
- Taking things apart, electronics → Electrical Engineering
- Making things work together → Networking
- Science fiction, robots, future tech → AI or Electrical Engineering

## Use Real-World Examples
- "You know how Siri works? That's AI!"
- "Ever wonder how Netflix knows what you like? That's data analytics!"
- "Want to stop hackers like in movies? That's cybersecurity!"
- "Love Instagram and TikTok? Software engineers build those!"

## Be Honest About Careers
✅ **Always use your knowledge to discuss:**
- What the job is really like
- How much money they can make (be honest, they care!)
- What companies hire these people
- If they can work from home or travel
- How hard is the program (be real but encouraging)
- What high school classes help prepare them

## Don't Overcomplicate
- ❌ Don't say: "Prerequisites include MAC 1105 with a C or higher"
- ✅ Instead say: "You'll need some math skills, but we'll help you with that!"
- ❌ Don't say: "The curriculum comprises 60 credit hours"
- ✅ Instead say: "It's a 2-year program, so you can start your career quickly!"

## Keep It Fresh
- DON'T remember everything from earlier (they might just be exploring different options!)
- Each question is a NEW chance to explore their interests
- If they ask about a different program, treat it as a new interest
- It's okay if they change their mind - that's normal for teens!

## Important Rules

### Use Curriculum Documents For:
- Specific course lists (but explain them simply)
- Program requirements
- Transfer opportunities to universities

### Use Your Knowledge For:
- Career descriptions and salaries
- What the jobs are actually like
- Industry trends and cool new tech
- Success stories and examples
- Study tips and college life advice

### Always Provide:
📞 **MDC Academic Advisor Contact:**
- Phone: **(305) 237-8888**
- Website: www.mdc.edu/advisement

# 📝 Output Format

You MUST respond with a JSON object in this format:

{
  "chatResponse": "Friendly, encouraging message using simple language",
  "careerPlan": {
    "programName": "Program name or null",
    "progress": 0,
    "requiredClasses": [],
    "transferUniversities": []
  }
}

**ChatResponse Guidelines:**
- Write like you're texting a friend (but still professional!)
- NO EMOJIS! Use plain text only - the system doesn't support special characters
- Ask follow-up questions about THEIR interests
- Share exciting facts about careers
- Be genuinely enthusiastic
- Keep paragraphs short and easy to read

**CareerPlan Guidelines:**
- Only populate when they show clear interest in ONE specific program
- Don't force them into a program too quickly
- It's okay to leave programName as null while exploring
- Don't track progress strictly - they're just exploring!
- When listing courses in requiredClasses, use PLAIN TEXT names only (no emojis, no special Unicode)
- Each course must have "name" (string) and "status" (pending/planned/in-progress/completed)

**Example Good Responses:**

"That's awesome that you like video games! Did you know people actually get paid to create games? That's what software engineers do!

At MDC, we have a Software Engineering program where you learn to build apps, games, and websites. Companies like EA, Microsoft, and even startups in Miami hire our graduates.

**Quick question:** Do you like the creative side (designing how games look) or the technical side (making them actually work)? Both are cool, just different paths!

Want to know more about what software engineers actually do every day, or should we explore other tech careers?"

IMPORTANT: Use only plain ASCII text - NO emojis, NO special Unicode characters!

Respond ONLY with valid JSON."""


class MDCAcademicAdvisor:
    def __init__(self):
        self.document_text = self.load_documents()
        self.document_summary = self._create_document_summary()
        self.api_key = OPENROUTER_API_KEY  # For conversational responses
        self.api_key_pdf = OPENROUTER_API_KEY_PDF  # For PDF processing if needed
        self.hf_api_key = HUGGINGFACE_API_KEY  # Hugging Face fallback
        
        # Debug: Print API key info (first/last 4 chars only for security)
        if self.api_key:
            print(f"[DEBUG] API Key loaded: {self.api_key[:10]}...{self.api_key[-4:]}")
        else:
            print(f"[ERROR] API Key is None or empty!")
        
        # Initialize OpenAI clients for both API keys
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        self.client_pdf = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key_pdf
        )
        
        # Initialize Hugging Face client
        if self.hf_api_key and self.hf_api_key != "your_huggingface_token_here":
            self.hf_client = InferenceClient(token=self.hf_api_key)
        else:
            self.hf_client = None
    
    def _create_document_summary(self) -> str:
        """Create a concise summary of documents for API context."""
        return """
# MDC PROGRAM DOCUMENTS SUMMARY

## Available Programs:
1. **Applied Artificial Intelligence (S9520)** - AI, machine learning, data science
2. **Data Analytics (S9510)** - Business intelligence, big data, statistical analysis
3. **Cybersecurity (S9515)** - Network security, ethical hacking, digital forensics
4. **Software Engineering (S9501)** - Programming, web/mobile apps, software development
5. **Networking (S9500)** - Network admin, cloud computing, infrastructure
6. **Electrical & Computer Engineering (S9100)** - Hardware, electronics, systems

## Key Information Available:
- Course requirements and credit hours for each program
- Prerequisites for upper-division courses
- General Education requirements (36 credits, 'C' or higher)
- Civic Literacy requirement (AMH 2010, AMH 2020, or POS 2041)
- Transfer agreements: FIU Connect4Success, UM Articulation Agreement

Note: Full curriculum details are available in the document library if specific course information is needed.
"""
        
    def load_documents(self) -> str:
        """Load and extract text from all PDFs in the specified directory."""
        pdf_dir = Path(PDF_DIRECTORY)
        
        if not pdf_dir.exists():
            print(f"Warning: PDF directory '{PDF_DIRECTORY}' does not exist.")
            return "# MDC Curriculum Documents\n(No documents loaded - directory not found)"
        
        document_text = "# MDC CURRICULUM DOCUMENTS AND ARTICULATION AGREEMENTS\n\n"
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"Warning: No PDF files found in '{PDF_DIRECTORY}'")
            return document_text + "(No PDF files found in directory)"
        
        print(f"Loading {len(pdf_files)} PDF files from {PDF_DIRECTORY}...")
        
        for pdf_file in pdf_files:
            try:
                document_text += f"\n\n## Document: {pdf_file.stem}\n\n"
                
                with open(pdf_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        text = page.extract_text()
                        if text.strip():
                            document_text += f"{text}\n"
                
                print(f"  ✓ Loaded {pdf_file.name}")
                
            except Exception as e:
                print(f"  ✗ Error loading {pdf_file.name}: {e}")
                document_text += f"(Error loading this document: {e})\n"
        
        return document_text
    
    def get_specific_course_info(self, program_name: str, question: str) -> str:
        """Use PDF API key to extract specific course information from documents."""
        if not self.api_key_pdf:
            return "Course information not available."
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"Extract specific course information from these MDC curriculum documents. Be concise and accurate.\n\n{self.document_text[:20000]}"
                },
                {
                    "role": "user",
                    "content": f"For the {program_name} program: {question}"
                }
            ]
            
            headers = {
                "Authorization": f"Bearer {self.api_key_pdf}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3001",
                "X-Title": "MDC Academic Advisor"
            }
            
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get('choices'):
                return data['choices'][0]['message']['content']
            return "Information not found."
            
        except Exception as e:
            print(f"[ERROR] Course info extraction error: {e}")
            return "Unable to retrieve course information at this time."
    
    def _try_huggingface_fallback(self, messages: List[Dict]) -> Dict:
        """Try Hugging Face Llama as fallback when OpenRouter fails."""
        if not self.hf_client:
            print("[INFO] Hugging Face client not available, using static fallback")
            return None
        
        try:
            print("[INFO] Trying Hugging Face Llama fallback...")
            
            # Convert messages to Hugging Face format
            prompt = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    prompt += f"System: {content}\n\n"
                elif role == "user":
                    prompt += f"User: {content}\n\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n\n"
            
            prompt += "Assistant (respond with valid JSON):"
            
            # Call Hugging Face API
            response = self.hf_client.text_generation(
                prompt,
                model=HUGGINGFACE_MODEL,
                max_new_tokens=1000,
                temperature=0.7,
                return_full_text=False
            )
            
            # Try to parse as JSON
            try:
                parsed = json.loads(response)
                if 'chatResponse' in parsed and 'careerPlan' in parsed:
                    print("[SUCCESS] Hugging Face fallback successful!")
                    return parsed
            except json.JSONDecodeError:
                # If not JSON, wrap the response
                print("[INFO] Hugging Face response wasn't JSON, wrapping it")
                return {
                    "chatResponse": response,
                    "careerPlan": {
                        "programName": None,
                        "progress": 0,
                        "requiredClasses": [],
                        "transferUniversities": []
                    }
                }
            
        except Exception as e:
            print(f"[ERROR] Hugging Face fallback failed: {e}")
            return None
    
    def _call_openrouter_with_retry(self, messages: List[Dict], max_retries: int = 3) -> str:
        """Call OpenRouter API with exponential backoff for rate limiting."""
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] OpenRouter attempt {attempt + 1}/{max_retries}")
                
                # Use requests library directly for full control
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": MODEL_NAME,
                    "messages": messages,
                    "temperature": 0.7
                }
                
                print(f"[DEBUG] Sending to {API_URL}")
                response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                print(f"[SUCCESS] OpenRouter API responded successfully!")
                return content
                
            except Exception as e:
                error_msg = str(e).lower()
                print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
                
                # Check if it's a rate limit error
                if '429' in error_msg or 'rate limit' in error_msg or 'too many requests' in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 3  # 3s, 6s, 12s...
                        print(f"[WARNING] Rate limit hit. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[ERROR] Rate limit exceeded after {max_retries} attempts")
                        raise
                else:
                    # For other errors, raise immediately - NO FALLBACK
                    print(f"[ERROR] Non-rate-limit error: {type(e).__name__}")
                    raise
        
        raise Exception("Max retries exceeded")

    
    def get_advice(self, chat_history: List[Dict]) -> Dict:
        """Send request to OpenRouter API and return the LLM's response."""
        if not self.api_key:
            return {
                "chatResponse": "Error: OpenRouter API key is not configured.",
                "careerPlan": {
                    "programName": None,
                    "progress": 0,
                    "requiredClasses": [],
                    "transferUniversities": []
                }
            }
        
        # Build messages with system instruction and document summary (not full text to avoid token limits)
        messages = [
            {
                "role": "system",
                "content": f"{SYSTEM_INSTRUCTION}\n\n---\n\n{self.document_summary}"
            }
        ]
        
        # Add ALL chat history - no limits for unlimited conversation
        print(f"[DEBUG] Processing {len(chat_history)} messages from chat history")
        
        for msg in chat_history:
            role = "assistant" if msg.get("sender") == "bot" or msg.get("role") == "model" else "user"
            text = msg.get("text") or msg.get("parts", [{}])[0].get("text", "")
            if text:
                messages.append({"role": role, "content": text})
        
        try:
            print(f"[DEBUG] Sending request to OpenRouter with {len(messages)} messages")
            
            # Use retry logic for rate limiting
            content = self._call_openrouter_with_retry(messages)

            print(f"[DEBUG] Raw content length: {len(content)}")
            print(f"[DEBUG] First 300 chars: {repr(content[:300])}")
            
            # Clean up the content - remove markdown code fences if present
            content_clean = content.strip()
            if content_clean.startswith("```json"):
                content_clean = content_clean[7:]
            if content_clean.startswith("```"):
                content_clean = content_clean[3:]
            if content_clean.endswith("```"):
                content_clean = content_clean[:-3]
            content_clean = content_clean.strip()
            
            # Remove control characters that break JSON parsing
            content_clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content_clean)
            
            print(f"[DEBUG] Cleaned content first 300: {repr(content_clean[:300])}")
            
            parsed_response = json.loads(content_clean)
            
            # Remove emojis and special Unicode characters from chatResponse
            if 'chatResponse' in parsed_response:
                chat_text = parsed_response['chatResponse']
                # Remove emojis and special Unicode characters (keep only ASCII + basic Latin)
                chat_text_clean = re.sub(r'[^\x00-\x7F]+', '', chat_text)
                # Clean up extra whitespace
                chat_text_clean = re.sub(r'\s+', ' ', chat_text_clean).strip()
                parsed_response['chatResponse'] = chat_text_clean
                print(f"[DEBUG] Removed emojis/unicode from chatResponse")
            
            # Clean requiredClasses array - remove emojis from course names
            if 'careerPlan' in parsed_response and parsed_response['careerPlan']:
                career_plan = parsed_response['careerPlan']
                
                # Clean requiredClasses
                if 'requiredClasses' in career_plan and isinstance(career_plan['requiredClasses'], list):
                    cleaned_classes = []
                    for course in career_plan['requiredClasses']:
                        if isinstance(course, dict) and 'name' in course:
                            # Remove emojis and special chars from course name
                            clean_name = re.sub(r'[^\x00-\x7F]+', '', str(course['name']))
                            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
                            course['name'] = clean_name
                            # Ensure status field exists
                            if 'status' not in course:
                                course['status'] = 'pending'
                            cleaned_classes.append(course)
                    career_plan['requiredClasses'] = cleaned_classes
                    print(f"[DEBUG] Cleaned {len(cleaned_classes)} course names")
                
                # Clean transferUniversities
                if 'transferUniversities' in career_plan and isinstance(career_plan['transferUniversities'], list):
                    cleaned_unis = []
                    for uni in career_plan['transferUniversities']:
                        if isinstance(uni, dict):
                            # Remove emojis from all text fields
                            for field in ['name', 'gpa', 'prereqs', 'notes']:
                                if field in uni:
                                    clean_text = re.sub(r'[^\x00-\x7F]+', '', str(uni[field]))
                                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                                    uni[field] = clean_text
                            cleaned_unis.append(uni)
                    career_plan['transferUniversities'] = cleaned_unis
                    print(f"[DEBUG] Cleaned {len(cleaned_unis)} university entries")
            
            # Validate structure
            if 'chatResponse' in parsed_response and 'careerPlan' in parsed_response:
                print(f"[SUCCESS] Valid JSON response from Claude!")
                return parsed_response
            else:
                print(f"[WARNING] Response missing required fields, trying to fix...")
                # Try to fix structure if response is close
                if 'chatResponse' in parsed_response:
                    parsed_response['careerPlan'] = {
                        "programName": None,
                        "progress": 0,
                        "requiredClasses": [],
                        "transferUniversities": []
                    }
                    return parsed_response
                raise ValueError("Invalid response structure from LLM")
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON Parse Error: {e}")
            print(f"[ERROR] Response was not valid JSON - cannot proceed without proper LLM response")
            # NO FALLBACK - raise the error
            raise Exception(f"LLM returned invalid JSON: {e}")
            
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            print(f"[ERROR] Failed to get response from LLM - NO FALLBACK AVAILABLE")
            # NO FALLBACK - raise the error
            raise

    
    def _handle_connection_error(self, chat_history: List[Dict]) -> Dict:
        """Handle connection errors intelligently by asking exploratory questions."""
        # Get the last user message
        last_user_message = ""
        for msg in reversed(chat_history):
            if msg.get("sender") == "user" or msg.get("role") == "user":
                last_user_message = msg.get("text", "").lower()
                break
        
        # Check if this is the first message or a greeting
        is_first_message = len([m for m in chat_history if m.get("sender") == "user"]) <= 1
        
        # Keywords for interest detection
        tech_keywords = {
            'ai': 'Applied Artificial Intelligence',
            'artificial intelligence': 'Applied Artificial Intelligence',
            'machine learning': 'Applied Artificial Intelligence',
            'data': 'Data Analytics',
            'analytics': 'Data Analytics',
            'data science': 'Data Analytics',
            'cyber': 'Cybersecurity',
            'security': 'Cybersecurity',
            'hacking': 'Cybersecurity',
            'software': 'Software Engineering',
            'programming': 'Software Engineering',
            'coding': 'Software Engineering',
            'developer': 'Software Engineering',
            'network': 'Networking',
            'networking': 'Networking',
            'electrical': 'Electrical and Computer Engineering Technology',
            'hardware': 'Electrical and Computer Engineering Technology',
            'engineering': 'Electrical and Computer Engineering Technology'
        }
        
        # Check for program interest
        detected_program = None
        for keyword, program in tech_keywords.items():
            if keyword in last_user_message:
                detected_program = program
                break
        
        # Generate appropriate response based on context
        if is_first_message:
            response_text = """Hello! I'm your MDC Academic Navigator. 

While I'm experiencing some connectivity issues with my advanced features, I can still help you explore your options at MDC!

**Miami Dade College offers these exciting technology programs:**
• 🤖 **Applied Artificial Intelligence** - AI, Machine Learning, Data Science
• 📊 **Data Analytics** - Business Intelligence, Big Data, Statistical Analysis
• 🔒 **Cybersecurity** - Network Security, Ethical Hacking, Digital Forensics
• 💻 **Software Engineering** - Application Development, Programming, Web Development
• 🌐 **Networking** - Network Administration, Cloud Computing, Infrastructure
• ⚡ **Electrical & Computer Engineering** - Hardware, Electronics, Systems Design

**What interests you most?**
- Do you enjoy solving problems with code?
- Are you interested in data and statistics?
- Do you like securing systems and networks?
- Are you fascinated by hardware and electronics?

📞 **Need personalized guidance?** Contact MDC Academic Advisors:
- Phone: **(305) 237-8888**
- Website: www.mdc.edu/advisement
- Live Chat: Available on MDC website

Tell me about your interests, and I'll help guide you to the right program!"""
        
        elif detected_program:
            # Student expressed interest in a specific program
            program_info = {
                'Applied Artificial Intelligence': {
                    'description': 'Focus on AI, machine learning, and intelligent systems',
                    'careers': 'AI Engineer, Machine Learning Specialist, Data Scientist',
                    'skills': 'Python, Machine Learning, Neural Networks, Data Analysis'
                },
                'Data Analytics': {
                    'description': 'Turn data into actionable insights for businesses',
                    'careers': 'Data Analyst, Business Intelligence Analyst, Data Engineer',
                    'skills': 'SQL, Python, Statistics, Data Visualization, Tableau'
                },
                'Cybersecurity': {
                    'description': 'Protect systems and networks from cyber threats',
                    'careers': 'Security Analyst, Penetration Tester, Security Engineer',
                    'skills': 'Network Security, Ethical Hacking, Risk Assessment, Compliance'
                },
                'Software Engineering': {
                    'description': 'Design and develop software applications',
                    'careers': 'Software Developer, Full-Stack Engineer, Mobile App Developer',
                    'skills': 'Java, Python, Web Development, Databases, Agile'
                },
                'Networking': {
                    'description': 'Build and manage computer networks and infrastructure',
                    'careers': 'Network Administrator, Cloud Engineer, Systems Engineer',
                    'skills': 'Cisco, Network Design, Cloud Computing, Linux'
                },
                'Electrical and Computer Engineering Technology': {
                    'description': 'Work with hardware, electronics, and computer systems',
                    'careers': 'Hardware Engineer, Systems Designer, Electronics Technician',
                    'skills': 'Circuit Design, Embedded Systems, Digital Electronics'
                }
            }
            
            info = program_info.get(detected_program, {})
            response_text = f"""Great choice! **{detected_program}** is an excellent program at MDC!

**About the Program:**
{info.get('description', 'A comprehensive technology program')}

**Typical Career Paths:**
{info.get('careers', 'Various technology roles')}

**Key Skills You'll Learn:**
{info.get('skills', 'Industry-relevant technical skills')}

**Next Steps:**
1. I recommend speaking with an MDC Academic Advisor for detailed course requirements
2. Review the full curriculum and prerequisites
3. Explore transfer opportunities to FIU, UM, and other universities

📞 **Contact MDC Academic Advisors:**
- Phone: **(305) 237-8888**
- Website: www.mdc.edu/advisement
- Email: advisement@mdc.edu

Would you like to know more about:
- Course requirements and prerequisites?
- Transfer opportunities to universities?
- Career outlook and salaries in this field?
- Other related MDC programs?"""
        
        else:
            # General exploratory conversation
            response_text = """I'm here to help, even though I'm experiencing some technical difficulties!

Let me ask you a few questions to find the best program for you:

**1. What do you enjoy doing?**
- Building and creating things with code?
- Analyzing data and finding patterns?
- Protecting systems from threats?
- Working with hardware and electronics?
- Managing networks and infrastructure?

**2. What's your career goal?**
- High-paying tech job?
- Remote work opportunities?
- Starting your own tech business?
- Working in a specific industry?

**3. Do you have any experience with:**
- Programming or coding?
- Math and statistics?
- Computer hardware?
- Problem-solving and logic?

📞 **For immediate assistance, contact MDC Academic Advisors:**
- Phone: **(305) 237-8888**
- Website: www.mdc.edu/advisement
- Walk-in: Available at all MDC campuses

Tell me more about your interests, and I'll recommend the perfect program for you!"""
        
        return {
            "chatResponse": response_text,
            "careerPlan": {
                "programName": detected_program,
                "progress": 0,
                "requiredClasses": [],
                "transferUniversities": []
            }
        }


# Initialize the advisor
advisor = MDCAcademicAdvisor()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "documents_loaded": len(advisor.document_text) > 100,
        "api_configured": bool(OPENROUTER_API_KEY),
        "api_pdf_configured": bool(OPENROUTER_API_KEY_PDF),
        "huggingface_configured": bool(advisor.hf_client)
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint that receives chat history and returns guidance."""
    try:
        data = request.get_json()
        chat_history = data.get('chatHistory', [])
        
        if not chat_history:
            return jsonify({
                "error": "Chat history is required"
            }), 400
        
        response = advisor.get_advice(chat_history)
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in /api/chat: {e}")
        return jsonify({
            "error": str(e),
            "chatResponse": "I encountered an error processing your request. Please try again.",
            "careerPlan": {
                "programName": None,
                "progress": 0,
                "requiredClasses": [],
                "transferUniversities": []
            }
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 MDC Academic Advisor Backend Server")
    print("="*60)
    print(f"API Key (Conversation) configured: {bool(OPENROUTER_API_KEY)}")
    print(f"API Key (PDF/Docs) configured: {bool(OPENROUTER_API_KEY_PDF)}")
    print(f"Hugging Face API configured: {bool(advisor.hf_client)}")
    print(f"PDF Directory: {PDF_DIRECTORY}")
    print(f"Documents loaded: {len(advisor.document_text)} characters")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
