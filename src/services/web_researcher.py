import os
import json
from pathlib import Path
from tavily import TavilyClient

class WebResearcher:
    """Service for conducting deep research using the Tavily Python Library."""

    def __init__(self, output_dir: str = "research/web"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = None
        if self.api_key:
            self.client = TavilyClient(api_key=self.api_key)

    def conduct_research(self, topic: str, model: str = "pro") -> dict:
        """
        Conduct deep research on a topic and return the report.
        Note: The library 'search' with search_depth='advanced' is similar to CLI 'research'.
        """
        if not self.client:
            return {
                "success": False,
                "error": "TAVILY_API_KEY not found in environment variables."
            }

        try:
            # Generate a safe filename
            safe_topic = "".join([c if c.isalnum() else "_" for c in topic[:50]])
            output_file = self.output_dir / f"research_{safe_topic}.md"
            
            # Use tavily-python for research
            # search_depth="advanced" corresponds to deep research
            search_depth = "advanced" if model == "pro" else "basic"
            
            response = self.client.search(query=topic, search_depth=search_depth, include_answer=True)
            
            # Format the response into a markdown report
            report = f"# Research Report: {topic}\n\n"
            report += f"## Summary\n{response.get('answer', 'No summary available.')}\n\n"
            report += "## Sources\n"
            for result in response.get('results', []):
                report += f"- [{result['title']}]({result['url']})\n"
                report += f"  > {result['content']}\n\n"
            
            output_file.write_text(report, encoding="utf-8")
            
            return {
                "success": True,
                "topic": topic,
                "report_path": str(output_file),
                "content": report
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    # Simple test execution
    researcher = WebResearcher(output_dir="tests/research")
    print("Testing WebResearcher (Library version)...")
    res = researcher.conduct_research("latest trends in agentic software delivery 2026", model="mini")
    if res["success"]:
        print(f"Success! Report saved to {res['report_path']}")
    else:
        print(f"Failed: {res['error']}")
