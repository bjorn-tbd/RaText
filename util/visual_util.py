import pandas as pd
import streamlit as st


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