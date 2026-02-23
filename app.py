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
# 🎨 CSS OTTIMIZZATO (MOBILE FRIENDLY + DARK MODE)
# ============================================
st.markdown("""
<style>
    /* Sfondo e Font */
    .stApp { background-color: #0e1117; font-family: 'Inter', sans-serif; }
    
    /* Nascondi bloatware Streamlit */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Layout Mobile: massimizza spazio */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Tabs Personalizzate */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        margin-bottom: 20px;
        border-bottom: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        color: #888;
        font-weight: 600;
        padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        color: #00d2ff !important;
        border-bottom: 2px solid #00d2ff;
        background-color: rgba(255,255,255,0.03);
    }

    /* Container Controlli Simulatore */
    .sim-controls {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Metriche Header */
    .metric-box {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-val { font-size: 20px; font-weight: 800; color: #fff; }
    .metric-lbl { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }

    /* Nascondi Sidebar vuota */
    section[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

PLOTLY_CONFIG = {'displayModeBar': False, 'scrollZoom': False, 'staticPlot': False, 'responsive': True}

# ============================================
# 💰 DATI PATRIMONIO
# ============================================
patrimonio = {
    "Postepay Evolution": {"saldo": 1000, "tipo": "Liquidità"},
    "Buddybank": {"saldo": 400, "tipo": "Liquidità"},
    "Revolut": {"saldo": 3000, "tipo": "Liquidità"},
    "Isybank": {"saldo": 700, "tipo": "Liquidità"},
    "Contanti": {"saldo": 2500, "tipo": "Liquidità"},
    "Degiro": {"saldo": 0, "tipo": "Investimento", "label": "Degiro (ETF)"}, # Si aggiorna dopo
    "Scalable Capital": {"saldo": 50, "tipo": "Investimento"},
    "Bondora": {"saldo": 4400, "tipo": "Investimento"},
    "Buono Fruttifero": {"saldo": 14000, "tipo": "Risparmio"},
    "TFR Lavoro": {"saldo": 2000, "tipo": "TFR"},
}

etf_data = {
    "Vanguard S&P 500": {"ticker": "VUSA.AS", "quote": 64, "backup": 7099.07, "classe": "Azionario USA"},
    "VanEck Semi": {"ticker": None, "quote": 23, "backup": 1423.02, "classe": "Settoriale Tech"},
    "Vanguard High Div": {"ticker": "VHYL.AS", "quote": 14, "backup": 1068.03, "classe": "Globale Div"},
    "Xtrackers AI": {"ticker": "XAIX.DE", "quote": 7, "backup": 1066.24, "classe": "Settoriale AI"},
    "iShares Gold": {"ticker": "IGLN.L", "quote": 6, "backup": 503.26, "classe": "Oro", "fx_ticker": "GBPEUR=X"},
    "Gl Aggregate Bond": {"ticker": "AGGH.AS", "quote": 100, "backup": 498.31, "classe": "Obbligazionario"},
    "MSCI China A": {"ticker": "CNYA.AS", "quote": 60, "backup": 307.06, "classe": "Emergenti Cina"},
}

# ============================================
# 📡 FETCH PREZZI (Logica Originale)
# ============================================
@st.cache_data(ttl=3600, show_spinner=False)
def get_prices(etf_dict):
    tickers = [d.get("ticker") for d in etf_dict.values() if d.get("ticker")]
    fx_tickers = [d.get("fx_ticker") for d in etf_dict.values() if d.get("fx_ticker")]
    all_t = list(set(tickers + fx_tickers))
    
    res = {}
    try:
        data = yf.download(all_t, period="5d", interval="1d", progress=False, group_by="ticker")
    except:
        data = None

    def get_last(tick):
        try:
            if data is None or data.empty: return None
            # Gestione struttura dati yfinance
            if len(all_t) == 1: s = data["Close"]
            else: s = data[tick]["Close"]
            return float(s.dropna().iloc[-1])
        except: return None

    for nome, d in etf_dict.items():
        base = float(d.get("backup", 0))
        if not d.get("ticker"):
            res[nome] = base
            continue
        
        price = get_last(d["ticker"])
        fx = 1.0
        if d.get("fx_ticker"):
            fx_val = get_last(d["fx_ticker"])
            if fx_val: fx = fx_val
            
        val_calc = round(price * d["quote"] * fx, 2) if price else base
        res[nome] = val_calc
        
    return res

prices_etf = get_prices(etf_data)
tot_etf = sum(prices_etf.values())
patrimonio["Degiro"]["saldo"] = tot_etf

# Calcoli Totali Aggiornati
net_worth = sum(v["saldo"] for v in patrimonio.values())
liquidita = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "Liquidità")
investito = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] in ["Investimento", "Risparmio"])
tfr = sum(v["saldo"] for v in patrimonio.values() if v["tipo"] == "TFR")

# ============================================
# 🖥️ HEADER
# ============================================
st.markdown(f"""
<div style="text-align: center; margin-bottom: 25px;">
    <h1 style="color:white; font-size: 46px; font-weight: 800; margin:0; text-shadow: 0 0 30px rgba(0,210,255,0.2);">€{net_worth:,.0f}</h1>
    <p style="color:#666; font-size: 12px; letter-spacing: 2px;">PATRIMONIO NETTO TOTALE</p>
</div>
""", unsafe_allow_html=True)

# KPI Responsive
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="metric-box" style="border-bottom: 2px solid #00d2ff"><div class="metric-val">€{investito:,.0f}</div><div class="metric-lbl">Investito ({(investito/net_worth*100):.0f}%)</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-box" style="border-bottom: 2px solid #3a7bd5"><div class="metric-val">€{liquidita:,.0f}</div><div class="metric-lbl">Liquidità</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-box" style="border-bottom: 2px solid #ff6b6b"><div class="metric-val">€{tfr:,.0f}</div><div class="metric-lbl">TFR</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# 📑 STRUTTURA A TAB (UI PULITA)
# ============================================
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔎 Asset & ETF", "🔮 Simulatore"])

# --- TAB 1: OVERVIEW COMPOSIZIONE ---
with tab1:
    col_a, col_b = st.columns([1, 1])
    
    # DATAFRAME GENERALE
    df_p = pd.DataFrame([{"Asset": k, "Saldo": v["saldo"], "Tipo": v["tipo"]} for k,v in patrimonio.items()])
    
    with col_a:
        # Pie Chart
        fig_pie = px.pie(df_p, values="Saldo", names="Tipo", hole=0.6, 
                         color_discrete_map={"Liquidità": "#3a7bd5", "Investimento": "#00d2ff", "Risparmio": "#f1c40f", "TFR": "#e74c3c"})
        fig_pie.update_layout(title_text="Distribuzione Macro", title_x=0.5, font_color="white", paper_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(t=40, b=10, l=10, r=10), showlegend=False)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True, config=PLOTLY_CONFIG)
        
    with col_b:
        # Bar Chart
        df_srt = df_p.sort_values("Saldo", ascending=True)
        fig_bar = go.Figure(go.Bar(
            x=df_srt["Saldo"], y=df_srt["Asset"], orientation='h',
            marker_color="#222", marker_line_color="#00d2ff", marker_line_width=1,
            text=[f"€{x:,.0f}" for x in df_srt["Saldo"]], textposition="outside"
        ))
        fig_bar.update_layout(title_text="Dettaglio Conti", title_x=0.5, font_color="white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, margin=dict(t=40, b=10, l=10, r=50), xaxis=dict(showgrid=False, showticklabels=False))
        st.plotly_chart(fig_bar, use_container_width=True, config=PLOTLY_CONFIG)

# --- TAB 2: DETTAGLI ETF & SUNBURST ---
with tab2:
    st.markdown("### 📈 Dettaglio Degiro (ETF)")
    # Tabella e Grafico ETF
    df_etf = pd.DataFrame([{"ETF": k, "Valore": v, "Classe": etf_data[k]["classe"]} for k,v in prices_etf.items()])
    df_etf = df_etf.sort_values("Valore", ascending=True)
    
    fig_etf = px.bar(df_etf, x="Valore", y="ETF", text_auto='.2s', color="Valore", color_continuous_scale="Viridis")
    fig_etf.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=300, margin=dict(t=10,b=10,l=10,r=10), xaxis=dict(showgrid=False))
    st.plotly_chart(fig_etf, use_container_width=True, config=PLOTLY_CONFIG)
    
    st.markdown("---")
    
    # Sunburst (Visualizzazione completa)
    sun_data = []
    for k, v in patrimonio.items():
        if k == "Degiro":
            for en, ev in prices_etf.items():
                sun_data.append({"Cat": "Investimento", "Sub": "Degiro", "Item": en, "Val": ev})
        else:
            sun_data.append({"Cat": v["tipo"], "Sub": v["tipo"], "Item": k, "Val": v["saldo"]})
    
    df_sun = pd.DataFrame(sun_data)
    fig_sun = px.sunburst(df_sun, path=["Cat", "Sub", "Item"], values="Val", color="Cat")
    fig_sun.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", font_color="white", margin=dict(t=10, b=10, l=10, r=10))
    
    with st.expander("🧠 Mappa Mentale Patrimonio (Clicca per aprire)", expanded=False):
        st.plotly_chart(fig_sun, use_container_width=True, config=PLOTLY_CONFIG)


# --- TAB 3: SIMULATORE & FUTURO ---
with tab3:
    st.markdown("### 🎛️ Configurazione Scenario")
    
    # CONTROLLI (Unico posto dove esistono, niente sidebar)
    with st.container():
        st.markdown('<div class="sim-controls">', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        with cc1:
            cm = st.slider("💰 Risparmio Mensile (€)", 100, 3000, 600, 50)
            ra = st.slider("📈 Rendimento Annuo (%)", 2.0, 15.0, 7.0, 0.5)
        with cc2:
            ed = st.slider("🏢 Entrate Extra (€/mese)", 0, 5000, 0, 100)
            vol = st.slider("🎲 Volatilità (%)", 5.0, 30.0, 14.0, 1.0)
        st.markdown('</div>', unsafe_allow_html=True)

    contributo_tot = cm + ed
    
    # 1. PROIEZIONE DETERMINISTICA
    st.markdown("#### 🔮 Proiezione Lineare (30 anni)")
    months = 30 * 12
    r_m = (1 + ra/100)**(1/12) - 1
    proj_vals = [net_worth]
    for _ in range(months):
        proj_vals.append(proj_vals[-1] * (1 + r_m) + contributo_tot)
        
    dates = pd.date_range(start=datetime.now(), periods=len(proj_vals), freq="ME")
    
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(x=dates, y=proj_vals, fill='tozeroy', mode='lines', line=dict(color='#00d2ff', width=3), name='Patrimonio'))
    
    # Milestones Panamera
    milestones = [
        (100_000, "🥈 €100k", "#3a7bd5"),
        (400_000, "🥇 Audi Q8", "#6c5ce7"),
        (1_000_000, "💎 Panamera", "#00ff88")
    ]
    for m_val, m_name, m_col in milestones:
        fig_proj.add_hline(y=m_val, line_dash="dash", line_color=m_col, annotation_text=m_name, annotation_position="top left", annotation_font_color=m_col)
        
    fig_proj.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=350, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(gridcolor="#333", tickprefix="€"), xaxis=dict(showgrid=False))
    st.plotly_chart(fig_proj, use_container_width=True, config=PLOTLY_CONFIG)

    # 2. MONTE CARLO (Originale ripristinato)
    st.markdown("---")
    st.markdown(f"#### 🎲 Monte Carlo (15 anni - {vol}% vol)")
    
    SIMULAZIONI = 200
    ANNI_MC = 15
    scenari = []
    
    np.random.seed(42)
    vol_m = (vol/100) / np.sqrt(12)
    
    for _ in range(SIMULAZIONI):
        vals = [net_worth]
        for _ in range(ANNI_MC * 12):
            # Rendimento casuale normale
            rnd = np.random.normal(r_m, vol_m)
            vals.append(vals[-1] * (1 + rnd) + contributo_tot)
        scenari.append(vals)
    
    fig_mc = go.Figure()
    dates_mc = pd.date_range(start=datetime.now(), periods=ANNI_MC*12 + 1, freq="ME")
    
    # Disegna primi 50 scenari semitrasparenti
    for s in scenari[:50]:
        fig_mc.add_trace(go.Scatter(x=dates_mc, y=s, mode='lines', line=dict(color='rgba(0, 210, 255, 0.1)', width=1), hoverinfo='skip', showlegend=False))
    
    # Mediana
    mediana = np.median(scenari, axis=0)
    fig_mc.add_trace(go.Scatter(x=dates_mc, y=mediana, mode='lines', name='Probabile (Mediana)', line=dict(color='white', width=3)))
    
    fig_mc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=350, margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(gridcolor="#333", tickprefix="€"), xaxis=dict(showgrid=False))
    st.plotly_chart(fig_mc, use_container_width=True, config=PLOTLY_CONFIG)
    
    # Stats finali
    end_vals = [s[-1] for s in scenari]
    prob_1m = sum(1 for x in end_vals if x >= 1_000_000) / SIMULAZIONI * 100
    st.caption(f"Probabilità di superare il Milione in 15 anni: **{prob_1m:.1f}%**")

# ============================================
# 📝 FOOTER NAVAL
# ============================================
st.markdown("---")
quote = "Seek wealth, not money or status. Wealth is assets that earn while you sleep."
st.markdown(f"""
<div style="text-align: center; color: #555; font-size: 13px; font-style: italic; padding-bottom: 30px;">
    "{quote}" — Naval Ravikant
</div>
""", unsafe_allow_html=True)

