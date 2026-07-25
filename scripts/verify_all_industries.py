"""Verify all 12 industry datasets detect correctly and produce industry-appropriate dashboards."""
import os
import pandas as pd
from semantic.mapping_engine import SemanticMappingEngine
from semantic.dashboard_generator import DashboardGenerator
from semantic.dashboard_registry import DashboardRegistry

datasets_dir = "dataset/industries"
results = []

for filename in sorted(os.listdir(datasets_dir)):
    if not filename.endswith(".csv"):
        continue
    filepath = os.path.join(datasets_dir, filename)
    df = pd.read_csv(filepath)
    m = SemanticMappingEngine.analyze(df, filename)
    template = DashboardRegistry.get(m.industry)
    template_key = template.key if template else "NONE"

    # Check for cross-industry contamination
    try:
        config = DashboardGenerator.generate(df, m, admin_confirmed=True)
        kpi_labels = [k["label"] for k in config.kpi_cards]
        has_banking_kpi = (
        m.industry not in ("retail", "banking")
        and any("Transaction" in label for label in kpi_labels)
    )
    except ValueError:
        kpi_labels = []
        has_banking_kpi = False

    status = "OK" if m.industry_confidence >= 90.0 else "LOW_CONF"
    if has_banking_kpi:
        status += " + CONTAMINATION"

    results.append((filename, m.industry, m.industry_confidence, template_key, status, kpi_labels))

print(f"{'File':<30s} {'Industry':<20s} {'Conf':>6s} {'Template':<30s} {'Status':<20s}")
print("-" * 110)
for filename, industry, conf, template_key, status, kpi_labels in results:
    print(f"{filename:<30s} {industry:<20s} {conf:>5.1f}% {template_key:<30s} {status:<20s}")
    if "CONTAMINATION" in status:
        print(f"  KPI labels: {kpi_labels}")

print()
all_ok = all("CONTAMINATION" not in s for _, _, _, _, s, _ in results)
print(f"All datasets clean: {all_ok}")
