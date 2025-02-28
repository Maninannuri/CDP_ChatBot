# Browser settings
CHROME_OPTIONS = [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-software-rasterizer"
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

REQUEST_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# Documentation URLs
CDP_URLS = {
    'segment': [
        "https://segment.com/docs/?ref=nav",
        "https://segment.com/docs/connections/sources/",
        "https://segment.com/docs/connections/destinations/",
        "https://segment.com/docs/guides/"
    ],
    'mparticle': [
        "https://docs.mparticle.com/",
        "https://docs.mparticle.com/guides/",
        "https://docs.mparticle.com/developers/",
        "https://docs.mparticle.com/integrations/"
    ],
    'lytics': [
        "https://docs.lytics.com/",
        "https://docs.lytics.com/docs/",
        "https://docs.lytics.com/reference/"
    ],
    'zeotap': [
        "https://docs.zeotap.com/home/en-us/",
        "https://docs.zeotap.com/docs/",
        "https://docs.zeotap.com/api/"
    ]
}

# Scraping settings
REQUEST_DELAY = 10
MAX_RETRIES = 3
WAIT_TIMEOUT = 10
