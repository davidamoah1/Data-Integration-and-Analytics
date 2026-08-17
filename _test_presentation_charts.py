"""Test presentation generation with real charts in PPTX."""

import csv
import io
import os
import sys
import zipfile

import requests

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Login
r = requests.post(
    "http://localhost:8001/api/auth/login",
    json={"email": "mysql_e2e_a@test.dataflow.io", "password": "TestPass123!"},
)
token = r.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create a realistic dataset with multiple chart types
csv_data = io.StringIO()
writer = csv.writer(csv_data)
writer.writerow(["product", "revenue", "quantity", "region", "date"])
for i in range(50):
    writer.writerow(
        [
            f"Product_{i%5}",
            100 + i * 10,
            5 + i,
            ["North", "South", "East", "West"][i % 4],
            f"2024-{(i%12)+1:02d}-15",
        ]
    )
csv_bytes = csv_data.getvalue().encode()

# Upload via dataset-workflow
files = {"file": ("sales_data.csv", csv_bytes, "text/csv")}
r2 = requests.post(
    "http://localhost:8001/dataset-workflow/run", headers=headers, files=files, timeout=120
)
print(f"Workflow status: {r2.status_code}")

if r2.status_code != 200:
    print(f"Error: {r2.text[:300]}")
    sys.exit(1)

raw_data = r2.json()
data = raw_data.get("data", raw_data)
wf_id = data.get("workflow_id")
print(f"Workflow ID: {wf_id}")

# Check dashboard charts
dashboard = data.get("stages", {}).get("dashboard_ready", {}).get("result", {})
charts = dashboard.get("recommended_charts", [])
print(f"Recommended charts: {len(charts)}")
for c in charts:
    print(f"  {c.get('type')}: {c.get('title')}")

# Generate presentation
r3 = requests.post(
    f"http://localhost:8001/dataset-workflow/{wf_id}/presentation",
    headers={**headers, "Content-Type": "application/json"},
    json={"template": "executive", "title": "Sales Analysis with Charts"},
    timeout=60,
)
print(f"\nPresentation status: {r3.status_code}")
print(f'Content-Type: {r3.headers.get("content-type")}')
print(f"Content-Length: {len(r3.content)}")

if r3.status_code != 200:
    print(f"Error: {r3.text[:400]}")
    sys.exit(1)

# Validate PPTX
pptx_data = io.BytesIO(r3.content)
if not zipfile.is_zipfile(pptx_data):
    print("FAIL: Not a valid ZIP/PPTX")
    sys.exit(1)

with zipfile.ZipFile(io.BytesIO(r3.content)) as z:
    files_in_pptx = z.namelist()
    slides = sorted([f for f in files_in_pptx if f.startswith("ppt/slides/slide")])
    charts_in_pptx = sorted([f for f in files_in_pptx if f.startswith("ppt/charts/")])
    embeddings = sorted([f for f in files_in_pptx if f.startswith("ppt/embeddings/")])

    print("\n=== PPTX Validation ===")
    print("Valid ZIP: YES")
    print(f"Total files: {len(files_in_pptx)}")
    print(f"Slides: {len(slides)}")
    print(f"Charts: {len(charts_in_pptx)}")
    print(f"Embeddings: {len(embeddings)}")
    print(f'Has [Content_Types].xml: {"[Content_Types].xml" in files_in_pptx}')
    print(f'Has ppt/ dir: {any(f.startswith("ppt/") for f in files_in_pptx)}')

    # List chart files
    for c in charts_in_pptx:
        print(f"  Chart file: {c}")

    # Check slide contents for chart references
    chart_slides = 0
    for slide_file in slides:
        content = z.read(slide_file).decode("utf-8", errors="replace")
        if "<c:chart" in content or "chart" in content.lower():
            chart_slides += 1
    print(f"Slides with chart references: {chart_slides}")

    # Check for placeholder/lorem ipsum content
    all_text = ""
    for slide_file in slides:
        content = z.read(slide_file).decode("utf-8", errors="replace")
        all_text += content
    bad_words = ["lorem ipsum", "TODO", "FIXME", "placeholder"]
    found_bad = [w for w in bad_words if w.lower() in all_text.lower()]
    print(f'Placeholder content found: {found_bad if found_bad else "NONE"}')

    # Check for real data values (Product_0, Product_1, etc.)
    has_real_data = "Product_" in all_text or "Revenue" in all_text or "revenue" in all_text
    print(f'Real data in slides: {"YES" if has_real_data else "NO"}')

    # File size
    file_size = len(r3.content)
    print(f"\nFile size: {file_size} bytes")
    print("Previous working size: 42,773 bytes")
    print(f'Size increased (charts added): {"YES" if file_size > 45000 else "NO"}')

    # Final verdict
    print("\n=== FINAL VERDICT ===")
    print(f'PPTX Generated: {"PASS" if file_size > 0 else "FAIL"}')
    print("PPTX Valid: PASS")
    print(f"Slides: {len(slides)}")
    print(f'Charts rendered: {"PASS" if len(charts_in_pptx) > 0 else "FAIL - no charts in PPTX"}')
    print(f'Real data: {"PASS" if has_real_data else "FAIL"}')
    print(f'No placeholders: {"PASS" if not found_bad else "FAIL"}')

# Save the PPTX for manual inspection
output_path = os.path.join(os.path.dirname(__file__), "_test_output.pptx")
with open(output_path, "wb") as f:
    f.write(r3.content)
print(f"\nPPTX saved to: {output_path}")
