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
            for col in table_info['columns']:
                col_def = f"{col['name']} {col['type']}"
                if col.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if col.get('autoincrement'):
                    col_def += " AUTOINCREMENT"
                if col.get('not_null'):
                    col_def += " NOT NULL"
                if col.get('unique'):
                    col_def += " UNIQUE"
                columns_sql.append(col_def)
        
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)});"
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
