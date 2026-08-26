"""Debug script to trace healthcare dataset through the full pipeline."""

import pandas as pd

from semantic.dashboard_generator import DashboardGenerator
from semantic.dashboard_registry import DashboardRegistry
from semantic.mapping_engine import SemanticMappingEngine

df = pd.read_csv("dataset/industries/healthcare.csv")
print(f"Columns: {list(df.columns)}")
print(f"Shape: {df.shape}")
print()

m = SemanticMappingEngine.analyze(df, "healthcare.csv")
print(f"Industry: {m.industry}")
print(f"Confidence: {m.industry_confidence:.1f}%")
print(f"Entities: {m.business_entities}")
print()

print("Column mappings:")
for mp in m.semantic_result.mappings:
    print(
        f"  {mp.column_name:25s} -> {mp.entity_key:20s} ({mp.industry:15s}) conf={mp.confidence:.2f}"
    )
print()

# Check what template is returned
template = DashboardRegistry.get(m.industry)
print(f"DashboardRegistry.get('{m.industry}'): {template.key if template else None}")
print()

# Try generating dashboard
try:
    c = DashboardGenerator.generate(df, m, admin_confirmed=True)
    print(f"Template: {c.template}")
    print(f"Title: {c.title}")
    print(f"KPI cards: {len(c.kpi_cards)}")
    print(f"Widgets: {len(c.widgets)}")
    print(f"Charts: {len(c.charts)}")
    print()
    print("KPI cards:")
    for k in c.kpi_cards:
        print(f"  {k['label']}")
    print()
    print("Widgets:")
    for w in c.widgets:
        print(f"  {w['key']} ({w['type']}) available={w['available']}")
except ValueError as e:
    print(f"BLOCKED: {e}")

# Also try without admin_confirmed
print()
print("--- Without admin_confirmed ---")
try:
    c = DashboardGenerator.generate(df, m, admin_confirmed=False)
    print(f"Template: {c.template}")
except ValueError as e:
    print(f"BLOCKED: {e}")
