class SEOService:
    """Business-logic entry point for future SEO modules."""

    def status(self):
        return {
            "crawler": "not_connected",
            "search_console": "not_connected",
            "analytics": "not_connected",
            "keywords": "not_connected",
            "competitors": "not_connected",
        }
