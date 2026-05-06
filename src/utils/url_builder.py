import urllib.parse
from typing import Dict, Any

def build_url(platform_name: str, config: Dict[str, Any], query: str) -> str:
    """
    Builds the target URL for a given platform and search query based on config.yaml.
    """
    platforms_config = config.get("platforms", {})
    platform_config = platforms_config.get(platform_name, {})
    
    base_url = platform_config.get("base_url")
    if not base_url:
        return ""
        
    encoded_query = urllib.parse.quote_plus(query)
    
    # Myntra expects a slug as well
    if platform_name == "myntra":
        slug = query.lower().replace(" ", "-")
        return base_url.format(slug=slug, encoded=encoded_query)
        
    # Other platforms just need the query formatted
    return base_url.format(query=encoded_query)
