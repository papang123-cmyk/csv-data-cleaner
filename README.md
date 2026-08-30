\# CSV Data Cleaner \& Validator



A Python automation tool for cleaning, validating, and organizing messy CSV files.



\## Features



\- Detects and removes duplicate rows

\- Normalizes column names

\- Cleans unnecessary whitespace

\- Standardizes names

\- Cleans and validates email addresses

\- Cleans numeric values

\- Standardizes dates

\- Detects missing values

\- Detects invalid email addresses

\- Detects negative values

\- Validates age values

\- Sorts records by age

\- Creates backups before saving results

\- Creates review files for questionable data

\- Generates detailed cleaning reports

\- Verifies the cleaned CSV before completing the process

\- Processes multiple CSV files automatically



\## How It Works



The program scans a folder for CSV files and processes each file through a series of cleaning and validation steps.



Original files are never overwritten.



The program creates:



\- `cleaned\_csv/` — cleaned CSV files

\- `review/` — questionable records requiring review

\- `backups/` — backups of original files

\- `reports/` — processing and data-quality reports



\## Technologies



\- Python

\- Pandas

\- Regular Expressions

\- pathlib

\- shutil



\## Example



The included `dirty.csv` contains intentionally messy data such as:



\- Missing values

\- Duplicate records

\- Invalid emails

\- Negative prices

\- Invalid ages

\- Inconsistent capitalization

\- Unnecessary spaces

\- Inconsistent dates



The program cleans what can safely be cleaned and reports issues that require human review.



\## Running the Program



Install the required packages:



```bash

pip install pandas send2trash



