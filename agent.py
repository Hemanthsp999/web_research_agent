import requests
import re
from bs4 import BeautifulSoup
from langchain_core.tools import Tool
from dotenv import load_dotenv
import os
import json
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

load_dotenv()

# load api keys
my_api = os.getenv("SERPER_API_KEY")

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


# returns list of urls from the search engines
def url_extract(query: str) -> str:
    """
    Extracts relevant URLs based on a search query.
    Args:
        query: The search query string
    Returns:
        A JSON string containing a list of URLs
    """
    search = GoogleSerperAPIWrapper()
    results = search.results(query)  # returns structured results (dict)

    urls = []
    if 'organic' in results:
        for result in results['organic']:
            url = result.get("link")
            if url:
                urls.append(url)

    # Return as JSON string for consistent formatting
    return json.dumps(urls)


# returns the content from the list of urls
def text_extract(url_list_str: str) -> str:
    """
    Extracts text from given URL links.
    Args:
        url_list_str: A JSON string containing a list of URLs
    Returns:
        A JSON string containing extracted text contents
    """
    # Parse the JSON string to get a list
    try:
        # Try to parse as JSON first
        url_list = json.loads(url_list_str)[:5]  # Only process top 5 results
        if not isinstance(url_list, list):
            url_list = [url_list_str]  # If not a list, make it a list with one item
    except json.JSONDecodeError:
        # If not valid JSON, try to extract URLs from the string
        url_matches = re.findall(r'https?://[^\s,\'"]+', url_list_str)
        if url_matches:
            url_list = url_matches
        else:
            # Fallback to treating the input as a single URL
            url_list = [url_list_str]

    contents = []
    for url in url_list:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = [p.get_text() for p in soup.find_all('p')]
            contents.append("\n".join(paragraphs[:10]))
        except Exception as e:
            contents.append(f"Error reading {url}: {e}")

    # Return as JSON string for consistent formatting
    return json.dumps(contents)


# returns contents of the query based on relevance, reliability and usefulness score
def content_analyzer(args: str) -> str:
    """
    Analyzes content for relevance and reliability.
    Args:
        args: A JSON string containing a query and a list of contents
    Returns:
        A string with analysis results
    """
    try:
        # Try to parse as JSON
        data = json.loads(args)
        if isinstance(data, dict) and "query" in data and "contents" in data:
            query = data["query"]
            contents = data["contents"]
        else:
            # If not the expected format, try to extract query and content from the string
            parts = args.split("\n", 1)
            query = parts[0]
            content_str = parts[1] if len(parts) > 1 else ""
            contents = [content_str]
    except json.JSONDecodeError:
        # If not valid JSON, treat the first line as query and the rest as content
        parts = args.split("\n", 1)
        query = parts[0]
        content_str = parts[1] if len(parts) > 1 else ""
        contents = [content_str]

    # If contents is a string (from json.loads), convert it to a list
    if isinstance(contents, str):
        try:
            contents = json.loads(contents)
        except json.JSONDecodeError:
            contents = [contents]

    results = []
    for content in contents:
        prompt = f"""
        You are a helpful research assistant. Analyze the following web content based on the user's query: {query}

        Web content:
        \"\"\"{content}\"\"\"

        1. Is the content relevant to the query? (Yes/No)
        2. How reliable is the source? (High/Medium/Low)
        3. Summarize the main point of the content in 4 lines.
        4. Give it a score out of 10 for usefulness.

        Answer in bullet points.
        """
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content_score = response.content

            score_match = re.search(r'score.*?(\d+)/10', content_score, re.IGNORECASE)
            score = int(score_match.group(1)) if score_match else 0

            if score >= 7:
                results.append(content_score)

        except Exception as e:
            results.append(f"Error analyzing content: {e}")

    return "\n\n".join(results) if results else "No relevant content found."


# returns latest news of the given topic
def news_aggregator(topic: str) -> str:
    """
    Gets recent news articles related to a topic.
    Args:
        topic: The topic to search for news
    Returns:
        A string with news results
    """
    search = GoogleSerperAPIWrapper()
    results = search.results(topic + " latest news")
    news_items = []

    if 'organic' in results:
        for result in results['organic'][:5]:  # limit to top 5 results
            title = result.get("title", "No Title")
            snippet = result.get("snippet", "No Snippet")
            link = result.get("link", "#")
            formatted = f"🔹 {title}\n{snippet}\n🔗 {link}"
            news_items.append(formatted)

    return "\n\n".join(news_items) if news_items else "No recent news found."


class Research_Agent:
    def __init__(self):
        # Initialize memory
        self.memory = ConversationBufferMemory(memory_key="research_history", return_messages=True)

        # Create tools with safer input handling
        tools = [
            Tool.from_function(
                func=url_extract,
                name="URL_Extractor",
                description="Extracts relevant URLs based on a search query. Input should be a search query string."
            ),
            Tool.from_function(
                func=text_extract,
                name="Text_Extractor",
                description="Extracts text content from URLs. Input should be a JSON string containing a list of URLs or a single URL string."
            ),
            Tool.from_function(
                func=content_analyzer,
                name="Content_Analyzer",
                description="Analyzes content for relevance and reliability. Input should be a JSON string containing a 'query' field and a 'contents' field with a list of text contents."
            ),
            Tool.from_function(
                func=news_aggregator,
                name="News_Aggregator",
                description="Gets recent news articles related to a topic. Input should be a topic string."
            )
        ]

        # Create the ReAct prompt template with required variables
        react_template = """Answer the following questions as best you can. You have access to the following tools:

        {tools}


        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question 
            should be based on:
                1. Is the content relevant to the query? (Yes/No)
                2. How reliable is the source? (High/Medium/Low)
                3. Summarize the main point of the content in 4 lines.
                4. Give it a score out of 10 for usefulness.
                5. Provide a list of answers from different websites.
        Answer in bullet points.

        Also give news articles with links for {input} in a clean, readable text format rather than JSON.

        Begin!

        {research_history}

        Question: {input}
        {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(react_template)

        # Create the ReAct agent
        agent = create_react_agent(llm, tools, prompt)

        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=2000
        )

    def run(self, query):
        """Run the research agent on a query"""
        try:

            if "latest news" in query.lower() or "recent news" in query.lower():
                news = news_aggregator(query)
                return news, [news]

            response = self.agent_executor.invoke({"input": query})
            # Return the output and an empty list for news (for compatibility)
            return response["output"], []
        except Exception as e:
            return f"Error running research agent: {str(e)}"

    def get_memory(self):
        """Return the conversation memory"""
        return self.memory.load_memory_variables({})["research_history"]
