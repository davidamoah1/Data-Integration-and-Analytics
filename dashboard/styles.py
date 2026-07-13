"""CSS styles for the Streamlit dashboard.

Extracted from app.py for maintainability.
"""

DARK_THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f0c29, #1a1a4e, #0f0c29);
    min-height: 100vh;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1400px;
}

.hero-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    border-radius: 20px;
    padding: 40px 48px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(102,126,234,0.35);
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 260px; height: 260px;
    background: rgba(255,255,255,0.07);
    border-radius: 50%;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 14px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 8px 0;
    letter-spacing: -0.5px;
    line-height: 1.15;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.82);
    margin: 0;
    font-weight: 400;
    line-height: 1.6;
}

.kpi-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.09), rgba(255,255,255,0.04));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
    margin-bottom: 8px;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.kpi-card-sales::before  { background: linear-gradient(90deg,#667eea,#764ba2); }
.kpi-card-profit::before { background: linear-gradient(90deg,#11998e,#38ef7d); }
.kpi-card-orders::before { background: linear-gradient(90deg,#f093fb,#f5576c); }
.kpi-card-avg::before    { background: linear-gradient(90deg,#4facfe,#00f2fe); }
.kpi-icon  { font-size: 1.6rem; margin-bottom: 10px; display: block; }
.kpi-value { font-family:'Space Grotesk',sans-serif; font-size:1.9rem; font-weight:700; color:#fff; line-height:1; margin-bottom:6px; }
.kpi-label { font-size:0.78rem; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:0.8px; font-weight:500; }

.section-header {
    font-family:'Space Grotesk',sans-serif;
    font-size:1.1rem; font-weight:600; color:#fff;
    margin:28px 0 4px 0;
}
.section-divider {
    height:1px;
    background:linear-gradient(90deg,rgba(102,126,234,0.5),transparent);
    margin:0 0 20px 0; border:none;
}

.chart-container {
    background: linear-gradient(145deg,rgba(255,255,255,0.07),rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(10px);
    margin-bottom: 20px;
}
.chart-title {
    font-family:'Space Grotesk',sans-serif;
    font-size:0.92rem; font-weight:600;
    color:rgba(255,255,255,0.82);
    margin-bottom:14px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#1a1a4e 0%,#0f0c29 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] label { color:rgba(255,255,255,0.75) !important; font-size:0.82rem; }

.sidebar-logo { font-family:'Space Grotesk',sans-serif; font-size:1.5rem; font-weight:700; color:white; padding:8px 0 20px 0; border-bottom:1px solid rgba(255,255,255,0.1); margin-bottom:20px; }
.sidebar-logo span { color:#a78bfa; }
.sidebar-section { font-size:0.7rem; font-weight:700; color:rgba(255,255,255,0.35); letter-spacing:1.2px; text-transform:uppercase; margin:20px 0 10px 0; }

.success-banner { background:linear-gradient(135deg,rgba(17,153,142,0.25),rgba(56,239,125,0.12)); border:1px solid rgba(56,239,125,0.3); border-radius:12px; padding:14px 18px; color:#38ef7d; font-size:0.88rem; font-weight:500; margin-bottom:20px; }
.warning-banner { background:linear-gradient(135deg,rgba(245,87,108,0.2),rgba(240,93,251,0.1)); border:1px solid rgba(245,87,108,0.35); border-radius:12px; padding:14px 18px; color:rgba(255,255,255,0.8); font-size:0.88rem; margin-bottom:20px; }
.info-banner { background:linear-gradient(135deg,rgba(102,126,234,0.2),rgba(118,75,162,0.1)); border:1px solid rgba(102,126,234,0.35); border-radius:12px; padding:14px 18px; color:rgba(255,255,255,0.8); font-size:0.88rem; margin-bottom:20px; }
.stat-pill { display:inline-block; background:rgba(102,126,234,0.18); border:1px solid rgba(102,126,234,0.3); border-radius:20px; padding:4px 12px; font-size:0.78rem; color:rgba(255,255,255,0.7); margin:2px 4px; }
.stat-pill strong { color:#a78bfa; }

.empty-state { text-align:center; padding:80px 40px; }
.empty-state-icon { font-size:4rem; margin-bottom:20px; opacity:0.6; }
.empty-state-title { font-family:'Space Grotesk',sans-serif; font-size:1.4rem; font-weight:600; color:rgba(255,255,255,0.75); margin-bottom:10px; }
.empty-state-desc { color:rgba(255,255,255,0.4); font-size:0.9rem; line-height:1.7; max-width:440px; margin:0 auto; }

.login-container { max-width:400px; margin:80px auto; background:linear-gradient(145deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03)); border:1px solid rgba(255,255,255,0.12); border-radius:20px; padding:40px; backdrop-filter:blur(12px); }
.login-title { font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:700; color:#fff; text-align:center; margin-bottom:8px; }
.login-subtitle { color:rgba(255,255,255,0.5); text-align:center; font-size:0.9rem; margin-bottom:28px; }

.stButton button { background:linear-gradient(135deg,#667eea,#764ba2) !important; color:white !important; border:none !important; border-radius:10px !important; font-weight:600 !important; box-shadow:0 4px 15px rgba(102,126,234,0.35) !important; }
.stButton button:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(102,126,234,0.45) !important; }

[data-testid="stFileUploader"] section { background:rgba(255,255,255,0.04); border:2px dashed rgba(102,126,234,0.45); border-radius:14px; }
[data-testid="stFileUploader"] section:hover { border-color:rgba(102,126,234,0.85); background:rgba(102,126,234,0.07); }
[data-testid="stFileUploader"] label { color:rgba(255,255,255,0.75) !important; }

.stSelectbox > div > div { background:rgba(255,255,255,0.05) !important; border-color:rgba(255,255,255,0.1) !important; color:white !important; }
.stTextInput > div > div > input { background:rgba(255,255,255,0.05) !important; border-color:rgba(255,255,255,0.1) !important; color:white !important; }

::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-thumb { background:rgba(102,126,234,0.4); border-radius:4px; }
"""

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="rgba(255,255,255,0.7)", size=12),
    margin=dict(t=30, b=30, l=10, r=10),
    legend=dict(
        bgcolor="rgba(255,255,255,0.05)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1,
        font=dict(color="rgba(255,255,255,0.65)", size=11),
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.06)",
        linecolor="rgba(255,255,255,0.1)",
        tickfont=dict(color="rgba(255,255,255,0.5)"),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.06)",
        linecolor="rgba(255,255,255,0.1)",
        tickfont=dict(color="rgba(255,255,255,0.5)"),
    ),
)

COLORS = ["#667eea", "#f093fb", "#38ef7d", "#4facfe", "#f5576c", "#ffd200", "#00f2fe", "#a78bfa"]
