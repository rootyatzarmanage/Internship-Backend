class UserAgentParser:
    @staticmethod
    def get_operating_system(
        user_agent: str
    )-> str:
        if "Windows" in user_agent:
            return "Windows"
        if "Linux" in user_agent:
            return "Linux"
        if "Android" in user_agent:
            return "Android"
        if "iPhone" in user_agent:
            return "iOS"
        if "iPad" in user_agent:
            return "iPadOS"
        if "Mac OS X" in user_agent:
            return "macOS"
        return "Unknown"
    
    @staticmethod
    def get_browser(user_agent: str) -> str:
        if not user_agent:
            return "Unknown"
        if any(bot in user_agent.lower() for bot in ["googlebot", "bingbot", "yandexbot", "baiduspider"]):
            return "Bot/Crawler"
        if "Brave/" in user_agent:
            return "Brave"
        if "Vivaldi/" in user_agent:
            return "Vivaldi"
        if "OPR/" in user_agent or "Opera/" in user_agent:
            return "Opera"
        if "Edg/" in user_agent or "Edge/" in user_agent:
            return "Edge"
        if "UCBrowser/" in user_agent:
            return "UC Browser"
        if "SamsungBrowser/" in user_agent:
            return "Samsung Internet"
        if "DuckDuckBrowser/" in user_agent:
            return "DuckDuckGo"
        if "wv" in user_agent.lower() and "Chromium" in user_agent:
            return "Android WebView"
        if "Chrome/" in user_agent:
            return "Chrome"
        if "Firefox/" in user_agent or "Fxios/" in user_agent:
            return "Firefox"
        if "Safari/" in user_agent and "Chrome/" not in user_agent:
            return "Safari"
        if "MSIE " in user_agent or "Trident/" in user_agent:
            return "Internet Explorer"
        return "Unknown"
    @staticmethod
    def get_device_type(user_agent: str) -> str:
        user_agent_lower = user_agent.lower()
        if "ipad" in user_agent_lower or "tablet" in user_agent_lower:
            return "Tablet"
        if "mobile" in user_agent_lower or "android" in user_agent_lower:
            return "Mobile"
        return "Desktop"
