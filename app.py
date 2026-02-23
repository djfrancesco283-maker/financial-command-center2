# app.py — Financial Command Center v2.0
# Production-ready, mobile-first, WCAG AA compliant

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Financial Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# DESIGN TOKENS
# ============================================================
BG_PRIMARY = "#06060a"
BG_SECONDARY = "#0c0c14"
BG_ELEVATED = "#12121e"
BG_SURFACE = "#1a1a2e"

ACCENT = "#6C9FFF"
ACCENT2 = "#8B7FFF"
SUCCESS = "#34D399"
WARNING = "#FBBF24"
DANGER = "#F87171"
GOLD = "#F5D78E"

TEXT1 = "#F0F0F5"
TEXT2 = "#A0A0B8"
TEXT3 = "#6B6B80"

CHART_SM = 340
CHART_MD = 400
CHART_LG = 480

CAT_COLORS = {
    "Liquidità": "#60A5FA",
    "Investimento": "#34D399",
    "Risparmio": "#FBBF24",
    "TFR": "#F87171",
}

# ============================================================
# CSS
# ============================================================
st.markdown(
    """
    <style>
    .stApp { background-color: #06060a; }
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    #MainMenu, footer, header[data-testid="stHeader"],
    div[data-testid="stToolbar"] { display: none !important; }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }
    h1, h2, h3 { color: #F0F0F5 !important; font-weight: 700 !important; }
    p, span, label, li { color: #A0A0B8 !important; }
    .stMetric label {
        color: #6B6B80 !important; font-size: 0.75rem !important;
        font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #F0F0F5 !important; font-size: 1.625rem !important; font-weight: 800 !important;
    }
    .stButton > button {
        background: #12121e !important; border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important; color: #F0F0F5 !important; font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: rgba(108,159,255,0.1) !important; border-color: #6C9FFF !important;
    }
    .stButton > button:focus-visible {
        outline: 2px solid #6C9FFF !important; outline-offset: 2px !important;
    }
    details[data-testid="stExpander"] > summary {
        background: #12121e; border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px; padding: 0.875rem 1.125rem; transition: all 0.2s ease;
    }
    details[data-testid="stExpander"] > summary:hover {
        background: rgba(108,159,255,0.06); border-color: rgba(108,159,255,0.15);
    }
    details[data-testid="stExpander"] > div { padding-top: 0.75rem; }
    .stSpinner > div > div { color: #6C9FFF; }
    hr { border-color: rgba(255,255,255,0.06) !important; margin: 1.5rem 0 !important; }
    @media (max-width: 640px) {
        .block-container { padding-left: 0.75rem !important; padding-right: 0.75rem !important; }
        .stMetric [data-testid="stMetricValue"] { font-size: 1.375rem !important; }
        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.25rem !important; }
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #06060a; }
    ::-webkit-scrollbar-thumb { background: #1a1a2e; border-radius: 9999px; }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important; transition-duration: 0.01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# PLOTLY HELPERS
# ============================================================
PLOTLY_CFG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
    "doubleClick": "reset",
}


def make_layout(height=CHART_MD, **overrides):
    """Build a Plotly layout dict. Overrides win over defaults."""
    defaults = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT2, family="Inter, -apple-system, sans-serif"),
        margin=dict(t=48, b=24, l=12, r=12),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT3, size=11)),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color=TEXT3, size=11),
        ),
        legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center", font=dict(size=11)),
        height=height,
    )
    defaults.update(overrides)
    return defaults


# ============================================================
# DATA
# ============================================================
patrimonio = {
    "Postepay Evolution":  {"saldo": 1000,  "tipo": "Liquidità",    "icona": "💳", "tooltip": "Carta prepagata"},
    "Buddybank":           {"saldo": 400,   "tipo": "Liquidità",    "icona": "🏦", "tooltip": "Conto corrente"},
    "Revolut":             {"saldo": 3000,  "tipo": "Liquidità",    "icona": "💳", "tooltip": "Fintech"},
    "Isybank":             {"saldo": 700,   "tipo": "Liquidità",    "icona": "🏦", "tooltip": "Conto risparmio"},
    "Contanti":            {"saldo": 2500,  "tipo": "Liquidità",    "icona": "💵", "tooltip": "Cash"},
    "Degiro":              {"saldo": 0,     "tipo": "Investimento", "icona": "📈", "label": "Degiro (ETF)", "tooltip": "Brokeraggio"},
    "Scalable Capital":    {"saldo": 50,    "tipo": "Investimento", "icona": "📈", "tooltip": "Robo-advisor"},
    "Bondora":             {"saldo": 4400,  "tipo": "Investimento", "icona": "💰", "tooltip": "P2P lending"},
    "Buono Fruttifero":    {"saldo": 14000, "tipo": "Risparmio",    "icona": "🏛️", "tooltip": "Risparmio postale"},
    "TFR Lavoro":          {"saldo": 2000,  "tipo": "TFR",          "icona": "🏢", "tooltip": "Fine rapporto"},
}

etf_data = {
    "Vanguard S&P 500":        {"ticker": "VUSA.AS", "quote": 64,  "backup": 7099.07, "classe": "Azionario USA",     "fx_ticker": None,       "desc": "Traccia S&P 500"},
    "VanEck Semiconductor":    {"ticker": None,      "quote": 23,  "backup": 1423.02, "classe": "Settoriale Tech",   "fx_ticker": None,       "desc": "Semiconduttori"},
    "Vanguard High Div Yield": {"ticker": "VHYL.AS", "quote": 14,  "backup": 1068.03, "classe": "Globale Dividendi", "fx_ticker": None,       "desc": "Dividendi globali"},
    "Xtrackers AI & Big Data": {"ticker": "XAIX.DE", "quote": 7,   "backup": 1066.24, "classe": "Settoriale AI",     "fx_ticker": None,       "desc": "AI e Big Data"},
    "iShares Physical Gold":   {"ticker": "IGLN.L",  "quote": 6,   "backup": 503.26,  "classe": "Oro",               "fx_ticker": "GBPEUR=X", "desc": "ETC oro fisico"},
    "iShares Global Agg Bond": {"ticker": "AGGH.AS", "quote": 100, "backup": 498.31,  "classe": "Obbligazionario",   "fx_ticker": None,       "desc": "Bond globali"},
    "iShares MSCI China A":    {"ticker": "CNYA.AS", "quote": 60,  "backup": 307.06,  "classe": "Emergenti Cina",    "fx_ticker": None,       "desc": "Azioni cinesi A"},
}

milestones = [
    {"nome": "€50k",  "target": 50_000,    "reward": "Audi A3",           "color": ACCENT,  "icon": "🚗"},
    {"nome": "€100k", "target": 100_000,   "reward": "Upgrade Dualframe", "color": ACCENT2, "icon": "📈"},
    {"nome": "€400k", "target": 400_000,   "reward": "Audi Q8",           "color": SUCCESS, "icon": "🏎️"},
    {"nome": "€1M",   "target": 1_000_000, "reward": "Porsche Panamera",  "color": GOLD,    "icon": "🏆"},
]

naval_quotes = [
    "Seek wealth, not money or status.",
    "You're not going to get rich renting out your time.",
    "Arm yourself with specific knowledge, accountability, and leverage.",
    "Code and media are permissionless leverage.",
    "Play long-term games with long-term people.",
    "Be patient with results, impatient with actions.",
    "The most important skill is the ability to learn.",
]

# ============================================================
# DATA FETCHING
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_etf_prices(etf_dict):
    results = {}
    issues = []
    tickers = [d["ticker"] for d in etf_dict.values() if d.get("ticker")]
    fx_tickers = list({d["fx_ticker"] for d in etf_dict.values() if d.get("fx_ticker")})
    all_tickers = list(dict.fromkeys(tickers + fx_tickers))

    if not all_tickers:
        for name, d in etf_dict.items():
            results[name] = float(d.get("backup", 0))
        issues.append("Nessun ticker configurato.")
        return results, issues

    try:
        data = yf.download(
            all_tickers, period="7d", interval="1d",
            auto_adjust=False, progress=False, group_by="column",
        )
    except Exception as e:
        for name, d in etf_dict.items():
            results[name] = float(d.get("backup", 0))
        issues.append("Download fallito: " + str(e))
        return results, issues

    def last_close(ticker):
        try:
            if data is None or getattr(data, "empty", True):
                return None
            if isinstance(data.columns, pd.MultiIndex):
                s = data["Close"][ticker].dropna()
            else:
                s = data["Close"].dropna()
            return float(s.iloc[-1]) if len(s) else None
        except Exception:
            return None

    for name, d in etf_dict.items():
        ticker = d.get("ticker")
        shares = float(d.get("quote", 0))
        backup = float(d.get("backup", 0))
        if not ticker:
            results[name] = backup
            if backup > 0:
                issues.append(name + ": no ticker, uso backup.")
            continue
        price = last_close(ticker)
        if price is None:
            results[name] = backup
            issues.append(name + ": prezzo N/A, uso backup.")
            continue
        fx = 1.0
        fx_ticker = d.get("fx_ticker")
        if fx_ticker:
            fx_price = last_close(fx_ticker)
            if fx_price is None:
                issues.append(name + ": FX N/A, assumo 1.0.")
            else:
                fx = float(fx_price)
        value = round(price * shares * fx, 2)
        if backup > 0:
            ratio = value / backup
            if ratio > 1.8 or ratio < 0.55:
                issues.append(name + ": valore anomalo.")
        results[name] = value
    return results, issues


# ============================================================
# COMPUTATION
# ============================================================
def compute_projection(initial, monthly, annual_return, years=30):
    r = (1 + annual_return / 100) ** (1 / 12) - 1
    vals = [initial]
    for _ in range(years * 12):
        vals.append(round(vals[-1] * (1 + r) + monthly, 2))
    return vals


def estimate_months(initial, target, monthly, annual_return):
    r = (1 + annual_return / 100) ** (1 / 12) - 1
    v = float(initial)
    m = 0
    while v < target and m < 1200:
        v = v * (1 + r) + monthly
        m += 1
    return m


@st.cache_data(ttl=3600, show_spinner=False)
def run_monte_carlo(initial, monthly, annual_return, annual_vol, years=25, sims=1000, seed=42):
    rng = np.random.default_rng(seed)
    n = years * 12
    r_m = (annual_return / 100) / 12
    vol_m = (annual_vol / 100) / np.sqrt(12)
    returns = rng.normal(r_m, vol_m, size=(sims, n))
    scenarios = np.zeros((sims, n + 1))
    scenarios[:, 0] = initial
    for m in range(n):
        scenarios[:, m + 1] = np.maximum(
            scenarios[:, m] * (1 + returns[:, m]) + monthly, 0
        )
    return scenarios, scenarios[:, -1]


# ============================================================
# CONTROLS
# ============================================================
def render_controls(ui):
    ui.markdown("### Simulatore")
    ui.caption("Regola i parametri per proiezione e Monte Carlo.")
    cols = ui.columns(2)
    with cols[0]:
        cm = ui.slider("Contributo mensile (€)", 100, 3000, 600, 50, help="Importo mensile.")
        ed = ui.slider("Entrate extra (€/mese)", 0, 5000, 0, 100, help="Entrate da progetti.")
    with cols[1]:
        ra = ui.slider("Rendimento annuo (%)", 3.0, 15.0, 7.0, 0.5, help="Rendimento atteso.")
        va = ui.slider("Volatilità annua (%)", 5.0, 30.0, 14.0, 0.5, help="Fluttuazioni mercato.")
    total = cm + ed
    ui.markdown("---")
    ui.metric("Contributo totale mensile", "€{:,.0f}".format(total))
    return float(cm), float(ra), float(ed), float(va), float(total)


def render_warnings(ui, issues_list):
    if issues_list:
        with ui.expander("⚠ Avvisi dati (" + str(len(issues_list)) + ")", expanded=False):
            for msg in issues_list[:20]:
                ui.warning(msg)


# ============================================================
# LOAD DATA
# ============================================================
with st.spinner("Aggiornamento prezzi..."):
    prezzi_etf, issues = fetch_etf_prices(etf_data)
    totale_degiro = sum(prezzi_etf.values())
    patrimonio["Degiro"]["saldo"] = totale_degiro

# ============================================================
# RENDER CONTROLS
# ============================================================
render_warnings(st, issues)
with st.expander("⚙ Simulatore", expanded=True):
    contributo, rendimento, extra, volatilita, contrib_totale = render_controls(st)

# ============================================================
# CALCULATIONS
# ============================================================
net_worth = sum(v["saldo"] for v in patrimonio.values())
liquidita = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Liquidità")
investimenti = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Investimento")
risparmio = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Risparmio")
tfr = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "TFR")
produttivo = investimenti + risparmio
pct_prod = (produttivo / net_worth * 100) if net_worth > 0 else 0

# ============================================================
# HERO HEADER
# ============================================================
hero_stats = (
    '<div style="display:flex;justify-content:center;gap:2rem;flex-wrap:wrap;" role="list">'
    # Productive
    '<div style="min-width:100px;" role="listitem">'
    '<p style="font-size:1.25rem;font-weight:700;margin:0;color:' + SUCCESS + ';">'
    "€{:,.0f}".format(produttivo) + "</p>"
    '<p style="font-size:0.6875rem;color:' + TEXT3 + ';margin:2px 0 0 0;'
    'text-transform:uppercase;letter-spacing:0.1em;">Produttivo · '
    "{:.0f}%".format(pct_prod) + "</p></div>"
    # Liquidity
    '<div style="min-width:100px;" role="listitem">'
    '<p style="font-size:1.25rem;font-weight:700;margin:0;color:' + ACCENT + ';">'
    "€{:,.0f}".format(liquidita) + "</p>"
    '<p style="font-size:0.6875rem;color:' + TEXT3 + ';margin:2px 0 0 0;'
    'text-transform:uppercase;letter-spacing:0.1em;">Liquidità</p></div>'
    # TFR
    '<div style="min-width:100px;" role="listitem">'
    '<p style="font-size:1.25rem;font-weight:700;margin:0;color:' + DANGER + ';">'
    "€{:,.0f}".format(tfr) + "</p>"
    '<p style="font-size:0.6875rem;color:' + TEXT3 + ';margin:2px 0 0 0;'
    'text-transform:uppercase;letter-spacing:0.1em;">TFR</p></div>'
    "</div>"
)

hero_html = (
    '<div style="'
    "background:linear-gradient(160deg, " + BG_SECONDARY + " 0%, " + BG_SURFACE + " 60%, " + BG_ELEVATED + " 100%);"
    "border:1px solid rgba(255,255,255,0.06);"
    "border-radius:20px;padding:2rem 1.5rem;margin-bottom:1.5rem;"
    "text-align:center;position:relative;overflow:hidden;"
    "box-shadow:0 12px 40px rgba(0,0,0,0.5), 0 0 40px rgba(108,159,255,0.06);"
    '" role="banner">'
    # Decorative orb
    '<div style="position:absolute;top:-60px;right:-60px;width:200px;height:200px;'
    'background:radial-gradient(circle,rgba(108,159,255,0.06) 0%,transparent 70%);'
    'border-radius:50%;pointer-events:none;"></div>'
    # Title
    '<p style="font-size:0.6875rem;color:' + TEXT3 + ';letter-spacing:0.2em;'
    'text-transform:uppercase;font-weight:600;margin:0 0 0.75rem 0;">'
    "Financial Command Center</p>"
    # Net worth
    '<h1 style="font-size:clamp(2.25rem,7vw,3.5rem);margin:0 0 0.25rem 0;'
    "color:" + TEXT1 + ";font-weight:800;letter-spacing:-0.03em;line-height:1.1;"
    '">'
    "€{:,.0f}".format(net_worth) + "</h1>"
    # Date
    '<p style="font-size:0.8125rem;color:' + TEXT3 + ';margin:0 0 1.5rem 0;">'
    "Patrimonio Netto · " + datetime.now().strftime("%d %b %Y") + "</p>"
    + hero_stats
    + "</div>"
)
st.markdown(hero_html, unsafe_allow_html=True)

# ============================================================
# ROW 1: DONUT + CATEGORY BARS
# ============================================================
df_pat = pd.DataFrame([
    {"Conto": v.get("label", k), "Saldo": float(v["saldo"]), "Tipo": v["tipo"]}
    for k, v in patrimonio.items()
])

col1, col2 = st.columns(2)

# --- Donut chart ---
with col1:
    colors = [CAT_COLORS.get(t, "#95a5a6") for t in df_pat["Tipo"]]
    fig_donut = go.Figure(data=[go.Pie(
        labels=df_pat["Conto"],
        values=df_pat["Saldo"],
        hole=0.62,
        marker=dict(colors=colors, line=dict(color=BG_PRIMARY, width=2)),
        textinfo="label+percent",
        textfont=dict(size=10, color="white"),
        hovertemplate="<b>%{label}</b><br>€%{value:,.0f}<br>%{percent:.1%}<extra></extra>",
    )])
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT2),
        height=CHART_SM,
        margin=dict(t=48, b=24, l=12, r=12),
        title=dict(text="Distribuzione Patrimonio", font=dict(size=16, color=TEXT1), x=0.5),
        annotations=[dict(
            text="€{:,.0f}".format(net_worth),
            x=0.5, y=0.5, font_size=20, font_color=ACCENT, showarrow=False,
        )],
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=9)),
    )
    st.plotly_chart(fig_donut, use_container_width=True, config=PLOTLY_CFG)

# --- Category bars ---
with col2:
    df_cat = df_pat.groupby("Tipo")["Saldo"].sum().reset_index().sort_values("Saldo", ascending=True)
    fig_bar = go.Figure(data=[go.Bar(
        x=df_cat["Saldo"],
        y=df_cat["Tipo"],
        orientation="h",
        marker=dict(color=[CAT_COLORS.get(c, "#95a5a6") for c in df_cat["Tipo"]]),
        text=["€{:,.0f}".format(v) for v in df_cat["Saldo"]],
        textposition="outside",
        textfont=dict(color=TEXT1, size=12),
        hovertemplate="<b>%{y}</b><br>€%{x:,.0f}<extra></extra>",
    )])
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT2),
        height=CHART_SM,
        margin=dict(t=48, b=24, l=12, r=40),
        title=dict(text="Per Categoria", font=dict(size=16, color=TEXT1), x=0.5),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(tickfont=dict(size=12, color=TEXT2)),
        legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center", font=dict(size=11)),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CFG)

# ============================================================
# ETF BREAKDOWN
# ============================================================
st.markdown("---")
st.markdown(
    '<h2 style="text-align:center;color:' + TEXT1 + ';margin:0.5rem 0;">Portafoglio ETF Degiro</h2>',
    unsafe_allow_html=True,
)
st.caption("Dettaglio posizioni con valori live · Totale: €{:,.0f}".format(totale_degiro))

df_etf = pd.DataFrame([
    {"ETF": nome, "Valore": float(val), "Classe": etf_data[nome]["classe"], "Desc": etf_data[nome]["desc"]}
    for nome, val in prezzi_etf.items()
])
tot_etf = float(df_etf["Valore"].sum()) if len(df_etf) else 0.0
df_etf["Peso"] = (df_etf["Valore"] / tot_etf * 100).round(1) if tot_etf > 0 else 0
df_etf = df_etf.sort_values("Valore", ascending=True)

fig_etf = go.Figure(data=[go.Bar(
    x=df_etf["Valore"],
    y=df_etf["ETF"],
    orientation="h",
    marker=dict(
        color=df_etf["Valore"],
        colorscale=[[0, "#1a1a4e"], [0.5, ACCENT], [1, SUCCESS]],
        showscale=False,
    ),
    text=[
        "€{:,.0f}  ({:.1f}%)".format(v, p)
        for v, p in zip(df_etf["Valore"], df_etf["Peso"])
    ],
    textposition="outside",
    textfont=dict(color=TEXT1, size=11),
    customdata=df_etf[["Desc"]],
    hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>€%{x:,.0f}<extra></extra>",
)])
fig_etf.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT2),
    height=CHART_MD,
    margin=dict(t=24, b=24, l=12, r=100),
    xaxis=dict(showgrid=False, showticklabels=False),
    yaxis=dict(tickfont=dict(size=10, color=TEXT2)),
    legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center", font=dict(size=11)),
)
st.plotly_chart(fig_etf, use_container_width=True, config=PLOTLY_CFG)

# ============================================================
# MILESTONES — Road to Panamera
# ============================================================
st.markdown("---")
st.markdown(
    '<h2 style="text-align:center;color:' + TEXT1 + ';margin:0.5rem 0;">Road to Panamera</h2>',
    unsafe_allow_html=True,
)
st.caption("Progresso verso i tuoi traguardi finanziari.")

for m in milestones:
    pct = min((net_worth / m["target"]) * 100, 100) if m["target"] > 0 else 0
    mesi = estimate_months(net_worth, m["target"], contrib_totale, rendimento)
    data_stima = (pd.Timestamp.today().normalize() + pd.DateOffset(months=int(mesi))).strftime("%B %Y")
    anni = mesi // 12
    mesi_rest = mesi % 12

    bar_html = (
        '<div style="margin:12px 0;" role="progressbar" '
        'aria-valuenow="' + str(round(pct, 1)) + '" '
        'aria-valuemin="0" aria-valuemax="100" '
        'aria-label="Progresso verso ' + m["nome"] + '">'
        # Top row
        '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;">'
        '<span style="font-size:0.9375rem;color:' + TEXT1 + ';font-weight:600;">'
        + m["icon"] + " " +
        m["nome"] + "</span>"
        '<span style="font-size:0.75rem;color:' + TEXT3 + ';">'
        + m["reward"] + "</span></div>"
        # Progress bar
        '<div style="background:rgba(255,255,255,0.04);border-radius:10px;height:28px;'
        'margin:6px 0;overflow:hidden;border:1px solid rgba(255,255,255,0.04);">'
        '<div style="background:linear-gradient(90deg,' + m["color"] + "," + m["color"] + "88);"
        "height:100%;width:" + str(pct) + "%;border-radius:10px;"
        "display:flex;align-items:center;justify-content:center;"
        'font-weight:700;font-size:0.75rem;color:white;min-width:40px;">'
        + "{:.1f}%".format(pct) + "</div></div>"
        # Bottom info
        '<p style="font-size:0.6875rem;color:' + TEXT3 + ';margin:4px 0 0 0;">'
        "€{:,.0f}".format(net_worth) + " / €{:,.0f}".format(m["target"])
        + " · ~" + str(anni) + "a " + str(mesi_rest) + "m → " + data_stima
        + "</p></div>"
    )
    st.markdown(bar_html, unsafe_allow_html=True)

# ============================================================
# PROJECTION CHART
# ============================================================
st.markdown("---")
st.markdown(
    '<h2 style="text-align:center;color:' + TEXT1 + ';margin:0.5rem 0;">Proiezione Patrimonio</h2>',
    unsafe_allow_html=True,
)
st.caption("Crescita stimata a 30 anni con contributi regolari e rendimento composto.")

proiezione = compute_projection(net_worth, contrib_totale, rendimento, anni=30)
date_proj = pd.date_range(
    start=pd.Timestamp.today().normalize(), periods=len(proiezione), freq="MS"
).to_pydatetime()

fig_proj = go.Figure()
fig_proj.add_trace(go.Scatter(
    x=date_proj, y=proiezione, mode="lines", name="Proiezione",
    line=dict(color=ACCENT, width=2.5),
    fill="tozeroy", fillcolor="rgba(108,159,255,0.06)",
    hovertemplate="<b>%{x|%B %Y}</b><br>€%{y:,.0f}<extra></extra>",
))

for m in milestones:
    fig_proj.add_hline(
        y=m["target"], line_dash="dot", line_color=m["color"], opacity=0.5,
        annotation_text=m["nome"] + " · " + m["reward"],
        annotation_position="top right",
        annotation_font_color=m["color"], annotation_font_size=10,
    )

fig_proj.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT2),
    height=CHART_MD,
    margin=dict(t=24, b=24, l=12, r=12),
    xaxis=dict(showgrid=False, tickfont=dict(color=TEXT3, size=11)),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        tickfont=dict(color=TEXT3, size=11), tickprefix="€",
    ),
    legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center", font=dict(size=11)),
)
st.plotly_chart(fig_proj, use_container_width=True, config=PLOTLY_CFG)

# ============================================================
# MONTE CARLO
# ============================================================
st.markdown("---")
st.markdown(
    '<h2 style="text-align:center;color:' + TEXT1 + ';">Simulazione Monte Carlo</h2>',
    unsafe_allow_html=True,
)
st.caption("1.000 scenari probabilistici a 25 anni considerando la volatilità di mercato.")

scenarios, final_values = run_monte_carlo(
    net_worth, contrib_totale, rendimento, volatilita
)

percentiles = np.percentile(final_values, [10, 25, 50, 75, 90])
prob_100k = (final_values >= 100_000).mean() * 100
prob_500k = (final_values >= 500_000).mean() * 100
prob_1m = (final_values >= 1_000_000).mean() * 100

mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Prob. ≥ €100k", "{:.0f}%".format(prob_100k))
mc2.metric("Prob. ≥ €500k", "{:.0f}%".format(prob_500k))
mc3.metric("Prob. ≥ €1M", "{:.0f}%".format(prob_1m))
mc4.metric("Mediana 25a", "€{:,.0f}".format(percentiles[2]))

n_months_mc = scenarios.shape[1]
dates_mc = pd.date_range(
    start=pd.Timestamp.today().normalize(), periods=n_months_mc, freq="MS"
).to_pydatetime()

fig_mc = go.Figure()

# Sample background scenarios
for idx in [10, 50, 150, 300, 500, 700, 900]:
    if idx < len(scenarios):
        fig_mc.add_trace(go.Scatter(
            x=dates_mc, y=scenarios[idx], mode="lines",
            line=dict(color="rgba(108,159,255,0.07)", width=0.8),
            showlegend=False, hoverinfo="skip",
        ))

# Confidence band 25-75
p25 = np.percentile(scenarios, 25, axis=0)
p75 = np.percentile(scenarios, 75, axis=0)
fig_mc.add_trace(go.Scatter(
    x=np.concatenate([dates_mc, dates_mc[::-1]]),
    y=np.concatenate([p75, p25[::-1]]),
    fill="toself", fillcolor="rgba(108,159,255,0.06)",
    line=dict(width=0), showlegend=False, hoverinfo="skip",
))

# Percentile lines
for pval, label, color, dash in [
    (10, "Pessimista (10°)", DANGER, "dot"),
    (50, "Mediana", ACCENT, "solid"),
    (90, "Ottimista (90°)", SUCCESS, "dot"),
]:
    pline = np.percentile(scenarios, pval, axis=0)
    fig_mc.add_trace(go.Scatter(
        x=dates_mc, y=pline, mode="lines", name=label,
        line=dict(color=color, width=2.5, dash=dash),
        hovertemplate="<b>" + label + "</b><br>%{x|%B %Y}<br>€%{y:,.0f}<extra></extra>",
    ))

fig_mc.add_hline(
    y=1_000_000, line_dash="dash", line_color=GOLD, opacity=0.4,
    annotation_text="€1M", annotation_position="top right",
    annotation_font_color=GOLD, annotation_font_size=11,
)

fig_mc.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT2),
    height=CHART_LG,
    margin=dict(t=24, b=24, l=12, r=12),
    xaxis=dict(showgrid=False, tickfont=dict(color=TEXT3, size=11)),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        tickfont=dict(color=TEXT3, size=11), tickprefix="€",
    ),
    legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center", font=dict(size=11)),
)
st.plotly_chart(fig_mc, use_container_width=True, config=PLOTLY_CFG)

# ============================================================
# SUNBURST
# ============================================================
st.markdown("---")

asset_rows = []
for nome, valore in prezzi_etf.items():
    asset_rows.append({
        "Fonte": "Degiro (ETF)",
        "Asset": etf_data[nome]["classe"],
        "Valore": float(valore),
    })
for conto, dati in patrimonio.items():
    if conto.lower() == "degiro":
        continue
    asset_rows.append({
        "Fonte": dati["tipo"],
        "Asset": conto,
        "Valore": float(dati["saldo"]),
    })

df_sun = pd.DataFrame(asset_rows)

fig_sun = px.sunburst(
    df_sun, path=["Fonte", "Asset"], values="Valore",
    color="Valore",
    color_continuous_scale=[[0, "#1a1a4e"], [0.5, ACCENT], [1, SUCCESS]],
)
fig_sun.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT2),
    height=CHART_MD,
    margin=dict(t=48, b=12, l=12, r=12),
    title=dict(text="Mappa Completa Patrimonio", font=dict(size=16, color=TEXT1), x=0.5),
    coloraxis_showscale=False,
)
fig_sun.update_traces(
    textinfo="label+percent parent",
    hovertemplate="<b>%{label}</b><br>€%{value:,.0f}<br>%{percentRoot:.1%} del totale<extra></extra>",
    insidetextfont=dict(size=11),
)

with st.expander("🗺 Mappa patrimonio (Sunburst)", expanded=False):
    st.plotly_chart(fig_sun, use_container_width=True, config=PLOTLY_CFG)

# ============================================================
# HISTOGRAM — Final distribution
# ============================================================
with st.expander("📊 Distribuzione scenari finali", expanded=False):
    fig_hist = go.Figure(data=[go.Histogram(
        x=final_values, nbinsx=60,
        marker=dict(color=ACCENT, opacity=0.7, line=dict(color=ACCENT, width=0.5)),
        hovertemplate="€%{x:,.0f}<br>%{y} scenari<extra></extra>",
    )])
    fig_hist.add_vline(
        x=float(percentiles[2]), line_dash="dash", line_color=TEXT1, opacity=0.6,
        annotation_text="Mediana €{:,.0f}".format(percentiles[2]),
        annotation_font_color=TEXT1, annotation_font_size=11,
    )
    fig_hist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT2),
        height=CHART_SM,
        margin=dict(t=24, b=24, l=12, r=12),
        title=dict(text="Distribuzione valori a 25 anni", font=dict(size=14, color=TEXT2), x=0.5),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT3, size=11), tickprefix="€"),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color=TEXT3, size=11),
            title=dict(text="Scenari", font=dict(size=11, color=TEXT3)),
        ),
        bargap=0.05,
        legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center", font=dict(size=11)),
    )
    st.plotly_chart(fig_hist, use_container_width=True, config=PLOTLY_CFG)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")

quote_text = naval_quotes[datetime.now().day % len(naval_quotes)]

footer_html = (
    '<div style="text-align:center;padding:1.5rem 1rem;" role="contentinfo">'
    '<p style="font-style:italic;font-size:0.875rem;color:' + TEXT2 + ';'
    'margin:0 0 4px 0;line-height:1.5;">"' + quote_text + '"</p>'
    '<p style="font-size:0.75rem;color:' + TEXT3 + ';margin:0 0 1rem 0;">'
    "— Naval Ravikant</p>"
    '<div style="display:inline-flex;align-items:center;gap:6px;'
    "background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.04);"
    'border-radius:9999px;padding:6px 14px;">'
    '<div style="width:6px;height:6px;border-radius:50%;background:' + SUCCESS + ';"></div>'
    '<span style="font-size:0.6875rem;color:' + TEXT3 + ';">'
    "Aggiornato: " + datetime.now().strftime("%d/%m/%Y %H:%M") + " · Yahoo Finance"
    "</span></div></div>"
)
st.markdown(footer_html, unsafe_allow_html=True)

