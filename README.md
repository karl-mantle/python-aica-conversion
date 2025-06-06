# python-aica-conversion

To future me

## Reqs

What you need:
- Windows/WSL2 (Ubuntu)
- Python3 (already installed probably but check)
- MariaDB

## Load Database

1. Install MariaDB if you deleted it
    - `sudo apt install mariadb-server -y`

2. Start service
    - `sudo service mysql start`

3. Start MariaDB shell
    - `sudo mariadb`

4. Make an empty database to hold the .sql dump
    - `CREATE DATABASE aicanetwork_latest;`
    - `EXIT;`

5. Import the dump to that database
    - `sudo mariadb aicanetwork_latest < /dumps/dump.sql`

6. Now the dump is in the DB

## Dump tables to CSVs

1. Python is preinstalled unless you removed it so you should make a virtual env to not interfere with the system packages

    - `python3 -m venv aica`

    - You might have to install venv again
    
    - Activate it - `source aica/bin/activate`

2. Install these packages
    - `pip install pandas mysql-connector-python pycountry_convert`

3. Add mariaDB details to the export_tables config

4. Run the script
    - `python3 export_tables.py`

5. Now there's a tonne of CSVs in `csvs` to transform

## Create CSVs

1. There's a script for each post-type that will create a CSV ready to import via WP All Import

2. Run them