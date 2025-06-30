import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import pandas as pd


def update_hostname_stats(hostname: str, day_windows: int, execute_date: datetime, data: pd.DataFrame, stats_path: str = "stats") -> None:
    count_log = []
    for day_count in range(day_windows):
        day = execute_date - timedelta(days=day_windows - 1) + timedelta(days=day_count)
        if hostname == "total":
            count_log.append(
                {
                    "published_date": day.strftime("%Y-%m-%d"),
                    "count": len(data[data["published_date"] == day.strftime("%Y-%m-%d")]),
                },
            )
        else:
            count_log.append(
                {
                    "published_date": day.strftime("%Y-%m-%d"),
                    "count": len(data[(data["host"] == hostname) & (data["published_date"] == day.strftime("%Y-%m-%d"))]),
                },
            )

    csv_file_path = stats_path / f"{hostname}-{execute_date.year}.csv"
    new_data_df = pd.DataFrame(count_log)

    # Check if CSV file exists
    if csv_file_path.exists():
        # Read existing data
        existing_df = pd.read_csv(csv_file_path)

        # Combine data, with new data overwriting existing entries for same published_date
        combined_df = pd.concat([existing_df, new_data_df], ignore_index=True)
        # Drop duplicates, keeping the last occurrence (new data takes precedence)
        combined_df = combined_df.drop_duplicates(subset=["published_date"], keep="last")

        # Sort by published_date for consistency
        combined_df = combined_df.sort_values("published_date").reset_index(drop=True)

        # Save the updated data
        combined_df.to_csv(csv_file_path, index=False)
    else:
        # Create new CSV file
        new_data_df.to_csv(csv_file_path, index=False)


def update_hostname_stats_csvs(sub_urls: dict[str, str], data: pd.DataFrame, execute_date: datetime, day_windows: int, stats_dir: str = "stats") -> None:
    """
    Update stats files for each hostname with the count of log entries.
    Creates CSV files if they don't exist, or updates existing ones by overwriting duplicated published_date entries.
    """

    # Create stats directory if it doesn't exist
    stats_path = Path(stats_dir)
    if not stats_path.exists():
        stats_path.mkdir(parents=True, exist_ok=True)

    for hostname in sub_urls:
        update_hostname_stats(hostname, day_windows, execute_date, data, stats_path)
    update_hostname_stats("total", day_windows, execute_date, data, stats_path)


def load_sub_urls(file_path: str) -> dict[str, str]:
    """
    Load subscription URLs from a JSON file.
    """
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def grep_rss_urls(sub_urls: dict[str, str], output_path: str, day_windows: int) -> pd.DataFrame:
    """
    Load subscription URLs from a JSON file.
    """
    logs = []
    execute_date = datetime.now(timezone.utc).date()

    for hostname, url in sub_urls.items():
        d = feedparser.parse(url)
        for entry in d.entries:
            try:
                post_date = datetime.fromisoformat(entry.published).astimezone(timezone.utc).date()
            except ValueError:
                if "GMT" in entry.published:
                    post_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc).date()
                elif "+0000" in entry.published:
                    post_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z").date()
                else:
                    post_date = datetime(2020, 1, 1, tzinfo=timezone.utc).date()  # Fallback date if parsing fails
            if post_date < execute_date - timedelta(days=day_windows):
                continue
            logs.append(
                {
                    "host": hostname,
                    "published_date": post_date.strftime("%Y-%m-%d"),
                    "title": entry.title,
                    "url": entry.link,
                },
            )
    data = pd.DataFrame(logs)
    data.to_csv(output_path, index=False)
    return data


if __name__ == "__main__":
    past_days = 7
    execute_date = datetime.now(timezone.utc).date()
    sub_urls = load_sub_urls("src/subscription.json")
    data = grep_rss_urls(sub_urls, f"archive/{execute_date:%Y-%m-%d}.csv", past_days)
    update_hostname_stats_csvs(sub_urls, data, execute_date, past_days)
