import matplotlib.patches as patches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import pandas as pd

HIT_COST = 4
CAPTAIN_COLOUR = "#ffd700"
VICE_CAPTAIN_COLOUR = "#c0c0c0"

BOX_HEIGHT = 0.84
BOX_WIDTH = 8
PLAYER_SPACING = 1
PLAYER_NAME_FONT_SIZE = 12
GAMEWEEK_SPACING = 12
POSITION_BORDER_WIDTH = 0.08
CAPTAIN_BORDER_WIDTH = 0.15

BG_COLOUR = "#1a1a1a"
CELL_BG_COLOUR = "#2d2d2d"
BENCH_BG_COLOUR = "#404040"
TEXT_COLOUR = "#ffffff"
STATS_COLOUR = "#a0a0a0"
CHIP_BACKGROUND_COLOUR = "#222222"
CHIP_BACKGROUND_ZORDERS = {
    "RU": -1.0,
    "WC": -5.0,
    "AA": -5.0,
    "DK": -5.0,
}
POSITION_COLOURS = {"KPR": "#4a1b7a", "FOR": "#0d4a6b", "MID": "#6b5c0d", "ANG": "#6b1d1d"}
BASE_Y = 15


def calculate_bezier(x_start, x_end, y_start, y_end):
    """
    Calculates a bezier curve using the 4 given points.
    These are used to draw the lines signifying transfers between gameweeks.
    """
    x_control1 = x_start + (x_end - x_start) * 0.3
    x_control2 = x_start + (x_end - x_start) * 0.7
    y_control1 = y_start + (y_end - y_start) * 0.02
    y_control2 = y_start + (y_end - y_start) * 0.98

    path_data = [
        ((x_start, y_start), mpath.Path.MOVETO),
        ((x_control1, y_control1), mpath.Path.CURVE4),
        ((x_control2, y_control2), mpath.Path.CURVE4),
        ((x_end, y_end), mpath.Path.CURVE4),
    ]

    return patches.PathPatch(
        mpath.Path(*zip(*path_data)),
        facecolor="none",
        edgecolor=TEXT_COLOUR,
        alpha=0.75,
        linewidth=1,
        zorder=-3.0,
    )


def calculate_player_cells(gw_idx, player_idx, player):
    y_pos = BASE_Y - player_idx * PLAYER_SPACING
    data = []

    # base cell
    data.append(
        patches.Rectangle(
            (gw_idx * GAMEWEEK_SPACING - BOX_WIDTH / 2, y_pos - BOX_HEIGHT / 2),
            BOX_WIDTH,
            BOX_HEIGHT,
            facecolor=CELL_BG_COLOUR if player["lineup"] else BENCH_BG_COLOUR,
            edgecolor="none",
        )
    )

    # position border
    data.append(
        patches.Rectangle(
            (gw_idx * GAMEWEEK_SPACING - BOX_WIDTH / 2, y_pos - BOX_HEIGHT / 2),
            BOX_WIDTH,
            POSITION_BORDER_WIDTH,
            facecolor=POSITION_COLOURS[player["pos"]],
            edgecolor="none",
        )
    )

    # captain border
    if player["captain"] == 1 and gw_idx > 0:
        data.append(
            patches.Rectangle(
                (gw_idx * GAMEWEEK_SPACING - BOX_WIDTH / 2, y_pos - BOX_HEIGHT / 2),
                CAPTAIN_BORDER_WIDTH,
                BOX_HEIGHT,
                facecolor=CAPTAIN_COLOUR,
                edgecolor="none",
            )
        )

    # vice captain border
    elif player["vicecaptain"] == 1 and gw_idx > 0:
        data.append(
            patches.Rectangle(
                (gw_idx * GAMEWEEK_SPACING - BOX_WIDTH / 2, y_pos - BOX_HEIGHT / 2),
                CAPTAIN_BORDER_WIDTH,
                BOX_HEIGHT,
                facecolor=VICE_CAPTAIN_COLOUR,
                edgecolor="none",
            )
        )

    return data


def create_squad_timeline(current_squad, statistics, picks, filename):
    df = pd.DataFrame(picks)
    df_squad = df[df["squad"] == 1]
    df_base = df[df["week"] == min(df["week"])]
    gameweeks = sorted(df_squad["week"].unique())
    base_week = min(gameweeks) - 1
    ru_week = df.loc[df["chip"] == "RU"].iloc[0]["week"] if len(df.loc[df["chip"] == "RU"]) > 0 else None

    fig, ax = plt.subplots(figsize=(24, 12))
    ax.set_facecolor(BG_COLOUR)
    fig.patch.set_facecolor(BG_COLOUR)

    player_indexes = {}
    display_weeks = [base_week] + gameweeks if base_week > 0 else gameweeks
    for gw_idx, week in enumerate(display_weeks):
        if week == base_week:
            gw_players = df_base[df_base["id"].isin(current_squad)]
            gw_players.loc[:, "lineup"] = 1
            ax.text(gw_idx * GAMEWEEK_SPACING, BASE_Y + 1, "Base", color=TEXT_COLOUR, fontsize=10, ha="center")
        else:
            gw_players = df_squad[df_squad["week"] == week]
            ax.text(gw_idx * GAMEWEEK_SPACING, BASE_Y + 1, f"GW{week}", color=TEXT_COLOUR, fontsize=10, ha="center")
            if "chip" in gw_players.columns and not gw_players["chip"].isna().all():
                try:
                    chip = gw_players.loc[gw_players["chip"] != ""]["chip"].iloc[0]
                except Exception:
                    chip = gw_players["chip"].iloc[0]
                if pd.notna(chip):
                    ax.text(gw_idx * GAMEWEEK_SPACING, BASE_Y + 0.7, chip, color=TEXT_COLOUR, fontsize=8, ha="center")

        starting_xi = gw_players[gw_players["lineup"] == 1].sort_values(["type", "xP"], ascending=[True, False]).reset_index()
        bench = gw_players[gw_players["lineup"] == 0].sort_values(["type", "xP"], ascending=[True, False]).reset_index()
        bench.index = bench.index + 11

        player_indexes[week] = {}
        # PLAYER CELLS STARTING XI
        for player_idx, player in starting_xi.iterrows():
            y_pos = BASE_Y - player_idx * PLAYER_SPACING
            player_indexes[week][player["id"]] = (y_pos, player["pos"])

            cells = calculate_player_cells(gw_idx, player_idx, player)
            for cell in cells:
                ax.add_patch(cell)
            text_pos = (gw_idx * GAMEWEEK_SPACING, y_pos + 0.15)
            ax.text(*text_pos, player["name"], color=TEXT_COLOUR, ha="center", va="center", fontsize=PLAYER_NAME_FONT_SIZE)

            if week != base_week:
                stats_text = f"{player['xP']:.1f} xPts : {int(player['xMin'])} xMin"
                ax.text(gw_idx * GAMEWEEK_SPACING, y_pos - 0.18, stats_text, color=STATS_COLOUR, ha="center", va="center", fontsize=8)

        # PLAYER CELLS BENCH
        for player_idx, player in bench.iterrows():
            y_pos = BASE_Y - player_idx * PLAYER_SPACING
            player_indexes[week][player["id"]] = (BASE_Y - player_idx * PLAYER_SPACING, player["pos"])
            cells = calculate_player_cells(gw_idx, player_idx, player)
            for cell in cells:
                ax.add_patch(cell)
            text_pos = (gw_idx * GAMEWEEK_SPACING, y_pos + 0.15)
            ax.text(*text_pos, player["name"], color=TEXT_COLOUR, ha="center", va="center", fontsize=PLAYER_NAME_FONT_SIZE)

            stats_text = f"{player['xP']:.1f} xPts : {int(player['xMin'])} xMin"
            ax.text(gw_idx * GAMEWEEK_SPACING, y_pos - 0.18, stats_text, color=STATS_COLOUR, ha="center", va="center", fontsize=8)

        # TRANSFERS
        prev_week_int = int(display_weeks[gw_idx - 1])
        transfers_in = picks.loc[(picks["week"] == week) & (picks["transfer_in"] == 1)]
        transfers_out = picks.loc[(picks["week"] == week) & (picks["transfer_out"] == 1)]

        for pos in ["KPR", "FOR", "MID", "ANG"]:
            players_out = transfers_out.loc[transfers_out["pos"] == pos].to_dict(orient="records")
            players_in = transfers_in.loc[transfers_in["pos"] == pos].to_dict(orient="records")

            for player_out, player_in in zip(players_out, players_in):
                skip_ru = int(prev_week_int == ru_week)
                x_start = (gw_idx - 1 - skip_ru) * GAMEWEEK_SPACING + BOX_WIDTH / 2
                x_end = gw_idx * GAMEWEEK_SPACING - BOX_WIDTH / 2
                y_start = player_indexes[prev_week_int - skip_ru][player_out["id"]][0]
                y_end = player_indexes[week][player_in["id"]][0]
                ax.add_patch(calculate_bezier(x_start, x_end, y_start, y_end))

        # GAMEWEEK STATISTICS
        if week != base_week:
            stats_y = BASE_Y - (player_idx + 0.5) * PLAYER_SPACING
            ax.text(gw_idx * GAMEWEEK_SPACING, stats_y - 0.4, f"{statistics[week]['xP']:.2f} xPts", color=TEXT_COLOUR, fontsize=12, ha="center")
            ax.text(
                gw_idx * GAMEWEEK_SPACING,
                stats_y - 0.8,
                f"ITB: {statistics[week - 1]['itb']} -> {statistics[week]['itb']:.1f}",
                color=TEXT_COLOUR,
                fontsize=10,
                ha="center",
            )

            if statistics[week]["chip"] not in ["RU", "WC"]:
                fts_available = statistics[week]["ft_state"]
                transfer_str = f"FTs: {statistics[week]['nt']}/{fts_available}"
                if statistics[week]["pt"] > 0:
                    transfer_str += f" (-{statistics[week]['pt'] * HIT_COST})"
                ax.text(gw_idx * GAMEWEEK_SPACING, stats_y - 1.2, transfer_str, color=TEXT_COLOUR, fontsize=10, ha="center")

    total_width = (len(display_weeks) - 1) * GAMEWEEK_SPACING + BOX_WIDTH
    ax.set_xlim(-5, total_width)
    bottom_limit = BASE_Y - (player_idx + 2.5) * PLAYER_SPACING
    top_limit = BASE_Y + 2.3
    ax.set_ylim(bottom_limit, top_limit)
    ax.axis("off")

    plt.title(filename, color=TEXT_COLOUR)
    chip_weeks = dict(df.loc[df["chip"] != ""][["week", "chip"]].drop_duplicates().values)

    for gw, chip in chip_weeks.items():
        x_center = (gw - base_week) * GAMEWEEK_SPACING
        # draw background rectangle on gws with active chip
        rect = patches.FancyBboxPatch(
            (x_center - GAMEWEEK_SPACING / 2, bottom_limit),
            GAMEWEEK_SPACING,
            top_limit - bottom_limit,
            edgecolor="none",
            facecolor=CHIP_BACKGROUND_COLOUR,
            zorder=CHIP_BACKGROUND_ZORDERS[chip],
            boxstyle=patches.BoxStyle("Round", pad=-0.5, rounding_size=1),
            alpha=0.9,
        )
        ax.add_patch(rect)
    plt.savefig("data/images/" + filename + ".png", bbox_inches="tight", facecolor=BG_COLOUR)
    plt.close()
