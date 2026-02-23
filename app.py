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
    page_title="Financial Command Center",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================
# 🎨 CSS AVANZATO (FIX MOBILE & UI)
# ============================================
st.markdown(
    """
<style>
    /* RESET AMBIENTE */
    .stApp { background-color: #050505; }
    
    /* NASCONDI ELEMENTI STANDARD STREAMLIT CHE CAUSANO CLUTTER */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;} /* Nasconde la barra colorata in alto */
    
    /* FIX DOPPIE BARRE SU MOBILE */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 1200px; /* Non allargare troppo su desktop wide */
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { 
        background-color: #111111; 
        border-right: 1px solid #222;
    }

    /* TYPOGRAPHY */
    h1, h2, h3, p, div, span { font-family: 'Inter', sans-serif; }
    
    /* TABS STYLE */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #666;
        font-weight: 600;
        padding: 0 10px; 
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #00d2ff !important;
        border-bottom: 2px solid #00d2ff;
    }

    /* EXPANDER PIÙ PULITO */
    details[data-testid="stExpander"] {
        background-color: #0f0f0f;
        border: 1px solid #222;
        border-radius: 8px;
    }
    
    /* RESPONSIVE FLEXBOX PER L'HEADER */
    .header-container {
        background: linear-gradient(180deg, #121212 0%, #0a0a0a 100%);
        border: 1px solid #222;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        text-align: center;
    }
    .kpi-wrapper {
        display: flex;
        flex-wrap: wrap; /* Fondamentale per mobile: va a capo */
        justify-content: center;
        gap: 20px;
        margin-top: 20px;
    }
    .kpi-box {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 10px 20px;
        min-width: 140px;
        flex: 1; /* Si adatta allo spazio */
    }

    /* MEDIA QUERIES MOBILE SPECIFICHE */
    @media (max-width: 600px) {
        .kpi-wrapper { gap: 10px; }
        .kpi-box { min-width: 45%; padding: 10px 5px; } /* 2 per riga su mobile */
        h1 { font-size: 36px !important; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================
# ⚡ PLOTLY CONFIG OTTIMIZZATA
# ============================================
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
    "staticPlot": False
}

# Altezze dinamiche
H_CHART = 350
MARGINS = dict(t=30, b=10, l=10, r=10)

# ============================================
# 💰 DATI PATRIMONIO
# ============================================
patrimonio = {
    "Postepay Evolution": {"saldo": 1000, "tipo": "Liquidità", "icona": "💳"},
    "Buddybank": {"saldo": 400, "tipo": "Liquidità", "icona": "🏦"},
    "Revolut": {"saldo": 3000, "tipo": "Liquidità", "icona": "💳"},
    "Isybank": {"saldo": 700, "tipo": "Liquidità", "icona": "🏦"},
    "Contanti": {"saldo": 2500, "tipo": "Liquidità", "icona": "💵"},
    "Degiro": {"saldo": 0, "tipo": "Investimento", "icona": "📈", "label": "Degiro (ETF)"},
    "Scalable Capital": {"saldo": 50, "tipo": "Investimento", "icona": "📈"},
    "Bondora": {"saldo": 4400, "tipo": "Investimento", "icona": "💰"},
    "Buono Fruttifero": {"saldo": 14000, "tipo": "Risparmio", "icona": "🏛️"},
    "TFR Lavoro": {"saldo": 2000, "tipo": "TFR", "icona": "🏢"},
}

# ============================================
# 📈 DATI ETF
# ============================================
etf_data = {
    "S&P 500 (VUSA)": {"ticker": "VUSA.AS", "quote": 64, "backup": 7099.07, "classe": "Azionario USA", "fx_ticker": None},
    "Semiconductor": {"ticker": None, "quote": 23, "backup": 1423.02, "classe": "Settoriale Tech", "fx_ticker": None},
    "All-World Div (VHYL)": {"ticker": "VHYL.AS", "quote": 14, "backup": 1068.03, "classe": "Globale Div.", "fx_ticker": None},
    "AI & Big Data": {"ticker": "XAIX.DE", "quote": 7, "backup": 1066.24, "classe": "Settoriale AI", "fx_ticker": None},
    "Phys. Gold": {"ticker": "IGLN.L", "quote": 6, "backup": 503.26, "classe": "Oro", "fx_ticker": "GBPEUR=X"},
    "Global Agg Bond": {"ticker": "AGGH.AS", "quote": 100, "backup": 498.31, "classe": "Obbligazionario", "fx_ticker": None},
    "MSCI China A": {"ticker": "CNYA.AS", "quote": 60, "backup": 307.06, "classe": "Em. Cina", "fx_ticker": None},
}

# ============================================
# 📡 PREZZI LIVE
# ============================================
@st.cache_data(ttl=3600, show_spinner=False)
def scarica_prezzi_live(etf_data_dict):
    risultati = {}
    issues = []
    
    # Crea lista unica di ticker validi per una sola chiamata API
    tickers_to_download = []
    for d in etf_data_dict.values():
        if d.get("ticker"): tickers_to_download.append(d["ticker"])
        if d.get("fx_ticker"): tickers_to_download.append(d["fx_ticker"])
    
    tickers_to_download = list(set(tickers_to_download))

    if not tickers_to_download:
        return {k: float(v["backup"]) for k, v in etf_data_dict.items()}, ["No tickers found"]

    try:
        data = yf.download(tickers_to_download, period="5d", interval="1d", progress=False, group_by="ticker")
    except:
        data = None

    for nome, d in etf_data_dict.items():
        ticker = d.get("ticker")
        valore = float(d.get("backup", 0)) # fallback
        
        if ticker and data is not None and not data.empty:
            try:
                # Gestione struttura dati complessa di yfinance recente
                if len(tickers_to_download) == 1:
                    hist = data["Close"]
                else:
                    hist = data[ticker]["Close"]
                
                price = float(hist.dropna().iloc[-1])
                
                fx = 1.0
                if d.get("fx_ticker"):
                    fx_hist = data[d["fx_ticker"]]["Close"]
                    fx = float(fx_hist.dropna().iloc[-1])
                
                valore = round(price * d["quote"] * fx, 2)
            except Exception:
                issues.append(f"Errore dato per {nome}")

        risultati[nome] = valore

    return risultati, issues

prezzi_etf, issues = scarica_prezzi_live(etf_data)
patrimonio["Degiro"]["saldo"] = sum(prezzi_etf.values())

# ============================================
# 🧮 CALCOLI
# ============================================
net_worth = sum(v["saldo"] for v in patrimonio.values())
liquidita = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Liquidità")
produttivo = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] in ["Investimento", "Risparmio"])
tfr = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "TFR")
pct_produttivo = (produttivo / net_worth * 100) if net_worth else 0

# ============================================
# 💎 HEADER (HTML/CSS OTTIMIZZATO)
# ============================================
st.markdown(f"""
<div class="header-container">
    <p style="color: #666; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px;">Financial Command Center</p>
    <h1 style="color: #fff; font-size: 48px; margin: 0; font-weight: 800; text-shadow: 0 0 20px rgba(0,210,255,0.3);">
        €{net_worth:,.0f}
    </h1>
    <div class="kpi-wrapper">
        <div class="kpi-box" style="border-left: 3px solid #00ff88;">
            <div style="font-size: 18px; color: #eee; font-weight: bold;">€{produttivo:,.0f}</div>
            <div style="font-size: 11px; color: #888;">INVESTITO ({pct_produttivo:.0f}%)</div>
        </div>
        <div class="kpi-box" style="border-left: 3px solid #3a7bd5;">
            <div style="font-size: 18px; color: #eee; font-weight: bold;">€{liquidita:,.0f}</div>
            <div style="font-size: 11px; color: #888;">LIQUIDITÀ</div>
        </div>
        <div class="kpi-box" style="border-left: 3px solid #ff6b6b;">
            <div style="font-size: 18px; color: #eee; font-weight: bold;">€{tfr:,.0f}</div>
            <div style="font-size: 11px; color: #888;">TFR</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# 📑 TAB LAYOUT
# ============================================
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔎 Dettagli Asset", "🔮 Futuro & Simulazioni"])

# ----------------- TAB 1: OVERVIEW -----------------
with tab1:
    col1, col2 = st.columns([1, 1]) # Su mobile Streamlit li impila automaticamente
    
    df_pat = pd.DataFrame([{"Label": v.get("label", k), "Valore": v["saldo"], "Tipo": v["tipo"]} for k, v in patrimonio.items()])
    colors_map = {"Liquidità": "#3a7bd5", "Investimento": "#00d2ff", "Risparmio": "#f1c40f", "TFR": "#e74c3c"}
    
    with col1:
        fig_pie = go.Figure(go.Pie(
            labels=df_pat["Tipo"], values=df_pat["Valore"], 
            hole=0.6,
            marker_colors=[colors_map.get(l, "#444") for l in df_pat["Tipo"]],
            textinfo='percent',
            textfont_size=14
        ))
        fig_pie.update_layout(
            title=dict(text="Distribuzione Macro", x=0.5, font=dict(color="white")),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            margin=MARGINS, height=H_CHART,
            showlegend=True,
            legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)

    with col2:
        df_sorted = df_pat.sort_values("Valore", ascending=True)
        fig_bar = go.Figure(go.Bar(
            x=df_sorted["Valore"], y=df_sorted["Label"], orientation='h',
            marker_color="#333", marker_line_color="#00d2ff", marker_line_width=1,
            text=[f"€{x:,.0f}" for x in df_sorted["Valore"]],
            textposition="auto"
        ))
        fig_bar.update_layout(
            title=dict(text="Saldo per Conto", x=0.5, font=dict(color="white")),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            margin=MARGINS, height=H_CHART,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(size=12))
        )
        st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)

# ----------------- TAB 2: DETTAGLI -----------------
with tab2:
    st.markdown("### 📈 ETF Detail (Degiro)")
    
    df_etf = pd.DataFrame([
        {"Nome": k, "Valore": v, "Classe": etf_data[k]["classe"]} 
        for k, v in prezzi_etf.items()
    ]).sort_values("Valore", ascending=True)
    
    fig_etf = go.Figure(go.Bar(
        x=df_etf["Valore"], y=df_etf["Nome"], orientation='h',
        marker=dict(color=df_etf["Valore"], colorscale="Viridis"),
        text=[f"€{v:,.0f}" for v in df_etf["Valore"]],
        textposition="inside"
    ))
    fig_etf.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
        margin=MARGINS, height=400,
        xaxis=dict(showgrid=False), yaxis=dict(tickfont=dict(size=11))
    )
    st.plotly_chart(fig_etf, use_container_width=True, config=PLOTLY_CONFIG)
    
    st.markdown("---")
    
    # Sunburst per vedere tutto insieme
    full_assets = []
    for k, v in patrimonio.items():
        if k == "Degiro":
            for n, p in prezzi_etf.items():
                full_assets.append({"Genitore": "Investimento", "Figlio": "Degiro", "Item": n, "Valore": p})
        else:
            full_assets.append({"Genitore": v["tipo"], "Figlio": v["tipo"], "Item": k, "Valore": v["saldo"]})
            
    df_sun = pd.DataFrame(full_assets)
    fig_sun = px.sunburst(
        df_sun, path=['Genitore', 'Item'], values='Valore',
        color='Valore', color_continuous_scale='Twilight'
    )
    fig_sun.update_layout(
        margin=dict(t=10, b=10, l=10, r=10), height=350,
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white")
    )
    with st.expander("🧠 Visualizzazione a raggiera (Sunburst)", expanded=False):
        st.plotly_chart(fig_sun, use_container_width=True, config=PLOTLY_CONFIG)

# ----------------- TAB 3: SIMULAZIONI -----------------
with tab3:
    col_sim_1, col_sim_2 = st.columns([1, 2])
    
    with col_sim_1:
        # INPUT SEMPLIFICATI IN UN CONTAINER
        st.markdown("#### 🎛️ Configura Scenario")
        with st.container(border=True):
            cm = st.number_input("Risparmio mensile (€)", value=600, step=50)
            ra = st.number_input("Rendimento Annuo (%)", value=7.0, step=0.5)
            ed = st.number_input("Entrate Extra Dualframe (€/mese)", value=0, step=100)
            anni_sim = 15
            
            tot_mensile = cm + ed
        
        st.info(f"Stai investendo: **€{tot_mensile*12:,.0f}** all'anno")

    with col_sim_2:
        # LOGICA DI PROIEZIONE
        r_mensile = (1 + ra / 100) ** (1 / 12) - 1
        months = anni_sim * 12
        values = [net_worth]
        for _ in range(months):
            values.append(values[-1] * (1 + r_mensile) + tot_mensile)
            
        x_dates = pd.date_range(start=datetime.now(), periods=len(values), freq="ME")
        
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=x_dates, y=values, mode='lines', 
            name='Proiezione', line=dict(color='#00d2ff', width=3),
            fill='tozeroy', fillcolor='rgba(0, 210, 255, 0.1)'
        ))
        
        # TARGET LINES
        targets = [
            (100_000, "100k", "#3a7bd5"),
            (400_000, "Q8 Target", "#6c5ce7"),
            (values[-1], "Previsto", "#00ff88")
        ]
        
        for val, label, color in targets:
            if values[-1] >= val:
                fig_proj.add_hline(y=val, line_dash="dot", line_color=color, annotation_text=label, annotation_font_color=color)

        fig_proj.update_layout(
            title="Proiezione a 15 anni",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            margin=MARGINS, height=400,
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#222", tickprefix="€")
        )
        st.plotly_chart(fig_proj, use_container_width=True, config=PLOTLY_CONFIG)

    # MONITOR NAVAL (MOBILE FRIENDLY)
    st.markdown("---")
    st.caption("“Seek wealth, not money or status.” — Naval Ravikant")
