import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

HIDE = False  # Toggle this to True to enable password protection

# ===============================
# --- Password Protection ---
# ===============================
def password_gate():
    CORRECT_PASSWORD = "3asba"
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = not HIDE
    if not st.session_state.authenticated and HIDE:
        st.title("🔐 Secure Access")
        password_input = st.text_input("Enter password to access dashboard:", type="password")
        if password_input == CORRECT_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()
        elif password_input:
            st.error("Incorrect password. Please try again.")
        st.stop()
    elif st.session_state.authenticated and "last_login" not in st.session_state:
        st.session_state.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ===============================
# --- Utility Functions ---
# ===============================
@st.cache_data(show_spinner=False)
def get_data(ticker: str, start, end):
    df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=True)
    if df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close'][ticker].to_frame(name="Close")
    else:
        df = df[['Close']]
    df['Daily Return'] = df['Close'].pct_change()
    df['Cumulative Return'] = (1 + df['Daily Return']).cumprod()
    df['Drawdown'] = df['Cumulative Return'] / df['Cumulative Return'].cummax() - 1
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    return df

@st.cache_data(show_spinner=False)
def get_earliest_date(ticker: str):
    try:
        df = yf.download(ticker, period="max", interval="1d", auto_adjust=True)
        if not df.empty:
            return df.index.min().date()
    except Exception:
        pass
    return pd.to_datetime("2012-01-01").date()

password_gate()

# ===============================
# --- Session State Setup ---
# ===============================
if "base_tickers" not in st.session_state:
    st.session_state.base_tickers = ["BTC-EUR","ETH-EUR", "CW8.PA" ,"PLTR","LQQ.PA" ,"PUST.PA","ESE.PA", "CL2.PA"]
if "extra_tickers" not in st.session_state:
    st.session_state.extra_tickers = []
if "selected_tickers" not in st.session_state:
    st.session_state.selected_tickers = []
if "initial_investment" not in st.session_state:
    st.session_state.initial_investment = 1000.0
if "show_price" not in st.session_state:
    st.session_state.show_price = True
if "show_volatility" not in st.session_state:
    st.session_state.show_volatility = True
if "show_drawdown" not in st.session_state:
    st.session_state.show_drawdown = True
if "show_sma" not in st.session_state:
    st.session_state.show_sma = False
if "sma_window" not in st.session_state:
    st.session_state.sma_window = 200

# ===============================
# --- Sidebar ---
# ===============================

st.sidebar.markdown("""
<div style='text-align: center; font-size: 0.8em; color: gray;'>
    © 2025 Karim Bargaoui 
    <a href='https://github.com/k-bargaoui' target='_blank'>github.com/k-bargaoui</a>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("📊 Dashboard Configuration")
st.sidebar.markdown("### Select or Add Tickers")
available_tickers = st.session_state.base_tickers + st.session_state.extra_tickers
selected = st.sidebar.multiselect(
    "Choose from list",
    available_tickers,
    default=st.session_state.selected_tickers
)
st.session_state.selected_tickers = selected
tickers = selected
custom_ticker = st.sidebar.text_input("➕ Add Custom Ticker", value="")
if st.sidebar.button("Add Ticker"):
    if custom_ticker:
        custom_ticker = custom_ticker.upper()
        if custom_ticker not in st.session_state.extra_tickers:
            st.session_state.extra_tickers.append(custom_ticker)
        if custom_ticker not in st.session_state.selected_tickers:
            st.session_state.selected_tickers.append(custom_ticker)
        st.rerun()

today = pd.to_datetime("today").date()
min_date = get_earliest_date(tickers[0]) if tickers else None

if min_date:
    start_date = st.sidebar.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=today
    )

    end_date = st.sidebar.date_input(
        "End Date",
        value=today,
        min_value=min_date,
        max_value=today
    )

    st.sidebar.caption(f"📅 Data available from `{min_date}` to `{today}`")
else:
    st.sidebar.info("👆 Select a ticker to enable date range selection.")
    start_date = None
    end_date = None



st.session_state.initial_investment = st.sidebar.number_input(
    "💰 Initial Investment (€)",
    min_value=100.0,
    value=st.session_state.initial_investment,
    step=100.0
)

st.sidebar.markdown("### Graph Options")
st.session_state.show_price = st.sidebar.checkbox("Show Price Chart", value=st.session_state.show_price)
st.session_state.show_volatility = st.sidebar.checkbox("Show Rolling Volatility", value=st.session_state.show_volatility)
st.session_state.show_drawdown = st.sidebar.checkbox("Show Drawdown", value=st.session_state.show_drawdown)

st.sidebar.markdown("### SMA Options")
st.session_state.show_sma = st.sidebar.checkbox("Overlay SMA", value=st.session_state.show_sma)

def update_sma_window():
    st.session_state.sma_window = st.session_state.sma_slider_value

st.sidebar.slider(
    "SMA Window (days)",
    min_value=10,
    max_value=200,
    value=st.session_state.sma_window,
    step=10,
    key="sma_slider_value",
    on_change=update_sma_window
)

if HIDE and st.session_state.authenticated:
    st.sidebar.markdown(f"🕒 Last Logged In: `{st.session_state.get('last_login', 'N/A')}`")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()
elif not HIDE:
    st.sidebar.markdown("🔓 Password protection is disabled.")

# ===============================
# --- Main Layout ---
# ===============================
st.title("📈 Backtest and Monitoring")
tab1, tab2, tab3, tab4 = st.tabs(["📌 Asset Analysis", "🏆 Performance Leaderboard", "📊 Portfolio Simulation", "🧠 Insights"])

# ===============================
# --- Tab 1: Individual Asset Analysis ---
# ===============================
with tab1:
    for ticker in tickers:
        st.header(ticker)
        df = get_data(ticker, start_date, end_date)
        if df.empty or len(df['Close'].dropna()) < 2:
            st.warning(f"No valid data for {ticker}.")
            continue
        st.caption(f"📈 {ticker} data available from `{df.index.min().date()}` to `{df.index.max().date()}`")
        if st.session_state.show_price:
            st.subheader("Price Chart")
            df[f"SMA{st.session_state.sma_window}"] = df['Close'].rolling(window=st.session_state.sma_window).mean()
            fig = px.line(df.reset_index(), x='Date', y='Close', title=f"{ticker} Price")
            if st.session_state.show_sma:
                fig.add_scatter(x=df.index, y=df[f"SMA{st.session_state.sma_window}"], mode='lines', name=f"SMA{st.session_state.sma_window}")
            st.plotly_chart(fig, use_container_width=True)
        if st.session_state.show_volatility:
            st.subheader("Rolling Volatility (30-day)")
            df['Rolling Volatility (%)'] = df['Daily Return'].rolling(30).std() * np.sqrt(252) * 100
            fig = px.line(df.reset_index(), x='Date', y='Rolling Volatility (%)', title=f"{ticker} Volatility")
            st.plotly_chart(fig, use_container_width=True)
        if st.session_state.show_drawdown:
            st.subheader("Drawdown (Max Loss from Peak)")
            df['Drawdown (%)'] = df['Drawdown'] * 100
            fig = px.line(df.reset_index(), x='Date', y='Drawdown (%)', title=f"{ticker} Drawdown (%)")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")



# ===============================
# --- Tab 2: Leaderboard ---
# ===============================
with tab2:
    st.subheader("🏆 Performance Leaderboard")
    leaderboard = []
    annual_returns = []
    for ticker in tickers:
        df = get_data(ticker, start_date, end_date)
        if df.empty or len(df['Close'].dropna()) < 2:
            continue
        initial_price, final_price = float(df['Close'].iloc[0]), float(df['Close'].iloc[-1])
        return_pct = ((final_price / initial_price) - 1) * 100
        invested_final_value = st.session_state.initial_investment * (final_price / initial_price)
        annualized_return = df['Daily Return'].mean() * 252
        annualized_volatility = df['Daily Return'].std() * np.sqrt(252)
        annualized_sharpe = annualized_return / annualized_volatility if annualized_volatility else np.nan
        leaderboard.append({
            "Ticker": ticker,
            "Return (%)": round(return_pct, 2),
            "Final Value (€)": round(invested_final_value, 2),
            "Annualized Return (%)": round(annualized_return * 100, 2),
            "Annualized Volatility (%)": round(annualized_volatility * 100, 2),
            "Sharpe Ratio": round(annualized_sharpe, 2)
        })
        df['Year'] = df.index.year
        grouped = df.groupby('Year')['Daily Return'].apply(lambda x: (1 + x).prod() - 1)
        for year, ret in grouped.items():
            annual_returns.append({"Ticker": ticker, "Year": year, "Return (%)": round(ret * 100, 2)})
    if leaderboard:
        leaderboard_df = pd.DataFrame(leaderboard).sort_values(by="Annualized Return (%)", ascending=False)
        st.dataframe(leaderboard_df, use_container_width=True)
        st.subheader("📅 Annual Returns by Year")
        annual_df = pd.DataFrame(annual_returns)
        fig = px.bar(annual_df, x="Year", y="Return (%)", color="Ticker", barmode="group", title="Annual Returns by Ticker")
        st.plotly_chart(fig, use_container_width=True)
        csv = leaderboard_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Leaderboard as CSV", data=csv, file_name="leaderboard.csv", mime="text/csv")
    else:
        st.info("No valid data to display in leaderboard.")

# ===============================
# --- Tab 3: Portfolio Simulation ---
# ===============================
with tab3:
    st.subheader("📊 Portfolio Simulation (Individual Ticker Evolution)")
    for ticker in tickers:
        df = get_data(ticker, start_date, end_date)
        if df.empty or len(df['Daily Return'].dropna()) < 2:
            continue
        cumulative = (1 + df['Daily Return']).cumprod()
        portfolio_value = st.session_state.initial_investment * cumulative
        portfolio_df = pd.DataFrame({
            "Date": df.index,
            "Portfolio Value": portfolio_value
        })
        fig = px.line(portfolio_df, x="Date", y="Portfolio Value", title=f"{ticker} Portfolio Value")
        st.plotly_chart(fig, use_container_width=True)
        st.metric(f"📈 Final Value for {ticker}", f"{portfolio_value.iloc[-1]:.2f} €")

# ===============================
# --- Tab 4: Insights ---
# ===============================
with tab4:
    st.subheader("🧠 Insights")
    for ticker in tickers:
        df = get_data(ticker, start_date, end_date)
        if df.empty or len(df['Close'].dropna()) < 2:
            st.warning(f"No valid data for {ticker}.")
            continue
        latest_price = df['Close'].iloc[-1]
        sma = df['Close'].rolling(window=st.session_state.sma_window).mean().iloc[-1]
        drawdown = df['Drawdown'].iloc[-1] * 100
        volatility = df['Daily Return'].rolling(30).std().iloc[-1] * np.sqrt(252) * 100
        sentiment = "bullish" if latest_price > sma else "bearish"
        stability = "low" if volatility < 30 else "high"
        recovery = "recovered" if drawdown > -10 else "struggled"

        st.markdown(f"""
        ### {ticker}
        - **Current Price**: €{latest_price:.2f}
        - **{st.session_state.sma_window}-day SMA**: €{sma:.2f}
        - **Drawdown from Peak**: {drawdown:.2f}%
        - **Volatility (30-day annualized)**: {volatility:.2f}%

        📌 *Insight*: {ticker} has **{recovery}** recently, with a drawdown of {drawdown:.2f}%.  
        The price is **{sentiment}** relative to its SMA, and volatility is **{stability}**, suggesting a {sentiment} outlook under current conditions.
        """)
        st.markdown("---")


# Spacer + Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; font-size: 0.8em; color: gray;'>
    © 2025 Karim Bargaoui 
    <a href='https://github.com/k-bargaoui' target='_blank'>github.com/k-bargaoui</a>
</div>
""", unsafe_allow_html=True)
