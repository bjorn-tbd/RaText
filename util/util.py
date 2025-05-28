import pandas as pd


def extract_concentration_data(entry: dict) -> pd.DataFrame:
    all_data = []

    for i in range(7):  # 7 strips
        offsets = [0, 9, 18, 27, 36, 45, 54, 63, 72]
        base_index = offsets[i]
        row = {"Strip": f"Strip {i + 1}"}

        pairs = {
            "Control": (f"{12 + base_index}_Control_alive", f"{13 + base_index}_Control_dead"),
            "1x": (f"{14 + base_index}_rc_1x_alive", f"{15 + base_index}_rc_1x_dead"),
            "5x": (f"{16 + base_index}_rc_5x_alive", f"{17 + base_index}_rc_5x_dead"),
            "10x": (f"{18 + base_index}_rc_10x_alive", f"{19 + base_index}_rc_10x_dead"),
        }

        for conc, (alive_col, dead_col) in pairs.items():
            row[f"{conc}_Alive"] = entry.get(alive_col, "")
            row[f"{conc}_Dead"] = entry.get(dead_col, "")

        all_data.append(row)

    return pd.DataFrame(all_data)