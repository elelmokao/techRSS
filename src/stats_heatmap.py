import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

# Load your data

sub_urls = json.load(open("src/subscription.json"))

# GitHub heatmap colors (light to dark)

github_colors = [
    "#ebedf0",  # 0
    "#c6e48b",  # 1
    "#7bc96f",  # 2
    "#239a3b",  # 3
    "#196127",  # 4
]

sub_urls["total"] = "url"
for hostname in sub_urls.keys():
    df = pd.read_csv(f"stats/{hostname}-2025.csv")
    yearlyrecord = np.zeros(shape=(50 * 7,))
    # iterate through each row in the DataFrame
    for index, row in df.iterrows():
        yearlyrecord[yearlyrecord.shape[0] - 1 - index] = row["count"]
    # Normalize data to 0-4 for color mapping
    max_count = yearlyrecord.max()
    normed = np.zeros_like(yearlyrecord) if max_count == 0 else np.clip(np.round(yearlyrecord / max_count * 4), 0, 4)
    data_2d = normed.reshape(50, 7).transpose()[::-1]

    fig, ax = plt.subplots(figsize=(10, 10))
    img = ax.matshow(data_2d, aspect="auto", cmap=ListedColormap(github_colors), vmin=0, vmax=4)
    ax.grid(color="white", lw=2, clip_on=False)
    ax.set_yticks([-0.5 + i for i in range(7)])
    # Add single-letter day labels on the left side (M T W T F S S)
    day_letters = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, letter in enumerate(day_letters):
        ax.text(
            -1.5,
            i,
            letter,
            va="center",
            ha="center",
            fontsize=10,
            fontweight="bold",
            color="#555",
            family="monospace",
        )
    ax.set_xticks([-0.5 + i for i in range(50)])
    ax.set_xticklabels([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.xaxis.set_tick_params(length=0, labelbottom=False)
    ax.yaxis.set_tick_params(length=0, labelbottom=False)
    plt.gca().set_aspect("equal")
    plt.title(f"TechRSS Recent Subscriptions - {hostname}  (2025)", fontsize=16, pad=20)
    plt.savefig(f"stats_fig/{hostname}.png", dpi=300, bbox_inches="tight", pad_inches=0.1)
