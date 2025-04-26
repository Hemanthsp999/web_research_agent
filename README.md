# Web Research Agent Assignment

A Streamlit-based intelligent research assistant that leverages LangChain, Google Search, and LLMs to gather, extract, and analyze web content.
The agent performs a multi-step process: extracting URLs, scraping content, analyzing relevance and reliability, and optionally fetching the latest news.
Designed for users who want quick, summarized, and trustworthy insights from the web in a chat-like interface.

# How Agent works ?

![Agent Work flow](flowchart.png)

## How Agent makes descision ?

    1. Start
    The user provides a research query through the Streamlit interface.

    2. Agent Initialization
    The Research Agent receives the query and begins processing. It decides the next action based on the nature of the query.

    3. Tool Selection
    The agent reasons whether it needs to use any tools to complete the task:

        If the query asks for latest news, it directly triggers the Latest News tool.

        Otherwise, it continues to extract and analyze information step-by-step.

    4. URL_Extractor
    The agent uses the URL_Extractor tool to search the web (via Google Serper API) and collect relevant URLs related to the query.

    5. Text_Extractor
    Once URLs are obtained, it uses Text_Extractor to scrape content from the web pages. It retrieves the first few paragraphs to get a readable summary.

    6. Content_Analyzer
    After getting the text, the agent uses Content_Analyzer to:

        Check if the content is relevant to the query.

        Assess the reliability (High/Medium/Low) of the source.

        Provide a summary and give a usefulness score out of 10.

    7. News Aggregator
    Then Agent searches for latest news of the particular topic.

    8. Decision Point
    After analysis, the agent determines whether it has enough useful information to answer the user or if it needs to continue using more tools.

    9. Response
    The agent formats and returns a final summarized answer to the user.

    10. End
    The session is stored in the research history for future reference or export.

## How you designed the prompts/instructions for the AI ?

    The prompts were designed using the ReAct (Reasoning + Acting) framework, which allows the AI model to:

    Think through the problem step-by-step

    Call predefined tools (i.e URL extractors, text scrapers)

    Receive observations

    Refine its approach iteratively

    Conclude with a well-structured final answer

    This approach enables the model to operate like a chain-of-thought researcher while delegating specific actions to external tools.

## How Agent handles problems ?

    - If a website is unreachable:

        Catches the error and logs it without crashing the app.

        Continues processing other available links.

    - If search results are weak:

        Returns "No relevant content found" if no good URLs or content is available.

    - If information from sources conflicts:

        Each content is scored independently.

        Only highly relevant and useful content is included in the final output.

    - If the API (like Gemini) fails:

        Retries the request a few times.

        Returns an error message if still unsuccessful, without breaking the session.

    - Memory and session management:

        Uses a lightweight memory buffer to keep context without overloading.

# How to setup ?

1. Clone the Project repo.

```bash
git clone <project_repo_link.git>
```

2. Open the Project folder.

```bash
cd "project_repo_name"
```

3. Create and Activate Environment

```bash
python3 -m venv env

source env/bin/activate
```

4. Install the Dependencies.

```bash
pip install -r requirements.txt
```

5. Run the project.

```bash
python main.py
```
