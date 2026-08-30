import os
import re
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd


# ============================================================
# SETTINGS
# ============================================================

INPUT_FOLDER = Path(".")
OUTPUT_FOLDER = Path("cleaned_csv")
REVIEW_FOLDER = Path("review")
BACKUP_FOLDER = Path("backups")
REPORT_FOLDER = Path("reports")

DATE_OUTPUT_FORMAT = "%Y-%m-%d"


# ============================================================
# CREATE REQUIRED FOLDERS
# ============================================================

def create_folders():

    OUTPUT_FOLDER.mkdir(exist_ok=True)
    REVIEW_FOLDER.mkdir(exist_ok=True)
    BACKUP_FOLDER.mkdir(exist_ok=True)
    REPORT_FOLDER.mkdir(exist_ok=True)


# ============================================================
# FIND CSV FILES
# ============================================================

def find_csv_files():

    if not INPUT_FOLDER.exists():
        print(f"Input folder does not exist: {INPUT_FOLDER}")
        return []

    csv_files = []

    for file in INPUT_FOLDER.rglob("*.csv"):

        # Don't process our own generated CSV files
        if OUTPUT_FOLDER in file.parents:
            continue

        if REVIEW_FOLDER in file.parents:
            continue

        if BACKUP_FOLDER in file.parents:
            continue

        csv_files.append(file)

    return csv_files


# ============================================================
# LOAD CSV
# ============================================================

def load_csv(file_path):

    try:

        df = pd.read_csv(file_path)

        print(f"\nLoaded: {file_path.name}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")

        return df

    except Exception as error:

        print(f"Could not load {file_path.name}")
        print(f"Reason: {error}")

        return None


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

def normalize_column_names(df):

    new_columns = []

    for column in df.columns:

        cleaned = str(column).strip().lower()

        cleaned = re.sub(
            r"\s+",
            "_",
            cleaned
        )

        cleaned = re.sub(
            r"[^a-z0-9_]",
            "",
            cleaned
        )

        new_columns.append(cleaned)

    df.columns = new_columns

    return df


# ============================================================
# ANALYZE CSV
# ============================================================

def analyze_csv(df):

    analysis = {}

    analysis["rows"] = len(df)

    analysis["columns"] = len(df.columns)

    analysis["column_names"] = list(df.columns)

    analysis["missing_values"] = (
        df.isna()
        .sum()
        .to_dict()
    )

    analysis["total_missing"] = int(
        df.isna()
        .sum()
        .sum()
    )

    return analysis


# ============================================================
# PRINT ANALYSIS
# ============================================================

def print_analysis(df, analysis):

    print("\n" + "=" * 50)
    print("CSV ANALYSIS")
    print("=" * 50)

    print(f"Rows: {analysis['rows']}")
    print(f"Columns: {analysis['columns']}")

    print("\nColumns:")

    for column in analysis["column_names"]:

        print(f"  - {column}")

    print("\nMissing values:")

    if analysis["total_missing"] == 0:

        print("  None")

    else:

        for column, amount in analysis["missing_values"].items():

            if amount > 0:

                print(
                    f"  {column}: {amount}"
                )


# ============================================================
# FIND EXACT DUPLICATES
# ============================================================

def find_duplicates(df):

    duplicate_mask = df.duplicated(
        keep=False
    )

    duplicates = df[
        duplicate_mask
    ].copy()

    return duplicates


# ============================================================
# REPORT EXACT DUPLICATES
# ============================================================

def report_duplicates(duplicates):

    if duplicates.empty:

        print("\nNo exact duplicate rows found.")

        return

    print("\n" + "=" * 50)
    print("EXACT DUPLICATES")
    print("=" * 50)

    print(
        f"Found {len(duplicates)} duplicate rows."
    )

    print(
        duplicates.to_string(
            index=False
        )
    )


# ============================================================
# ASK YES / NO
# ============================================================

def ask_yes_no(question):

    while True:

        answer = input(
            f"\n{question} (yes/no): "
        ).strip().lower()

        if answer in ["yes", "y"]:
            return True

        if answer in ["no", "n"]:
            return False

        print(
            "Please enter yes or no."
        )


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):

    before = len(df)

    df = df.drop_duplicates(
        keep="first"
    )

    removed = before - len(df)

    return df, removed


# ============================================================
# CLEAN SPACES
# ============================================================

def clean_spaces(df):

    changed = 0

    for column in df.columns:

        if (
            df[column].dtype == "object"
            or
            pd.api.types.is_string_dtype(
                df[column]
            )
        ):

            before = df[column].copy()

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .str.replace(
                    r"\s+",
                    " ",
                    regex=True
                )
            )

            changed += (
                before.fillna("")
                .astype(str)
                !=
                df[column]
                .fillna("")
                .astype(str)
            ).sum()

    return df, changed


# ============================================================
# CLEAN NAMES
# ============================================================

def clean_names(df):

    possible_name_columns = [
        "name",
        "first_name",
        "last_name",
        "full_name"
    ]

    changed = 0

    for column in possible_name_columns:

        if column not in df.columns:
            continue

        before = df[column].copy()

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .str.title()
        )

        changed += (
            before.fillna("")
            .astype(str)
            !=
            df[column]
            .fillna("")
            .astype(str)
        ).sum()

    return df, changed


# ============================================================
# CLEAN CATEGORIES
# ============================================================

def clean_categories(df):

    if "category" not in df.columns:

        return df

    df["category"] = (
        df["category"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    return df


# ============================================================
# CLEAN EMAILS
# ============================================================

def clean_emails(df):

    email_columns = [
        "email",
        "email_address",
        "e_mail"
    ]

    changed = 0

    for column in email_columns:

        if column not in df.columns:
            continue

        before = df[column].copy()

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        changed += (
            before.fillna("")
            .astype(str)
            !=
            df[column]
            .fillna("")
            .astype(str)
        ).sum()

    return df, changed


# ============================================================
# VALIDATE EMAILS
# ============================================================

def find_invalid_emails(df):

    invalid_rows = []

    email_columns = [
        "email",
        "email_address",
        "e_mail"
    ]

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    for column in email_columns:

        if column not in df.columns:
            continue

        for index, value in df[column].items():

            if pd.isna(value):
                continue

            value = str(value).strip()

            if not re.match(pattern, value):

                invalid_rows.append({
                    "row": index,
                    "column": column,
                    "value": value,
                    "reason": "Invalid email"
                })

    return invalid_rows


# ============================================================
# CLEAN PHONE NUMBERS
# ============================================================

def clean_phone_numbers(df):

    if "phone" not in df.columns:

        return df

    def clean_phone(value):

        if pd.isna(value):

            return value

        value = str(value)

        digits = re.sub(
            r"\D",
            "",
            value
        )

        # Remove Indian country code
        if (
            digits.startswith("91")
            and
            len(digits) == 12
        ):

            digits = digits[2:]

        return digits

    df["phone"] = (
        df["phone"]
        .apply(clean_phone)
    )

    return df


# ============================================================
# CLEAN NUMERIC COLUMNS
# ============================================================

def clean_numeric_column(df, column):

    if column not in df.columns:

        return df

    df[column] = (
        df[column]
        .astype("string")
        .str.replace(
            ",",
            "",
            regex=False
        )
        .str.replace(
            r"[₹$€£]",
            "",
            regex=True
        )
        .str.strip()
    )

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    return df


def clean_numbers(df):

    possible_numeric_columns = [
        "age",
        "salary",
        "price",
        "amount",
        "income",
        "quantity"
    ]

    for column in possible_numeric_columns:

        if column in df.columns:

            df = clean_numeric_column(
                df,
                column
            )

    return df


# ============================================================
# STANDARDIZE DATES
# ============================================================

def standardize_dates(df):

    possible_date_columns = [
        "date",
        "join_date",
        "joining_date",
        "birth_date",
        "dob",
        "date_of_birth",
        "created_date",
        "transaction_date"
    ]

    changed = 0

    for column in possible_date_columns:

        if column not in df.columns:
            continue

        before = df[column].copy()

        parsed = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        df[column] = (
            parsed
            .dt.strftime(
                DATE_OUTPUT_FORMAT
            )
        )

        changed += (
            before.fillna("")
            .astype(str)
            !=
            df[column]
            .fillna("")
            .astype(str)
        ).sum()

    return df, changed


# ============================================================
# FIND MISSING VALUES
# ============================================================

def find_missing_values(df):

    missing_rows = []

    for index, row in df.iterrows():

        for column in df.columns:

            value = row[column]

            if pd.isna(value):

                missing_rows.append({
                    "row": index,
                    "column": column,
                    "value": "",
                    "reason": "Missing value"
                })

    return missing_rows


# ============================================================
# FIND NEGATIVE VALUES
# ============================================================

def find_negative_values(df):

    problems = []

    numeric_columns = [
        "salary",
        "price",
        "amount",
        "income",
        "quantity"
    ]

    for column in numeric_columns:

        if column not in df.columns:
            continue

        for index, value in df[column].items():

            if pd.isna(value):
                continue

            if value < 0:

                problems.append({
                    "row": index,
                    "column": column,
                    "value": value,
                    "reason": "Negative value"
                })

    return problems


# ============================================================
# VALIDATE AGE
# ============================================================

def validate_age(df):

    problems = []

    if "age" not in df.columns:

        return problems

    for index, value in df["age"].items():

        if pd.isna(value):
            continue

        if value < 0:

            problems.append({
                "row": index,
                "column": "age",
                "value": value,
                "reason": "Negative age"
            })

        elif value > 120:

            problems.append({
                "row": index,
                "column": "age",
                "value": value,
                "reason": "Unusually high age"
            })

    return problems


# ============================================================
# FIND EMPTY STRINGS
# ============================================================

def find_unusual_values(df):

    problems = []

    for column in df.columns:

        for index, value in df[column].items():

            if pd.isna(value):
                continue

            value = str(value).strip()

            if value == "":

                problems.append({
                    "row": index,
                    "column": column,
                    "value": value,
                    "reason": "Empty value"
                })

    return problems


# ============================================================
# COLLECT ALL PROBLEMS
# ============================================================

def collect_problems(df):

    problems = []

    problems.extend(
        find_missing_values(df)
    )

    problems.extend(
        find_invalid_emails(df)
    )

    problems.extend(
        find_negative_values(df)
    )

    problems.extend(
        validate_age(df)
    )

    problems.extend(
        find_unusual_values(df)
    )

    return problems


# ============================================================
# FIND POSSIBLE DUPLICATES
# ============================================================

def find_possible_duplicates(df):

    possible_duplicates = []

    if "name" not in df.columns:

        return possible_duplicates

    temp = df.copy()

    temp["__name"] = (
        temp["name"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    if "city" in temp.columns:

        temp["__city"] = (
            temp["city"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

    if "phone" in temp.columns:

        temp["__phone"] = (
            temp["phone"]
            .astype("string")
            .str.replace(
                r"\D",
                "",
                regex=True
            )
        )

    if "email" in temp.columns:

        temp["__email"] = (
            temp["email"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

    for i in range(len(temp)):

        for j in range(i + 1, len(temp)):

            same_name = (
                pd.notna(
                    temp.iloc[i]["__name"]
                )
                and
                pd.notna(
                    temp.iloc[j]["__name"]
                )
                and
                temp.iloc[i]["__name"]
                ==
                temp.iloc[j]["__name"]
            )

            if not same_name:
                continue

            matches = 0

            if (
                "__phone" in temp.columns
                and
                pd.notna(
                    temp.iloc[i]["__phone"]
                )
                and
                pd.notna(
                    temp.iloc[j]["__phone"]
                )
                and
                temp.iloc[i]["__phone"]
                ==
                temp.iloc[j]["__phone"]
            ):

                matches += 1

            if (
                "__email" in temp.columns
                and
                pd.notna(
                    temp.iloc[i]["__email"]
                )
                and
                pd.notna(
                    temp.iloc[j]["__email"]
                )
                and
                temp.iloc[i]["__email"]
                ==
                temp.iloc[j]["__email"]
            ):

                matches += 1

            if (
                "__city" in temp.columns
                and
                pd.notna(
                    temp.iloc[i]["__city"]
                )
                and
                pd.notna(
                    temp.iloc[j]["__city"]
                )
                and
                temp.iloc[i]["__city"]
                ==
                temp.iloc[j]["__city"]
            ):

                matches += 1

            if matches >= 1:

                possible_duplicates.append({
                    "row_1": temp.index[i],
                    "row_2": temp.index[j],
                    "name": temp.iloc[i]["name"],
                    "reason":
                        "Same name and another matching field"
                })

    return possible_duplicates


# ============================================================
# PRINT PROBLEM REPORT
# ============================================================

def print_problem_report(problems):

    if not problems:

        print(
            "\nNo data quality problems found."
        )

        return

    print("\n" + "=" * 50)
    print("DATA QUALITY PROBLEMS")
    print("=" * 50)

    print(
        f"Problems found: {len(problems)}"
    )

    limit = 20

    for problem in problems[:limit]:

        print(
            f"Row {problem['row']} | "
            f"{problem['column']} | "
            f"{problem['value']} | "
            f"{problem['reason']}"
        )

    if len(problems) > limit:

        print(
            f"\n...and "
            f"{len(problems) - limit} more."
        )


# ============================================================
# CREATE REVIEW FILE
# ============================================================

def create_review_file(
    df,
    problems,
    original_name
):

    if not problems:

        return None

    problem_indexes = set()

    for problem in problems:

        problem_indexes.add(
            problem["row"]
        )

    review_df = df.loc[
        df.index.intersection(
            problem_indexes
        )
    ].copy()

    if review_df.empty:

        return None

    review_path = (
        REVIEW_FOLDER
        /
        f"review_{original_name}"
    )

    review_df.to_csv(
        review_path,
        index=False
    )

    return review_path


# ============================================================
# SORT BY AGE
# ============================================================

def sort_by_age(df):

    if "age" not in df.columns:

        return df, False

    df = df.sort_values(
        by="age",
        ascending=True,
        na_position="last"
    )

    return df, True


# ============================================================
# BACKUP ORIGINAL
# ============================================================

def backup_original(file_path):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_name = (
        f"{file_path.stem}_"
        f"{timestamp}"
        f"{file_path.suffix}"
    )

    backup_path = (
        BACKUP_FOLDER
        /
        backup_name
    )

    shutil.copy2(
        file_path,
        backup_path
    )

    return backup_path


# ============================================================
# SAVE CLEANED CSV
# ============================================================

def save_cleaned_csv(
    df,
    original_file
):

    output_path = (
        OUTPUT_FOLDER
        /
        f"cleaned_{original_file.name}"
    )

    df.to_csv(
        output_path,
        index=False
    )

    return output_path


# ============================================================
# VERIFY CLEANED FILE
# ============================================================

def verify_cleaned_file(
    output_path,
    cleaned_df
):

    if not output_path.exists():

        return (
            False,
            "Output file does not exist."
        )

    try:

        verified_df = pd.read_csv(
            output_path
        )

    except Exception as error:

        return (
            False,
            f"Could not reopen cleaned CSV: {error}"
        )

    if len(verified_df.columns) == 0:

        return (
            False,
            "Output contains no columns."
        )

    if list(verified_df.columns) != list(
        cleaned_df.columns
    ):

        return (
            False,
            "Column structure changed unexpectedly."
        )

    if len(verified_df) != len(cleaned_df):

        return (
            False,
            "Row count changed after saving."
        )

    return (
        True,
        f"Verification passed. {len(verified_df)} rows remain."
    )


# ============================================================
# CREATE REPORT
# ============================================================

def create_report(
    file_path,
    original_df,
    cleaned_df,
    duplicates_found,
    duplicates_removed,
    possible_duplicates,
    problems,
    output_path,
    verification_message
):

    report_path = (
        REPORT_FOLDER
        /
        f"{file_path.stem}_report.txt"
    )

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as report:

        report.write(
            "CSV CLEANING REPORT\n"
        )

        report.write(
            "=" * 50 + "\n\n"
        )

        report.write(
            f"File: {file_path.name}\n"
        )

        report.write(
            f"Processed: {datetime.now()}\n\n"
        )

        report.write(
            "ORIGINAL DATA\n"
        )

        report.write(
            f"Rows: {len(original_df)}\n"
        )

        report.write(
            f"Columns: {len(original_df.columns)}\n\n"
        )

        report.write(
            "DUPLICATES\n"
        )

        report.write(
            f"Exact duplicate rows: "
            f"{duplicates_found}\n"
        )

        report.write(
            f"Exact duplicates removed: "
            f"{duplicates_removed}\n"
        )

        report.write(
            f"Possible duplicate pairs: "
            f"{len(possible_duplicates)}\n\n"
        )

        report.write(
            "DATA QUALITY\n"
        )

        report.write(
            f"Problems detected: "
            f"{len(problems)}\n\n"
        )

        for problem in problems:

            report.write(
                f"Row {problem['row']} | "
                f"{problem['column']} | "
                f"{problem['value']} | "
                f"{problem['reason']}\n"
            )

        report.write(
            "\nPOSSIBLE DUPLICATES\n"
        )

        for duplicate in possible_duplicates:

            report.write(
                f"Rows "
                f"{duplicate['row_1']} and "
                f"{duplicate['row_2']} | "
                f"{duplicate['name']} | "
                f"{duplicate['reason']}\n"
            )

        report.write(
            "\nOUTPUT\n"
        )

        report.write(
            f"Output: {output_path}\n"
        )

        report.write(
            f"Final rows: {len(cleaned_df)}\n"
        )

        report.write(
            f"Verification: "
            f"{verification_message}\n"
        )

    return report_path


# ============================================================
# PROCESS ONE CSV
# ============================================================

def process_csv(file_path):

    print("\n")
    print("#" * 60)
    print(
        f"PROCESSING: {file_path.name}"
    )
    print("#" * 60)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    df = load_csv(file_path)

    if df is None:

        return False

    original_df = df.copy()

    # --------------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------------

    analysis = analyze_csv(df)

    print_analysis(
        df,
        analysis
    )

    print(
        "\nOriginal columns:"
    )

    print(
        list(df.columns)
    )

    # --------------------------------------------------------
    # NORMALIZE COLUMNS
    # --------------------------------------------------------

    df = normalize_column_names(df)

    print(
        "\nCleaned columns:"
    )

    print(
        list(df.columns)
    )

    # --------------------------------------------------------
    # EXACT DUPLICATES
    # --------------------------------------------------------

    duplicates = find_duplicates(df)

    duplicates_found = len(
        duplicates
    )

    duplicates_removed = 0

    report_duplicates(
        duplicates
    )

    if not duplicates.empty:

        delete_duplicates = ask_yes_no(
            "Remove duplicate rows?"
        )

        if delete_duplicates:

            df, duplicates_removed = (
                remove_duplicates(df)
            )

            print(
                f"\nRemoved "
                f"{duplicates_removed} "
                f"duplicate rows."
            )

        else:

            print(
                "Duplicates kept."
            )

    # --------------------------------------------------------
    # CLEAN SPACES
    # --------------------------------------------------------

    df, spaces_changed = clean_spaces(df)

    print(
        f"\nWhitespace cleaned in "
        f"{spaces_changed} cells."
    )

    # --------------------------------------------------------
    # CLEAN NAMES
    # --------------------------------------------------------

    df, names_changed = clean_names(df)

    print(
        f"Name formatting changed in "
        f"{names_changed} cells."
    )

    # --------------------------------------------------------
    # CLEAN CATEGORIES
    # --------------------------------------------------------

    df = clean_categories(df)

    print(
        "Categories standardized."
    )

    # --------------------------------------------------------
    # CLEAN EMAILS
    # --------------------------------------------------------

    df, emails_changed = clean_emails(df)

    print(
        f"Email formatting changed in "
        f"{emails_changed} cells."
    )

    # --------------------------------------------------------
    # CLEAN PHONES
    # --------------------------------------------------------

    df = clean_phone_numbers(df)

    print(
        "Phone numbers standardized."
    )

    # --------------------------------------------------------
    # CLEAN NUMBERS
    # --------------------------------------------------------

    df = clean_numbers(df)

    print(
        "Numeric columns standardized."
    )

    # --------------------------------------------------------
    # STANDARDIZE DATES
    # --------------------------------------------------------

    df, dates_changed = standardize_dates(df)

    print(
        f"Date formatting changed in "
        f"{dates_changed} cells."
    )

    # --------------------------------------------------------
    # POSSIBLE DUPLICATES
    # --------------------------------------------------------

    possible_duplicates = (
        find_possible_duplicates(df)
    )

    if possible_duplicates:

        print("\n" + "=" * 50)
        print("POSSIBLE DUPLICATES")
        print("=" * 50)

        print(
            f"Possible duplicate pairs found: "
            f"{len(possible_duplicates)}"
        )

        for duplicate in possible_duplicates:

            print(
                f"\nRows "
                f"{duplicate['row_1']} and "
                f"{duplicate['row_2']}"
            )

            print(
                f"Name: "
                f"{duplicate['name']}"
            )

            print(
                f"Reason: "
                f"{duplicate['reason']}"
            )

    else:

        print(
            "\nNo possible duplicates found."
        )

    # --------------------------------------------------------
    # FIND DATA QUALITY PROBLEMS
    # --------------------------------------------------------

    problems = collect_problems(df)

    print_problem_report(
        problems
    )

    # --------------------------------------------------------
    # REVIEW FILE
    # --------------------------------------------------------

    review_path = None

    if problems:

        create_review = ask_yes_no(
            "Create review file?"
        )

        if create_review:

            review_path = (
                create_review_file(
                    df,
                    problems,
                    file_path.name
                )
            )

            if review_path:

                print(
                    "\nReview file created:"
                )

                print(
                    review_path
                )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    df, sorted_age = sort_by_age(df)

    if sorted_age:

        print(
            "\nRecords sorted by age."
        )

    else:

        print(
            "\nNo Age column found."
        )

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------

    try:

        backup_path = backup_original(
            file_path
        )

        print(
            "\nBackup created:"
        )

        print(
            backup_path
        )

    except Exception as error:

        print(
            "\nWARNING:"
        )

        print(
            "Could not create backup."
        )

        print(error)

        print(
            "\nSkipping this file for safety."
        )

        return False

    # --------------------------------------------------------
    # SAVE CLEANED CSV
    # --------------------------------------------------------

    try:

        output_path = save_cleaned_csv(
            df,
            file_path
        )

        print(
            "\nCleaned CSV created:"
        )

        print(
            output_path
        )

    except Exception as error:

        print(
            "\nCould not save cleaned CSV."
        )

        print(error)

        return False

    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    verified, verification_message = (
        verify_cleaned_file(
            output_path,
            df
        )
    )

    print("\n" + "=" * 50)

    if verified:

        print(
            "VERIFICATION PASSED"
        )

    else:

        print(
            "VERIFICATION FAILED"
        )

    print(
        verification_message
    )

    print("=" * 50)

    # --------------------------------------------------------
    # CREATE REPORT
    # --------------------------------------------------------

    report_path = create_report(
        file_path=file_path,
        original_df=original_df,
        cleaned_df=df,
        duplicates_found=duplicates_found,
        duplicates_removed=duplicates_removed,
        possible_duplicates=possible_duplicates,
        problems=problems,
        output_path=output_path,
        verification_message=verification_message
    )

    print(
        "\nReport created:"
    )

    print(
        report_path
    )

    return verified


# ============================================================
# PROCESS ALL CSV FILES
# ============================================================

def process_all_csv_files():

    create_folders()

    csv_files = find_csv_files()

    if not csv_files:

        print(
            "\nNo CSV files found."
        )

        print(
            f"Put CSV files inside: "
            f"{INPUT_FOLDER}"
        )

        return

    print("\n" + "=" * 60)
    print("CSV CLEANER")
    print("=" * 60)

    print(
        f"\nFound {len(csv_files)} CSV file(s)."
    )

    successful = 0
    failed = 0

    for file_path in csv_files:

        try:

            result = process_csv(
                file_path
            )

            if result:

                successful += 1

            else:

                failed += 1

        except Exception as error:

            failed += 1

            print(
                "\n" + "!" * 60
            )

            print(
                f"ERROR PROCESSING "
                f"{file_path.name}"
            )

            print(
                error
            )

            print(
                "This file was skipped."
            )

            print(
                "!" * 60
            )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 60
    )

    print(
        f"Files found: "
        f"{len(csv_files)}"
    )

    print(
        f"Successfully processed: "
        f"{successful}"
    )

    print(
        f"Failed: "
        f"{failed}"
    )

    print(
        "\nOriginal files were NOT overwritten."
    )

    print(
        f"Cleaned files → "
        f"{OUTPUT_FOLDER}"
    )

    print(
        f"Review files → "
        f"{REVIEW_FOLDER}"
    )

    print(
        f"Backups → "
        f"{BACKUP_FOLDER}"
    )

    print(
        f"Reports → "
        f"{REPORT_FOLDER}"
    )

    print(
        "\nCSV CLEANING COMPLETE."
    )


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    process_all_csv_files()