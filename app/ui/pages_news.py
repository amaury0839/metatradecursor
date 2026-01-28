"""News and sentiment page - Works for both local and remote modes"""

import streamlit as st

# Try to import local modules
try:
    from app.news.sentiment import get_sentiment_analyzer
    from app.core.config import get_config
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


def render_news():
    """Render news and sentiment page - auto-detects local or remote mode"""
    if LOCAL_MODE:
        render_news_local()
    else:
        st.info("News and sentiment analysis runs on the local trading bot server.")
        st.info("Use the local UI to view news sentiment.")


def render_news_local():
    """Render news and sentiment page - Local mode"""
    sentiment = get_sentiment_analyzer()
    config = get_config()
    
    st.subheader("📰 News & Sentiment Analysis")
    
    # Provider info
    st.markdown("### News Provider")
    provider_name = "NewsAPI" if sentiment.provider.is_available() and config.news.provider == "newsapi" else "Stub (Mock)"
    st.info(f"Current provider: **{provider_name}**")
    
    if provider_name == "Stub (Mock)":
        st.warning("Using stub provider. Configure NEWS_API_KEY in .env for real news.")
    
    st.divider()
    
    # Symbol selection
    st.markdown("### Analyze Sentiment")
    symbol = st.selectbox(
        "Select symbol",
        options=config.trading.default_symbols,
        index=0
    )
    
    hours_back = st.slider(
        "Hours to look back",
        min_value=1,
        max_value=48,
        value=24,
        step=1
    )
    
    if st.button("Get Sentiment Analysis"):
        with st.spinner("Analyzing sentiment..."):
            result = sentiment.get_sentiment(symbol, hours_back)
            
            if result:
                # Score visualization
                score = result.get('score', 0.0)
                st.markdown("### Sentiment Score")
                
                # Color based on score
                if score > 0.3:
                    color = "green"
                    label = "🟢 Bullish"
                elif score < -0.3:
                    color = "red"
                    label = "🔴 Bearish"
                else:
                    color = "gray"
                    label = "⚪ Neutral"
                
                st.markdown(f"**{label}** (Score: {score:.2f})")
                st.progress((score + 1) / 2)  # Normalize to 0-1
                
                st.divider()
                
                # Summary
                st.markdown("### Summary")
                st.info(result.get('summary', 'No summary available'))
                
                st.divider()
                
                # Headlines
                st.markdown("### Recent Headlines")
                headlines = result.get('headlines', [])
                if headlines:
                    for i, headline in enumerate(headlines[:10], 1):
                        st.text(f"{i}. {headline}")
                else:
                    st.info("No headlines available")
                
                st.divider()
                
                # Confidence
                confidence = result.get('confidence', 0.5)
                st.metric("Analysis Confidence", f"{confidence:.2%}")
            else:
                st.error("Failed to get sentiment analysis")
    
    st.divider()
    
    # Cache management
    st.markdown("### Cache Management")
    if st.button("Clear Sentiment Cache"):
        sentiment.clear_cache()
        st.success("Cache cleared!")

