"""Modern UI Components - Reusable Components for Dashboard"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
import plotly.graph_objects as go
import plotly.express as px
from app.ui.themes_modern import get_theme


class MetricsDisplay:
    """Metrics and KPI display components"""
    
    @staticmethod
    def kpi_card(label: str, value: Any, unit: str = "", 
                 change: Optional[float] = None, 
                 is_positive: bool = True,
                 color: Optional[str] = None):
        """Display a professional KPI card
        
        Args:
            label: Card label
            value: Main value
            unit: Unit of measurement
            change: Change percentage
            is_positive: Whether change is positive
            color: Override color
        """
        theme = get_theme()
        colors = theme.get_colors()
        
        if color is None:
            color = colors["primary"]
        
        change_text = ""
        if change is not None:
            change_arrow = "📈" if is_positive else "📉"
            change_color = colors["success"] if is_positive else colors["error"]
            change_text = f'<span style="color: {change_color}; font-size: 12px;">{change_arrow} {change:+.2f}%</span>'
        
        card_html = f"""
        <div class="metric-card" style="background-color: {colors['card']}; border-color: {colors['border']};">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color: {color};">{value}{unit}</div>
            <div class="metric-change">{change_text}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    
    @staticmethod
    def display_metrics(metrics: Dict[str, Any], cols: int = 4):
        """Display multiple metrics in a grid
        
        Args:
            metrics: Dict with metric_name -> {value, unit, change, positive}
            cols: Number of columns
        """
        columns = st.columns(cols)
        
        for idx, (label, data) in enumerate(metrics.items()):
            with columns[idx % cols]:
                MetricsDisplay.kpi_card(
                    label=label,
                    value=data.get("value", "N/A"),
                    unit=data.get("unit", ""),
                    change=data.get("change"),
                    is_positive=data.get("positive", True)
                )


class ChartComponents:
    """Chart and visualization components"""
    
    @staticmethod
    def line_chart(data: pd.DataFrame, x: str, y: str, title: str,
                   color: Optional[str] = None):
        """Display a modern line chart
        
        Args:
            data: DataFrame with data
            x: X-axis column
            y: Y-axis column
            title: Chart title
            color: Override line color
        """
        theme = get_theme()
        colors = theme.get_colors()
        
        if color is None:
            color = colors["primary"]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data[x],
            y=data[y],
            mode='lines+markers',
            name=y,
            line=dict(color=color, width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)"
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x,
            yaxis_title=y,
            template="plotly_dark" if theme.is_dark else "plotly_white",
            hovermode='x unified',
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        
        return fig
    
    @staticmethod
    def bar_chart(data: pd.DataFrame, x: str, y: str, title: str,
                  color: Optional[str] = None):
        """Display a modern bar chart"""
        theme = get_theme()
        colors = theme.get_colors()
        
        if color is None:
            color = colors["primary"]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data[x],
            y=data[y],
            marker_color=color,
            name=y
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x,
            yaxis_title=y,
            template="plotly_dark" if theme.is_dark else "plotly_white",
            hovermode='x',
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        
        return fig
    
    @staticmethod
    def pie_chart(data: Dict[str, float], title: str):
        """Display a modern pie chart"""
        theme = get_theme()
        colors_dict = theme.get_colors()
        colors_list = [colors_dict["primary"], colors_dict["secondary"], 
                      colors_dict["success"], colors_dict["warning"]]
        
        fig = go.Figure(data=[go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            marker=dict(colors=colors_list),
            textposition='inside',
            textinfo='percent+label'
        )])
        
        fig.update_layout(
            title=title,
            template="plotly_dark" if theme.is_dark else "plotly_white",
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        
        return fig
    
    @staticmethod
    def gauge_chart(value: float, max_value: float = 100, 
                    title: str = "Progress", thresholds: Optional[Dict] = None):
        """Display a gauge chart"""
        theme = get_theme()
        colors = theme.get_colors()
        
        # Determine color based on value
        if thresholds:
            if value >= thresholds.get("critical", 80):
                gauge_color = colors["error"]
            elif value >= thresholds.get("warning", 50):
                gauge_color = colors["warning"]
            else:
                gauge_color = colors["success"]
        else:
            gauge_color = colors["primary"]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            title={'text': title},
            delta={'reference': max_value * 0.8},
            gauge={
                'axis': {'range': [0, max_value]},
                'bar': {'color': gauge_color},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': "rgba(44, 160, 44, 0.3)"},
                    {'range': [max_value * 0.5, max_value * 0.8], 'color': "rgba(255, 165, 0, 0.3)"},
                    {'range': [max_value * 0.8, max_value], 'color': "rgba(214, 39, 40, 0.3)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_dark" if theme.is_dark else "plotly_white",
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        
        return fig


class TableComponents:
    """Table display components"""
    
    @staticmethod
    def trades_table(df: pd.DataFrame):
        """Display trades in a styled table"""
        theme = get_theme()
        colors = theme.get_colors()
        
        # Format dataframe for display
        display_df = df.copy()
        
        # Color code P&L
        def format_pnl(val):
            if pd.isna(val):
                return val
            return f"{'🟢' if val > 0 else '🔴'} {val:.2f}"
        
        if "P&L" in display_df.columns:
            display_df["P&L"] = display_df["P&L"].apply(format_pnl)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
        )
    
    @staticmethod
    def positions_table(df: pd.DataFrame):
        """Display open positions in a styled table"""
        theme = get_theme()
        
        # Format dataframe
        display_df = df.copy()
        
        # Add visual indicators
        if "Risk" in display_df.columns:
            display_df["Risk"] = display_df["Risk"].apply(
                lambda x: f"🔴 {x:.2f}%" if x > 3 else f"🟡 {x:.2f}%" if x > 1.5 else f"🟢 {x:.2f}%"
            )
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=300,
        )


class AlertComponents:
    """Alert and notification components"""
    
    @staticmethod
    def alert_box(message: str, alert_type: str = "info"):
        """Display an alert box
        
        Args:
            message: Alert message
            alert_type: success, warning, error, info
        """
        theme = get_theme()
        colors = theme.get_colors()
        
        icon_map = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }
        
        color_map = {
            "success": colors["success"],
            "warning": colors["warning"],
            "error": colors["error"],
            "info": colors["primary"]
        }
        
        color = color_map.get(alert_type, colors["primary"])
        icon = icon_map.get(alert_type, "•")
        
        alert_html = f"""
        <div style="
            background-color: {colors['card']};
            border-left: 4px solid {color};
            padding: 12px 16px;
            border-radius: 4px;
            margin: 10px 0;
            border: 1px solid {colors['border']};
        ">
            <span style="color: {color}; font-weight: bold; font-size: 16px;">{icon}</span>
            <span style="color: {colors['text']}; margin-left: 8px;">{message}</span>
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)
    
    @staticmethod
    def status_indicator(status: str, text: str):
        """Display a status indicator with text"""
        status_symbols = {
            "active": "🟢",
            "inactive": "🔴",
            "warning": "🟡",
            "pending": "🔵",
        }
        
        symbol = status_symbols.get(status, "•")
        st.markdown(f"### {symbol} {text}")


class FormComponents:
    """Form input components"""
    
    @staticmethod
    def number_slider(label: str, min_value: float, max_value: float,
                      step: float = 1.0, default: Optional[float] = None,
                      help_text: Optional[str] = None) -> float:
        """Display a styled number slider"""
        if default is None:
            default = (min_value + max_value) / 2
        
        return st.slider(
            label,
            min_value=min_value,
            max_value=max_value,
            value=default,
            step=step,
            help=help_text
        )
    
    @staticmethod
    def select_option(label: str, options: List[str], 
                      default: Optional[str] = None,
                      help_text: Optional[str] = None) -> str:
        """Display a styled select box"""
        return st.selectbox(label, options, index=0, help=help_text)


def render_header():
    """Render main header with logo and navigation"""
    theme = get_theme()
    colors = theme.get_colors()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown(f"## 📈 AI Trading Bot")
    
    with col2:
        st.markdown(f"**Status:** 🟢 Active | **Positions:** 12/50 | **Equity:** $10,250")
    
    with col3:
        st.markdown("")  # Placeholder
    
    st.divider()
