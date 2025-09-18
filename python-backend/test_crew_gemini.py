#!/usr/bin/env python3
"""Test script to directly test CrewAI with Gemini configuration."""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

# Load environment variables
load_dotenv()

def get_gemini_llm():
    """Get Gemini LLM instance for testing."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    print(f"Using Google API Key: {api_key[:10]}...")
    
    # Use LiteLLM format for Google AI Studio (gemini/ prefix)
    llm = LLM(
        model="gemini/gemini-2.5-flash",
        api_key=api_key
    )
    
    print(f"Created LLM: {llm}")
    print(f"LLM model: {getattr(llm, 'model', 'No model attribute')}")
    
    return llm

def test_simple_crew():
    """Test a simple CrewAI crew with Gemini."""
    try:
        llm = get_gemini_llm()
        
        # Create a simple agent
        agent = Agent(
            role="Test Agent",
            goal="You are a test agent that provides simple responses.",
            backstory="You are helpful and concise.",
            llm=llm,
            verbose=True
        )
        
        # Create a simple task
        task = Task(
            description="Say hello and confirm you are using Gemini 2.5 Flash model.",
            expected_output="A simple greeting confirming the model being used.",
            agent=agent,
            llm=llm
        )
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            llm=llm,
            verbose=True
        )
        
        print("Starting crew execution...")
        result = crew.kickoff()
        print(f"Result: {result}")
        
        return str(result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"

if __name__ == "__main__":
    test_simple_crew()