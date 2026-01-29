import aiohttp
from typing import Optional
from .base import BaseSkill


class WeatherSkill(BaseSkill):
    """
    Fetches real-time weather data using OpenWeatherMap API.
    Demonstrates: Async HTTP requests, Error handling, Context memory usage.
    """
    name = "weather"
    keywords = ["weather", "hava", "forecast", "derece", "sıcaklık"]
    description = "Provides current weather information for any city."

    async def execute(self, args: str) -> str:
        if "help" in args:
            return "💡 **Usage:** `weather London`, `hava durumu Ankara`"

        try:
            # 1. Smart City Extraction
            parts = args.strip().split()
            # Remove trigger words to find the city name more accurately
            clean_parts = [p for p in parts if p.lower() not in self.keywords]
            city = clean_parts[-1] if clean_parts else None

            # 2. Fallback to Memory
            if not city and self.data_manager:
                city = self.data_manager.context_memory.get("last_weather_city")

            if not city:
                return "🌍 Please specify a city (e.g., 'weather London')."

            # 3. Secure API Key Access
            api_key = self.data_manager.get_api_key("weather") if self.data_manager else None
            if not api_key:
                return "⚠️ **Config Error:** Weather API Key is missing in `.env`."

            # 4. Async Request
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=en"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 404:
                        return f"❌ City '{city}' not found."
                    data = await resp.json()

            if data.get("cod") != 200:
                return f"⚠️ API Error: {data.get('message', 'Unknown error')}"

            # 5. Extract Data
            temp = data['main']['temp']
            desc = data['weather'][0]['description'].capitalize()
            humidity = data['main']['humidity']
            feels_like = data['main']['feels_like']

            # 6. Update Context
            if self.data_manager:
                self.data_manager.context_memory["last_weather_city"] = city
                self.data_manager.save_context()

            return f"""
            ### 🌤️ Weather in {city.capitalize()}
            - **Status:** {desc}
            - **Temp:** {temp}°C (Feels like {feels_like}°C)
            - **Humidity:** %{humidity}
            """
        except Exception as e:
            return f"❌ WeatherSkill System Error: {str(e)}"