import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yfinance as yf
import numpy as np

# =========================================================
# 1. CONFIGURATION ET STYLE (MODE TRADER PRO)
# =========================================================
st.set_page_config(layout="wide", page_title="Crypto Pro Dashboard", page_icon="⚡")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
        color: #e0e0e0;
    }

    /* FOND DEGRADÉ SOMBRE */
    .stApp {
        background: rgb(10,10,25);
        background: linear-gradient(170deg, rgba(10,10,25,1) 0%, rgba(20,5,40,1) 60%, rgba(0,0,0,1) 100%);
        background-attachment: fixed;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 15, 30, 0.9);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
    }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }
    
    /* CARTES */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    
    h1, h2, h3 { color: #ffffff; font-weight: 800; text-shadow: 0 0 15px rgba(100, 50, 255, 0.4); }
    h5 { color: #b8a4ff; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem; }
    
    /* METRICS */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(90deg, #00f2c3, #0099ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stMetricLabel"] { color: #888; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# --- LISTE DES CRYPTOS ---
tickers = {
    "BITCOIN": "BTC-EUR", "ETHEREUM": "ETH-EUR", "SOLANA": "SOL-EUR", "BNB": "BNB-EUR",
    "XRP": "XRP-EUR", "CARDANO": "ADA-EUR", "DOGECOIN": "DOGE-EUR", "AVALANCHE": "AVAX-EUR", 
    "TRON": "TRX-EUR", "POLKADOT": "DOT-EUR", "LINK": "LINK-EUR", "POLYGON": "MATIC-EUR",
    "SHIBA INU": "SHIB-EUR", "LITECOIN": "LTC-EUR", "NEAR": "NEAR-EUR", "PEPE": "PEPE-EUR",
    "FANTOM": "FTM-EUR", "RENDER": "RNDR-EUR"
}

# =========================================================
# 2. CALCULS TECHNIQUES (RSI, VOLATILITÉ)
# =========================================================
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=3600)
def get_global_data():
    global_data = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="1mo") 
            fi = t.fast_info
            
            if len(hist) > 0:
                last = fi.last_price
                prev = fi.previous_close
                var = ((last - prev) / prev) * 100 if prev else 0
                volatility = hist['Close'].pct_change().std() * 100
                
                global_data.append({
                    "Crypto": name, "Symbole": sym, "Prix": last,
                    "Variation %": var, "Volume": fi.last_volume,
                    "Volatilité": volatility
                })
        except: continue
    return pd.DataFrame(global_data)

@st.cache_data(ttl=3600)
def get_detail_data(symbol, period="1y"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        hist['RSI'] = calculate_rsi(hist['Close'])
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        
        inf = stock.info
        fi = stock.fast_info
        
        year_high = inf.get('fiftyTwoWeekHigh', fi.last_price)
        current = fi.last_price
        drawdown = ((current - year_high) / year_high) * 100 if year_high and year_high > 0 else 0

        info_dict = {
            "last": current, 
            "prev": fi.previous_close,
            "yearLow": inf.get('fiftyTwoWeekLow', 0),
            "yearHigh": year_high,
            "drawdown": drawdown,
            "rsi": hist['RSI'].iloc[-1] if len(hist) > 14 else 50
        }
        return hist, info_dict
    except: return None, None

@st.cache_data(ttl=3600)
def get_historical_data(symbol, period="1y"):
    try: return yf.Ticker(symbol).history(period=period)['Close']
    except: return None

# =========================================================
# 3. NAVIGATION
# =========================================================
st.sidebar.title("⚡ Crypto Pro")
page = st.sidebar.radio("Menu :", ["Vue Marché 🌍", "Analyse Technique 🔍"])

if st.sidebar.button("🔄 Actualiser"):
    st.cache_data.clear()
    st.rerun()

# COULEURS
c_neon = "#00f2c3"
c_purple = "#8e44ad"
c_danger = "#ff0055"
c_warn = "#f39c12"

# =========================================================
# PAGE 1 : VUE MARCHÉ (GLOBALE)
# =========================================================
if page == "Vue Marché 🌍":
    st.title("🌍 Radar du Marché Crypto")
    
    with st.spinner("Analyse de la volatilité..."):
        df_global = get_global_data()
        
    best = df_global.loc[df_global['Variation %'].idxmax()]
    volatil = df_global.loc[df_global['Volatilité'].idxmax()]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Top Perf 24h 🚀", f"{best['Crypto']}", f"{best['Variation %']:.2f} %")
    col2.metric("Plus Volatile ⚡", f"{volatil['Crypto']}", f"Risk: {volatil['Volatilité']:.1f}")
    col3.metric("Volume Leader 📊", df_global.sort_values('Volume', ascending=False).iloc[0]['Crypto'])
    
    st.divider()

    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.subheader("📊 Top Liquidité (Volume 24h)")
        df_vol = df_global.sort_values(by="Volume", ascending=False).head(10)
        fig_vol = px.bar(df_vol, x='Volume', y='Crypto', orientation='h', 
                         color='Volume', color_continuous_scale=['#2c3e50', c_neon])
        fig_vol.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                              xaxis=dict(showgrid=False), yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig_vol, use_container_width=True)

    with c_right:
        st.subheader("🎯 Matrice Risque/Gain")
        st.caption("ℹ️ HAUT = Ça monte | DROITE = Risqué (Volatile)")
        
        fig_scatter = px.scatter(
            df_global, 
            x="Volatilité", 
            y="Variation %", 
            color="Variation %",
            size="Volume", 
            text="Symbole", 
            color_continuous_scale="RdYlGn",
            hover_name="Crypto",
            hover_data={"Volatilité": ":.2f", "Variation %": ":.2f%", "Volume": ":,.0f", "Symbole": False}
        )
        
        fig_scatter.update_traces(
            textposition='top center', 
            marker=dict(line=dict(width=1, color='white'), opacity=0.9),
            textfont=dict(color='white', size=11)
        )
        
        fig_scatter.update_layout(
            height=460, 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(255,255,255,0.05)', 
            xaxis_title="RISQUE (Volatilité mensuelle)", 
            yaxis_title="PERFORMANCE (24h)",
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', zeroline=False)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()
    
    st.subheader("📋 Tableau de Bord (Prix & Volume)")
    try:
        st.dataframe(df_global[['Crypto', 'Prix', 'Variation %', 'Volume', 'Volatilité']].style.format(
            {"Prix": "{:.4f} €", "Variation %": "{:+.2f} %", "Volume": "{:,.0f}", "Volatilité": "{:.1f}"}
        ).background_gradient(subset=["Variation %"], cmap="RdYlGn", vmin=-5, vmax=5), use_container_width=True)
    except:
        st.dataframe(df_global[['Crypto', 'Prix', 'Variation %', 'Volume', 'Volatilité']], use_container_width=True)


# =========================================================
# PAGE 2 : ANALYSE TECHNIQUE (DÉTAILLÉE)
# =========================================================
elif page == "Analyse Technique 🔍":
    
    st.sidebar.markdown("---")
    selected_name = st.sidebar.selectbox("Crypto :", list(tickers.keys()))
    symbol = tickers[selected_name]

    st.sidebar.markdown("---")
    period = st.sidebar.radio("Zoom :", ["3 Mois", "6 Mois", "1 An"], index=1)
    p_map = {"3 Mois": "3mo", "6 Mois": "6mo", "1 An": "1y"}
    
    with st.spinner("Calcul des indicateurs..."):
        hist, info = get_detail_data(symbol, period=p_map[period])
        btc_hist = get_historical_data("BTC-EUR", period=p_map[period])

    # --- CORRECTION ICI (BUG FIX) ---
    if hist is None:
        st.error("Erreur de récupération des données.")
        st.stop() # On utilise st.stop() sur une nouvelle ligne
    # --------------------------------

    def plot_rsi_gauge(rsi_val):
        color = c_danger if rsi_val > 70 else (c_neon if rsi_val < 30 else "#ffffff")
        status = "SURACHAT" if rsi_val > 70 else ("SURVENTE" if rsi_val < 30 else "Neutre")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = rsi_val,
            title = {'text': f"RSI (Momentum)<br><span style='font-size:0.6em;color:{color}'>{status}</span>"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': color},
                     'steps': [{'range': [0, 30], 'color': 'rgba(0,255,136,0.2)'},
                               {'range': [70, 100], 'color': 'rgba(255,0,85,0.2)'}],
                     'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': rsi_val}}
        ))
        fig.update_layout(height=200, margin=dict(t=40, b=10, l=30, r=30), paper_bgcolor='rgba(0,0,0,0)')
        return fig

    def plot_pro_chart(df):
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Prix'))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color=c_warn, width=2), name='Moyenne 50j'))
        
        fig.update_layout(height=350, margin=dict(t=10, b=10, l=0, r=0), 
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          xaxis=dict(showgrid=False, rangeslider=dict(visible=False)), 
                          yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                          legend=dict(orientation="h", y=1, x=0))
        return fig
    
    def plot_drawdown(current, high, low):
        dd = ((current - high) / high) * 100
        fig = go.Figure(go.Indicator(
            mode = "number", value = dd, number = {'suffix': "%", 'font': {'color': c_danger if dd < -20 else "white"}},
            title = {"text": "Distance du Sommet (ATH 1 an)"}
        ))
        fig.update_layout(height=150, margin=dict(t=30, b=0), paper_bgcolor='rgba(0,0,0,0)')
        return fig

    st.title(f"🔍 Analyse : {selected_name}")

    col_L, col_M, col_R = st.columns([1, 1.5, 1.5], gap="medium")

    with col_L:
        st.write("##### ⚡ Momentum (RSI)")
        st.caption("ℹ️ >70: Surchauffe (Attention) | <30: Opportunité")
        st.plotly_chart(plot_rsi_gauge(info['rsi']), use_container_width=True)
        
        if info['rsi'] > 70:
            st.warning("⚠️ Zone de Surchauffe")
        elif info['rsi'] < 30:
            st.success("✅ Zone d'Opportunité")
        else:
            st.info("🔹 Zone Neutre")
            
        st.divider()
        
        st.write("##### 📉 Distance du Sommet")
        st.caption("ℹ️ % de chute depuis le plus haut annuel")
        st.plotly_chart(plot_drawdown(info['last'], info['yearHigh'], info['yearLow']), use_container_width=True)
        st.caption(f"Sommet 1 an : **{info['yearHigh']:.2f}€**")

    with col_M:
        st.write("##### 🎯 Prix & Tendance")
        k1, k2 = st.columns(2)
        var = ((info['last']-info['prev'])/info['prev'])*100
        k1.metric("Prix Actuel", f"{info['last']:.4f}€")
        k2.metric("24h", f"{var:+.2f}%", delta=f"{var:+.2f}%")
        
        st.write("##### 📈 Comparaison vs Bitcoin")
        if btc_hist is not None:
            norm_crypto = (hist['Close'] / hist['Close'].iloc[0]) * 100
            norm_btc = (btc_hist / btc_hist.iloc[0]) * 100
            
            fig_cmp = go.Figure()
            fig_cmp.add_trace(go.Scatter(x=hist.index, y=norm_crypto, name=selected_name, line=dict(color=c_neon)))
            fig_cmp.add_trace(go.Scatter(x=hist.index, y=norm_btc, name="Bitcoin", line=dict(color="orange", dash='dot')))
            fig_cmp.update_layout(height=250, margin=dict(t=10, b=10, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  yaxis=dict(showgrid=False), xaxis=dict(showgrid=False), showlegend=True, legend=dict(orientation='h'))
            st.plotly_chart(fig_cmp, use_container_width=True)

    with col_R:
        st.write("##### 🕯️ Graphique Technique (SMA 50)")
        st.plotly_chart(plot_pro_chart(hist), use_container_width=True)
        
        st.caption(f"Plus bas an: {info['yearLow']:.2f}€ | Plus haut an: {info['yearHigh']:.2f}€")
