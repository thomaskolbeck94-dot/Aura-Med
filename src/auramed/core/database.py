import sqlite3
import os
import csv
import io
from typing import Optional, Dict, List

DB_PATH = os.environ.get("AURAMED_DB_PATH", "auramed.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database schema based on the official BfArM 3-table structure."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Fertigarzneimittel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS REFERENCE_MEDICINAL_PRODUCT (
                RMP_KEY TEXT PRIMARY KEY,
                RMP_PZN TEXT,
                RMP_COUNT_SUBSTANCE INTEGER,
                RMP_MULTIPLE_PPT BOOLEAN,
                RMP_PFM_PUT_SHORT TEXT,
                RMP_PFM_NAME TEXT,
                RMP_MPD_NAME TEXT
            )
        """)
        
        # 2. Komponenten
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS REFERENCE_PHARMACEUTICAL_PRODUCT (
                RPP_KEY TEXT PRIMARY KEY,
                RMP_KEY TEXT,
                RPP_NUMBER INTEGER,
                RPP_PFM_PUT_SHORT TEXT,
                FOREIGN KEY (RMP_KEY) REFERENCES REFERENCE_MEDICINAL_PRODUCT(RMP_KEY) ON DELETE CASCADE
            )
        """)
        
        # 3. Wirkstoffe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS REFERENCE_SUBSTANCE (
                RSE_KEY TEXT PRIMARY KEY,
                RPP_KEY TEXT,
                RSE_SUBSTANCE_NAME TEXT,
                RSE_SUBSTANCE_ID TEXT,
                FOREIGN KEY (RPP_KEY) REFERENCES REFERENCE_PHARMACEUTICAL_PRODUCT(RPP_KEY) ON DELETE CASCADE
            )
        """)
        
        # 4. Inventory (für Endnutzer Scans)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pzn TEXT NOT NULL,
                batch_lot TEXT,
                serial_number TEXT,
                expiry_date TEXT,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pzn) REFERENCES REFERENCE_MEDICINAL_PRODUCT(RMP_KEY)
            )
        """)
        
        conn.commit()


def import_dsv_data(table_name: str, dsv_string: str):
    """
    Simulates importing DSV (Pipe | separated) data directly into the specified SQLite table.
    Uses INSERT OR REPLACE to update existing records seamlessly.
    """
    if not dsv_string.strip():
        return
        
    reader = csv.DictReader(io.StringIO(dsv_string.strip()), delimiter='|')
    
    with get_connection() as conn:
        cursor = conn.cursor()
        for row in reader:
            columns = ', '.join(row.keys())
            placeholders = ', '.join('?' * len(row))
            sql = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(sql, tuple(row.values()))
        conn.commit()

def populate_mock_data():
    """Populates the database with mock data using DSV format."""
    
    # Mock RMP (Fertigarzneimittel)
    rmp_data = """RMP_KEY|RMP_PZN|RMP_COUNT_SUBSTANCE|RMP_MULTIPLE_PPT|RMP_PFM_PUT_SHORT|RMP_PFM_NAME|RMP_MPD_NAME
06453257|06453257|1|0|Sirup|Sirup|Prospan Hustensaft
12345678|12345678|1|0|FTA|Filmtabletten|Ibuprofen 400mg akut
00000000|00000000|2|0|Pul|Pulver|Aspirin Complex Beutel
"""
    import_dsv_data("REFERENCE_MEDICINAL_PRODUCT", rmp_data)

    # Mock RPP (Komponenten)
    rpp_data = """RPP_KEY|RMP_KEY|RPP_NUMBER|RPP_PFM_PUT_SHORT
06453257-1|06453257|1|Sirup
12345678-1|12345678|1|FTA
00000000-1|00000000|1|Pul
"""
    import_dsv_data("REFERENCE_PHARMACEUTICAL_PRODUCT", rpp_data)

    # Mock RSE (Wirkstoffe)
    rse_data = """RSE_KEY|RPP_KEY|RSE_SUBSTANCE_NAME|RSE_SUBSTANCE_ID
06453257-1-1|06453257-1|Efeublätter-Trockenextrakt|ASK-1234
12345678-1-1|12345678-1|Ibuprofen|ASK-5678
00000000-1-1|00000000-1|Acetylsalicylsäure|ASK-9012
00000000-1-2|00000000-1|Pseudoephedrin|ASK-3456
"""
    import_dsv_data("REFERENCE_SUBSTANCE", rse_data)

def is_valid_api_key(api_key: str) -> bool:
    """
    Dummy-Funktion für Open Source Release.
    In der SaaS-Version wird hier die Datenbank geprüft.
    """
    return True


def lookup_pzn(pzn: str) -> Optional[Dict]:
    """
    Looks up a medication by its PZN, joining the 3 BfArM tables to construct a complete dictionary.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Fetch Medicinal Product
        cursor.execute("SELECT * FROM REFERENCE_MEDICINAL_PRODUCT WHERE RMP_KEY = ?", (pzn,))
        rmp_row = cursor.fetchone()
        
        if not rmp_row:
            return None
            
        rmp = dict(rmp_row)
        
        # Fetch Substances via Pharmaceutical Product
        # We join RPP and RSE to get all substances for this medicinal product
        cursor.execute("""
            SELECT RSE.RSE_SUBSTANCE_NAME 
            FROM REFERENCE_PHARMACEUTICAL_PRODUCT RPP
            JOIN REFERENCE_SUBSTANCE RSE ON RPP.RPP_KEY = RSE.RPP_KEY
            WHERE RPP.RMP_KEY = ?
        """, (pzn,))
        
        substance_rows = cursor.fetchall()
        substances = [row["RSE_SUBSTANCE_NAME"] for row in substance_rows]
        
        # Construct the response matching the API's expected format
        return {
            "pzn": rmp["RMP_KEY"],
            "name": rmp["RMP_MPD_NAME"],
            "dosage_form": rmp["RMP_PFM_PUT_SHORT"],
            "active_ingredients": ", ".join(substances)
        }

# Initialize db on module import for the prototype
# In a real app, this would be managed by migrations (e.g. Alembic)
init_db()
populate_mock_data()
