import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import StringIO

# Color mapping for concentrations
CONCENTRATION_COLORS = {
    "Control": "#d4edda",  # Green
    "1x": "#fff3cd",       # Yellow
    "5x": "#ffeeba",       # Orange
    "10x": "#f8d7da",      # Red
}


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
def draw_mortality_donut(title, percentage, color):
    fig, ax = plt.subplots()
    sizes = [percentage, 100 - percentage]
    colors = [color, "#e0e0e0"]

    ax.pie(
        sizes,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.4)
    )
    ax.text(0, 0, f"{percentage:.1f}%", ha="center", va="center", fontsize=14, weight='bold')
    ax.set_title(title)
    ax.axis("equal")
    return fig


# Show mortality donut charts for selected batch
def show_mortality_charts(data_tuples):
    # Let user pick a batch
    selected_batch = st.selectbox("Select a batch:", [t[0] for t in data_tuples])
    selected_df = dict(data_tuples)[selected_batch]

    # Compute average mortalities
    mortality_1x = selected_df["1x_Mortality (%)"].mean()
    mortality_5x = selected_df["5x_Mortality (%)"].mean()
    mortality_10x = selected_df["10x_Mortality (%)"].mean()

    # Show three side-by-side donut charts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.pyplot(draw_mortality_donut("1x Mortality", mortality_1x, "#FFA07A"))
    with col2:
        st.pyplot(draw_mortality_donut("5x Mortality", mortality_5x, "#FA8072"))
    with col3:
        st.pyplot(draw_mortality_donut("10x Mortality", mortality_10x, "#FF6347"))