# python-aica-conversion

## Requirements

- Windows/WSL2 (Ubuntu)
- Python3 (already installed probably but check)
- MariaDB

## Load Database

1. **Install MariaDB**

   ```bash
   sudo apt install mariadb-server -y
   ```

2. **Start service**

   ```bash
   sudo service mysql start
   ```

3. **Open MariaDB shell**

   ```bash
   sudo mariadb
   ```

4. **Create a new database for the SQL dump**

   ```sql
   CREATE DATABASE aicanetwork_latest;
   EXIT;
   ```

5. **Import the SQL dump**

   ```bash
   sudo mariadb aicanetwork_latest < /dumps/dump.sql
   ```

6. Database is now ready.

## Dump tables to CSVs

1. **Set up a Python virtual environment**

   ```bash
   python3 -m venv aica
   source aica/bin/activate
   ```

2. **Install required Python packages**

   ```bash
   pip install pandas mysql-connector-python pycountry_convert unidecode
   ```

3. **Add MariaDB connection details to** `export_tables.py`

4. **Run the export script**

   ```bash
   python3 export_tables.py
   ```

5. Now there's a tonne of CSVs in `csvs`

## Create CSVs for WP All Import

1. There's a script for each post-type that will turn raw CSVs into a WP All Import-ready CSVs.

2. Run them all
   ```bash
   python3 create_deals.py
   python3 create_firms.py
   python3 create_members.py
   ```
