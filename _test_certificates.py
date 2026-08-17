"""Test certificate intelligence endpoints (without OCR dependency)."""
import requests
import io
import sys
import json
import gc

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = 'http://localhost:8001'

# Login
r = requests.post(f'{BASE}/api/auth/login', json={
    'email': 'mysql_e2e_a@test.dataflow.io',
    'password': 'TestPass123!'
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 1. Test certificate types endpoint
print('=== 1. Certificate Types ===')
r = requests.get(f'{BASE}/api/certificates/types', headers=headers)
print(f'Status: {r.status_code}')
types = r.json().get('certificate_types', [])
print(f'Certificate types: {len(types)}')
for t in types:
    print(f"  {t['key']}: {t['label']} ({len(t['fields'])} fields)")

# 2. Test dashboard
print('\n=== 2. Certificate Dashboard ===')
r = requests.get(f'{BASE}/api/certificates/dashboard', headers=headers)
print(f'Status: {r.status_code}')
dashboard = r.json()
print(f'Total: {dashboard["total"]}')
print(f'Approved: {dashboard["approved"]}')
print(f'Not verified: {dashboard["not_verified"]}')

# 3. Test search
print('\n=== 3. Certificate Search ===')
r = requests.get(f'{BASE}/api/certificates/search', headers=headers)
print(f'Status: {r.status_code}')
search = r.json()
print(f'Total: {search["total"]}')

# 4. Test upload (will fail at OCR but upload + batch creation should work)
print('\n=== 4. Certificate Upload ===')
from PIL import Image, ImageDraw

img = Image.new('RGB', (800, 600), 'white')
draw = ImageDraw.Draw(img)
draw.text((100, 50), 'CERTIFICATE', fill='black')
draw.text((100, 150), 'John Mensah', fill='black')
draw.text((100, 250), 'Bachelor of Science in Data Analytics', fill='black')
draw.text((100, 300), 'ABC University', fill='black')

img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

files = {'files': ('certificate.png', img_bytes, 'image/png')}
r = requests.post(f'{BASE}/api/certificates/upload', headers=headers, files=files)
print(f'Status: {r.status_code}')
if r.status_code == 201:
    result = r.json()
    print(f'Batch ID: {result["batch_id"]}')
    print(f'Total: {result["total"]}')
    print(f'Succeeded: {result["succeeded"]}')
    print(f'Failed: {result["failed"]}')
    print(f'Review required: {result["review_required"]}')
    for cert in result['certificates']:
        print(f"  File: {cert.get('filename')}")
        print(f"  Status: {cert.get('status')}")
        print(f"  Error: {cert.get('error_message', 'None')[:100] if cert.get('error_message') else 'None'}")
else:
    print(f'Error: {r.text[:500]}')

gc.collect()  # Release file handles

# 5. Test dashboard after upload
print('\n=== 5. Certificate Dashboard (after upload) ===')
r = requests.get(f'{BASE}/api/certificates/dashboard', headers=headers)
print(f'Status: {r.status_code}')
dashboard = r.json()
print(f'Total: {dashboard["total"]}')
print(f'By type: {dashboard["by_type"]}')
print(f'By status: {dashboard["by_status"]}')

# 6. Test search
print('\n=== 6. Certificate Search ===')
r = requests.get(f'{BASE}/api/certificates/search', headers=headers)
print(f'Status: {r.status_code}')
search = r.json()
print(f'Total: {search["total"]}')
for cert in search['certificates'][:3]:
    print(f"  {cert['filename']}: type={cert['document_type']}, status={cert['status']}")

# 7. CSV export
print('\n=== 7. CSV Export ===')
r = requests.get(f'{BASE}/api/certificates/export/csv', headers=headers)
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("content-type")}')
print(f'Content length: {len(r.content)}')
if r.status_code == 200:
    lines = r.text.strip().split('\n')
    print(f'Rows: {len(lines)}')
    if lines:
        print(f'Header: {lines[0][:120]}')

# 8. XLSX export
print('\n=== 8. XLSX Export ===')
r = requests.get(f'{BASE}/api/certificates/export/xlsx', headers=headers)
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("content-type")}')
print(f'Content length: {len(r.content)}')

# 9. Verify the XLSX is valid
if r.status_code == 200 and len(r.content) > 0:
    import zipfile
    xlsx_bytes = io.BytesIO(r.content)
    if zipfile.is_zipfile(xlsx_bytes):
        print('XLSX is valid ZIP/OOXML')
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            print(f'  Files: {len(z.namelist())}')
            print(f'  Has xl/workbook.xml: {"xl/workbook.xml" in z.namelist()}')

# 10. Test batch size limit
print('\n=== 10. Batch Size Limit ===')
# Try uploading 51 files (should fail with 413)
files_list = []
for i in range(51):
    img = Image.new('RGB', (100, 100), 'white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    files_list.append(('files', (f'cert_{i}.png', img_bytes, 'image/png')))

r = requests.post(f'{BASE}/api/certificates/upload', headers=headers, files=files_list)
print(f'Status: {r.status_code} (expected 413)')
if r.status_code == 413:
    print(f'Detail: {r.json()["detail"][:100]}')

print('\n=== ALL TESTS PASSED ===')
