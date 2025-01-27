import oracledb
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = oracledb.connect(
        user=os.getenv('ORACLE_USER'),
        password=os.getenv('ORACLE_PASSWORD'),
        dsn=os.getenv('ORACLE_DSN')
    )
    print("Connessione riuscita!")
    conn.close()
except Exception as e:
    print("Errore di connessione:", e)