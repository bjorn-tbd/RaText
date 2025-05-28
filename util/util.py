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


def calculate_mortality_percentages(mortality_data: pd.DataFrame) -> pd.DataFrame:
    """ Calculate mortality percentages for each concentration in the DataFrame.
    Args:
        df (pd.DataFrame): DataFrame containing alive and dead counts for each concentration.

    Returns:
        pd.DataFrame: DataFrame with additional columns for mortality percentages.
    """
    new_mortality_data = []
    for box_id, df in mortality_data:
        df = df.copy()  # avoid modifying original
        for conc in ["1x", "5x", "10x"]:
            alive_col = f"{conc}_Alive"
            dead_col = f"{conc}_Dead"
            mortality_col = f"{conc}_Mortality (%)"

            df[mortality_col] = df.apply(
                lambda row: (row[dead_col] / (row[alive_col] + row[dead_col]) * 100)
                if (row[alive_col] + row[dead_col]) > 0 else 0.0,
                axis=1
            )
        new_mortality_data.append((box_id, df))
    return new_mortality_data