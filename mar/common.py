# -*- coding: utf-8 -*-
# common.py

"""
Shared constants and utility helpers for CLI parsing, data handling, and reporting.

"""

from __future__ import annotations

import csv
import pydoc
import re
import sys
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from tabulate import tabulate

# -----------------------------
# Builtins monkey-patch for input "exit"
# -----------------------------


def _custom_input(prompt: str = "") -> str:
    """Wrap built-in input to allow 'exit' to quit gracefully."""
    user_input = _original_input(prompt)
    if user_input.lower() == "exit":
        print("Exiting the program.")
        sys.exit()
    return user_input


# Set __builtins__ module or a dictionary
if isinstance(__builtins__, dict):
    _original_input = __builtins__["input"]
    __builtins__["input"] = _custom_input
else:
    _original_input = __builtins__.input
    __builtins__.input = _custom_input


# -----------------------------
# Formula helpers
# -----------------------------

MICROS_PER_UNIT = Decimal("1000000")


def micros_to_decimal(
    micros: Optional[int | str],
    quantize: Optional[Decimal] = None,
    rounding=ROUND_HALF_UP,
) -> Decimal:
    """Convert micro-units to Decimal without precision loss."""
    if micros in (None, ""):
        value = Decimal("0")
    else:
        value = Decimal(str(micros)) / MICROS_PER_UNIT
    if quantize is not None:
        return value.quantize(quantize, rounding=rounding)
    return value


# -----------------------------
# Console errors
# -----------------------------


def user_error(err_type: int) -> None:
    """Exit with a consistent user-facing error message."""
    if err_type == 1:
        sys.exit("Problem with MAIN loop.")
    if err_type == 2:
        sys.exit("Invalid input.")
    elif err_type in [3, 4]:
        sys.exit("Problem with output data.")


# -----------------------------
# Table / CSV display
# -----------------------------


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from a filename string."""
    return re.sub(r'[<>:"/\\|?*]', "", name)


def save_csv(table_data, headers) -> None:
    """Persist table data to a CSV in the user's home directory."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_file_name = f"gads_report_{timestamp}.csv"
    print(f"Default file name: {default_file_name}")

    file_name_input = input("Enter a file name (or leave blank for default): ").strip()
    if file_name_input:
        base_name = file_name_input.replace(".csv", "").strip()
        safe_name = sanitize_filename(base_name)
        if not safe_name:
            print("Invalid file name entered. Using default instead.")
            file_name = default_file_name
        else:
            file_name = f"{safe_name}.csv"
    else:
        file_name = default_file_name

    file_path = Path.home() / file_name
    try:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(table_data)
        print(f"\nData saved to: {file_path}\n")
    except Exception as e:
        print(f"\nFailed to save file: {e}\n")


def display_table(table_data, headers, auto_view: bool = False) -> None:
    """Render tabular data via 'tabulate'."""
    if auto_view:
        print(tabulate(table_data, headers, tablefmt="simple_grid"))
    else:
        input(
            "Report ready for viewing. Press ENTER to display results and 'Q' to exit output when done..."
        )
        pydoc.pager(tabulate(table_data, headers=headers, tablefmt="simple_grid"))


def data_handling_options(
    table_data,
    headers,
    auto_view: bool = False,
    preselected_output: Optional[str] = None,
) -> None:
    """Handle report output mode (CSV vs. table)."""
    if auto_view:
        if not table_data or not headers:
            print("No data to display.")
            return
        display_table(table_data, headers, auto_view=True)
        return

    report_view = preselected_output
    if not report_view:
        print(
            "How would you like to view the report?\n1. CSV\n2. Display table on screen\n"
        )
        report_view = input("Choose 1 or 2 ('exit' to exit): ").strip().lower()

    if report_view in ("1", "csv"):
        save_csv(table_data, headers)
    elif report_view in ("2", "table"):
        display_table(table_data, headers)
    elif report_view == "auto":
        display_table(table_data, headers, auto_view=True)
    else:
        print("Invalid input, please select one of the indicated options.")
        sys.exit(1)


# -----------------------------
# Timedate parsing / ranges
# -----------------------------

SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%Y%m%d")


def parse_supported_date(date_str: str) -> date:
    """Parse date string using supported formats."""
    for fmt in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except (TypeError, ValueError):
            continue
    raise ValueError(f"Unsupported date format: {date_str}")


def validate_date_input(
    date_str: Optional[str], default_today: bool = False
) -> Optional[str]:
    """Validate a date string and normalize optional defaults."""
    if not date_str:
        if default_today:
            today = date.today()
            today_str = today.strftime("%Y-%m-%d")
            print(f"No date entered. Defaulting to today's date: {today_str}")
            return today_str
        print(
            "Invalid date format. Please use YYYY-MM-DD or YYYYMMDD (e.g., 2025-03-14 or 20250314)."
        )
        return None
    try:
        parse_supported_date(date_str)
        return date_str
    except ValueError:
        print(
            "Invalid date format. Please use YYYY-MM-DD or YYYYMMDD (e.g., 2025-02-06 or 20250206)."
        )
        return None


def get_last30days() -> tuple[str, date, date, str]:
    today_actual = date.today()
    start_date = today_actual - timedelta(days=30)
    end_date = today_actual - timedelta(days=1)
    return "Date range", start_date, end_date, "date"


def get_last_calendar_month() -> tuple[str, date, date, str]:
    today_actual = date.today()
    first_of_this_month = today_actual.replace(day=1)
    last_day_prev_month = first_of_this_month - timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)
    return "Last calendar month", first_day_prev_month, last_day_prev_month, "month"


def get_quarter_dates(year: int, quarter: int) -> tuple[date, date]:
    if quarter not in (1, 2, 3, 4):
        raise ValueError("Quarter must be between 1 and 4")
    if quarter == 1:
        return date(year, 1, 1), date(year, 3, 31)
    if quarter == 2:
        return date(year, 4, 1), date(year, 6, 30)
    if quarter == 3:
        return date(year, 7, 1), date(year, 9, 30)
    return date(year, 10, 1), date(year, 12, 31)


def get_current_quarter_to_date() -> tuple[str, date, date, str]:
    today_actual = date.today()
    year = today_actual.year
    month = today_actual.month
    current_quarter = (month - 1) // 3 + 1
    q_start, _ = get_quarter_dates(year, current_quarter)
    start_date = q_start
    end_date = today_actual - timedelta(days=1)
    return "Date range", start_date, end_date, "quarter"


def get_previous_calendar_quarter() -> tuple[str, date, date, str]:
    today_actual = date.today()
    year = today_actual.year
    month = today_actual.month
    current_quarter = (month - 1) // 3 + 1
    if current_quarter == 1:
        prev_quarter = 4
        year -= 1
    else:
        prev_quarter = current_quarter - 1
    start_date, end_date = get_quarter_dates(year, prev_quarter)
    return "Date range", start_date, end_date, "quarter"


def get_timerange(
    force_single: bool = False,
) -> tuple[str, str | date, str | date, str]:
    """Prompt for a single date or range, with validation."""
    if force_single:
        date_opt = "Specific date"
        print("The report you selected only accepts a single date for reporting.")
        spec_date_input = input(
            "Enter the date (YYYY-MM-DD or YYYYMMDD) or press ENTER for today: "
        ).strip()
        spec_date = validate_date_input(spec_date_input, default_today=True)
        if spec_date:
            start_date = end_date = spec_date
            time_seg = "date"
            return date_opt, start_date, end_date, time_seg

    while True:
        print("Reporting time range:\n1. Specific date\n2. Range of dates\n")
        date_opt_input = input("Enter 1 or 2: ").strip()
        # specific date
        if date_opt_input == "1":
            date_opt = "Specific date"
            while True:
                spec_date_input = input(
                    "Enter the date (YYYY-MM-DD or YYYYMMDD) or press ENTER for today: "
                ).strip()
                spec_date = validate_date_input(spec_date_input, default_today=True)
                if spec_date:
                    start_date = end_date = spec_date
                    time_seg = "date"
                    print(
                        "Single date option selected, defaulting time segmentation to 'date'."
                    )
                    return date_opt, start_date, end_date, time_seg
        # range
        elif date_opt_input == "2":
            date_opt = "Date range"
            while True:
                start_input = input("Start Date (YYYY-MM-DD or YYYYMMDD): ").strip()
                end_input = input("End Date (YYYY-MM-DD or YYYYMMDD): ").strip()
                start_val = validate_date_input(start_input, default_today=True)
                end_val = validate_date_input(end_input, default_today=True)
                if not (start_val and end_val):
                    continue
                start_dt = parse_supported_date(start_val)
                end_dt = parse_supported_date(end_val)
                if start_dt > end_dt:
                    print("Start date cannot be later than end date. Please re-enter.")
                    continue
                start_date = start_val
                end_date = end_val
                while True:
                    print(
                        "\nDate range segmentation:\n"
                        "1. Day\n"
                        "2. Week\n"
                        "3. Month\n"
                        "4. Quarter\n"
                        "5. Year\n"
                    )
                    time_seg_input = input(
                        "Select from one of the above numbered options (1-5): "
                    ).strip()
                    time_seg_options = {
                        "1": "date",
                        "2": "week",
                        "3": "month",
                        "4": "quarter",
                        "5": "year",
                    }
                    time_seg = time_seg_options.get(time_seg_input)
                    if time_seg:
                        return date_opt, start_date, end_date, time_seg
                    print("Invalid segmentation option, please choose 1-5.")
        else:
            print("Invalid option, please enter 1 or 2.")
