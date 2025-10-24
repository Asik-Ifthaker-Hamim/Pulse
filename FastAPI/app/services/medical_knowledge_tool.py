from app.core.config import settings
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.schemas.knowledge_schema import MedicalKnowledgeOutput
from typing import Optional, List, Dict, Any 

def get_medical_knowledge(question: str) -> MedicalKnowledgeOutput:
    """
    Performs a Tavily search and synthesizes results using ChatOpenAI,
    returning a structured Pydantic output. Initializes tools per request.

    Args:
        question: The medical question to research.

    Returns:
        A MedicalKnowledgeOutput object containing the results or error info.
    """
    search = None
    llm = None
    search_results_list: Optional[List[Dict[str, Any]]] = None
    
    try:
        search = TavilySearchResults(
            max_results=5,
            tavily_api_key=settings.TAVILY_API_KEY
        )
    except Exception as e:
        error_msg = f"Error initializing Search tool: {e}"
        print(error_msg)
        return MedicalKnowledgeOutput(
            status="error_initialization", original_question=question, error_message=error_msg
        )

    try:
        llm = ChatOpenAI(
            model="gpt-4o", openai_api_key=settings.OPENAI_API_KEY, temperature=0
        )
    except Exception as e:
        error_msg = f"Error initializing Language Model: {e}"
        print(error_msg)
        return MedicalKnowledgeOutput(
            status="error_initialization", original_question=question, error_message=error_msg
        )

    # Perform Search
    try:
        # Store the list directly
        search_results_list = search.invoke({"query": question})
    except Exception as e:
        error_msg = f"Error during search: {e}"
        print(f"Error during Tavily search for '{question}': {e}")
        return MedicalKnowledgeOutput(
            status="error_search", original_question=question, error_message=error_msg
        )

    search_results_prompt_str = "\n\n".join([f"Title: {res.get('title', 'N/A')}\nURL: {res.get('url', 'N/A')}\nContent: {res.get('content', 'N/A')}" for res in search_results_list])


    prompt_template = f"""
You are a clinical assistant AI specialized in synthesizing medical information.
Your task is to review the provided search results and create a concise, accurate summary tailored for a busy doctor.
Focus on the key findings, evidence, and conclusions relevant to the original query.
If citations or source references are available in the results, please include them. Maintain medical accuracy.

Original Query: {question}

Search Results:
{search_results_prompt_str} # Use the string version for the prompt

Synthesized Summary for Doctor:
"""

    messages = [
        HumanMessage(content=prompt_template)
    ]

    # Perform Synthesis
    try:
        response = llm.invoke(messages)
        summary_text = response.content.strip()

        return MedicalKnowledgeOutput(
            status="success",
            original_question=question,
            summary=summary_text,
            raw_search_results=search_results_list 
        )
    except Exception as e:
        error_msg = f"Error during synthesis: {e}"
        print(f"Error during OpenAI synthesis for query '{question}': {e}")
        return MedicalKnowledgeOutput(
            status="error_synthesis",
            original_question=question,
            raw_search_results=search_results_list, 
            error_message=error_msg
        )