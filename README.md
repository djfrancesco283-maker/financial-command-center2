# Financial Command Center v2

Dashboard Streamlit personale per monitorare patrimonio, composizione asset e proiezioni finanziarie.

## Requisiti
- Python 3.10+

## Setup rapido
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Avvio
```bash
streamlit run app.py
```

## Cosa include
- Breakdown del patrimonio per conto e categoria.
- Valorizzazione ETF con prezzi live da Yahoo Finance (con fallback ai valori backup).
- Simulatore con contributo mensile, rendimento e volatilità.
- Proiezione a 30 anni e simulazione Monte Carlo (1.000 scenari).

## Note importanti
- La simulazione Monte Carlo è un modello semplificato: usa rendimenti mensili normalmente distribuiti.
- In caso di dati mancanti/non disponibili, l'app usa valori backup e mostra avvisi.
- Non è consulenza finanziaria.
