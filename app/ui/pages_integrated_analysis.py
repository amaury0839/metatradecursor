"""Streamlit page for integrated analysis summary"""

import streamlit as st
from app.trading.integrated_analysis import get_integrated_analyzer
from app.core.config import get_config


def render_integrated_analysis():
    """Render integrated analysis page"""
    st.header("📊 Análisis Integrado")
    
    config = get_config()
    analyzer = get_integrated_analyzer()
    
    st.markdown("""
    Este análisis combina:
    - 📈 **Technical**: RSI, EMA, Trend
    - 📰 **Sentiment**: News sentiment (con cache de 1 hora)
    - 🤖 **AI**: Decision engine
    """)
    
    # Select symbol
    symbols = config.trading.default_symbols
    selected_symbol = st.selectbox("Selecciona símbolo:", symbols, key="integrated_symbol")
    
    if selected_symbol:
        with st.spinner(f"Analizando {selected_symbol}..."):
            analysis = analyzer.analyze_symbol(selected_symbol)
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Score Combinado", f"{analysis['combined_score']:.2f}")
        
        with col2:
            st.metric("Señal", analysis['signal'], delta=f"{analysis['confidence']:.0%}")
        
        with col3:
            st.metric("Fuentes", len(analysis['available_sources']))
        
        # Display by source
        st.subheader("📈 Análisis Técnico")
        if analysis["technical"]:
            tech = analysis["technical"]
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Signal**: {tech['signal']}")
            with col2:
                st.info(f"**Reason**: {tech['reason']}")
            
            if tech['data']:
                st.json(tech['data'])
        else:
            st.warning("No hay análisis técnico disponible")
        
        # Sentiment
        st.subheader("📰 Análisis de Sentimiento")
        if analysis["sentiment"]:
            sent = analysis["sentiment"]
            col1, col2 = st.columns(2)
            
            with col1:
                score = sent.get("score", 0)
                if score > 0.3:
                    st.success(f"**Score**: {score:.2f} (Positivo)")
                elif score < -0.3:
                    st.error(f"**Score**: {score:.2f} (Negativo)")
                else:
                    st.info(f"**Score**: {score:.2f} (Neutral)")
            
            with col2:
                st.info(f"**Summary**: {sent.get('summary', 'N/A')}")
            
            if sent.get('headlines'):
                with st.expander(f"📰 {len(sent['headlines'])} headlines encontrados"):
                    for i, headline in enumerate(sent['headlines'][:5], 1):
                        st.write(f"{i}. {headline}")
        else:
            st.info("Análisis de sentimiento en caché o no disponible (se carga cada hora)")
        
        # Combined analysis
        st.subheader("🔄 Análisis Combinado")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Score", f"{analysis['combined_score']:.2f}")
        with col2:
            st.metric("Señal", analysis['signal'])
        with col3:
            st.metric("Confianza", f"{analysis['confidence']:.0%}")
        
        st.info(f"**Fuentes disponibles**: {', '.join(analysis['available_sources'])}")


if __name__ == "__main__":
    render_integrated_analysis()

