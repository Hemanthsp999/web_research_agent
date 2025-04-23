import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from dotenv import load_dotenv
import os
from langchain.agents import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import GoogleSerperAPIWrapper

load_dotenv()

my_api = os.getenv("SERPER_API_KEY")


class Research_Agent():
    @tool
    def url_extract_agent(query: str) -> list[str]:
        """
        Tool to scrape the web URLs for better research.
        """
        search = GoogleSerperAPIWrapper()
        results = search.results(query)  # returns structured results (dict)

        urls = []
        if 'organic' in results:
            for result in results['organic']:
                url = result.get("link")
                if url:
                    urls.append(url)

        print("Extracted URLs:")
        for u in urls:
            print(u)

        return urls

    @tool
    def text_extract_agent(url_list: list[str]) -> list[str]:
        """
        Tool to extract text from the given URL links.
        Args: {url_list}

        Return:
            - Text from specific paragraph
            - Highlight the text
        """
        contents = []
        for url in url_list:
            print(f"URL: {url}")
            try:
                response = requests.get(url, timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')
                paragraphs = [p.get_text() for p in soup.find_all('p')]
                contents.append("\n".join(paragraphs[:10]))
            except Exception as e:
                print(f"Error reading {url}: {e}")
                contents.append("")

        return contents

    @tool
    def content_analyzer_agent(query: str, contents: list[str]) -> list[str]:
        """
        Tool to check the relevance and reliability of extracted content.
        Returns a list of relevance and reliability scores or remarks."
        """


# Example usage
agent = Research_Agent()
res = agent.url_extract_agent("what is AI")
get_text = agent.text_extract_agent({"url_list": res})
print(get_text)
