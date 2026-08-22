import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(
    page_title="XBID Intraday Microstructure Engine",
    page_icon="⚡",
    layout="wide"
)

# Dark Quantitative Theme Styling
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #050b1f;
        border: 2px solid #0055ff;
        padding: 16px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(0, 85, 255, 0.25);
    }
    div[data-testid="stMetricLabel"] {
        color: #ffffff;
        font-size: 0.9rem;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
    }
    hr {
        border-top: 1px solid #0044ff;
        margin: 25px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Intraday Continuous (XBID) Microstructure Engine")
st.markdown("<p style='color: #cbd5e1; font-size: 1.05rem; margin-top: -10px;'>Level-2 Order Book simulation, <b>Order Flow Imbalance (OFI)</b>, and <b>VWAP execution dynamics</b> for German 15-minute contracts.</p>", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### ⚙️ Microstructure Parameters")
horizon_min = st.sidebar.slider("Execution Horizon (Minutes to Gate)", min_value=30, max_value=180, value=120, step=15)
base_price = st.sidebar.number_input("Day-Ahead Benchmark Anchor (€/MWh)", min_value=20.0, max_value=250.0, value=85.0, step=5.0)
volatility = st.sidebar.slider("Fundamental Price Volatility (σ)", min_value=0.1, max_value=1.5, value=0.45, step=0.05)
urgency = st.sidebar.slider("Gate Closure Urgency Multiplier", min_value=0.5, max_value=2.5, value=1.0, step=0.1)

# Simulator Functions
def compute_micro_price(bid, ask, b_depth, a_depth):
    tot = b_depth + a_depth
    return (bid * a_depth + ask * b_depth) / np.maximum(tot, 1e-6)

def compute_ofi(b_depth, a_depth):
    tot = b_depth + a_depth
    return (b_depth - a_depth) / np.maximum(tot, 1e-6)

def generate_market_data(n_minutes, base_p, vol, urg):
    np.random.seed(42)
    timestamps = pd.date_range(start="2026-08-22 18:00:00", periods=n_minutes, freq="min")
    drift = np.cumsum(np.random.normal(0, vol, n_minutes))
    fundamental_price = base_p + drift

    time_to_gate = np.linspace(n_minutes, 1, n_minutes)
    urgency_factor = np.exp(-time_to_gate / (35.0 / urg))

    bid_spread = np.maximum(0.15, 0.35 + np.random.exponential(0.2, n_minutes) + (urgency_factor * 1.2))
    ask_spread = np.maximum(0.15, 0.35 + np.random.exponential(0.2, n_minutes) + (urgency_factor * 1.2))

    best_bid = fundamental_price - bid_spread
    best_ask = fundamental_price + ask_spread
    mid_price = (best_bid + best_ask) / 2.0
    spread_eur = best_ask - best_bid

    bid_depth_mw = np.maximum(2.0, np.random.poisson(14, n_minutes) + (1.0 - urgency_factor) * 18.0)
    ask_depth_mw = np.maximum(2.0, np.random.poisson(14, n_minutes) + (urgency_factor) * 22.0)

    ofi = compute_ofi(bid_depth_mw, ask_depth_mw)
    micro_price = compute_micro_price(best_bid, best_ask, bid_depth_mw, ask_depth_mw)

    trade_volume_mw = np.random.poisson(6, n_minutes) + (urgency_factor * 28.0).astype(int)
    trade_prices = mid_price + (ofi * (spread_eur / 2.0)) + np.random.normal(0, 0.08, n_minutes)
    cumulative_volume = np.cumsum(trade_volume_mw)
    vwap_eur = np.cumsum(trade_prices * trade_volume_mw) / np.maximum(cumulative_volume, 1e-6)

    return pd.DataFrame({
        "timestamp": timestamps,
        "minutes_to_gate": np.round(time_to_gate, 0),
        "best_bid": np.round(best_bid, 2),
        "best_ask": np.round(best_ask, 2),
        "mid_price": np.round(mid_price, 2),
        "micro_price": np.round(micro_price, 2),
        "spread_eur": np.round(spread_eur, 2),
        "bid_depth_mw": np.round(bid_depth_mw, 1),
        "ask_depth_mw": np.round(ask_depth_mw, 1),
        "ofi": np.round(ofi, 3),
        "traded_volume_mw": trade_volume_mw,
        "trade_price_eur": np.round(trade_prices, 2),
        "vwap_eur": np.round(vwap_eur, 2)
    })

df = generate_market_data(horizon_min, base_price, volatility, urgency)

# Metrics
total_traded_mwh = np.sum(df["traded_volume_mw"]) * 0.25
final_vwap = df["vwap_eur"].iloc[-1]
avg_spread = df["spread_eur"].mean()
peak_ofi = df["ofi"].abs().max()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Traded Volume", f"{total_traded_mwh:,.2f} MWh")
k2.metric("Executed VWAP Benchmark", f"€{final_vwap:.2f}/MWh")
k3.metric("Average Bid-Ask Spread", f"€{avg_spread:.2f}/MWh")
k4.metric("Max Order Flow Imbalance (|OFI|)", f"{peak_ofi:.3f}")

st.markdown("<hr>", unsafe_allow_html=True)

# Plotly Styling
pure_blue_legend = dict(
    orientation="h",
    yanchor="bottom",
    y=1.05,
    xanchor="right",
    x=1.0,
    bgcolor="#003cd2",
    bordercolor="#ffffff",
    borderwidth=2,
    font=dict(color="#ffffff", size=12, family="Arial, sans-serif")
)

pure_blue_hover = dict(
    bgcolor="#002db3",
    bordercolor="#ffffff",
    font=dict(color="#ffffff", size=13, family="Arial, sans-serif")
)

# Plot 1: Order Book L2 Price & VWAP
st.markdown("#### 1. Level-2 Order Book Pricing, Micro-Price & Executed VWAP")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=df["timestamp"], y=df["best_ask"], name="Best Ask", line=dict(color="#ef4444", width=1.4, dash="dot")))
fig1.add_trace(go.Scatter(x=df["timestamp"], y=df["best_bid"], name="Best Bid", line=dict(color="#10b981", width=1.4, dash="dot")))
fig1.add_trace(go.Scatter(x=df["timestamp"], y=df["micro_price"], name="L2 Micro-Price", line=dict(color="#0284c7", width=2.0)))
fig1.add_trace(go.Scatter(x=df["timestamp"], y=df["vwap_eur"], name="Cumulative VWAP", line=dict(color="#f59e0b", width=2.4)))

fig1.update_layout(
    template="plotly_dark",
    plot_bgcolor="#060913",
    paper_bgcolor="#060913",
    height=420,
    margin=dict(l=20, r=20, t=55, b=20),
    legend=pure_blue_legend,
    hoverlabel=pure_blue_hover,
    xaxis=dict(gridcolor="#1e293b", title="Timeline to Gate Closure"),
    yaxis=dict(gridcolor="#1e293b", title="Price [€/MWh]"),
    hovermode="x unified"
)
st.plotly_chart(fig1, use_container_width=True)

# Plot 2: Spread & L2 Depth Imbalance
st.markdown("#### 2. Bid-Ask Spread Dynamics & Order Flow Imbalance (OFI)")
fig2 = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.10,
    subplot_titles=("Bid-Ask Spread (€/MWh)", "Order Book L2 Liquidity Depth (Bid vs Ask MW)")
)

fig2.add_trace(go.Scatter(x=df["timestamp"], y=df["spread_eur"], name="Spread (€/MWh)", line=dict(color="#8b5cf6", width=2.0)), row=1, col=1)

fig2.add_trace(go.Bar(x=df["timestamp"], y=df["bid_depth_mw"], name="Bid Depth (MW)", marker_color="#10b981"), row=2, col=1)
fig2.add_trace(go.Bar(x=df["timestamp"], y=-df["ask_depth_mw"], name="Ask Depth (MW)", marker_color="#ef4444"), row=2, col=1)

fig2.update_layout(
    template="plotly_dark",
    plot_bgcolor="#060913",
    paper_bgcolor="#060913",
    height=500,
    margin=dict(l=20, r=20, t=55, b=20),
    legend=pure_blue_legend,
    hoverlabel=pure_blue_hover,
    hovermode="x unified"
)
fig2.update_xaxes(gridcolor="#1e293b")
fig2.update_yaxes(gridcolor="#1e293b")

st.plotly_chart(fig2, use_container_width=True)
