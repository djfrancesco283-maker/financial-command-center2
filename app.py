# app.py — Financial Command Center v2.0
# Production-ready, mobile-first, WCAG AA compliant

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
@@ -572,61 +571,61 @@ st.markdown(
)
st.caption("Crescita stimata a 30 anni con contributi regolari e rendimento composto.")

proiezione = compute_projection(net_worth, contrib_totale, rendimento, years=30)
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
    **make_layout(
        height=CHART_MD,
        margin=dict(t=24, b=24, l=12, r=12),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT3, size=11)),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color=TEXT3, size=11),
            tickprefix="€",
        ),
    )
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
@@ -657,61 +656,61 @@ fig_mc.add_trace(go.Scatter(
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
    **make_layout(
        height=CHART_LG,
        margin=dict(t=24, b=24, l=12, r=12),
        xaxis=dict(showgrid=False, tickfont=dict(color=TEXT3, size=11)),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color=TEXT3, size=11),
            tickprefix="€",
        ),
    )
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
@@ -731,64 +730,63 @@ fig_sun.update_layout(
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
        **make_layout(
            height=CHART_SM,
            margin=dict(t=24, b=24, l=12, r=12),
            title=dict(text="Distribuzione valori a 25 anni", font=dict(size=14, color=TEXT2), x=0.5),
            xaxis=dict(showgrid=False, tickfont=dict(color=TEXT3, size=11), tickprefix="€"),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(255,255,255,0.04)",
                tickfont=dict(color=TEXT3, size=11),
                title=dict(text="Scenari", font=dict(size=11, color=TEXT3)),
            ),
            bargap=0.05,
        )
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
