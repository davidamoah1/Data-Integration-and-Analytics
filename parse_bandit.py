import json
import os
import sys
import tempfile

report_path = (
    os.getenv("BANDIT_REPORT_PATH")
    or (sys.argv[1] if len(sys.argv) > 1 else None)
    or os.path.join(tempfile.gettempdir(), "bandit_report.json")
)

with open(report_path) as f:
    d = json.load(f)
totals = d.get("metrics", {}).get("_totals", {})
print(f"HIGH: {totals.get('SEVERITY.HIGH', 0)}")
print(f"MEDIUM: {totals.get('SEVERITY.MEDIUM', 0)}")
print(f"LOW: {totals.get('SEVERITY.LOW', 0)}")
# Show any HIGH issues
for r in d.get("results", []):
    if r.get("issue_severity") == "HIGH":
        print(f"  HIGH: {r.get('test_id')} in {r.get('filename')}:{r.get('line_number')}")
