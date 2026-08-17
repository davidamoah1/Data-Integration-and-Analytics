"""Test presentation generation end-to-end."""
import requests
import json
import csv
import io
import zipfile

# Login
r = requests.post('http://localhost:8001/api/auth/login', json={
    'email': 'mysql_e2e_a@test.dataflow.io',
    'password': 'TestPass123!'
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create a small CSV dataset
csv_data = io.StringIO()
writer = csv.writer(csv_data)
writer.writerow(['product', 'revenue', 'quantity', 'region', 'date'])
for i in range(20):
    writer.writerow([
        f'Product_{i%5}',
        100 + i * 10,
        5 + i,
        ['North', 'South', 'East', 'West'][i % 4],
        f'2024-{(i%12)+1:02d}-01'
    ])
csv_bytes = csv_data.getvalue().encode()

# Upload via dataset-workflow
files = {'file': ('test_sales.csv', csv_bytes, 'text/csv')}
r2 = requests.post('http://localhost:8001/dataset-workflow/run',
                    headers=headers, files=files, timeout=120)
print(f'Workflow status: {r2.status_code}')

if r2.status_code != 200:
    print(f'Error: {r2.text[:300]}')
    exit(1)

raw_data = r2.json()
print(f'Response keys: {list(raw_data.keys())}')
# Handle wrapped response
if 'data' in raw_data and raw_data.get('success'):
    data = raw_data['data']
else:
    data = raw_data
print(f'Data keys: {list(data.keys()) if isinstance(data, dict) else type(data)}')
print(f'Data preview: {json.dumps(data, default=str)[:500]}')
wf_id = data.get('workflow_id') if isinstance(data, dict) else None
print(f'Workflow ID: {wf_id}')
stages = data.get('stages', {}) if isinstance(data, dict) else {}
print(f'Stages: {len(stages)}')
if isinstance(stages, dict):
    for name, s in list(stages.items())[:5]:
        print(f'  {name}: {s.get("status")}')
else:
    for s in stages[:5]:
        print(f'  {s.get("stage")}: {s.get("status")}')

# Generate presentation
r3 = requests.post(
    f'http://localhost:8001/dataset-workflow/{wf_id}/presentation',
    headers={**headers, 'Content-Type': 'application/json'},
    json={'template': 'executive', 'title': 'Sales Analysis'},
    timeout=60,
)
print(f'Presentation status: {r3.status_code}')
print(f'Content-Type: {r3.headers.get("content-type")}')
print(f'Content-Length: {len(r3.content)}')

if r3.status_code == 200:
    pptx_data = io.BytesIO(r3.content)
    if zipfile.is_zipfile(pptx_data):
        with zipfile.ZipFile(pptx_data) as z:
            files_in_pptx = z.namelist()
            slides = [f for f in files_in_pptx if f.startswith('ppt/slides/slide')]
            print(f'Valid PPTX: YES')
            print(f'Slides: {len(slides)}')
            print(f'Files in archive: {len(files_in_pptx)}')
            # Check for content types
            has_content_types = '[Content_Types].xml' in files_in_pptx
            has_ppt_dir = any(f.startswith('ppt/') for f in files_in_pptx)
            print(f'Has [Content_Types].xml: {has_content_types}')
            print(f'Has ppt/ directory: {has_ppt_dir}')
    else:
        print('Valid PPTX: NO - not a valid ZIP')
else:
    print(f'Error: {r3.text[:400]}')
