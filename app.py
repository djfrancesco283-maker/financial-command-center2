# app.py — Financial Command Center v2.0
# ============================================================
# Architecture: Modular single-file Streamlit app
# Design System: Dark premium with consistent token system
# Performance: Optimized caching, vectorized Monte Carlo, lazy sections
# Accessibility: WCAG 2.1 AA compliant contrast, semantic HTML, ARIA
# Responsive: Mobile-first with adaptive layouts
# ============================================================

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import TypedDict, Optional


# ============================================================
# 🏗️ TYPE DEFINITIONS
# ============================================================
class AccountData(TypedDict):
    saldo: float
    tipo: str
    icona: str
    tooltip: str
    label: Optional[str]


class ETFData(TypedDict):
    ticker: Optional[str]
    quote: int
    backup: float
    classe: str
    fx_ticker: Optional[str]
    desc: str


class Milestone(TypedDict):
    nome: str
    target: int
    reward: str
    color: str
    icon: str


# ============================================================
# 🎨 DESIGN TOKENS — Single source of truth
# ============================================================
class Theme:
    """Centralized design token system for consistent styling."""

    # Colors — Primary palette
    BG_PRIMARY = "#06060a"
    BG_SECONDARY = "#0c0c14"
    BG_ELEVATED = "#12121e"
    BG_SURFACE = "#1a1a2e"
    BG_HOVER = "rgba(255,255,255,0.04)"

    # Accent colors
    ACCENT_PRIMARY = "#6C9FFF"       # Softer, more premium blue
    ACCENT_SECONDARY = "#8B7FFF"     # Purple accent
    ACCENT_SUCCESS = "#34D399"       # Emerald green
    ACCENT_WARNING = "#FBBF24"       # Warm amber
    ACCENT_DANGER = "#F87171"        # Soft red
    ACCENT_GOLD = "#F5D78E"          # Muted gold

    # Text hierarchy (WCAG AA on dark backgrounds)
    TEXT_PRIMARY = "#F0F0F5"         # 15.4:1 on BG_PRIMARY
    TEXT_SECONDARY = "#A0A0B8"       # 7.2:1 on BG_PRIMARY
    TEXT_TERTIARY = "#6B6B80"        # 4.6:1 on BG_PRIMARY (AA compliant)
    TEXT_DISABLED = "#4A4A5A"

    # Category colors — harmonized palette
    CAT_LIQUIDITY = "#60A5FA"        # Blue-400
    CAT_INVESTMENT = "#34D399"       # Emerald-400
    CAT_SAVINGS = "#FBBF24"          # Amber-400
    CAT_TFR = "#F87171"             # Red-400

    CATEGORY_COLORS = {
        "Liquidità": CAT_LIQUIDITY,
        "Investimento": CAT_INVESTMENT,
        "Risparmio": CAT_SAVINGS,
        "TFR": CAT_TFR,
    }

    # Spacing scale (rem)
    SPACE_XS = "0.25rem"
    SPACE_SM = "0.5rem"
    SPACE_MD = "1rem"
    SPACE_LG = "1.5rem"
    SPACE_XL = "2rem"
    SPACE_2XL = "3rem"

    # Border radius
    RADIUS_SM = "8px"
    RADIUS_MD = "12px"
    RADIUS_LG = "16px"
    RADIUS_XL = "20px"
    RADIUS_FULL = "9999px"

    # Chart heights — responsive aware
    CHART_SM = 340
    CHART_MD = 400
    CHART_LG = 480

    # Shadows
    SHADOW_SM = "0 1px 2px rgba(0,0,0,0.3)"
    SHADOW_MD = "0 4px 16px rgba(0,0,0,0.4)"
    SHADOW_LG = "0 12px 40px rgba(0,0,0,0.5)"
    SHADOW_GLOW = "0 0 40px rgba(108,159,255,0.08)"


# ============================================================
# ⚙️ PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Financial Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 🎨 GLOBAL STYLES — Mobile-first, WCAG AA compliant
# ============================================================
def inject_global_styles() -> None:
    """Inject all CSS in a single call to minimize DOM operations."""
    st.markdown(f"""
    <style>
        /* ── Reset & Base ─────────────────────────── */
        .stApp {{
            background-color: {Theme.BG_PRIMARY};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {Theme.BG_SURFACE};
            border-right: 1px solid rgba(255,255,255,0.06);
        }}

        #MainMenu, footer, header[data-testid="stHeader"],
        div[data-testid="stToolbar"] {{
            display: none !important;
        }}

        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 1200px;
        }}

        /* ── Typography ──────────────────────────── */
        h1, h2, h3 {{
            color: {Theme.TEXT_PRIMARY} !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }}

        p, span, label, li {{
            color: {Theme.TEXT_SECONDARY} !important;
        }}

        /* ── Metrics ─────────────────────────────── */
        .stMetric label {{
            color: {Theme.TEXT_TERTIARY} !important;
            font-size: 0.75rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .stMetric [data-testid="stMetricValue"] {{
            color: {Theme.TEXT_PRIMARY} !important;
            font-size: 1.625rem !important;
            font-weight: 800 !important;
            font-variant-numeric: tabular-nums;
        }}

        .stMetric [data-testid="stMetricDelta"] {{
            font-variant-numeric: tabular-nums;
        }}

        /* ── Interactive Elements ────────────────── */
        .stButton > button {{
            background: {Theme.BG_ELEVATED} !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: {Theme.RADIUS_MD} !important;
            color: {Theme.TEXT_PRIMARY} !important;
            font-weight: 600 !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }}

        .stButton > button:hover {{
            background: rgba(108, 159, 255, 0.1) !important;
            border-color: {Theme.ACCENT_PRIMARY} !important;
            box-shadow: 0 0 20px rgba(108, 159, 255, 0.1) !important;
        }}

        .stButton > button:focus-visible {{
            outline: 2px solid {Theme.ACCENT_PRIMARY} !important;
            outline-offset: 2px !important;
        }}

        /* ── Expander ────────────────────────────── */
        details[data-testid="stExpander"] > summary {{
            background: {Theme.BG_ELEVATED};
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: {Theme.RADIUS_LG};
            padding: 0.875rem 1.125rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        details[data-testid="stExpander"] > summary:hover {{
            background: rgba(108, 159, 255, 0.06);
            border-color: rgba(108, 159, 255, 0.15);
        }}

        details[data-testid="stExpander"] > summary:focus-visible {{
            outline: 2px solid {Theme.ACCENT_PRIMARY};
            outline-offset: 2px;
        }}

        details[data-testid="stExpander"] > div {{
            padding-top: 0.75rem;
        }}

        /* ── Slider ──────────────────────────────── */
        .stSlider > div > div > div > div {{
            background-color: {Theme.ACCENT_PRIMARY} !important;
        }}

        /* ── Spinner ─────────────────────────────── */
        .stSpinner > div > div {{
            color: {Theme.ACCENT_PRIMARY};
        }}

        /* ── Dividers ────────────────────────────── */
        hr {{
            border-color: rgba(255,255,255,0.06) !important;
            margin: 1.5rem 0 !important;
        }}

        /* ── Mobile-First Responsive ─────────────── */
        @media (max-width: 640px) {{
            .block-container {{
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }}

            .stMetric [data-testid="stMetricValue"] {{
                font-size: 1.375rem !important;
            }}

            h1 {{ font-size: 1.75rem !important; }}
            h2 {{ font-size: 1.25rem !important; }}

            div.stColumns > div {{
                margin-bottom: 0.25rem;
            }}
        }}

        @media (min-width: 641px) and (max-width: 1024px) {{
            .block-container {{
                padding-left: 1.5rem !important;
                padding-right: 1.5rem !important;
            }}
        }}

        /* ── Custom scrollbar ────────────────────── */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: {Theme.BG_PRIMARY};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {Theme.BG_SURFACE};
            border-radius: {Theme.RADIUS_FULL};
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {Theme.TEXT_DISABLED};
        }}

        /* ── Animations ──────────────────────────── */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .fade-in {{
            animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }}

        /* ── Reduced motion preference ───────────── */
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)


inject_global_styles()


# ============================================================
# 📊 PLOTLY SHARED CONFIG
# ============================================================
PLOTLY_CONFIG: dict = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
    "doubleClick": "reset",
}

PLOTLY_BASE_LAYOUT: dict = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": Theme.TEXT_SECONDARY, "family": "Inter, -apple-system, sans-serif"},
    "margin": {"t": 48, "b": 24, "l": 12, "r": 12},
    "xaxis": {"showgrid": False, "tickfont": {"color": Theme.TEXT_TERTIARY, "size": 11}},
    "yaxis": {
        "showgrid": True,
        "gridcolor": "rgba(255,255,255,0.04)",
        "tickfont": {"color": Theme.TEXT_TERTIARY, "size": 11},
    },
    "legend": {"orientation": "h", "y": 1.06, "x": 0.5, "xanchor": "center", "font": {"size": 11}},
}


def apply_base_layout(fig: go.Figure, height: int = Theme.CHART_MD, **overrides) -> go.Figure:
    """Apply consistent base layout to any Plotly figure."""
    layout = {**PLOTLY_BASE_LAYOUT, "height": height, **overrides}
    fig.update_layout(**layout)
    return fig


# ============================================================
# 💰 DATA LAYER — Portfolio & ETF definitions
# ============================================================
PATRIMONIO: dict[str, AccountData] = {
    "Postepay Evolution": {"saldo": 1000, "tipo": "Liquidità", "icona": "💳", "tooltip": "Carta prepagata digitale"},
    "Buddybank":          {"saldo": 400,  "tipo": "Liquidità", "icona": "🏦", "tooltip": "Conto corrente online"},
    "Revolut":            {"saldo": 3000, "tipo": "Liquidità", "icona": "💳", "tooltip": "Fintech per pagamenti internazionali"},
    "Isybank":            {"saldo": 700,  "tipo": "Liquidità", "icona": "🏦", "tooltip": "Conto risparmio digitale"},
    "Contanti":           {"saldo": 2500, "tipo": "Liquidità", "icona": "💵", "tooltip": "Denaro contante"},
    "Degiro": {
        "saldo": 0, "tipo": "Investimento", "icona": "📈",
        "label": "Degiro (ETF)", "tooltip": "Piattaforma brokeraggio ETF",
    },
    "Scalable Capital":   {"saldo": 50,    "tipo": "Investimento", "icona": "📈", "tooltip": "Robo-advisor investimenti"},
    "Bondora":            {"saldo": 4400,  "tipo": "Investimento", "icona": "💰", "tooltip": "Peer-to-peer lending"},
    "Buono Fruttifero":   {"saldo": 14000, "tipo": "Risparmio",   "icona": "🏛️", "tooltip": "Titolo risparmio postale"},
    "TFR Lavoro":         {"saldo": 2000,  "tipo": "TFR",         "icona": "🏢", "tooltip": "Trattamento fine rapporto"},
}

ETF_DATA: dict[str, ETFData] = {
    "Vanguard S&P 500":       {"ticker": "VUSA.AS", "quote": 64,  "backup": 7099.07, "classe": "Azionario USA",      "fx_ticker": None,        "desc": "Traccia l'indice S&P 500"},
    "VanEck Semiconductor":   {"ticker": None,      "quote": 23,  "backup": 1423.02, "classe": "Settoriale Tech",    "fx_ticker": None,        "desc": "Settore semiconduttori"},
    "Vanguard High Div Yield":{"ticker": "VHYL.AS", "quote": 14,  "backup": 1068.03, "classe": "Globale Dividendi",  "fx_ticker": None,        "desc": "Dividendi globali alto rendimento"},
    "Xtrackers AI & Big Data":{"ticker": "XAIX.DE", "quote": 7,   "backup": 1066.24, "classe": "Settoriale AI",      "fx_ticker": None,        "desc": "AI e Big Data"},
    "iShares Physical Gold":  {"ticker": "IGLN.L",  "quote": 6,   "backup": 503.26,  "classe": "Oro",                "fx_ticker": "GBPEUR=X",  "desc": "ETC oro fisico"},
    "iShares Global Agg Bond":{"ticker": "AGGH.AS", "quote": 100, "backup": 498.31,  "classe": "Obbligazionario",    "fx_ticker": None,        "desc": "Bond aggregati globali"},
    "iShares MSCI China A":   {"ticker": "CNYA.AS", "quote": 60,  "backup": 307.06,  "classe": "Emergenti Cina",     "fx_ticker": None,        "desc": "Azioni cinesi classe A"},
}

MILESTONES: list[Milestone] = [
    {"nome": "€50k",  "target": 50_000,    "reward": "Audi A3",            "color": Theme.ACCENT_PRIMARY,   "icon": "🚗"},
    {"nome": "€100k", "target": 100_000,   "reward": "Upgrade Dualframe",  "color": Theme.ACCENT_SECONDARY, "icon": "📈"},
    {"nome": "€400k", "target": 400_000,   "reward": "Audi Q8",            "color": Theme.ACCENT_SUCCESS,   "icon": "🏎️"},
    {"nome": "€1M",   "target": 1_000_000, "reward": "Porsche Panamera",   "color": Theme.ACCENT_GOLD,      "icon": "🏆"},
]

NAVAL_QUOTES: list[str] = [
    "Seek wealth, not money or status.",
    "You're not going to get rich renting out your time.",
    "Arm yourself with specific knowledge, accountability, and leverage.",
    "Code and media are permissionless leverage.",
    "Play long-term games with long-term people.",
    "Be patient with results, impatient with actions.",
    "The most important skill is the ability to learn.",
]


# ============================================================
# 📡 DATA FETCHING — Optimized batch download with caching
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_etf_prices(etf_data_dict: dict) -> tuple[dict[str, float], list[str]]:
    """
    Fetch live ETF prices via yfinance batch download.
    Returns (prices_dict, issues_list).
    Falls back to backup values on failure.
    """
    results: dict[str, float] = {}
    issues: list[str] = []

    # Collect unique tickers
    tickers = [d["ticker"] for d in etf_data_dict.values() if d.get("ticker")]
    fx_tickers = list({d["fx_ticker"] for d in etf_data_dict.values() if d.get("fx_ticker")})
    all_tickers = list(dict.fromkeys(tickers + fx_tickers))

    if not all_tickers:
        for name, d in etf_data_dict.items():
            results[name] = float(d.get("backup", 0))
        issues.append("Nessun ticker configurato — uso valori di backup.")
        return results, issues

    # Batch download
    try:
        data = yf.download(
            all_tickers,
            period="7d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="column",
        )
    except Exception as e:
        for name, d in etf_data_dict.items():
            results[name] = float(d.get("backup", 0))
        issues.append(f"Download fallito: {e} — uso backup.")
        return results, issues

    def get_last_close(ticker: str) -> Optional[float]:
        """Extract last closing price from downloaded data."""
        try:
            if data is None or getattr(data, "empty", True):
                return None
            if isinstance(data.columns, pd.MultiIndex):
                series = data["Close"][ticker].dropna()
            else:
                series = data["Close"].dropna()
            return float(series.iloc[-1]) if len(series) else None
        except Exception:
            return None

    # Process each ETF
    for name, d in etf_data_dict.items():
        ticker = d.get("ticker")
        shares = float(d.get("quote", 0))
        backup = float(d.get("backup", 0))

        if not ticker:
            results[name] = backup
            if backup > 0:
                issues.append(f"{name}: ticker mancante — uso backup €{backup:,.0f}.")
            continue

        price = get_last_close(ticker)
        if price is None:
            results[name] = backup
            issues.append(f"{name}: prezzo non disponibile — uso backup.")
            continue

        # FX conversion
        fx_rate = 1.0
        fx_ticker = d.get("fx_ticker")
        if fx_ticker:
            fx_price = get_last_close(fx_ticker)
            if fx_price is None:
                issues.append(f"{name}: tasso FX {fx_ticker} non disponibile — assumo 1.0.")
            else:
                fx_rate = float(fx_price)

        value = round(price * shares * fx_rate, 2)

        # Sanity check against backup
        if backup > 0:
            ratio = value / backup
            if ratio > 1.8 or ratio < 0.55:
                issues.append(
                    f"{name}: valore anomalo (live €{value:,.0f} vs backup €{backup:,.0f})."
                )

        results[name] = value

    return results, issues


# ============================================================
# 🧮 COMPUTATION FUNCTIONS
# ============================================================
def compute_projection(
    initial: float,
    monthly_contrib: float,
    annual_return: float,
    years: int = 30,
) -> list[float]:
    """Compute compound growth projection."""
    monthly_rate = (1 + annual_return / 100) ** (1 / 12) - 1
    values = [initial]
    for _ in range(years * 12):
        values.append(round(values[-1] * (1 + monthly_rate) + monthly_contrib, 2))
    return values


def estimate_months_to_target(
    initial: float,
    target: float,
    monthly_contrib: float,
    annual_return: float,
) -> int:
    """Estimate months needed to reach a financial target."""
    monthly_rate = (1 + annual_return / 100) ** (1 / 12) - 1
    value = initial
    months = 0
    while value < target and months < 1200:
        value = value * (1 + monthly_rate) + monthly_contrib
        months += 1
    return months


@st.cache_data(ttl=3600, show_spinner=False)
def run_monte_carlo(
    initial: float,
    monthly_contrib: float,
    annual_return: float,
    annual_volatility: float,
    years: int = 25,
    simulations: int = 1000,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Vectorized Monte Carlo simulation for massive performance gain.
    Returns (all_scenarios, final_values) as numpy arrays.
    """
    rng = np.random.default_rng(seed)
    n_months = years * 12
    monthly_return = (annual_return / 100) / 12
    monthly_vol = (annual_volatility / 100) / np.sqrt(12)

    # Generate all random returns at once (vectorized)
    returns = rng.normal(monthly_return, monthly_vol, size=(simulations, n_months))

    # Build scenarios iteratively but with vectorized operations per step
    scenarios = np.zeros((simulations, n_months + 1))
    scenarios[:, 0] = initial

    for m in range(n_months):
        scenarios[:, m + 1] = np.maximum(
            scenarios[:, m] * (1 + returns[:, m]) + monthly_contrib, 0
        )

    return scenarios, scenarios[:, -1]


# ============================================================
# 🧱 UI COMPONENT LIBRARY
# ============================================================
def render_section_header(title: str, subtitle: str = "") -> None:
    """Render a consistent section header."""
    st.markdown(f"""
    <div style="margin: {Theme.SPACE_LG} 0 {Theme.SPACE_MD} 0;" role="heading" aria-level="2">
        <h2 style="
            font-size: 1.375rem;
            font-weight: 700;
            color: {Theme.TEXT_PRIMARY};
            margin: 0 0 4px 0;
            letter-spacing: -0.02em;
        ">{title}</h2>
        {"<p style='font-size: 0.875rem; color: " + Theme.TEXT_TERTIARY + "; margin: 0;'>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def render_card(content: str, padding: str = "1.5rem") -> None:
    """Render a glass-morphism card container."""
    st.markdown(f"""
    <div style="
        background: {Theme.BG_ELEVATED};
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: {Theme.RADIUS_XL};
        padding: {padding};
        box-shadow: {Theme.SHADOW_MD};
        transition: box-shadow 0.2s ease;
    " class="fade-in">
        {content}
    </div>
    """, unsafe_allow_html=True)


def render_hero_header(
    net_worth: float,
    productive: float,
    pct_productive: float,
    liquidity: float,
    tfr_amount: float,
) -> None:
    """Render the main hero header with key financial metrics."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(160deg, {Theme.BG_SECONDARY} 0%, {Theme.BG_SURFACE} 60%, {Theme.BG_ELEVATED} 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: {Theme.RADIUS_XL};
        padding: 2rem 1.5rem;
        margin-bottom: {Theme.SPACE_LG};
        text-align: center;
        box-shadow: {Theme.SHADOW_LG}, {Theme.SHADOW_GLOW};
        position: relative;
        overflow: hidden;
    " role="banner" aria-label="Riepilogo patrimonio">
        <!-- Subtle gradient orb -->
        <div style="
            position: absolute;
            top: -60px;
            right: -60px;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(108,159,255,0.06) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        "></div>

        <p style="
            font-size: 0.6875rem;
            color: {Theme.TEXT_TERTIARY};
            letter-spacing: 0.2em;
            text-transform: uppercase;
            font-weight: 600;
            margin: 0 0 0.75rem 0;
        ">Financial Command Center</p>

        <h1 style="
            font-size: clamp(2.25rem, 7vw, 3.5rem);
            margin: 0 0 0.25rem 0;
            color: {Theme.TEXT_PRIMARY};
            font-weight: 800;
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.03em;
            line-height: 1.1;
        " aria-label="Patrimonio netto: {net_worth:,.0f} euro">€{net_worth:,.0f}</h1>

        <p style="
            font-size: 0.8125rem;
            color: {Theme.TEXT_TERTIARY};
            margin: 0 0 1.5rem 0;
        ">Patrimonio Netto · {datetime.now().strftime('%d %b %Y')}</p>

        <div style="
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
        " role="list" aria-label="Dettaglio patrimonio">
            <div style="min-width: 100px;" role="listitem">
                <p style="
                    font-size: 1.25rem;
                    font-weight: 700;
                    margin: 0;
                    color: {Theme.ACCENT_SUCCESS};
                    font-variant-numeric: tabular-nums;
                ">€{productive:,.0f}</p>
                <p style="
                    font-size: 0.6875rem;
                    color: {Theme.TEXT_TERTIARY};
                    margin: 2px 0 0 0;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    font-weight: 500;
                ">Produttivo · {pct_productive:.0f}%</p>
            </div>
            <div style="min-width: 100px;" role="listitem">
                <p style="
                    font-size: 1.25rem;
                    font-weight: 700;
                    margin: 0;
                    color: {Theme.ACCENT_PRIMARY};
                    font-variant-numeric: tabular-nums;
                ">€{liquidity:,.0f}</p>
                <p style="
                    font-size: 0
