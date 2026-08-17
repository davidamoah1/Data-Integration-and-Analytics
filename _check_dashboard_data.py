"""Check what data is available from the dashboard stage for chart rendering."""
import requests
import json
import csv
import io

r = requests.post('http://localhost:8001/api/auth/login', json={
    'email': 'mysql_e2e_a@test.dataflow.io',
    'password': 'TestPass123!'
})
token = r.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create dataset
csv_data = io.StringIO()
writer = csv.writer(csv_data)
writer.writerow(['product', 'revenue', 'quantity', 'region', 'date'])
for i in range(30):
    writer.writerow([
        f'Product_{i%5}',
        100 + i * 10,
        5 + i,
        ['North', 'South', 'East', 'West'][i % 4],
        f'2024-{(i%12)+1:02d}-15'
    ])
csv_bytes = csv_data.getvalue().encode()
files = {'file': ('sales_data.csv', csv_bytes, 'text/csv')}
r2 = requests.post('http://localhost:8001/dataset-workflow/run', headers=headers, files=files, timeout=120)
data = r2.json()['data']
wf_id = data['workflow_id']

# Look at the dashboard stage result
dashboard = data['stages'].get('dashboard_ready', {}).get('result', {})
print('=== Dashboard recommended_charts ===')
charts = dashboard.get('recommended_charts', [])
for c in charts[:8]:
    print(f"  {c.get('type')}: {c.get('title')}")
    if c.get('x_axis'):
        print(f"    x_axis: {c.get('x_axis')}, y_axis: {c.get('y_axis')}")
    if c.get('column'):
        print(f"    column: {c.get('column')}")
    if c.get('measure'):
        print(f"    measure: {c.get('measure')}")
print(f"  Total charts: {len(charts)}")
print()

# Profile data 
profiled = data['stages'].get('profiled', {}).get('result', {})
print('=== Profile data ===')
print(f"  Rows: {profiled.get('row_count')}, Columns: {profiled.get('column_count')}")
col_stats = profiled.get('column_stats', {})
for col_name, stats in list(col_stats.items())[:5]:
    print(f"  {col_name}: dtype={stats.get('dtype')}, unique={stats.get('unique_count')}")
    if stats.get('top_values'):
        print(f"    top_values: {stats.get('top_values')[:3]}")
    if stats.get('mean') is not None:
        print(f"    mean={stats.get('mean')}, min={stats.get('min')}, max={stats.get('max')}")
print()

# Insights
insights = data['stages'].get('insights_generated', {}).get('result', {})
print(f"=== Insights ({insights.get('total_insights')}) ===")
for ins in insights.get('insights', [])[:3]:
    print(f"  {ins.get('type')}: {ins.get('title')}")

print(f"\nWorkflow ID: {wf_id}")
