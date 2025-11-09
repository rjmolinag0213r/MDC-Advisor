"""
Test script for MDC Academic Advisor Backend
Run this to verify the backend is working correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import advisor, OPENROUTER_API_KEY, PDF_DIRECTORY

def test_configuration():
    """Test that configuration is correct"""
    print("Testing Configuration...")
    
    # Check API key
    assert OPENROUTER_API_KEY, "❌ API key not configured"
    print(f"✓ API Key configured: {OPENROUTER_API_KEY[:20]}...")
    
    # Check PDF directory
    pdf_dir = Path(PDF_DIRECTORY)
    assert pdf_dir.exists(), f"❌ PDF directory not found: {PDF_DIRECTORY}"
    print(f"✓ PDF Directory exists: {PDF_DIRECTORY}")
    
    # Check PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))
    assert len(pdf_files) > 0, "❌ No PDF files found"
    print(f"✓ Found {len(pdf_files)} PDF files")
    
    # Check document text loaded
    assert len(advisor.document_text) > 1000, "❌ Documents not loaded properly"
    print(f"✓ Documents loaded: {len(advisor.document_text)} characters")
    
    print("\n✅ Configuration test passed!\n")

def test_simple_query():
    """Test a simple query to the advisor"""
    print("Testing Simple Query...")
    
    chat_history = [
        {
            "sender": "user",
            "text": "Hello, what programs are available?",
            "role": "user"
        }
    ]
    
    response = advisor.get_advice(chat_history)
    
    # Check response structure
    assert "chatResponse" in response, "❌ Missing chatResponse"
    assert "careerPlan" in response, "❌ Missing careerPlan"
    print(f"✓ Response structure valid")
    
    # Check chatResponse
    assert len(response["chatResponse"]) > 0, "❌ Empty chatResponse"
    print(f"✓ Chat response received: {len(response['chatResponse'])} characters")
    
    # Check careerPlan structure
    career_plan = response["careerPlan"]
    assert "programName" in career_plan, "❌ Missing programName"
    assert "progress" in career_plan, "❌ Missing progress"
    assert "requiredClasses" in career_plan, "❌ Missing requiredClasses"
    assert "transferUniversities" in career_plan, "❌ Missing transferUniversities"
    print(f"✓ Career plan structure valid")
    
    print(f"\n📝 Sample Response:")
    print(f"   {response['chatResponse'][:200]}...")
    
    print("\n✅ Simple query test passed!\n")

def test_program_specific_query():
    """Test a program-specific query"""
    print("Testing Program-Specific Query...")
    
    chat_history = [
        {
            "sender": "user",
            "text": "I'm interested in Applied Artificial Intelligence",
            "role": "user"
        }
    ]
    
    response = advisor.get_advice(chat_history)
    
    # Check that we got a meaningful response
    assert len(response["chatResponse"]) > 100, "❌ Response too short"
    print(f"✓ Received detailed response")
    
    # Check if response mentions AI or relevant terms
    response_text = response["chatResponse"].lower()
    has_relevant_content = any(term in response_text for term in [
        "artificial intelligence", "ai", "program", "course"
    ])
    assert has_relevant_content, "❌ Response doesn't seem relevant to AI program"
    print(f"✓ Response contains relevant information")
    
    print(f"\n📝 Sample Response:")
    print(f"   {response['chatResponse'][:300]}...")
    
    print("\n✅ Program-specific query test passed!\n")

if __name__ == "__main__":
    print("="*60)
    print("🧪 MDC Academic Advisor Backend Tests")
    print("="*60)
    print()
    
    try:
        test_configuration()
        test_simple_query()
        test_program_specific_query()
        
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nYour backend is ready to use!")
        print("Start the server with: python app.py")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
