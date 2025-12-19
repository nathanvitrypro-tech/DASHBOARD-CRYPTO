import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yfinance as yf
import numpy as np

# =========================================================
# 1. CONFIGURATION ET STYLE
# =========================================================
st.set_page_config(layout="wide", page_title="Crypto Investor Dash", page_icon="💎")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
        color: #e0e0e0;
    }
    
    .stApp {
        background: rgb(10,10,25);
        background: linear-gradient(170deg, rgba(10,10,25,1) 0%, rgba(20,5,40,1) 60%, rgba(0,0,0,1) 100%);
        background-attachment: fixed;
    }
    
    /* Optimisation des marges */
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    
    /* Cards Transparente */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
    }
    
    h1, h2, h3 { color: #ffffff; font-weight: 800; }
    h5 { color: #b8a4ff; font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Metrics Colorés */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        background: linear-gradient(90deg, #00f2c3, #0099ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Radio Button Style */
    div[role="radiogroup"] > label > div:first-child {
        background-color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)

# --- LISTE DES CRYPTOS (Blue Chips) ---
tickers = {
    "BITCOIN": "BTC-EUR", "ETHEREUM": "ETH-EUR", "SOLANA": "SOL-EUR", "BNB": "BNB-EUR",
    "XRP": "XRP-EUR", "CARDANO": "ADA-EUR", "DOGECOIN": "DOGE-EUR", "AVALANCHE": "AVAX-EUR", 
    "TRON": "TRX-EUR", "POLKADOT": "DOT-EUR", "LINK": "LINK-EUR", "POLYGON": "MATIC-EUR",
    "SHIBA INU": "SHIB-EUR", "LITECOIN": "LTC-EUR", "NEAR": "NEAR-EUR",
    "UNISWAP": "UNI-EUR", "STELLAR": "XLM-EUR", "COSMOS": "ATOM-EUR"
}

# =========================================================
# 2. FONCTIONS INTELLIGENTES
# =========================================================
def calculate_indicators(data):
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # SMA (Moyennes Mobiles)
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    
    # MACD (Nouvel indicateur Trend)
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema12 - ema26
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    return data

def calculate_sharpe_ratio(data):
    # Ratio de Sharpe Annualisé (Return / Risk)
    daily_returns = data['Close'].pct_change().dropna()
    mean_return = daily_returns.mean()
    std_dev = daily_returns.std()
    
    if std_dev == 0: return 0
    # 252 jours de trading crypto (365 en réalité mais 252 est le standard finance)
    # Pour crypto on utilise souvent 365, prenons 365 pour être précis
    annualized_sharpe = (mean_return / std_dev) * np.sqrt(365)
    return annualized_sharpe

def get_signal(price, sma50, sma200, rsi, macd, macd_signal):
    score = 0
    # Trend
    if price > sma50: score += 1
    if price > sma200: score += 2 
    # Momentum
    if rsi < 30: score += 1 
    if rsi > 70: score -= 1
    # MACD Cross
    if macd > macd_signal: score += 1
    
    if score >= 4: return "🟢 ACHAT FORT"
    elif score >= 1: return "🟢 ACHAT"
    elif score <= -1: return "🔴 VENTE"
    else: return "⚪ NEUTRE"

@st.cache_data(ttl=3600)
def get_global_data():
    global_data = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="6mo") 
            fi = t.fast_info
            
            if fi.last_price is None: continue 
            
            if len(hist) > 50:
                hist = calculate_indicators(hist)
                last = fi.last_price
                prev = fi.previous_close
                var = ((last - prev) / prev) * 100 
                volatility = hist['Close'].pct_change().std() * 100
                
                # Signal
                last_rsi = hist['RSI'].iloc[-1]
                last_macd = hist['MACD'].iloc[-1]
                last_sig = hist['Signal_Line'].iloc[-1]
                sma50 = hist['SMA50'].iloc[-1]
                sma200 = hist['SMA200'].iloc[-1] if len(hist) > 200 else sma50
                
                signal = get_signal(last, sma50, sma200, last_rsi, last_macd, last_sig)
                
                global_data.append({
                    "Crypto": name, "Symbole": sym, "Prix": last,
                    "Variation %": var, "Volume": fi.last_volume,
                    "Volatilité": volatility, "RSI": last_rsi, "Signal": signal
                })
        except: continue
    return pd.DataFrame(global_data)

@st.cache_data(ttl=3600)
def get_detail_data(symbol, period="1y"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        if hist.empty: return None, None

        hist = calculate_indicators(hist)
        sharpe = calculate_sharpe_ratio(hist)
        
        inf = stock.info
        fi = stock.fast_info
        
        last = fi.last_price if fi.last_price else 0
        high = inf.get('fiftyTwoWeekHigh', last)
        if not high: high = last
            
        info_dict = {
            "last": last, "prev": fi.previous_close,
            "yearHigh": high, "yearLow": inf.get('fiftyTwoWeekLow', 0),
            "rsi": hist['RSI'].iloc[-1],
            "sma200": hist['SMA200'].iloc[-1] if 'SMA200' in hist.columns and not pd.isna(hist['SMA200'].iloc[-1]) else None,
            "sharpe": sharpe
        }
        return hist, info_dict
    except: return None, None

@st.cache_data(ttl=3600)
def get_btc_data(period="1y"):
    return yf.Ticker("BTC-EUR").history(period=period)['Close']

# =========================================================
# 3. INTERFACE
# =========================================================
st.sidebar.title("💎 Crypto Investor")
page = st.sidebar.radio("Navigation", ["Vue Globale 🌍", "Analyse Deep Dive 🔍"])
if st.sidebar.button("Actualiser Data"): st.cache_data.clear(); st.rerun()

# --- COULEURS ---
c_up = "#00f2c3"
c_down = "#ff0055"

if page == "Vue Globale 🌍":
    st.title("🌍 Marché & Opportunités")
    
    with st.spinner("Analyse des tendances..."):
        df = get_global_data()
        
    if not df.empty:
        # KPI ROW
        c1, c2, c3, c4 = st.columns(4)
        best = df.loc[df['Variation %'].idxmax()]
        worst = df.loc[df['Variation %'].idxmin()]
        c1.metric("🚀 Top Perf", best['Crypto'], f"{best['Variation %']:.2f}%")
        c2.metric("💀 Flop Perf", worst['Crypto'], f"{worst['Variation %']:.2f}%")
        c3.metric("🔥 Volatilité Max", df.loc[df['Volatilité'].idxmax()]['Crypto'])
        c4.metric("💰 Volume Leader", df.sort_values('Volume', ascending=False).iloc[0]['Crypto'])
        
        st.divider()
        
        # --- MATRICE OPTIMISÉE ---
        c_mat, c_list = st.columns([2, 1])
        
        with c_mat:
            st.subheader("🎯 Matrice Risque/Récompense")
            st.caption("ℹ️ HAUT = Gains | GAUCHE = Stable | DROITE = Risqué")
            
            # Label propre : seulement les gros volumes
            top_vol_symbols = df.sort_values('Volume', ascending=False).head(8)['Symbole'].tolist()
            df['Label'] = df.apply(lambda x: x['Symbole'] if x['Symbole'] in top_vol_symbols else "", axis=1)

            fig = px.scatter(df, x="Volatilité", y="Variation %", size="Volume", 
                             color="Signal", 
                             text="Label", hover_name="Crypto",
                             color_discrete_map={"🟢 ACHAT": c_up, "🟢 ACHAT FORT": "#00ff00", "🔴 VENTE": c_down, "⚪ NEUTRE": "grey"})
            
            fig.update_traces(textposition='top center', textfont=dict(color='white', size=11))
            fig.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)',
                              xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Risque (Volatilité)"),
                              yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title="Performance 24h"))
            st.plotly_chart(fig, use_container_width=True)

        with c_list:
            st.subheader("🚦 Algo Signaux")
            st.caption("Basé sur RSI + Moyennes Mobiles + MACD")
            st.dataframe(df[['Symbole', 'Prix', 'Signal']].style.applymap(
                lambda v: f'color: {c_up}; font-weight: bold' if "ACHAT" in v else (f'color: {c_down}' if "VENTE" in v else 'color: gray'), 
                subset=['Signal']
            ).format({"Prix": "{:.4f}€"}), height=450, use_container_width=True)

elif page == "Analyse Deep Dive 🔍":
    st.sidebar.markdown("---")
    sel_crypto = st.sidebar.selectbox("Sélectionner l'actif :", list(tickers.keys()))
    sym = tickers[sel_crypto]
    
    # --- NOYAU TEMPOREL (NEW) ---
    st.sidebar.markdown("### ⏱️ Échelle de Temps")
    time_frame = st.sidebar.radio("Zoom Graphique :", ["6 Mois", "1 An", "5 Ans"], index=1)
    period_map = {"6 Mois": "6mo", "1 An": "1y", "5 Ans": "5y"}
    selected_period = period_map[time_frame]
    
    with st.spinner(f"Chargement {time_frame}..."):
        hist, info = get_detail_data(sym, period=selected_period)
    
    if hist is None: st.error("Pas de données").stop()

    # --- HEADER ---
    st.title(f"{sel_crypto} ({sym})")
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    var = ((info['last'] - info['prev'])/info['prev'])*100
    dist_ath = ((info['last'] - info['yearHigh'])/info['yearHigh'])*100
    
    # Metric SHARPE RATIO (NEW)
    sharpe = info['sharpe']
    sharpe_color = "normal" if sharpe > 1 else ("off" if sharpe > 0 else "inverse")
    sharpe_label = "Excellent" if sharpe > 2 else ("Bon" if sharpe > 1 else "Risqué")
    
    col_kpi1.metric("Prix Actuel", f"{info['last']:.4f} €", f"{var:.2f}%")
    col_kpi2.metric("Distance ATH", f"{dist_ath:.1f}%", help="Distance au plus haut annuel")
    col_kpi3.metric("Ratio Sharpe (Risk/Reward)", f"{sharpe:.2f}", sharpe_label, delta_color=sharpe_color, help="> 1 est bon. Indique si le gain vaut le risque pris.")
    col_kpi4.metric("RSI (Momentum)", f"{info['rsi']:.1f}")

    st.divider()

    # --- GRAPHIQUES ---
    c_g1, c_g2 = st.columns([1, 3])

    with c_g1:
        st.subheader("⚡ Force")
        # Jauge redimensionnée
        fig_rsi = go.Figure(go.Indicator(
            mode="gauge+number", value=info['rsi'],
            gauge={'axis': {'range': [0, 100]}, 
                   'bar': {'color': c_down if info['rsi']>70 else (c_up if info['rsi']<30 else "white")},
                   'steps': [{'range': [0, 30], 'color': 'rgba(0,255,136,0.1)'}, {'range': [70, 100], 'color': 'rgba(255,0,85,0.1)'}]}
        ))
        fig_rsi.update_layout(height=250, margin=dict(t=30, b=10, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        st.caption(f"**Analyse sur {time_frame} :**")
        if info['sharpe'] < 0:
            st.warning("⚠️ Attention : Rendement négatif ajusté au risque sur cette période.")
        elif info['sharpe'] > 2:
            st.success("💎 Pépite : Excellent rendement pour le risque pris.")

    with c_g2:
        st.subheader(f"🕯️ Graphique {time_frame} (SMA 50 & 200)")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Prix"))
        
        # Moyennes mobiles
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color="orange", width=1), name="Moyenne 50j"))
        
        # SMA 200 seulement si assez de données
        if info['sma200']:
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], line=dict(color="#00f2c3", width=2), name="Moyenne 200j (Trend Long)"))

        fig.update_layout(height=500, margin=dict(t=20, b=20, l=0, r=0), 
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          xaxis_rangeslider_visible=False, yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                          legend=dict(orientation="h", y=1.05))
        st.plotly_chart(fig, use_container_width=True)
