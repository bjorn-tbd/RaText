
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Colors for resistance levels
CONCENTRATION_COLORS_RESISTANCE = {
    "low": "#97e9aaE6",     # Green, 90% opacity
    "medium": "#ffeebaE6",  # Orange, 90% opacity
    "high": "#f8d7daE6",    # Red, 90% opacity
    "none": "#add8e6E6"     # Light Blue, 90% opacity
}

# Color mapping for concentrations
CONCENTRATION_COLORS = {
    "Control": "#ffffff",  # White
    "1x": "#d4edda",       # Green
    "5x": "#ffeeba",       # Orange
    "10x": "#f8d7da",      # Red
}

def __get_marker_color(row):
    # Calculate survival % at each resistance concentration
    # Defensive: handle missing mortality values as 100% mortality (0% survival)
    def survival_at(mortality_col):
        val = row.get(mortality_col)
        return 100 - val if pd.notna(val) else 0

    survival_1x = survival_at("1x_Mortality (%)")
    survival_5x = survival_at("5x_Mortality (%)")
    survival_10x = survival_at("10x_Mortality (%)")

    # Check highest applicable resistance level where survival >= 25%
    if survival_10x >= 25:
        return CONCENTRATION_COLORS_RESISTANCE["high"]
    elif survival_5x >= 25:
        return CONCENTRATION_COLORS_RESISTANCE["medium"]
    elif survival_1x >= 25:
        return CONCENTRATION_COLORS_RESISTANCE["low"]
    else:
        return CONCENTRATION_COLORS_RESISTANCE["none"]
    

def render_colored_table(df: pd.DataFrame):
    def style_cell(conc: str, val: any) -> str:
        color = CONCENTRATION_COLORS.get(conc.split("_")[0], "#ffffff")
        return f'<td style="background-color: {color}; text-align: center;">{val}</td>'

    html = '<table style="width: 100%; border-collapse: collapse;" border="1">'
    html += "<thead><tr><th>Strip</th>"

    for conc in ["Control", "1x", "5x", "10x"]:
        html += f'<th colspan="2" style="background-color: {CONCENTRATION_COLORS[conc]};">{conc}</th>'
    html += "</tr><tr><th></th>"
    for _ in ["Control", "1x", "5x", "10x"]:
        html += "<th>Alive</th><th>Dead</th>"
    html += "</tr></thead><tbody>"

    for _, row in df.iterrows():
        html += f"<tr><td>{row['Strip']}</td>"
        for conc in ["Control", "1x", "5x", "10x"]:
            html += style_cell(f"{conc}_Alive", row[f"{conc}_Alive"])
            html += style_cell(f"{conc}_Dead", row[f"{conc}_Dead"])
        html += "</tr>"

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# Draw a single donut chart for mortality
def draw_resistance_donut(title, percentage, color):
    fig, ax = plt.subplots(facecolor="#f6f6f6")
    sizes = [percentage, 100 - percentage]
    colors = [color, "#e0e0e0"]

    ax.pie(
        sizes,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.4),
    )
    ax.text(0, 0, f"{percentage:.1f}%", ha="center", va="center", fontsize=14, weight='bold')
    ax.set_title(title, fontdict={'fontsize': 28, 'weight': 'bold'})
    ax.axis("equal")
    fig.patch.set_facecolor("#f6f6f6")
    return fig


def show_resistance_charts(grouped, region_column):
    if grouped is None or grouped.empty:
        st.warning("No data matched any region in the GeoJSON.")
        return

    for _, row in grouped.iterrows():
        st.markdown(f"### Region: {row[region_column]}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.pyplot(draw_resistance_donut("Light resistance", row["1x"], "#d4edda"))
        with col2:
            st.pyplot(draw_resistance_donut("Medium Resistance", row["5x"], "#ffeeba"))
        with col3:
            st.pyplot(draw_resistance_donut("High Resistance", row["10x"], "#f8d7da"))


def new_map(raw_coords):
    if raw_coords:
        df_coords = pd.concat(raw_coords, ignore_index=True)

        # Ensure required columns
        if not {'latitude', 'longitude'}.issubset(df_coords.columns):
            st.error("Missing latitude or longitude columns")
            return

        # Create color column as RGBA list
        df_coords['color'] = df_coords.apply(__get_marker_color, axis=1)

        # Optional: control point size by intensity
        # TODO: have the size increase with mortality fully. Currently, it is set to 10x, others not counted.
        df_coords['size'] = df_coords["10x_Mortality (%)"].fillna(50) * 40
        df_coords['size'] = df_coords['size'] * 20


        st.map(
            df_coords,
            latitude="latitude",
            longitude="longitude",
            color="color",
            size="size",
            use_container_width=True
        )