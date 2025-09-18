"""
CrewAI Agents for the Useless Chatbot AI Backend
This module defines specialized agents for research, analysis, and writing tasks.
"""

import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_llm():
    """Get the LLM instance for CrewAI agents."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment")
    
    return ChatOpenAI(
        model_name="openrouter/sonoma-sky-alpha",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=1024
    )


# Define the Research Agent (simplified without tools)
research_agent = Agent(
    role='Research Specialist',
    goal='Find accurate, up-to-date information to answer user queries',
    backstory="""You are an expert research specialist with years of experience
    in finding reliable information. You excel at analyzing questions and
    providing comprehensive research-based responses using your knowledge.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm()
)

# Define the Analysis Agent
analysis_agent = Agent(
    role='Information Analyst',
    goal='Analyze and validate information to ensure accuracy and relevance',
    backstory="""You are a meticulous information analyst with expertise in 
    fact-checking and data validation. You have a keen eye for inconsistencies,
    can identify reliable sources, and excel at synthesizing information from
    multiple sources. Your role is to verify and enhance research findings.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm()
)

# Define the Writer Agent
writer_agent = Agent(
    role='Content Writer',
    goal='Create clear, engaging, and well-structured responses',
    backstory="""You are a skilled content writer specializing in creating
    engaging and informative content. You excel at taking complex information
    and presenting it in a clear, accessible way. Your writing is accurate,
    well-structured, and tailored to the user's needs.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm()
)


def process_user_query(message: str) -> str:
    """Process user query using CrewAI agents."""
    try:
        # Define tasks for each agent
        research_task = Task(
            description=f"""Research and gather information about: {message}
            Provide comprehensive information that directly addresses the user's question.
            Include relevant facts, details, and context.""",
            agent=research_agent,
            expected_output="Detailed research findings with relevant information"
        )
        
        analysis_task = Task(
            description="""Analyze the research findings for accuracy and relevance.
            Verify information quality and identify key insights.
            Ensure the information directly answers the user's question.""",
            agent=analysis_agent,
            expected_output="Analyzed and validated information with key insights",
            context=[research_task]
        )
        
        writing_task = Task(
            description="""Create a clear, well-structured response based on the
            research and analysis. Make the information accessible and engaging
            for the user. Ensure the response directly addresses their question.""",
            agent=writer_agent,
            expected_output="Clear, well-structured final response",
            context=[research_task, analysis_task]
        )
        
        # Create and execute the crew
        crew = Crew(
            agents=[research_agent, analysis_agent, writer_agent],
            tasks=[research_task, analysis_task, writing_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the crew and get results
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"Error processing query: {str(e)}"