"""Optional GA4 integration for GEORUSH.

GA4 remains disabled until credentials and a property ID are configured.
Preferred future setup: a Google service account with Analytics Viewer access
and GOOGLE_APPLICATION_CREDENTIALS pointing to its JSON key, plus GA4_PROPERTY_ID.
"""
import os
from datetime import date, timedelta


def config_status():
    property_id = os.getenv("GA4_PROPERTY_ID", "").strip()
    credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    return {
        "configured": bool(property_id and credentials),
        "property_id": property_id,
        "credentials_configured": bool(credentials),
        "credentials_path_set": bool(credentials),
        "source": "GA4 Data API" if property_id and credentials else "Not connected",
    }


def run_report(start_date="28daysAgo", end_date="today"):
    status = config_status()
    if not status["configured"]:
        return {
            "success": False,
            "connected": False,
            "error": "GA4 is not configured. Set GA4_PROPERTY_ID and GOOGLE_APPLICATION_CREDENTIALS, then grant the service account Viewer access to the GA4 property.",
            **status,
        }
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
    except ImportError:
        return {
            "success": False,
            "connected": False,
            "error": "Google Analytics Data API client is not installed. Install google-analytics-data when GA4 integration is enabled.",
            **status,
        }

    try:
        client = BetaAnalyticsDataClient()
        request = RunReportRequest(
            property=f"properties/{status['property_id']}",
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="engagementRate"),
                Metric(name="eventCount"),
            ],
        )
        response = client.run_report(request)
        rows = []
        for row in response.rows:
            rows.append({
                "date": row.dimension_values[0].value,
                "active_users": int(row.metric_values[0].value or 0),
                "sessions": int(row.metric_values[1].value or 0),
                "engagement_rate": float(row.metric_values[2].value or 0),
                "event_count": int(row.metric_values[3].value or 0),
            })
        return {"success": True, "connected": True, "property_id": status["property_id"], "date_range": {"start": start_date, "end": end_date}, "rows": rows, **status}
    except Exception as exc:
        return {"success": False, "connected": False, "error": str(exc), **status}
