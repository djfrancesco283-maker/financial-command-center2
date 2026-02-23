# app.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================
# ⚙️ CONFIGURAZIONE PAGINA
# ============================================
st.set_page_config(
    page_title="💰 Financial Command Center",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================
# ⚙️ PREFERENZA UI (un SOLO pannello controlli)
# ============================================
if "use_sidebar_controls" not in st.session_state:
    # Default perfetto per mobile: controlli IN PAGINA, niente sidebar duplicata
    st.session_state.use_sidebar_controls = False

# Toggle in pagina (così da mobile lo vedi sempre)
with st.container():
    c1, c2 = st.columns([1, 2])
    with c1:
        st.session_state.use_sidebar_controls = st.toggle(
            "📌 Controlli in sidebar (desktop)",
            value=st.session_state.use_sidebar_controls,
        )
    with c2:
        st.caption(
            "✅ Mobile: usa i controlli in pagina. ✅ Desktop: attiva la sidebar se preferisci."
        )

use_sidebar_controls = st.session_state.use_sidebar_controls

# ============================================
# 🎨 CSS (mobile-first + NO duplicati + header condizionale)
# ============================================
BASE_CSS = """
<style>
    .stApp { background-color: #0a0a0a; }
    section[data-testid="stSidebar"] { background-color: #1a1a2e; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    h1, h2, h3, p, span, label { color: #ffffff !important; }

    .stMetric label { color: #9aa0a6 !important; }
    .stMetric [data-testid="stMetricValue"] {
        color: #00d2ff !important;
        font-size: 28px !important;
        font-weight: 800 !important;
    }

    .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 2rem !important;
    }

    /* Expander più premium */
    details[data-testid="stExpander"] > summary {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 10px 12px;
    }
    details[data-testid="stExpander"] > summary:hover {
        background: rgba(255,255,255,0.06);
    }

    /* Mobile tweaks */
    @media (max-width: 768px) {
        .block-container { padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
        .stMetric [data-testid="stMetricValue"] { font-size: 24px !important; }
    }
</style>
"""

# Header/toolbar: se NON usi sidebar controls → nascondo tutto (zero barre in alto)
HEADER_HIDE_CSS = """
<style>
header[data-testid="stHeader"] { display: none; }
div[data-testid="stToolbar"] { display: none; }
</style>
"""

# Se usi sidebar controls → tengo header/toolbar (serve hamburger) ma trasparente
HEADER_STEALTH_CSS = """
<style>
header[data-testid="stHeader"]{
  background: rgba(0,0,0,0) !important;
  box-shadow: none !important;
}
div[data-testid="stToolbar"]{
  background: rgba(0,0,0,0) !important;
}
</style>
"""

st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(HEADER_STEALTH_CSS if use_sidebar_controls else HEADER_HIDE_CSS, unsafe_allow_html=True)

# ============================================
# ⚡ PLOTLY CONFIG (pulito su mobile)
# ============================================
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
}

H_SMALL = 360
H_MED = 440
H_BIG = 520

# ============================================
# 💰 DATI PATRIMONIO (100% manuale)
# ============================================
patrimonio = {
    "Postepay Evolution": {"saldo": 1000, "tipo": "Liquidità", "icona": "💳"},
    "Buddybank": {"saldo": 400, "tipo": "Liquidità", "icona": "🏦"},
    "Revolut": {"saldo": 3000, "tipo": "Liquidità", "icona": "💳"},
    "Isybank": {"saldo": 700, "tipo": "Liquidità", "icona": "🏦"},
    "Contanti": {"saldo": 2500, "tipo": "Liquidità", "icona": "💵"},
    "Degiro": {"saldo": 0, "tipo": "Investimento", "icona": "📈", "label": "Degiro (ETF tracciati)"},
    "Scalable Capital": {"saldo": 50, "tipo": "Investimento", "icona": "📈"},
    "Bondora": {"saldo": 4400, "tipo": "Investimento", "icona": "💰"},
    "Buono Fruttifero Postale": {"saldo": 14000, "tipo": "Risparmio", "icona": "🏛️"},
    "TFR Lavoro": {"saldo": 2000, "tipo": "TFR", "icona": "🏢"},
}

# ============================================
# 📈 DATI ETF DEGIRO (100% manuale)
# NOTE:
# - ticker=None => usa backup
# - fx_ticker opzionale (es: GBPEUR=X / USDEUR=X)
# ============================================
etf_data = {
    "Vanguard S&P 500 UCITS ETF": {"ticker": "VUSA.AS", "quote": 64, "backup": 7099.07, "classe": "Azionario USA", "fx_ticker": None},
    "VanEck Semiconductor UCITS ETF": {"ticker": None, "quote": 23, "backup": 1423.02, "classe": "Settoriale Tech", "fx_ticker": None},
    "Vngrd FTSE All-Wld Hgh Div Yld": {"ticker": "VHYL.AS", "quote": 14, "backup": 1068.03, "classe": "Globale Dividendi", "fx_ticker": None},
    "Xtrackers AI & Big Data": {"ticker": "XAIX.DE", "quote": 7, "backup": 1066.24, "classe": "Settoriale AI", "fx_ticker": None},
    "iShares Physical Gold ETC": {"ticker": "IGLN.L", "quote": 6, "backup": 503.26, "classe": "Oro", "fx_ticker": "GBPEUR=X"},
    "iShares Core Gl Aggregate Bond": {"ticker": "AGGH.AS", "quote": 100, "backup": 498.31, "classe": "Obbligazionario", "fx_ticker": None},
    "iShares MSCI China A": {"ticker": "CNYA.AS", "quote": 60, "backup": 307.06, "classe": "Emergenti Cina", "fx_ticker": None},
}

# ============================================
# 📡 PREZZI LIVE (batch download - veloce)
# ============================================
@st.cache_data(ttl=3600, show_spinner=False)
def scarica_prezzi_live(etf_data_dict: dict):
    risultati = {}
    issues = []

    tickers = [d.get("ticker") for d in etf_data_dict.values() if d.get("ticker")]
    fx_tickers = list({d.get("fx_ticker") for d in etf_data_dict.values() if d.get("fx_ticker")})
    all_tickers = list(dict.fromkeys(tickers + fx_tickers))

    if not all_tickers:
        for nome, d in etf_data_dict.items():
            risultati[nome] = float(d.get("backup", 0))
        issues.append("Nessun ticker configurato → uso backup per tutti.")
        return risultati, issues

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
        for nome, d in etf_data_dict.items():
            risultati[nome] = float(d.get("backup", 0))
        issues.append(f"Download Yahoo fallito: {e} → uso backup per tutti.")
        return risultati, issues

    def last_close(ticker: str):
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

    for nome, d in etf_data_dict.items():
        ticker = d.get("ticker")
        quote = float(d.get("quote", 0))
        backup = float(d.get("backup", 0))

        if not ticker:
            risultati[nome] = backup
            issues.append(f"{nome}: ticker mancante → uso backup.")
            continue

        prezzo = last_close(ticker)
        if prezzo is None:
            risultati[nome] = backup
            issues.append(f"{nome}: prezzo non disponibile → uso backup.")
            continue

        fx = 1.0
        fx_ticker = d.get("fx_ticker")
        if fx_ticker:
            fx_rate = last_close(fx_ticker)
            if fx_rate is None:
                issues.append(f"{nome}: FX {fx_ticker} non disponibile → assumo 1.0 (controlla!).")
            else:
                fx = float(fx_rate)

        valore = round(prezzo * quote * fx, 2)

        if backup > 0:
            ratio = valore / backup
            if ratio > 1.8 or ratio < 0.55:
                issues.append(f"{nome}: valore sospetto (live €{valore:,.2f} vs backup €{backup:,.2f}).")

        risultati[nome] = valore

    return risultati, issues


prezzi_etf, issues = scarica_prezzi_live(etf_data)
totale_degiro_etf = sum(prezzi_etf.values())
patrimonio["Degiro"]["saldo"] = totale_degiro_etf

# ============================================
# 🎛️ CONTROLLI (UNA sola posizione)
# ============================================
def render_controlli(ui):
    ui.markdown("## 🎛️ Simulatore")
    ui.markdown("---")

    cm = ui.slider("💰 Contributo mensile (€)", 100, 3000, 600, 50, key="cm")
    ra = ui.slider("📈 Rendimento annuo atteso (%)", 3.0, 15.0, 7.0, 0.5, key="ra")
    ed = ui.slider("🏢 Entrate extra Dualframe (€/mese)", 0, 5000, 0, 100, key="ed")
    va = ui.slider("🎲 Volatilità annua stimata (%)", 5.0, 30.0, 14.0, 0.5, key="va")

    contrib_tot = cm + ed
    ui.markdown("---")
    ui.markdown(f"### 💰 Contributo totale: €{contrib_tot:,.0f}/mese")

    return float(cm), float(ra), float(ed), float(va), float(contrib_tot)

def render_warning(ui):
    if issues:
        with ui.expander("⚠️ Warning dati (prezzi/FX)", expanded=False):
            for msg in issues[:40]:
                ui.warning(msg)

if use_sidebar_controls:
    # Sidebar mode: controlli solo in sidebar, NO pannello in pagina
    with st.sidebar:
        render_warning(st)
        contributo_mensile, rendimento_annuo, entrate_dualframe, volatilita_annua, contributo_totale = render_controlli(st)
else:
    # Mobile-first: controlli solo in pagina, sidebar vuota (zero duplicati)
    render_warning(st)
    with st.expander("🎛️ Simulatore (in pagina)", expanded=True):
        contributo_mensile, rendimento_annuo, entrate_dualframe, volatilita_annua, contributo_totale = render_controlli(st)

# ============================================
# 🧮 CALCOLI BASE
# ============================================
net_worth = sum(v["saldo"] for v in patrimonio.values())
liquidita = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Liquidità")
investimenti = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Investimento")
risparmio = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Risparmio")
tfr = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "TFR")

produttivo = investimenti + risparmio
pct_produttivo = (produttivo / net_worth) * 100 if net_worth > 0 else 0

# ============================================
# 💎 HEADER
# ============================================
st.markdown(
    f"""
<div style="
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    border-radius: 20px;
    padding: 26px;
    margin-bottom: 14px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.30);
">
    <p style="font-size: 13px; color: #9aa0a6; letter-spacing: 3px; margin: 0;">
        FRANCESCO FINANCIAL COMMAND CENTER
    </p>
    <h1 style="
        font-size: clamp(40px, 7vw, 58px);
        margin: 10px 0 4px 0;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5, #00d2ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
    ">€{net_worth:,.0f}</h1>
    <p style="font-size: 15px; color: #c9c9c9; margin: 0;">
        Patrimonio Netto al {datetime.now().strftime('%d/%m/%Y')}
    </p>
    <div style="display: flex; justify-content: center; gap: 32px; margin-top: 16px; flex-wrap: wrap;">
        <div>
            <p style="font-size: 22px; margin: 0; color: #00ff88;">€{produttivo:,.0f}</p>
            <p style="font-size: 11px; color: #9aa0a6;">💰 PRODUTTIVO ({pct_produttivo:.0f}%)</p>
        </div>
        <div>
            <p style="font-size: 22px; margin: 0; color: #ffaa00;">€{liquidita:,.0f}</p>
            <p style="font-size: 11px; color: #9aa0a6;">💧 LIQUIDITÀ</p>
        </div>
        <div>
            <p style="font-size: 22px; margin: 0; color: #ff6b6b;">€{tfr:,.0f}</p>
            <p style="font-size: 11px; color: #9aa0a6;">🏢 TFR</p>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================
# 📊 RIGA 1: Torta + Barre
# ============================================
colors_map = {
    "Liquidità": "#3498db",
    "Investimento": "#2ecc71",
    "Risparmio": "#f1c40f",
    "TFR": "#e74c3c",
}

df_pat = pd.DataFrame(
    [{"Conto": v.get("label", k), "Saldo": float(v["saldo"]), "Tipo": v["tipo"]} for k, v in patrimonio.items()]
)

col1, col2 = st.columns(2)

with col1:
    colors = [colors_map.get(t, "#95a5a6") for t in df_pat["Tipo"]]
    fig_torta = go.Figure(
        data=[go.Pie(
            labels=df_pat["Conto"],
            values=df_pat["Saldo"],
            hole=0.58,
            marker=dict(colors=colors, line=dict(color="#121212", width=2)),
            textinfo="label+percent",
            textfont=dict(size=11, color="white"),
        )]
    )
    fig_torta.update_layout(
        title=dict(text="🍩 Distribuzione Patrimonio", font=dict(size=18, color="white"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=H_SMALL,
        margin=dict(t=50, b=20, l=10, r=10),
        annotations=[dict(text=f"€{net_worth:,.0f}", x=0.5, y=0.5, font_size=22, font_color="#00d2ff", showarrow=False)],
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center", font=dict(size=10)),
    )
    st.plotly_chart(fig_torta, use_container_width=True, config=PLOTLY_CONFIG)

with col2:
    df_cat = df_pat.groupby("Tipo")["Saldo"].sum().reset_index().sort_values("Saldo", ascending=True)
    fig_bar = go.Figure(
        data=[go.Bar(
            x=df_cat["Saldo"],
            y=df_cat["Tipo"],
            orientation="h",
            marker=dict(color=[colors_map.get(c, "#95a5a6") for c in df_cat["Tipo"]]),
            text=[f"€{v:,.0f}" for v in df_cat["Saldo"]],
            textposition="outside",
            textfont=dict(color="white", size=13),
        )]
    )
    fig_bar.update_layout(
        title=dict(text="📊 Patrimonio per Categoria", font=dict(size=18, color="white"), x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=H_SMALL,
        margin=dict(t=50, b=20, l=10, r=30),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(tickfont=dict(size=13, color="#ddd")),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)

# ============================================
# 📈 ETF
# ============================================
st.markdown("---")

df_etf = pd.DataFrame(
    [{"ETF": nome, "Valore": float(valore), "Classe": etf_data[nome]["classe"]} for nome, valore in prezzi_etf.items()]
)
tot_etf = float(df_etf["Valore"].sum()) if len(df_etf) else 0.0
df_etf["Peso %"] = (df_etf["Valore"] / tot_etf * 100).round(1) if tot_etf > 0 else 0
df_etf = df_etf.sort_values("Valore", ascending=True)

fig_etf = go.Figure(
    data=[go.Bar(
        x=df_etf["Valore"],
        y=df_etf["ETF"],
        orientation="h",
        marker=dict(color=df_etf["Valore"], colorscale="Viridis"),
        text=[f"€{v:,.0f} ({p}%)" for v, p in zip(df_etf["Valore"], df_etf["Peso %"])],
        textposition="outside",
        textfont=dict(color="white", size=12),
    )]
)
fig_etf.update_layout(
    title=dict(text=f"📈 Degiro — ETF tracciati (Totale: €{totale_degiro_etf:,.0f})", font=dict(size=18, color="white"), x=0.5),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=H_MED,
    margin=dict(t=60, b=20, l=10, r=120),
    xaxis=dict(showgrid=False, showticklabels=False),
    yaxis=dict(tickfont=dict(size=11, color="#ddd")),
)
st.plotly_chart(fig_etf, use_container_width=True, config=PLOTLY_CONFIG)

# ============================================
# 🏎️ ROAD TO PANAMERA
# ============================================
st.markdown("---")

milestones = [
    {"nome": "🥉 €50k", "target": 50_000, "reward": "Audi A3 🚗", "color": "#00d2ff"},
    {"nome": "🥈 €100k", "target": 100_000, "reward": "Upgrade Dualframe 📈", "color": "#3a7bd5"},
    {"nome": "🥇 €400k", "target": 400_000, "reward": "Audi Q8 🏎️", "color": "#6c5ce7"},
    {"nome": "💎 €1M", "target": 1_000_000, "reward": "Porsche Panamera 🏆", "color": "#00ff88"},
]

def stima_mesi_target(patrimonio_iniziale, target, contributo_mensile, rendimento_annuo):
    r_mensile = (1 + rendimento_annuo / 100) ** (1 / 12) - 1
    valore = float(patrimonio_iniziale)
    mesi = 0
    while valore < target and mesi < 1200:
        valore = valore * (1 + r_mensile) + contributo_mensile
        mesi += 1
    return mesi

st.markdown('<h2 style="text-align: center; color: #00d2ff; margin-top: 10px;">🏎️ Road to Panamera</h2>', unsafe_allow_html=True)

for m in milestones:
    pct = min((net_worth / m["target"]) * 100, 100) if m["target"] > 0 else 0
    mesi = stima_mesi_target(net_worth, m["target"], contributo_totale, rendimento_annuo)
    data_stima = (pd.Timestamp.today().normalize() + pd.DateOffset(months=int(mesi))).strftime("%B %Y")
    anni = mesi // 12
    mesi_rest = mesi % 12

    st.markdown(
        f"""
    <div style="margin: 14px 0;">
        <div style="display: flex; justify-content: space-between; gap: 12px;">
            <span style="font-size: 16px; color: white;">{m['nome']}</span>
            <span style="font-size: 13px; color: #9aa0a6;">{m['reward']}</span>
        </div>
        <div style="background: #232323; border-radius: 12px; height: 26px; margin: 6px 0; overflow: hidden;">
            <div style="
                background: linear-gradient(90deg, {m['color']}, {m['color']}88);
                height: 100%;
                width: {pct}%;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 13px;
                color: white;
            ">{pct:.1f}%</div>
        </div>
        <p style="font-size: 12px; color: #b9b9b9; margin: 0;">
            €{net_worth:,.0f} / €{m['target']:,.0f} — ⏱️ ~{anni}a {mesi_rest}m → {data_stima}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ============================================
# 🔮 PROIEZIONE
# ============================================
st.markdown("---")
st.markdown('<h2 style="text-align: center; color: #00d2ff; margin-top: 6px;">🔮 Proiezione Patrimonio</h2>', unsafe_allow_html=True)

def calcola_proiezione(patrimonio_iniziale, contributo_mensile, rendimento_annuo, anni=30):
    r_mensile = (1 + rendimento_annuo / 100) ** (1 / 12) - 1
    valori = [float(patrimonio_iniziale)]
    for _ in range(anni * 12):
        nuovo = valori[-1] * (1 + r_mensile) + contributo_mensile
        valori.append(round(nuovo, 2))
    return valori

proiezione = calcola_proiezione(net_worth, contributo_totale, rendimento_annuo, anni=30)
anni_lista = pd.date_range(start=pd.Timestamp.today().normalize(), periods=len(proiezione), freq="MS").to_pydatetime()

fig_proj = go.Figure()
fig_proj.add_trace(
    go.Scatter(
        x=anni_lista,
        y=proiezione,
        mode="lines",
        name="Proiezione",
        line=dict(color="#00d2ff", width=3),
        fill="tozeroy",
        fillcolor="rgba(0, 210, 255, 0.10)",
        hovertemplate="<b>%{x|%B %Y}</b><br>€%{y:,.0f}<extra></extra>",
    )
)
for m in milestones:
    fig_proj.add_hline(
        y=m["target"],
        line_dash="dash",
        line_color=m["color"],
        opacity=0.5,
        annotation_text=f"{m['nome']} — {m['reward']}",
        annotation_font_color=m["color"],
        annotation_font_size=11,
    )
fig_proj.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=H_MED,
    margin=dict(t=20, b=20, l=10, r=10),
    xaxis=dict(showgrid=False, tickfont=dict(color="#9aa0a6")),
    yaxis=dict(showgrid=True, gridcolor="#222", tickfont=dict(color="#9aa0a6"), tickprefix="€"),
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
)
st.plotly_chart(fig_proj, use_container_width=True, config=PLOTLY_CONFIG)

# ============================================
# 🎲 MONTE CARLO
# ============================================
st.markdown("---")
st.markdown('<h2 style="text-align: center; color: #00d2ff;">🎲 Simulazione Monte Carlo (1.000 scenari)</h2>', unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def monte_carlo(patrimonio_iniziale, contributo_mensile, rendimento_annuo, volatilita_annua, anni=25, simulazioni=1000, seed=42):
    rng = np.random.default_rng(seed)
    r_m = (1 + rendimento_annuo / 100) ** (1 / 12) - 1
    vol_m = (volatilita_annua / 100) / np.sqrt(12)

    tutti_scenari = []
    valori_finali = []

    for _ in range(simulazioni):
        valori = [float(patrimonio_iniziale)]
        for _m in range(anni * 12):
            rendimento = rng.normal(r_m, vol_m)
            nuovo = valori[-1] * (1 + rendimento) + contributo_mensile
            valori.append(max(nuovo, 0))
        tutti_scenari.append(valori)
        valori_finali.append(valori[-1])

    return tutti_scenari, valori_finali

scenari, valori_finali = monte_carlo(net_worth, contributo_totale, rendimento_annuo, volatilita_annua)
arr = np.array(valori_finali) if len(valori_finali) else np.array([0.0])

percentili = np.percentile(arr, [10, 25, 50, 75, 90])
prob_milione = (arr >= 1_000_000).mean() * 100
prob_500k = (arr >= 500_000).mean() * 100
prob_100k = (arr >= 100_000).mean() * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("🎯 Prob. €100k", f"{prob_100k:.0f}%")
c2.metric("🎯 Prob. €500k", f"{prob_500k:.0f}%")
c3.metric("🎯 Prob. €1M", f"{prob_milione:.0f}%")
c4.metric("📊 Mediana 25 anni", f"€{percentili[2]:,.0f}")

fig_mc = go.Figure()
mesi_mc = len(scenari[0]) if scenari else 0
anni_mc = pd.date_range(start=pd.Timestamp.today().normalize(), periods=mesi_mc, freq="MS").to_pydatetime()

for i in range(min(80, len(scenari))):
    fig_mc.add_trace(
        go.Scatter(
            x=anni_mc,
            y=scenari[i],
            mode="lines",
            line=dict(color="rgba(0, 210, 255, 0.06)", width=1),
            showlegend=False,
            hoverinfo="skip",
        )
    )

scenari_array = np.array(scenari) if scenari else np.array([])
if scenari_array.size:
    for p, nome, colore in [(10, "Pessimista (10°)", "#e74c3c"), (50, "Mediana", "#00d2ff"), (90, "Ottimista (90°)", "#00ff88")]:
        percentile = np.percentile(scenari_array, p, axis=0)
        fig_mc.add_trace(
            go.Scatter(
                x=anni_mc,
                y=percentile,
                mode="lines",
                name=nome,
                line=dict(color=colore, width=2),
                hovertemplate=f"<b>{nome}</b><br>%{{x|%B %Y}}<br>€%{{y:,.0f}}<extra></extra>",
            )
        )

fig_mc.add_hline(
    y=1_000_000,
    line_dash="dash",
    line_color="#FFD700",
    opacity=0.5,
    annotation_text="💎 €1M — Porsche Panamera",
    annotation_font_color="#FFD700",
)

fig_mc.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=H_BIG,
    margin=dict(t=10, b=20, l=10, r=10),
    xaxis=dict(showgrid=False, tickfont=dict(color="#9aa0a6")),
    yaxis=dict(showgrid=True, gridcolor="#222", tickfont=dict(color="#9aa0a6"), tickprefix="€"),
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
)
st.plotly_chart(fig_mc, use_container_width=True, config=PLOTLY_CONFIG)

# ============================================
# 🧠 SUNBURST
# ============================================
st.markdown("---")

asset_data = []
for nome, valore in prezzi_etf.items():
    asset_data.append({"Fonte": "Degiro (ETF tracciati)", "Asset": etf_data[nome]["classe"], "Valore": float(valore)})
for conto, dati in patrimonio.items():
    if conto.lower() == "degiro":
        continue
    fonte = dati["tipo"]
    asset_data.append({"Fonte": fonte, "Asset": conto, "Valore": float(dati["saldo"])})

df_sun = pd.DataFrame(asset_data)

fig_sun = px.sunburst(df_sun, path=["Fonte", "Asset"], values="Valore", color="Valore", color_continuous_scale="Viridis")
fig_sun.update_layout(
    title=dict(text="🧠 Mappa Completa Patrimonio", font=dict(size=18, color="white"), x=0.5),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    height=H_MED,
    margin=dict(t=60, b=10, l=10, r=10),
)
fig_sun.update_traces(
    textinfo="label+percent parent",
    hovertemplate="<b>%{label}</b><br>€%{value:,.0f}<br>%{percentRoot:.1%} del totale<extra></extra>",
)

with st.expander("🧠 Mappa Completa Patrimonio (Sunburst)", expanded=False):
    st.plotly_chart(fig_sun, use_container_width=True, config=PLOTLY_CONFIG)

# ============================================
# 📝 FOOTER
# ============================================
st.markdown("---")
frasi_naval = [
    "Seek wealth, not money or status.",
    "You're not going to get rich renting out your time.",
    "Arm yourself with specific knowledge, accountability, and leverage.",
    "Code and media are permissionless leverage.",
    "Play long-term games with long-term people.",
    "Be patient with results, impatient with actions.",
    "The most important skill is the ability to learn.",
]
frase = frasi_naval[datetime.now().day % len(frasi_naval)]
st.markdown(
    f"""
<div style="text-align: center; padding: 18px; color: #666;">
    <p style="font-style: italic; font-size: 14px; margin: 0 0 6px 0;">"{frase}"</p>
    <p style="font-size: 12px; margin: 0 0 10px 0;">— Naval Ravikant</p>
    <p style="font-size: 11px; margin: 0;">Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>
""",
    unsafe_allow_html=True,
)
