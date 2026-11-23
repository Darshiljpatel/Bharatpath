"""
BharatPath – Production Excel Dataset Loader
File: etl/load_excel_to_db.py
Description: Reads all 13 data sheets from data/BharatPath_Database_Final.xlsx,
             parses BC/AD year formats into signed integers, constructs JSONB
             artefact_metadata, and populates database/bharatpath_dev.db.
"""

import os
import re
import json
import sqlite3
import pandas as pd

EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'BharatPath_Database_Final.xlsx')
DEV_DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'bharatpath_dev.db')

def clean_cell(val):
    if pd.isna(val) or val is None:
        return None
    return val

def parse_year_to_num(val):
    """Converts '<digits> BC' to negative int, '<digits> AD' to positive int."""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip().upper()
    m = re.match(r'^(\d+)\s*(BC|BCE|AD|CE)?$', s)
    if not m:
        return None
    num = int(m.group(1))
    era = m.group(2)
    if era in ('BC', 'BCE'):
        return -num
    return num

def load_all_excel_data():
    print(f"Reading workbook: {EXCEL_FILE}")
    xl = pd.ExcelFile(EXCEL_FILE)

    if os.path.exists(DEV_DB_FILE):
        try: os.remove(DEV_DB_FILE)
        except Exception: pass

    conn = sqlite3.connect(DEV_DB_FILE)
    cur = conn.cursor()

    # Create Tables matching the SQL Schema
    cur.executescript("""
    CREATE TABLE sources (
        source_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author_or_editor TEXT NOT NULL,
        source_type TEXT NOT NULL,
        publisher TEXT,
        publication_year TEXT,
        url TEXT,
        note TEXT
    );

    CREATE TABLE regions (
        region_id TEXT PRIMARY KEY,
        region_name TEXT NOT NULL UNIQUE,
        historical_names TEXT,
        present_day_area TEXT NOT NULL,
        present_day_country TEXT NOT NULL,
        geographic_setting TEXT,
        historical_significance TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id)
    );

    CREATE TABLE historical_periods (
        period_id TEXT PRIMARY KEY,
        period_name TEXT NOT NULL UNIQUE,
        era TEXT NOT NULL CHECK (era IN ('Ancient', 'Early Medieval', 'Medieval')),
        start_year TEXT NOT NULL,
        end_year TEXT NOT NULL,
        start_year_num INTEGER,
        end_year_num INTEGER,
        dating_note TEXT NOT NULL,
        defining_features TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id)
    );

    CREATE TABLE cities (
        city_id TEXT PRIMARY KEY,
        ancient_name TEXT NOT NULL,
        modern_name TEXT NOT NULL,
        present_day_state TEXT NOT NULL,
        present_day_country TEXT NOT NULL,
        region_id TEXT NOT NULL REFERENCES regions(region_id),
        river_or_coast TEXT,
        city_type TEXT NOT NULL,
        period_id TEXT NOT NULL REFERENCES historical_periods(period_id),
        historical_significance TEXT NOT NULL,
        latitude REAL NOT NULL CHECK (latitude BETWEEN -90.0 AND 90.0),
        longitude REAL NOT NULL CHECK (longitude BETWEEN -180.0 AND 180.0),
        source_id TEXT REFERENCES sources(source_id),
        artefact_metadata TEXT DEFAULT '{}'
    );

    CREATE TABLE kingdoms (
        kingdom_id TEXT PRIMARY KEY,
        kingdom_name TEXT NOT NULL UNIQUE,
        polity_type TEXT NOT NULL,
        capital_city_id TEXT REFERENCES cities(city_id),
        region_id TEXT NOT NULL REFERENCES regions(region_id),
        period_id TEXT NOT NULL REFERENCES historical_periods(period_id),
        start_year TEXT NOT NULL,
        end_year TEXT NOT NULL,
        start_year_num INTEGER,
        end_year_num INTEGER,
        dating_note TEXT NOT NULL,
        founder TEXT,
        notable_ruler TEXT,
        historical_significance TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id),
        artefact_metadata TEXT DEFAULT '{}'
    );

    CREATE TABLE ports (
        port_id TEXT PRIMARY KEY,
        port_name TEXT NOT NULL,
        present_day_location TEXT NOT NULL,
        city_id TEXT REFERENCES cities(city_id),
        coast TEXT NOT NULL,
        port_type TEXT NOT NULL,
        period_id TEXT NOT NULL REFERENCES historical_periods(period_id),
        active_period_note TEXT NOT NULL,
        overseas_connections TEXT,
        trade_note TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        source_id TEXT REFERENCES sources(source_id)
    );

    CREATE TABLE trade_routes (
        route_id TEXT PRIMARY KEY,
        route_name TEXT NOT NULL UNIQUE,
        route_type TEXT NOT NULL,
        start_city_id TEXT NOT NULL REFERENCES cities(city_id),
        end_city_id TEXT NOT NULL REFERENCES cities(city_id),
        period_id TEXT NOT NULL REFERENCES historical_periods(period_id),
        start_year TEXT NOT NULL,
        end_year TEXT NOT NULL,
        start_year_num INTEGER,
        end_year_num INTEGER,
        dating_note TEXT NOT NULL,
        description TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id),
        artefact_metadata TEXT DEFAULT '{}'
    );

    CREATE TABLE route_city (
        route_id TEXT NOT NULL REFERENCES trade_routes(route_id),
        city_id TEXT NOT NULL REFERENCES cities(city_id),
        stop_sequence INTEGER NOT NULL,
        stop_role TEXT NOT NULL,
        note TEXT,
        PRIMARY KEY (route_id, city_id)
    );

    CREATE TABLE commodities (
        commodity_id TEXT PRIMARY KEY,
        commodity_name TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL,
        primary_source_area TEXT NOT NULL,
        trade_direction TEXT NOT NULL,
        attested_in TEXT NOT NULL,
        description TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id)
    );

    CREATE TABLE route_commodity (
        route_id TEXT NOT NULL REFERENCES trade_routes(route_id),
        commodity_id TEXT NOT NULL REFERENCES commodities(commodity_id),
        trade_direction TEXT NOT NULL,
        evidence_note TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id),
        PRIMARY KEY (route_id, commodity_id)
    );

    CREATE TABLE currencies (
        currency_id TEXT PRIMARY KEY,
        coin_name TEXT NOT NULL UNIQUE,
        metal TEXT NOT NULL,
        issuing_kingdom_id TEXT REFERENCES kingdoms(kingdom_id),
        issuer_note TEXT,
        period_id TEXT NOT NULL REFERENCES historical_periods(period_id),
        start_year TEXT NOT NULL,
        end_year TEXT NOT NULL,
        start_year_num INTEGER,
        end_year_num INTEGER,
        dating_note TEXT NOT NULL,
        weight_standard TEXT,
        description TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id),
        artefact_metadata TEXT DEFAULT '{}'
    );

    CREATE TABLE travellers (
        traveller_id TEXT PRIMARY KEY,
        traveller_name TEXT NOT NULL,
        homeland TEXT NOT NULL,
        role TEXT NOT NULL,
        arrival_year TEXT NOT NULL,
        departure_year TEXT,
        arrival_year_num INTEGER,
        departure_year_num INTEGER,
        dating_note TEXT NOT NULL,
        period_id TEXT NOT NULL REFERENCES historical_periods(period_id),
        kingdom_visited_id TEXT REFERENCES kingdoms(kingdom_id),
        main_city_visited_id TEXT REFERENCES cities(city_id),
        account_title TEXT NOT NULL,
        key_observation TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id),
        artefact_metadata TEXT DEFAULT '{}'
    );

    CREATE TABLE cultural_exchanges (
        exchange_id TEXT PRIMARY KEY,
        exchange_name TEXT NOT NULL,
        exchange_type TEXT NOT NULL,
        from_region_id TEXT NOT NULL REFERENCES regions(region_id),
        to_region_id TEXT NOT NULL REFERENCES regions(region_id),
        period_id TEXT NOT NULL REFERENCES historical_periods(period_id),
        start_year TEXT NOT NULL,
        end_year TEXT NOT NULL,
        start_year_num INTEGER,
        end_year_num INTEGER,
        dating_note TEXT NOT NULL,
        description TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        source_id TEXT REFERENCES sources(source_id),
        artefact_metadata TEXT DEFAULT '{}'
    );

    CREATE TABLE audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        operation TEXT NOT NULL,
        record_id TEXT,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        old_data TEXT,
        new_data TEXT
    );
    """)

    # 1. Sources (41)
    df_src = pd.read_excel(EXCEL_FILE, sheet_name='Sources').where(pd.notnull, None)
    for _, row in df_src.iterrows():
        cur.execute("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?)", (
            row['source_id'], row['title'], row['author_or_editor'], row['source_type'],
            row['publisher'], str(row['publication_year']) if row['publication_year'] else None,
            row['url'], row['note']
        ))

    # 2. Regions (33)
    df_reg = pd.read_excel(EXCEL_FILE, sheet_name='Regions').where(pd.notnull, None)
    for _, row in df_reg.iterrows():
        cur.execute("INSERT INTO regions VALUES (?,?,?,?,?,?,?,?)", (
            row['region_id'], row['region_name'], row['historical_names'], row['present_day_area'],
            row['present_day_country'], row['geographic_setting'], row['historical_significance'], row['source_id']
        ))

    # 3. Historical_Periods (32)
    df_hp = pd.read_excel(EXCEL_FILE, sheet_name='Historical_Periods').where(pd.notnull, None)
    for _, row in df_hp.iterrows():
        s_num = parse_year_to_num(row['start_year'])
        e_num = parse_year_to_num(row['end_year'])
        cur.execute("INSERT INTO historical_periods VALUES (?,?,?,?,?,?,?,?,?,?)", (
            row['period_id'], row['period_name'], row['era'], row['start_year'], row['end_year'],
            s_num, e_num, row['dating_note'], row['defining_features'], row['source_id']
        ))

    # 4. Cities (73)
    df_cit = pd.read_excel(EXCEL_FILE, sheet_name='Cities')
    for _, row in df_cit.iterrows():
        meta = {
            "present_day_state": clean_cell(row['present_day_state']),
            "present_day_country": clean_cell(row['present_day_country']),
            "river_or_coast": clean_cell(row['river_or_coast']),
            "city_type": clean_cell(row['city_type'])
        }
        cur.execute("INSERT INTO cities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            clean_cell(row['city_id']), clean_cell(row['ancient_name']), clean_cell(row['modern_name']), clean_cell(row['present_day_state']),
            clean_cell(row['present_day_country']), clean_cell(row['region_id']), clean_cell(row['river_or_coast']), clean_cell(row['city_type']),
            clean_cell(row['period_id']), clean_cell(row['historical_significance']), float(row['latitude']), float(row['longitude']),
            clean_cell(row['source_id']), json.dumps(meta)
        ))

    # 5. Kingdoms (31)
    df_kg = pd.read_excel(EXCEL_FILE, sheet_name='Kingdoms')
    for _, row in df_kg.iterrows():
        s_num = parse_year_to_num(row['start_year'])
        e_num = parse_year_to_num(row['end_year'])
        meta = {
            "founder": clean_cell(row['founder']),
            "notable_ruler": clean_cell(row['notable_ruler']),
            "dating_note": clean_cell(row['dating_note']),
            "polity_type": clean_cell(row['polity_type'])
        }
        cur.execute("INSERT INTO kingdoms VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            clean_cell(row['kingdom_id']), clean_cell(row['kingdom_name']), clean_cell(row['polity_type']), clean_cell(row['capital_city_id']),
            clean_cell(row['region_id']), clean_cell(row['period_id']), clean_cell(row['start_year']), clean_cell(row['end_year']),
            s_num, e_num, clean_cell(row['dating_note']), clean_cell(row['founder']), clean_cell(row['notable_ruler']),
            clean_cell(row['historical_significance']), clean_cell(row['source_id']), json.dumps(meta)
        ))

    # 6. Ports (28)
    df_pt = pd.read_excel(EXCEL_FILE, sheet_name='Ports').where(pd.notnull, None)
    for _, row in df_pt.iterrows():
        cur.execute("INSERT INTO ports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            row['port_id'], row['port_name'], row['present_day_location'], row['city_id'],
            row['coast'], row['port_type'], row['period_id'], row['active_period_note'],
            row['overseas_connections'], row['trade_note'], float(row['latitude']), float(row['longitude']),
            row['source_id']
        ))

    # 7. Trade_Routes (26)
    df_tr = pd.read_excel(EXCEL_FILE, sheet_name='Trade_Routes').where(pd.notnull, None)
    for _, row in df_tr.iterrows():
        s_num = parse_year_to_num(row['start_year'])
        e_num = parse_year_to_num(row['end_year'])
        meta = {"dating_note": row['dating_note']}
        cur.execute("INSERT INTO trade_routes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            row['route_id'], row['route_name'], row['route_type'], row['start_city_id'],
            row['end_city_id'], row['period_id'], row['start_year'], row['end_year'],
            s_num, e_num, row['dating_note'], row['description'], row['source_id'], json.dumps(meta)
        ))

    # 8. Route_City (68)
    df_rc = pd.read_excel(EXCEL_FILE, sheet_name='Route_City').where(pd.notnull, None)
    for _, row in df_rc.iterrows():
        cur.execute("INSERT INTO route_city VALUES (?,?,?,?,?)", (
            row['route_id'], row['city_id'], int(row['stop_sequence']), row['stop_role'], row['note']
        ))

    # 9. Commodities (30)
    df_cm = pd.read_excel(EXCEL_FILE, sheet_name='Commodities').where(pd.notnull, None)
    for _, row in df_cm.iterrows():
        cur.execute("INSERT INTO commodities VALUES (?,?,?,?,?,?,?,?)", (
            row['commodity_id'], row['commodity_name'], row['category'], row['primary_source_area'],
            row['trade_direction'], row['attested_in'], row['description'], row['source_id']
        ))

    # 10. Route_Commodity (79)
    df_rcom = pd.read_excel(EXCEL_FILE, sheet_name='Route_Commodity').where(pd.notnull, None)
    for _, row in df_rcom.iterrows():
        cur.execute("INSERT INTO route_commodity VALUES (?,?,?,?,?)", (
            row['route_id'], row['commodity_id'], row['trade_direction'], row['evidence_note'], row['source_id']
        ))

    # 11. Currencies (32)
    df_cu = pd.read_excel(EXCEL_FILE, sheet_name='Currencies').where(pd.notnull, None)
    for _, row in df_cu.iterrows():
        s_num = parse_year_to_num(row['start_year'])
        e_num = parse_year_to_num(row['end_year'])
        meta = {
            "dating_note": clean_cell(row['dating_note']),
            "weight_standard": clean_cell(row['weight_standard']),
            "issuer_note": clean_cell(row['issuer_note'])
        }
        cur.execute("INSERT INTO currencies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            row['currency_id'], row['coin_name'], row['metal'], row['issuing_kingdom_id'],
            row['issuer_note'], row['period_id'], row['start_year'], row['end_year'],
            s_num, e_num, row['dating_note'], row['weight_standard'], row['description'],
            row['source_id'], json.dumps(meta)
        ))

    # 12. Travellers (28)
    df_tv = pd.read_excel(EXCEL_FILE, sheet_name='Travellers').where(pd.notnull, None)
    for _, row in df_tv.iterrows():
        arr_num = parse_year_to_num(row['arrival_year'])
        dep_num = parse_year_to_num(row['departure_year'])
        meta = {
            "dating_note": row['dating_note'],
            "account_title": row['account_title'],
            "key_observation": row['key_observation']
        }
        cur.execute("INSERT INTO travellers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            row['traveller_id'], row['traveller_name'], row['homeland'], row['role'],
            row['arrival_year'], row['departure_year'], arr_num, dep_num, row['dating_note'],
            row['period_id'], row['kingdom_visited_id'], row['main_city_visited_id'],
            row['account_title'], row['key_observation'], row['source_id'], json.dumps(meta)
        ))

    # 13. Cultural_Exchanges (30)
    df_ce = pd.read_excel(EXCEL_FILE, sheet_name='Cultural_Exchanges').where(pd.notnull, None)
    for _, row in df_ce.iterrows():
        s_num = parse_year_to_num(row['start_year'])
        e_num = parse_year_to_num(row['end_year'])
        meta = {
            "dating_note": row['dating_note'],
            "evidence_type": row['evidence_type']
        }
        cur.execute("INSERT INTO cultural_exchanges VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            row['exchange_id'], row['exchange_name'], row['exchange_type'], row['from_region_id'],
            row['to_region_id'], row['period_id'], row['start_year'], row['end_year'],
            s_num, e_num, row['dating_note'], row['description'], row['evidence_type'],
            row['source_id'], json.dumps(meta)
        ))

    conn.commit()

    # Verification
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    tables = [r[0] for r in cur.fetchall()]
    total_loaded = 0
    print(f"\nLoaded {len(tables)} tables into {DEV_DB_FILE}:")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cur.fetchone()[0]
        if t != 'audit_log':
            total_loaded += cnt
        print(f" - {t:<22}: {cnt} rows")

    conn.close()
    print(f"\nSUCCESS: Exactly {total_loaded} master records loaded into database/bharatpath_dev.db!")

if __name__ == '__main__':
    load_all_excel_data()
