import sqlite3
import yaml
from pathlib import Path
import pandas as pd
import hashlib

class database:
    def __init__(self):
        """Initialize the database by creating a connection, cursor, and loading the configuration."""
        cursor, conn = self.create_db()
        self.cursor = cursor
        self.conn = conn
        self.config = self.get_config()

    def get_config(self):
        """Load the database configuration from a YAML file."""
        config_path = Path(__file__).parent.parent / "configs" / "db.yml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def create_db(self):
        """Create a SQLite database connection and return the cursor and connection."""
        conn = sqlite3.connect("db/gym_data.db")
        cursor = conn.cursor()
        return cursor, conn
    
    def create_tables(self):
        """Create tables based on the configuration."""
        for table_name, table_info in self.config['tables'].items():
                columns_sql = []
                pk_cols = []
                autoinc_col = None

                # build basic column definitions, collect PKs and AUTOINC info
                for col in table_info['columns']:
                    col_name = col['name']
                    col_def = f"{col_name} {col['type']}"
                    if col.get('not_null'):
                        col_def += " NOT NULL"
                    if col.get('unique'):
                        col_def += " UNIQUE"

                    if col.get('primary_key'):
                        pk_cols.append(col_name)
                        if col.get('autoincrement'):
                            autoinc_col = col_name

                    columns_sql.append(col_def)

                # Handle AUTOINCREMENT only when a single PK column requests it
                if autoinc_col and len(pk_cols) == 1:
                    # replace that column's definition to include PRIMARY KEY AUTOINCREMENT
                    for i, col in enumerate(table_info['columns']):
                        if col['name'] == autoinc_col:
                            columns_sql[i] = f"{autoinc_col} {col['type']} PRIMARY KEY AUTOINCREMENT"
                            break
                    # remove from pk_cols so we don't also add a table-level PK for it
                    pk_cols = [c for c in pk_cols if c != autoinc_col]
                else:
                    if autoinc_col and len(pk_cols) > 1:
                        print(f"Warning: AUTOINCREMENT requested for '{autoinc_col}' but multiple primary keys defined for table '{table_name}'. AUTOINCREMENT will be ignored.")

                # construct CREATE TABLE SQL; if multiple PKs, add table-level PRIMARY KEY
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)}"
                if pk_cols:
                    create_sql += f", PRIMARY KEY ({', '.join(pk_cols)})"
                create_sql += ");"

                print(f"Creating table {table_name}: {create_sql}")
                self.cursor.execute(create_sql)
                self.conn.commit()

    def from_csv_to_db(self):
        df = pd.read_excel(self.config['files']['path'])
        table_name = self.config['files']['table']
        column_mappings = {col['excel_column']: col['name'] for col in self.config['tables'][table_name]['columns'] if 'excel_column' in col}
        df = df[list(column_mappings.keys())]
        df = df.dropna(subset=self.config['tables']['gym_sessions']['columns'][1]['excel_column'])
        df.rename(columns=column_mappings, inplace=True)
        df.to_sql(table_name, self.conn, if_exists='append', index=False)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_user_credentials(self, username, password):
        hashed_password = self.hash_password(password)
        select_sql = "SELECT * FROM users WHERE username = ? AND password = ?;"
        self.cursor.execute(select_sql, (username, hashed_password))
        user = self.cursor.fetchone()
        return user is not None
    
    def insert_gym_session(self, date, duration, gym_name, category):
        try:
            insert_sql = """
            INSERT INTO gym_sessions (id, date, duration, gym_name, category)
            VALUES (?, ?, ?, ?, ?);
            """
            self.cursor.execute(insert_sql, (date, duration, gym_name, category))
            self.conn.commit()
            self.drop_duplicates(self.config['files']['table'][0], ['date', 'duration', 'gym_name', 'category'])
            return True
        except sqlite3.IntegrityError as e:
            print(f"Error inserting gym session: {e}")
            return False
        
    def upsert_gym_session(self):
        """Upsert the gym data because I can't be bothered to check if it exists first."""
        df = pd.read_excel(self.config['files']['path'])
        df['Day'] = df['Day'].astype(str)
        df['Minutes in Gym'] = df['Minutes in Gym'].astype(str)
        table_name = self.config['files']['table']
        column_mappings = {col['excel_column']: col['name'] for col in self.config['tables'][table_name]['columns'] if 'excel_column' in col}
        df = df[list(column_mappings.keys())]
        df = df.dropna(subset=self.config['tables']['gym_sessions']['columns'][3]['excel_column'])
        df.rename(columns=column_mappings, inplace=True)
        # Build insert columns and placeholders from the DataFrame (columns are already DB names)
        insert_cols = df.columns.tolist()
        placeholders = ", ".join(["?" for _ in insert_cols])

        # Determine PK columns defined in the config for ON CONFLICT clause
        pk_cols = [c['name'] for c in self.config['tables'][table_name]['columns'] if c.get('primary_key')]

        insert_sql = f"INSERT INTO {table_name} ({', '.join(insert_cols)}) VALUES ({placeholders})"
        if pk_cols:
            insert_sql += f" ON CONFLICT({', '.join(pk_cols)}) DO NOTHING"
        insert_sql += ";"

        # executemany expects an iterable of tuples; to_records gives numpy records so convert to list of tuples
        values = [tuple(r) for r in df.to_numpy()]
        self.conn.executemany(insert_sql, values)
        self.conn.commit()

    def drop_duplicates(self, table_name, subset_columns):
        cols = ', '.join(subset_columns)
        delete_sql = f"""
        DELETE FROM {table_name}
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM {table_name}
            GROUP BY {cols}
        );
        """
        self.cursor.execute(delete_sql)
        self.conn.commit()

db = database()
db.create_tables()
db.from_csv_to_db()
