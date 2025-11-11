import sqlite3
import yaml
from pathlib import Path
import pandas as pd

class database:
    def __init__(self):
        cursor, conn = self.create_db()
        self.cursor = cursor
        self.conn = conn
        self.config = self.get_config()
        self.create_tables()
        self.from_csv_to_db()

    def get_config(self):
        config_path = Path(__file__).parent.parent / "configs" / "db.yml"
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def create_db(self):
        conn = sqlite3.connect("db/gym_data.db")
        cursor = conn.cursor()
        return cursor, conn
    
    def create_tables(self):
        
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
        df.rename(columns=column_mappings, inplace=True)
        df.to_sql(table_name, self.conn, if_exists='append', index=False)

if __name__ == "__main__":
    db = database()