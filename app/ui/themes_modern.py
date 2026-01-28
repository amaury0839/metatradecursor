"""Modern Theme System - Professional Color Palettes and Styling"""

import streamlit as st
from typing import Dict, Any

class ColorPalette:
    """Modern color palette with professional colors"""
    
    # Primary Colors
    PRIMARY = "#1F77B4"          # Professional Blue
    SECONDARY = "#FF7F0E"       # Accent Orange
    ACCENT = "#FF7F0E"          # Same as secondary
    
    # Status Colors
    SUCCESS = "#2CA02C"          # Green
    WARNING = "#FFA500"          # Amber
    ERROR = "#D62728"            # Red
    INFO = "#1F77B4"             # Blue
    NEUTRAL = "#7F7F7F"          # Gray
    
    # Dark Theme
    DARK_BG = "#0D1117"
    DARK_CARD = "#161B22"
    DARK_BORDER = "#30363D"
    DARK_TEXT = "#E6EDF3"
    DARK_TEXT_SECONDARY = "#8B949E"
    
    # Light Theme
    LIGHT_BG = "#FFFFFF"
    LIGHT_CARD = "#F6F8FA"
    LIGHT_BORDER = "#E1E4E8"
    LIGHT_TEXT = "#24292E"
    LIGHT_TEXT_SECONDARY = "#6A737D"
    
    # Chart Colors
    CHART_COLORS = [
        "#1F77B4",  # Blue
        "#FF7F0E",  # Orange
        "#2CA02C",  # Green
        "#D62728",  # Red
        "#9467BD",  # Purple
        "#8C564B",  # Brown
        "#E377C2",  # Pink
        "#7F7F7F",  # Gray
    ]


class ThemeConfig:
    """Theme configuration and styling"""
    
    def __init__(self, theme: str = "dark"):
        self.theme = theme
        self.is_dark = theme == "dark"
        self.palette = ColorPalette()
        
        # Set theme colors
        if self.is_dark:
            self.bg_color = self.palette.DARK_BG
            self.card_color = self.palette.DARK_CARD
            self.text_color = self.palette.DARK_TEXT
            self.text_secondary = self.palette.DARK_TEXT_SECONDARY
            self.border_color = self.palette.DARK_BORDER
        else:
            self.bg_color = self.palette.LIGHT_BG
            self.card_color = self.palette.LIGHT_CARD
            self.text_color = self.palette.LIGHT_TEXT
            self.text_secondary = self.palette.LIGHT_TEXT_SECONDARY
            self.border_color = self.palette.LIGHT_BORDER
    
    def apply_theme(self):
        """Apply theme to Streamlit"""
        st.set_page_config(
            page_title="AI Forex Trading Bot",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                "Get Help": "https://github.com",
                "Report a bug": "https://github.com",
                "About": "AI Forex Trading Bot v2.0"
            }
        )
        
        # Streamlit theming via markdown/CSS
        self._inject_css()
    
    def _inject_css(self):
        """Inject custom CSS for theming"""
        css = f"""
        <style>
        :root {{
            --primary-color: {self.palette.PRIMARY};
            --secondary-color: {self.palette.SECONDARY};
            --success-color: {self.palette.SUCCESS};
            --warning-color: {self.palette.WARNING};
            --error-color: {self.palette.ERROR};
            --bg-color: {self.bg_color};
            --card-color: {self.card_color};
            --text-color: {self.text_color};
            --text-secondary: {self.text_secondary};
            --border-color: {self.border_color};
        }}
        
        * {{
            color: {self.text_color};
        }}
        
        body {{
            background-color: {self.bg_color};
        }}
        
        .stMetric {{
            background-color: {self.card_color};
            border-radius: 8px;
            padding: 16px;
            border: 1px solid {self.border_color};
        }}
        
        .stTabs {{
            background-color: {self.card_color};
            border-radius: 8px;
            border: 1px solid {self.border_color};
        }}
        
        .stDataFrame {{
            background-color: {self.card_color};
            border-radius: 8px;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: {self.text_color} !important;
        }}
        
        [data-testid="stAppViewContainer"] {{
            background-color: {self.bg_color};
        }}
        
        [data-testid="stSidebar"] {{
            background-color: {self.card_color};
            border-right: 1px solid {self.border_color};
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {self.text_secondary};
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, {self.card_color} 0%, {self.border_color} 100%);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {self.border_color};
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .metric-label {{
            color: {self.text_secondary};
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-value {{
            color: {self.palette.PRIMARY};
            font-size: 28px;
            font-weight: 700;
            margin: 8px 0;
        }}
        
        .metric-change {{
            font-size: 12px;
            font-weight: 500;
        }}
        
        .metric-change.positive {{
            color: {self.palette.SUCCESS};
        }}
        
        .metric-change.negative {{
            color: {self.palette.ERROR};
        }}
        
        .section-header {{
            border-bottom: 2px solid {self.palette.PRIMARY};
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .info-box {{
            background-color: {self.card_color};
            border-left: 4px solid {self.palette.INFO};
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        
        .success-box {{
            background-color: {self.card_color};
            border-left: 4px solid {self.palette.SUCCESS};
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        
        .warning-box {{
            background-color: {self.card_color};
            border-left: 4px solid {self.palette.WARNING};
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        
        .error-box {{
            background-color: {self.card_color};
            border-left: 4px solid {self.palette.ERROR};
            padding: 12px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    def get_colors(self) -> Dict[str, str]:
        """Get color dictionary for current theme"""
        return {
            "primary": self.palette.PRIMARY,
            "secondary": self.palette.SECONDARY,
            "success": self.palette.SUCCESS,
            "warning": self.palette.WARNING,
            "error": self.palette.ERROR,
            "neutral": self.palette.NEUTRAL,
            "bg": self.bg_color,
            "card": self.card_color,
            "text": self.text_color,
            "text_secondary": self.text_secondary,
            "border": self.border_color,
        }


def get_theme() -> ThemeConfig:
    """Get or create theme in session state"""
    if "theme" not in st.session_state:
        st.session_state.theme = ThemeConfig(theme="dark")
    return st.session_state.theme


def apply_global_theme():
    """Apply global theme styling"""
    theme = get_theme()
    theme.apply_theme()
    return theme


# Styling Utilities
def metric_card(label: str, value: str, change: str = None, is_positive: bool = True):
    """Display a styled metric card"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.metric(label, value)
    
    if change:
        with col2:
            theme = get_theme()
            change_color = "🟢" if is_positive else "🔴"
            st.markdown(f"{change_color} **{change}**")


def section_header(title: str, icon: str = ""):
    """Display a styled section header"""
    st.markdown(f"### {icon} {title}")
    st.divider()


def info_box(message: str, title: str = "ℹ️ Info"):
    """Display an info box"""
    st.markdown(f"""
    <div class="info-box">
        <strong>{title}</strong><br>
        {message}
    </div>
    """, unsafe_allow_html=True)


def success_box(message: str, title: str = "✅ Success"):
    """Display a success box"""
    st.markdown(f"""
    <div class="success-box">
        <strong>{title}</strong><br>
        {message}
    </div>
    """, unsafe_allow_html=True)


def warning_box(message: str, title: str = "⚠️ Warning"):
    """Display a warning box"""
    st.markdown(f"""
    <div class="warning-box">
        <strong>{title}</strong><br>
        {message}
    </div>
    """, unsafe_allow_html=True)


def error_box(message: str, title: str = "❌ Error"):
    """Display an error box"""
    st.markdown(f"""
    <div class="error-box">
        <strong>{title}</strong><br>
        {message}
    </div>
    """, unsafe_allow_html=True)
