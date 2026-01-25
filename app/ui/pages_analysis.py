"""Analysis logs page for Streamlit UI"""

import streamlit as st
import pandas as pd
from datetime import datetime
from app.core.analysis_logger import get_analysis_logger


def render_analysis_logs():
    """Render analysis logs page"""
    st.title("📊 Análisis en Tiempo Real")
    
    logger = get_analysis_logger()
    
    # Filter options
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        analysis_type = st.selectbox(
            "Tipo de Análisis",
            ["TODOS", "TECHNICAL", "AI", "EXECUTION", "RISK"]
        )
    
    with col2:
        status = st.selectbox(
            "Estado",
            ["TODOS", "SUCCESS", "WARNING", "ERROR"]
        )
    
    with col3:
        symbol = st.text_input("Símbolo (ej: EURUSD)", value="")
    
    with col4:
        limit = st.slider("Últimos N análisis", 10, 500, 100)
    
    # Get logs with filters
    filters = {}
    if analysis_type != "TODOS":
        filters["analysis_type"] = analysis_type
    if status != "TODOS":
        filters["status"] = status
    if symbol:
        filters["symbol"] = symbol.upper()
    if limit:
        filters["limit"] = limit
    
    logs = logger.get_logs(**filters)
    
    if not logs:
        st.info("No hay análisis para mostrar con los filtros seleccionados")
        return
    
    # Display stats
    st.subheader("📈 Resumen")
    col1, col2, col3, col4 = st.columns(4)
    
    success_count = sum(1 for log in logs if log["status"] == "SUCCESS")
    warning_count = sum(1 for log in logs if log["status"] == "WARNING")
    error_count = sum(1 for log in logs if log["status"] == "ERROR")
    
    with col1:
        st.metric("Total Análisis", len(logs))
    with col2:
        st.metric("✅ Éxito", success_count, delta=None)
    with col3:
        st.metric("⚠️ Advertencias", warning_count)
    with col4:
        st.metric("❌ Errores", error_count)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Tabla", "Timeline", "Por Símbolo", "Por Tipo"])
    
    with tab1:
        render_table_view(logs)
    
    with tab2:
        render_timeline_view(logs)
    
    with tab3:
        render_by_symbol_view(logs)
    
    with tab4:
        render_by_type_view(logs)
    
    # Auto-refresh
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Actualizar"):
            st.rerun()


def render_table_view(logs):
    """Display logs as a table"""
    st.subheader("Tabla de Análisis")
    
    # Prepare data for display
    data = []
    for log in logs:
        data.append({
            "⏰ Hora": log["timestamp"],
            "📍 Símbolo": log["symbol"],
            "🕐 TF": log.get("timeframe", ""),
            "🔍 Tipo": log["analysis_type"],
            "📊 Estado": log["status"],
            "💬 Mensaje": log["message"],
        })
    
    # Add status colors
    df = pd.DataFrame(data)
    
    # Display with styling
    def color_status(val):
        if val == "SUCCESS":
            return "background-color: #90EE90"
        elif val == "WARNING":
            return "background-color: #FFD700"
        else:
            return "background-color: #FFB6C6"
    
    st.dataframe(
        df.style.applymap(color_status, subset=["📊 Estado"]),
        use_container_width=True,
        height=600
    )


def render_timeline_view(logs):
    """Display logs as a timeline"""
    st.subheader("Timeline de Análisis")
    
    for log in logs:
        # Color badge based on status
        if log["status"] == "SUCCESS":
            badge = "✅"
        elif log["status"] == "WARNING":
            badge = "⚠️"
        else:
            badge = "❌"
        
        # Type icon
        type_icon = {
            "TECHNICAL": "📊",
            "AI": "🤖",
            "EXECUTION": "💹",
            "RISK": "⚠️"
        }.get(log["analysis_type"], "•")
        
        col1, col2, col3 = st.columns([0.5, 2, 5])
        
        with col1:
            st.write(f"**{badge}**")
        
        with col2:
            st.write(f"**{log['timestamp']}**")
            st.caption(f"{type_icon} {log['symbol']} {log.get('timeframe', '')}")
        
        with col3:
            st.write(f"**{log['analysis_type']}**: {log['message']}")
            if log.get("details"):
                with st.expander("Detalles"):
                    st.json(log["details"])


def render_by_symbol_view(logs):
    """Group and display by symbol"""
    st.subheader("Análisis por Símbolo")
    
    # Group by symbol
    symbols = {}
    for log in logs:
        sym = log.get("symbol", "UNKNOWN")
        if sym not in symbols:
            symbols[sym] = []
        symbols[sym].append(log)
    
    # Display summary for each symbol
    cols = st.columns(min(3, len(symbols)))
    
    for idx, (symbol, symbol_logs) in enumerate(sorted(symbols.items())):
        with cols[idx % len(cols)]:
            success = sum(1 for l in symbol_logs if l["status"] == "SUCCESS")
            warning = sum(1 for l in symbol_logs if l["status"] == "WARNING")
            error = sum(1 for l in symbol_logs if l["status"] == "ERROR")
            
            st.metric(
                f"📊 {symbol}",
                f"{len(symbol_logs)} análisis",
                f"✅{success} ⚠️{warning} ❌{error}"
            )
    
    # Detailed view
    st.subheader("Detalle por Símbolo")
    selected_symbol = st.selectbox(
        "Seleccionar símbolo",
        list(symbols.keys())
    )
    
    if selected_symbol:
        symbol_logs = symbols[selected_symbol]
        
        # Group by type
        types = {}
        for log in symbol_logs:
            atype = log["analysis_type"]
            if atype not in types:
                types[atype] = []
            types[atype].append(log)
        
        for atype, type_logs in types.items():
            with st.expander(f"{atype} ({len(type_logs)} análisis)"):
                for log in type_logs:
                    status_emoji = "✅" if log["status"] == "SUCCESS" else "⚠️" if log["status"] == "WARNING" else "❌"
                    st.write(f"{status_emoji} **{log['timestamp']}** - {log['message']}")
                    if log.get("details"):
                        st.json(log["details"])


def render_by_type_view(logs):
    """Group and display by analysis type"""
    st.subheader("Análisis por Tipo")
    
    # Group by type
    types = {}
    for log in logs:
        atype = log["analysis_type"]
        if atype not in types:
            types[atype] = {"SUCCESS": 0, "WARNING": 0, "ERROR": 0, "logs": []}
        types[atype]["logs"].append(log)
        types[atype][log["status"]] += 1
    
    # Display summary
    cols = st.columns(min(4, len(types)))
    
    type_icons = {
        "TECHNICAL": "📊",
        "AI": "🤖",
        "EXECUTION": "💹",
        "RISK": "⚠️"
    }
    
    for idx, (atype, stats) in enumerate(types.items()):
        with cols[idx % len(cols)]:
            icon = type_icons.get(atype, "•")
            st.metric(
                f"{icon} {atype}",
                len(stats["logs"]),
                f"✅{stats['SUCCESS']} ⚠️{stats['WARNING']} ❌{stats['ERROR']}"
            )
    
    # Detailed view
    st.subheader("Detalle por Tipo")
    
    detail_idx = 0
    for atype, stats in types.items():
        icon = type_icons.get(atype, "•")
        with st.expander(f"{icon} {atype} ({len(stats['logs'])} análisis)"):
            for log_idx, log in enumerate(sorted(stats["logs"], key=lambda x: x["timestamp"], reverse=True)):
                status_emoji = "✅" if log["status"] == "SUCCESS" else "⚠️" if log["status"] == "WARNING" else "❌"
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.write(f"**{status_emoji}** {log['symbol']}")
                with col2:
                    st.write(f"*{log['timestamp']}* - {log['message']}")
                
                if log.get("details"):
                    # Usar combinación de tipo, índice de log y contador global para clave única
                    detail_key = f"details-{atype}-{log_idx}-{detail_idx}"
                    with st.expander("Detalles", key=detail_key):
                        try:
                            st.json(log["details"])
                        except Exception:
                            st.write(str(log["details"]))
                    detail_idx += 1
