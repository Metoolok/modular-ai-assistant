import aiohttp
from .base import BaseSkill


class NewsSkill(BaseSkill):
    """
    Aggregates top headlines based on topics.
    Demonstrates: API Integration, JSON Parsing.
    """
    name = "news"
    keywords = ["news", "haber", "gündem", "headline"]
    description = "Fetches latest news headlines."

    async def execute(self, args: str) -> str:
        api_key = self.data_manager.get_api_key("news") if self.data_manager else None
        if not api_key: return "⚠️ **Config Error:** News API Key is missing."

        # Smart Topic Extraction
        parts = args.split()
        # Filter out keywords to find the actual topic
        topic_parts = [p for p in parts if p.lower() not in self.keywords]
        topic = topic_parts[0] if topic_parts else "technology"

        url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={api_key}&language=en&sortBy=publishedAt"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status != 200:
                        return "⚠️ Failed to fetch news. Check API limits."
                    data = await resp.json()

            articles = data.get("articles", [])[:5]
            if not articles: return f"ℹ️ No recent news found for topic: '{topic}'."

            formatted = []
            for i, a in enumerate(articles):
                source = a.get('source', {}).get('name', 'Unknown')
                date = a.get('publishedAt', '')[:10]
                formatted.append(f"{i + 1}. **[{a['title']}]({a['url']})**\n   _{source} • {date}_")

            return f"### 📰 Headlines: {topic.capitalize()}\n" + "\n".join(formatted)
        except Exception as e:
            return f"❌ News Error: {str(e)}"