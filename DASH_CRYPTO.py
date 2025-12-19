import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yfinance as yf
import numpy as np

# =========================================================
# 1. CONFIGURATION ET STYLE (MODE CRYPTO)
# =========================================================
st.set_page_config(layout="wide", page_title="Crypto Dashboard", page_icon="🪙")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;800&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
        color: #e0e0e0;
    }

    /* FOND DEGRADÉ SOMBRE (VIOLET/NOIR) */
    .stApp {
        background: rgb(5,5,20);
        background: linear-gradient(160deg, rgba(5,5,20,1) 0%, rgba(20,0,40,1) 50%, rgba(0,0,0,1) 100%);
        background-attachment: fixed;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: rgba(20, 0, 40, 0.8);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }

    /* CARTES */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px);
        margin-bottom: 20px;
    }

    h1, h2, h3 { color: #ffffff; font-weight: 800; text-shadow: 0 0 10px rgba(150, 0, 255, 0.5); }
    h5 { color: #d6b4fc; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; font-size: 0.85rem; }

    /* CHIFFRES NEON (VIOLET/ORANGE) */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(45deg, #f39c12, #8e44ad);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stMetricLabel"] { color: #b0b0b0; font-size: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- LISTE DES CRYPTOS (EN EUR) ---
tickers = {
    "BITCOIN": "BTC-EUR",
    "ETHEREUM": "ETH-EUR",
    "SOLANA": "SOL-EUR",
    "BNB": "BNB-EUR",
    "XRP": "XRP-EUR",
    "CARDANO": "ADA-EUR",
    "DOGECOIN": "DOGE-EUR",
    "AVALANCHE": "AVAX-EUR",
    "TRON": "TRX-EUR",
    "POLKADOT": "DOT-EUR",
    "CHAINLINK": "LINK-EUR",
    "POLYGON": "MATIC-EUR",
    "SHIBA INU": "SHIB-EUR",
    "LITECOIN": "LTC-EUR",
    "UNISWAP": "UNI-EUR",
    "STELLAR": "XLM-EUR",
    "NEAR": "NEAR-EUR",
    "PEPE": "PEPE-EUR"
}


# =========================================================
# 2. FONCTIONS DE RÉCUPÉRATION
# =========================================================
@st.cache_data(ttl=3600)
def get_global_data():
    global_data = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            fi = t.fast_info
            last = fi.last_price
            prev = fi.previous_close
            var = ((last - prev) / prev) * 100 if prev else 0
            # SECURITE : Si mcap est vide, on met 0
            mcap = fi.market_cap if fi.market_cap is not None else 0

            global_data.append({
                "Crypto": name, "Symbole": sym, "Prix": last,
                "Variation %": var, "Market Cap": mcap, "Volume": fi.last_volume
            })
        except:
            continue
    return pd.DataFrame(global_data)


@st.cache_data(ttl=3600)
def get_multi_history(tickers_dict, period="1y"):
    symbols = list(tickers_dict.values())
    data = yf.download(symbols, period=period, progress=False)['Close']
    return data


@st.cache_data(ttl=3600)
def get_detail_data(symbol, period="1y"):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        inf = stock.info

        data_points = {
            "yearLow": inf.get('fiftyTwoWeekLow', 0),
            "yearHigh": inf.get('fiftyTwoWeekHigh', 0),
            "volume24h": inf.get('volume24Hr', 0),
            "supply": inf.get('circulatingSupply', 0),
            "description": inf.get('description', 'Pas de description.')
        }

        fi = stock.fast_info

        # --- CORRECTION DU BUG ICI ---
        # On vérifie si market_cap existe, sinon 0
        mcap_safe = fi.market_cap if fi.market_cap is not None else 0

        info_dict = {
            "last": fi.last_price,
            "prev": fi.previous_close,
            "mcap": mcap_safe,  # On utilise la valeur sécurisée
            **data_points
        }
        return hist, info_dict
    except Exception as e:
        return None, None


@st.cache_data(ttl=3600)
def get_historical_data(symbol, period="1y"):
    try:
        return yf.Ticker(symbol).history(period=period)['Close']
    except:
        return None


# =========================================================
# 3. NAVIGATION
# =========================================================
st.sidebar.title("💎 Crypto App")
page = st.sidebar.radio("Menu :", ["Marché Global 🌍", "Analyse Crypto 🔍"])

if st.sidebar.button("🔄 Actualiser"):
    st.cache_data.clear()
    st.rerun()

# COULEURS CRYPTO
color_up = "#00ff88"
color_down = "#ff0055"
color_btc = "#f7931a"

# =========================================================
# PAGE 1 : MARCHÉ GLOBAL
# =========================================================
if page == "Marché Global 🌍":
    st.title("🌍 Vue d'ensemble Crypto")

    with st.spinner("Scan de la Blockchain..."):
        df_global = get_global_data()

    best_perf = df_global.loc[df_global['Variation %'].idxmax()]
    worst_perf = df_global.loc[df_global['Variation %'].idxmin()]
    total_cap = df_global['Market Cap'].sum() / 1e9

    col1, col2, col3 = st.columns(3)
    col1.metric("Top Gainer 🚀", f"{best_perf['Crypto']}", f"{best_perf['Variation %']:.2f} %")
    col2.metric("Top Loser 📉", f"{worst_perf['Crypto']}", f"{worst_perf['Variation %']:.2f} %")
    col3.metric("Total Market (Suivi)", f"{total_cap:.2f} Mds €")

    st.divider()

    st.subheader("📈 Course des Altcoins (vs BTC)")

    col_conf1, col_conf2 = st.columns([1, 2])

    with col_conf1:
        time_period_global = st.radio("Période :", ["1 Mois", "3 Mois", "6 Mois", "1 An"], index=3, horizontal=True)
        period_map_global = {"1 Mois": "1mo", "3 Mois": "3mo", "6 Mois": "6mo", "1 An": "1y"}
        selected_yahoo_period_global = period_map_global[time_period_global]

    with col_conf2:
        selected_tickers = st.multiselect("Comparer :", list(tickers.keys()), default=["ETHEREUM", "SOLANA", "BNB"])

    df_history_dynamic = get_multi_history(tickers, period=selected_yahoo_period_global)

    if selected_tickers:
        fig_comp = go.Figure()
        for name in selected_tickers:
            sym = tickers[name]
            if sym in df_history_dynamic.columns:
                series = df_history_dynamic[sym].dropna()
                if not series.empty:
                    first_price = series.iloc[0]
                    normalized_series = ((series - first_price) / first_price) * 100
                    fig_comp.add_trace(go.Scatter(x=series.index, y=normalized_series, mode='lines', name=name))
        fig_comp.update_layout(hovermode="x unified", margin=dict(t=10, b=0, l=0, r=0), height=450,
                               paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'),
                               legend=dict(orientation="h", y=1.02, font=dict(color='white')))
        st.plotly_chart(fig_comp, use_container_width=True)

    st.divider()

    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("📊 Prix en Direct")
        st.dataframe(df_global.style.format({"Prix": "{:.4f} €", "Variation %": "{:+.2f} %", "Market Cap": "{:,.0f}"})
                     .background_gradient(subset=["Variation %"], cmap="RdYlGn", vmin=-5, vmax=5),
                     use_container_width=True, height=600)
    with c2:
        st.subheader("🗺️ Dominance (Market Cap)")
        fig_tree = px.treemap(df_global, path=['Crypto'], values='Market Cap', color='Variation %',
                              color_continuous_scale=['#ff0055', '#1a1a2e', '#00ff88'], color_continuous_midpoint=0)
        fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=600, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_tree, use_container_width=True)

# =========================================================
# PAGE 2 : ANALYSE CRYPTO
# =========================================================
elif page == "Analyse Crypto 🔍":

    st.sidebar.markdown("---")
    selected_name = st.sidebar.selectbox("Choisir une Crypto :", list(tickers.keys()))
    symbol = tickers[selected_name]

    st.sidebar.markdown("---")
    time_period_detail = st.sidebar.radio("Zoom :", ["1 Mois", "3 Mois", "6 Mois", "1 An", "2 Ans"], index=3)
    period_map_detail = {"1 Mois": "1mo", "3 Mois": "3mo", "6 Mois": "6mo", "1 An": "1y", "2 Ans": "2y"}
    selected_yahoo_period_detail = period_map_detail[time_period_detail]

    with st.spinner(f"Chargement {selected_name}..."):
        hist, info = get_detail_data(symbol, period=selected_yahoo_period_detail)
        btc_hist = get_historical_data("BTC-EUR", period=selected_yahoo_period_detail)

    if hist is None or hist.empty:
        st.error("Données indisponibles.")
        st.stop()


    # --- FONCTIONS GRAPHIQUES ---
    def plot_candlestick_crypto(df):
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                     increasing_line_color=color_up, decreasing_line_color=color_down, name='Prix'))
        fig.update_layout(margin=dict(t=10, b=20, l=0, r=0), height=300, xaxis_rangeslider_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'))
        return fig


    def plot_volume_bar(df):
        colors = [color_up if row['Close'] > row['Open'] else color_down for index, row in df.iterrows()]
        fig = go.Figure(go.Bar(x=df.index, y=df['Volume'], marker_color=colors))
        fig.update_layout(title="Volume des Transactions", height=200, margin=dict(t=30, b=10, l=10, r=10),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          xaxis=dict(visible=False), yaxis=dict(showgrid=False))
        return fig


    def plot_vs_bitcoin(crypto_series, btc_series, name):
        df = pd.concat([crypto_series, btc_series], axis=1, join='inner')
        df.columns = ['Crypto', 'BTC']
        df = (df / df.iloc[0]) * 100

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=df.index, y=df['Crypto'], mode='lines', name=name, line=dict(color='#8e44ad', width=2)))
        fig.add_trace(go.Scatter(x=df.index, y=df['BTC'], mode='lines', name="Bitcoin",
                                 line=dict(color=color_btc, width=2, dash='dot')))
        fig.update_layout(title=f"Performance relative vs Bitcoin", height=250, margin=dict(t=40, b=0, l=0, r=0),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#333'),
                          legend=dict(orientation="h", y=1.1, font=dict(color='white')))
        return fig


    def plot_52week_range(current, low, high):
        if not low or not high: return go.Figure()
        fig = go.Figure()
        fig.add_shape(type="rect", x0=low, y0=0, x1=high, y1=1, fillcolor="#333", line=dict(color="rgba(0,0,0,0)"),
                      layer="below")
        fig.add_shape(type="rect", x0=low, y0=0, x1=current, y1=1, fillcolor="#8e44ad",
                      line=dict(color="rgba(0,0,0,0)"), layer="below")
        fig.add_trace(go.Scatter(x=[current], y=[1.3], mode='text', text=["▼"], textfont=dict(size=20, color="white"),
                                 showlegend=False))
        fig.update_layout(title=dict(text="Range Annuel (Min/Max)", font=dict(size=14, color="white")),
                          xaxis=dict(showgrid=False, tickvals=[low, high], ticktext=[f"{low:.4f}", f"{high:.4f}"],
                                     tickfont=dict(color='white')),
                          yaxis=dict(visible=False, range=[0, 2]), margin=dict(t=30, b=20, l=10, r=10),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=120)
        return fig


    # --- CONTENU DE LA PAGE ---
    st.title(f"🪙 Analyse : {selected_name}")

    col_left, col_mid, col_right = st.columns([1, 1.5, 1.5], gap="medium")

    with col_left:
        with st.container():
            st.write("##### 📊 Volumes & Range")
            st.plotly_chart(plot_volume_bar(hist), use_container_width=True, config={'displayModeBar': False})
            st.divider()
            if info['yearLow'] and info['yearHigh']:
                st.plotly_chart(plot_52week_range(info['last'], info['yearLow'], info['yearHigh']),
                                use_container_width=True, config={'displayModeBar': False})

    with col_mid:
        with st.container():
            st.write("##### 🚀 Indicateurs Clés")
            kpi1, kpi2, kpi3 = st.columns(3)
            var_day = ((info['last'] - info['prev']) / info['prev']) * 100

            # --- AFFICHAGE SECURISE ---
            # Si market cap est 0, on affiche "N/A" ou 0.0, mais on évite le crash
            mcap_display = f"{info['mcap'] / 1e9:.1f} B€" if info['mcap'] > 0 else "N/A"

            kpi1.metric("Prix", f"{info['last']:.4f}€")
            kpi2.metric("24h", f"{var_day:+.2f}%", delta=f"{var_day:+.2f}%")
            kpi3.metric("Market Cap", mcap_display)

            st.divider()

            if btc_hist is not None and not btc_hist.empty:
                st.plotly_chart(plot_vs_bitcoin(hist['Close'], btc_hist, selected_name), use_container_width=True,
                                config={'displayModeBar': False})

    with col_right:
        with st.container():
            st.write(f"##### 🕯️ Chart ({time_period_detail})")
            st.plotly_chart(plot_candlestick_crypto(hist), use_container_width=True, config={'displayModeBar': False})

        with st.container():
            st.write("##### ℹ️ Infos Token")
            supply = info.get('supply', 0)
            if supply:
                st.metric("Circulating Supply", f"{supply:,.0f}")
            else:
                st.info("Supply inconnu")

            st.caption("Données temps réel fournies par Yahoo Finance.")