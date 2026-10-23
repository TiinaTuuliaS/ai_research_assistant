"""Expose limited compositions, including archived ones, without rewriting reports."""
def report_status(result, status="completed"):
    if status == "limited" or (status == "completed" and any(marker in (result or "")
            for marker in ("**Rajattu raportti:**", "**Limited report:**"))):
        return "limited"
    return status
