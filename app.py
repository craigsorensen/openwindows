"""
Open Windows Notification Script

Monitors indoor and outdoor temperatures and sends push notifications
advising when to open or close windows for optimal cooling.

Morning (6 AM - 1:59 PM): Alerts to CLOSE windows if it's getting hotter outside.
Evening (6 PM - 11:59 PM): Alerts to OPEN windows once it's cooled off outside,
    but only if it was hot enough during the day to warrant it.
"""
from __future__ import annotations
import os
import sys
import logging
from dataclasses import dataclass
from datetime import datetime
from weather_api import weather
from indoor_temp import get_indoor_temperature
from send_push import push
from dbman import db


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class Config:
    """All tunable parameters in one place."""

    # Credential paths (relative to home directory)
    api_key_path: str = ".config/.weatherapi.txt"
    push_cred_path: str = ".openwindows_push_api.txt"

    # Weather location (zip code for WeatherAPI.com)
    local_zipcode: str = "97477"

    # Compensates for the fact that it may still feel warm outside even as
    # the thermometer drops.  Subtracted from outdoor temp before comparisons.
    # Set to 0 to disable.
    outside_degree_buffer: int = 2

    # The outdoor daily-high must reach at least this value (°F) before the
    # "open windows" logic will fire.
    outside_degree_trigger: int = 80

    # The outdoor daily-high must exceed the indoor daily-high by at least
    # this many degrees before the "open windows" logic will fire.
    degree_delta: int = 5


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(log_path: str) -> logging.Logger:
    """Configure a logger that writes to both a file and the console."""
    logger = logging.getLogger("open_windows")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
    )

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


# ---------------------------------------------------------------------------
# Credential helpers
# ---------------------------------------------------------------------------

def load_weather_api_key(filepath: str, logger: logging.Logger) -> str:
    """Read the weather API key from disk or exit with a clear error."""
    if not os.path.isfile(filepath):
        logger.critical(
            "No API credential file found. Expected: %s  — see README for setup instructions.",
            filepath,
        )
        sys.exit(1)

    with open(filepath, "r") as f:
        key = f.readline().strip()

    if not key:
        logger.critical(
            "API credential file is empty: %s  — see README for setup instructions.",
            filepath,
        )
        sys.exit(1)

    return key


def load_push_credentials(filepath: str, logger: logging.Logger) -> tuple[str, str]:
    """Read Pushover token and user key from disk or exit with a clear error."""
    if not os.path.isfile(filepath):
        logger.critical(
            "No push credential file found. Expected: %s  — see README for setup instructions.",
            filepath,
        )
        sys.exit(1)

    with open(filepath, "r") as f:
        creds = f.readlines()

    try:
        token = creds[0].strip().split(":")[1]
        user = creds[1].strip().split(":")[1]
    except (IndexError, KeyError):
        logger.critical(
            "Push credential file is malformed: %s  — expected TOKEN:<value> and USER:<value> on separate lines.",
            filepath,
        )
        sys.exit(1)

    return token, user


# ---------------------------------------------------------------------------
# Temperature helpers
# ---------------------------------------------------------------------------

def fetch_indoor_temp(logger: logging.Logger) -> int:
    """Get the current indoor temperature, or exit on failure."""
    try:
        raw = get_indoor_temperature()
        return round(float(raw["temperature"]))
    except Exception as exc:
        logger.critical("Failed to read indoor temperature: %s", exc)
        sys.exit(1)


def fetch_outdoor_temp(api_key: str, zipcode: str, logger: logging.Logger) -> int:
    """Get the current outdoor temperature, or exit on failure."""
    try:
        wm = weather.WeatherMan(api_key, zipcode)
        return int(round(wm.temperature))
    except Exception as exc:
        logger.critical("Failed to read outdoor temperature: %s", exc)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Time boundary
# ---------------------------------------------------------------------------

def get_time_boundary(hour: int) -> str:
    """
    Return the current operational window based on hour of day.

    'close'  — Morning (6 AM – 1:59 PM): evaluate whether to close windows.
    'open'   — Evening (6 PM – 11:59 PM): evaluate whether to open windows.
    'OOB'    — Outside operational boundary; do nothing.
    """
    if 6 <= hour < 14:
        return "close"
    if 18 <= hour < 24:
        return "open"
    return "OOB"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def initialize_db(dbman, pretty_date: str, logger: logging.Logger) -> dict:
    """Load or create the temperature database, resetting stale data."""
    if dbman.check_if_db_file_exists():
        tempdb = dbman.get_db()
        if tempdb["db_creation_date"] != pretty_date:
            logger.info("DB is from %s — recreating for today.", tempdb["db_creation_date"])
            tempdb = dbman.create_blank_db()
            dbman.write_database_to_disk(tempdb)
        else:
            logger.debug("DB is current (created %s).", pretty_date)
    else:
        logger.info("No database found — creating a new one.")
        tempdb = dbman.create_blank_db()
        dbman.write_database_to_disk(tempdb)

    return tempdb


def update_max_temps(
    tempdb: dict, indoor: int, outdoor: int, dbman, logger: logging.Logger
) -> dict:
    """Update daily-high records if current readings exceed stored values."""
    changed = False

    if indoor > tempdb["indoor_max_temp"]:
        logger.info("Indoor temp %d > stored max %d — updating.", indoor, tempdb["indoor_max_temp"])
        tempdb["indoor_max_temp"] = indoor
        changed = True

    if outdoor > tempdb["outdoor_max_temp"]:
        logger.info("Outdoor temp %d > stored max %d — updating.", outdoor, tempdb["outdoor_max_temp"])
        tempdb["outdoor_max_temp"] = outdoor
        changed = True

    if changed:
        dbman.write_database_to_disk(tempdb)

    return tempdb


# ---------------------------------------------------------------------------
# Notification logic
# ---------------------------------------------------------------------------

def handle_close_window(
    tempdb: dict, outdoor: int, indoor: int, buffer: int,
    token: str, user: str, dbman, message: str, logger: logging.Logger,
) -> None:
    """
    Morning logic: if the adjusted outdoor temp has risen to meet or exceed
    the indoor temp, it's time to close the windows before more heat gets in.
    """
    adjusted_outdoor = outdoor - buffer

    if adjusted_outdoor >= indoor:
        logger.info("CLOSE WINDOWS — outdoor adjusted (%d) >= indoor (%d).", adjusted_outdoor, indoor)
        push.send(token, user, f"CLOSE WINDOWS! {message}")
        tempdb["notification_sent"] = True
        dbman.write_database_to_disk(tempdb)
    else:
        logger.info(
            "No action — outdoor adjusted (%d) still below indoor (%d). Windows can stay open.",
            adjusted_outdoor, indoor,
        )


def handle_open_window(
    tempdb: dict, outdoor: int, indoor: int, buffer: int,
    cfg: Config, token: str, user: str, dbman, message: str, logger: logging.Logger,
) -> None:
    """
    Evening logic: if the day was hot enough (daily high exceeded trigger and
    delta thresholds), check whether it has cooled off enough outside to open
    the windows.
    """
    daily_delta = tempdb["outdoor_max_temp"] - tempdb["indoor_max_temp"]

    logger.debug(
        "Daily delta: %d (need >= %d) | Outdoor max: %d (need >= %d)",
        daily_delta, cfg.degree_delta, tempdb["outdoor_max_temp"], cfg.outside_degree_trigger,
    )

    if daily_delta < cfg.degree_delta or tempdb["outdoor_max_temp"] < cfg.outside_degree_trigger:
        logger.info(
            "Day was not hot enough to trigger open-window logic. Doing nothing."
        )
        return

    adjusted_outdoor = outdoor - buffer

    if adjusted_outdoor <= indoor:
        logger.info("OPEN WINDOWS — outdoor adjusted (%d) <= indoor (%d).", adjusted_outdoor, indoor)
        push.send(token, user, f"OPEN WINDOWS! {message}")
        tempdb["notification_sent"] = True
        dbman.write_database_to_disk(tempdb)
    else:
        logger.info(
            "Still warmer outside adjusted (%d) than inside (%d). Doing nothing.",
            adjusted_outdoor, indoor,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    cfg = Config()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    home_dir = os.path.expanduser("~")

    # Paths
    log_path = os.path.join(script_dir, "app.log")
    db_path = os.path.join(script_dir, "tempdb.json")
    api_key_file = os.path.join(home_dir, cfg.api_key_path)
    push_cred_file = os.path.join(home_dir, cfg.push_cred_path)

    logger = setup_logging(log_path)
    logger.debug("DB path: %s", db_path)

    # Load credentials (exits on failure)
    weather_api_key = load_weather_api_key(api_key_file, logger)
    token, user = load_push_credentials(push_cred_file, logger)

    # Read temperatures (exits on failure)
    indoor_temp = fetch_indoor_temp(logger)
    outdoor_temp = fetch_outdoor_temp(weather_api_key, cfg.local_zipcode, logger)

    now = datetime.now()
    hour = now.hour
    pretty_date = now.strftime("%b-%d-%Y")
    adjusted_outdoor = outdoor_temp - cfg.outside_degree_buffer
    message = f"Inside: {indoor_temp} || Outside: {outdoor_temp} || Outside Adjusted: {adjusted_outdoor}"
    logger.info(message)

    boundary = get_time_boundary(hour)

    # Database setup
    dbman_instance = db.db_manager(db_path)
    tempdb = initialize_db(dbman_instance, pretty_date, logger)
    tempdb = update_max_temps(tempdb, indoor_temp, outdoor_temp, dbman_instance, logger)

    # Check notification lock
    if tempdb["notification_sent"]:
        logger.info("Notification already sent today — exiting.")
        sys.exit(0)

    # Act on the current time boundary
    if boundary == "close":
        handle_close_window(
            tempdb, outdoor_temp, indoor_temp, cfg.outside_degree_buffer,
            token, user, dbman_instance, message, logger,
        )
    elif boundary == "open":
        handle_open_window(
            tempdb, outdoor_temp, indoor_temp, cfg.outside_degree_buffer,
            cfg, token, user, dbman_instance, message, logger,
        )
    else:
        logger.info("Outside operational boundary (hour=%d). %s", hour, message)


if __name__ == "__main__":
    main()
