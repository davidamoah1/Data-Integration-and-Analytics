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

[data-testid="stMain"] { background:radial-gradient(circle at 12% 12%,rgba(102,126,234,0.2),transparent 34%),radial-gradient(circle at 88% 88%,rgba(17,153,142,0.12),transparent 32%),#090b16; }
[data-testid="stMainBlockContainer"] { max-width:1200px; padding-top:8vh; }
.login-shell { text-align:center; padding:1.25rem 1rem 1.6rem; }
.login-brand-mark { width:58px; height:58px; display:flex; align-items:center; justify-content:center; margin:0 auto 1rem; border:1px solid rgba(167,139,250,0.55); border-radius:18px; background:linear-gradient(145deg,#7c3aed,#4f46e5); color:#fff; font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:800; box-shadow:0 12px 32px rgba(79,70,229,0.4); }
.login-eyebrow { color:#a78bfa; font-size:0.68rem; font-weight:800; letter-spacing:0.17em; margin-bottom:0.75rem; }
.login-title { font-family:'Space Grotesk',sans-serif; font-size:2.1rem; line-height:1.1; font-weight:700; color:#fff; letter-spacing:-0.04em; margin-bottom:0.65rem; }
.login-subtitle { max-width:360px; margin:0 auto; color:rgba(255,255,255,0.58); text-align:center; font-size:0.94rem; line-height:1.6; }
[data-testid="stForm"]:has(#login_form) { margin:0 auto; padding:1.65rem; border:1px solid rgba(255,255,255,0.11); border-radius:20px; background:linear-gradient(145deg,rgba(24,28,48,0.88),rgba(14,17,32,0.94)); box-shadow:0 22px 55px rgba(0,0,0,0.25); }
[data-testid="stForm"]:has(#login_form) [data-testid="stTextInput"] { margin-bottom:0.45rem; }
[data-testid="stForm"]:has(#login_form) label { color:rgba(255,255,255,0.8) !important; font-size:0.82rem !important; font-weight:650 !important; }
[data-testid="stForm"]:has(#login_form) input { min-height:46px; border-radius:10px !important; background:rgba(255,255,255,0.055) !important; border:1px solid rgba(255,255,255,0.12) !important; }
[data-testid="stForm"]:has(#login_form) input:focus { border-color:#8b5cf6 !important; box-shadow:0 0 0 3px rgba(139,92,246,0.18) !important; }
[data-testid="stForm"]:has(#login_form) [data-testid="stFormSubmitButton"] { margin-top:0.7rem; }
[data-testid="stForm"]:has(#login_form) [data-testid="stFormSubmitButton"] button { min-height:47px; border-radius:11px !important; font-size:0.94rem; }
.login-security { margin-top:1.1rem; color:rgba(255,255,255,0.38); text-align:center; font-size:0.72rem; letter-spacing:0.02em; }
.login-security span { margin:0 0.4rem; color:#8b5cf6; }

.stButton button { background:linear-gradient(135deg,#667eea,#764ba2) !important; color:white !important; border:none !important; border-radius:10px !important; font-weight:600 !important; box-shadow:0 4px 15px rgba(102,126,234,0.35) !important; }
.stButton button:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(102,126,234,0.45) !important; }

[data-testid="stFileUploader"] section { background:rgba(255,255,255,0.04); border:2px dashed rgba(102,126,234,0.45); border-radius:14px; }
[data-testid="stFileUploader"] section:hover { border-color:rgba(102,126,234,0.85); background:rgba(102,126,234,0.07); }
[data-testid="stFileUploader"] label { color:rgba(255,255,255,0.75) !important; }

.stSelectbox > div > div { background:rgba(255,255,255,0.05) !important; border-color:rgba(255,255,255,0.1) !important; color:white !important; }
.stTextInput > div > div > input { background:rgba(255,255,255,0.05) !important; border-color:rgba(255,255,255,0.1) !important; color:white !important; }

::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-thumb { background:rgba(102,126,234,0.4); border-radius:4px; }

/* Accessibility — keyboard focus indicators */
*:focus-visible {
    outline: 2px solid #a78bfa !important;
    outline-offset: 2px !important;
}
.stButton button:focus-visible {
    outline: 2px solid #a78bfa !important;
    outline-offset: 2px !important;
}
.stTextInput input:focus-visible,
.stSelectbox div:focus-visible {
    outline: 2px solid #a78bfa !important;
}

/* Accessibility — respect reduced motion */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}

/* Accessibility — high contrast for KPI labels */
.kpi-label { color: rgba(255,255,255,0.65); }
.empty-state-desc { color: rgba(255,255,255,0.55); }
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

RESPONSIVE_CSS = """
@media (max-width: 768px) {
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1rem !important; }
    .hero-title { font-size: 1.5rem !important; }
    .hero-subtitle { font-size: 0.9rem !important; }
    .kpi-card { min-width: 140px !important; }
    .kpi-value { font-size: 1.5rem !important; }
    .section-header { font-size: 1.1rem !important; }
    [data-testid="stSidebar"] { min-width: 250px !important; }
    [data-testid="stMainBlockContainer"] { padding-top: 2.5rem !important; }
    .login-shell { padding: 0.5rem 0.5rem 1.2rem !important; }
    .login-title { font-size: 1.8rem !important; }
    [data-testid="stForm"]:has(#login_form) { padding: 1.25rem !important; border-radius: 16px !important; }
    .stColumns > div { flex-direction: column !important; }
}
@media (max-width: 480px) {
    .hero-badge { font-size: 0.7rem !important; }
    .hero-title { font-size: 1.2rem !important; }
    .kpi-card { min-width: 120px !important; padding: 12px !important; }
    .kpi-value { font-size: 1.2rem !important; }
    .kpi-label { font-size: 0.7rem !important; }
}
@media (pointer: coarse) {
    .stButton button { min-height: 44px; font-size: 1rem; }
    .stSelectbox > div > div { min-height: 44px; }
}
.onboarding-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 20px 0;
}
.success-banner {
    background: rgba(56,239,125,0.1);
    border: 1px solid rgba(56,239,125,0.3);
    border-radius: 10px;
    padding: 14px 18px;
    color: #38ef7d;
    font-size: 0.9rem;
    margin: 12px 0;
}
.warning-banner {
    background: rgba(245,87,108,0.1);
    border: 1px solid rgba(245,87,108,0.3);
    border-radius: 10px;
    padding: 14px 18px;
    color: #f5576c;
    font-size: 0.9rem;
    margin: 12px 0;
}
.info-banner {
    background: rgba(79,172,254,0.08);
    border: 1px solid rgba(79,172,254,0.2);
    border-radius: 10px;
    padding: 12px 18px;
    color: rgba(255,255,255,0.7);
    font-size: 0.85rem;
    margin: 10px 0;
}
.loading-skeleton {
    background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

/* RC1: Toast notifications */
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; }
.toast {
    background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 12px;
    padding: 14px 20px;
    color: rgba(255,255,255,0.9);
    font-size: 0.88rem;
    margin-bottom: 10px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease-out;
    max-width: 380px;
}
.toast-success { border-left: 3px solid #38ef7d; }
.toast-warning { border-left: 3px solid #f5576c; }
.toast-info { border-left: 3px solid #667eea; }
@keyframes slideIn { from { transform: translateX(400px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

/* RC1: Confirmation dialog */
.confirm-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.6);
    z-index: 9998;
    display: flex; align-items: center; justify-content: center;
    animation: fadeIn 0.2s ease-out;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.confirm-dialog {
    background: linear-gradient(145deg, #1a1a4e, #0f0c29);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 32px;
    max-width: 420px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.confirm-icon { font-size: 2.5rem; margin-bottom: 16px; }
.confirm-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 600; color: #fff; margin-bottom: 8px; }
.confirm-message { color: rgba(255,255,255,0.6); font-size: 0.9rem; line-height: 1.5; margin-bottom: 24px; }

/* RC1: Footer */
.app-footer {
    text-align: center;
    padding: 24px 0 8px 0;
    margin-top: 40px;
    border-top: 1px solid rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.25);
    font-size: 0.75rem;
}
.app-footer a { color: rgba(167,139,250,0.6); text-decoration: none; }

/* RC1: KPI trend indicator */
.kpi-trend { font-size: 0.72rem; margin-top: 4px; }
.kpi-trend-up { color: #38ef7d; }
.kpi-trend-down { color: #f5576c; }
.kpi-trend-flat { color: rgba(255,255,255,0.4); }

/* RC1: Improved data table styling */
.stDataFrame { border-radius: 12px; overflow: hidden; }
.stDataFrame [data-testid="stDataFrameResizable"] {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}

/* RC1: Chat input styling */
.stChatInput textarea {
    background: rgba(255,255,255,0.05) !important;
    border-color: rgba(255,255,255,0.12) !important;
    color: white !important;
    border-radius: 12px !important;
}

/* RC1: Tab styling */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,0.04);
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
    color: rgba(255,255,255,0.6) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(102,126,234,0.15) !important;
    color: #a78bfa !important;
    border-bottom: 2px solid #667eea;
}

/* RC1: Badge / tag styling */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-success { background: rgba(56,239,125,0.15); color: #38ef7d; border: 1px solid rgba(56,239,125,0.3); }
.badge-warning { background: rgba(245,87,108,0.15); color: #f5576c; border: 1px solid rgba(245,87,108,0.3); }
.badge-info { background: rgba(102,126,234,0.15); color: #a78bfa; border: 1px solid rgba(102,126,234,0.3); }
"""
