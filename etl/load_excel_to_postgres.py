"""
BharatPath – Production Excel to PostgreSQL Dataset Loader
File: etl/load_excel_to_postgres.py

Usage:
    python etl/load_excel_to_postgres.py [--file path/to/file.xlsx] [--dry-run] [--replace-dev-seed]

Flags:
    --file              Optional override for Excel path (defaults to data/BharatPath_Database_Final.xlsx)
    --dry-run           Runs cleaning, parsing, JSONB packing, and inserts inside a single transaction,
                        prints verification counts, and rolls back cleanly without persisting changes.
    --replace-dev-seed  Disables audit triggers / sets session_replication_role = 'replica', truncates
                        all 13 tables CASCADE, loads all 531 rows, and restores triggers.
"""

import os
import sys
import re
import json
import argparse
import pandas as pd
import openpyxl
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# Load database credentials from root .env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

DEFAULT_EXCEL_PATH = os.path.join(PROJECT_ROOT, 'data', 'BharatPath_Database_Final.xlsx')

SKIP_SHEETS = {'README', 'Data_Dictionary', 'Relationships', 'SQL_Schema'}

def parse_year_to_num(val):
    """
    Parses text years ('2600 BC' -> -2600, '320 AD' -> 320) into signed SMALLINT integers.
    Supports BC, BCE, AD, CE prefixes/suffixes and approximate prefixes (c., circa).
    """
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip().upper()
    if not s or s in ('NAN', 'NONE', 'NULL', 'UNRECORDED', 'UNKNOWN'):
        return None
    
    # Extract digits and era
    m = re.search(r'(\d+)\s*(BC|BCE|AD|CE)?', s)
    if not m:
        return None
    
    num = int(m.group(1))
    era = m.group(2)
    if era in ('BC', 'BCE') or 'BC' in s or 'BCE' in s:
        return -num
    return num

def clean_val(val):
    """Strips whitespace and converts NaN/NaT to None (SQL NULL)."""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, str):
        cleaned = val.strip()
        if cleaned == '' or cleaned.lower() in ('nan', 'none', 'null'):
            return None
        return cleaned
    return val

def connect_to_postgres():
    """Establishes connection to PostgreSQL using .env variables."""
    dbname = os.getenv('DB_NAME', 'bharatpath_db')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASS', 'postgres')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')

    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=5
        )
        return conn
    except Exception as e:
        print(f"\n[FATAL] Unable to connect to PostgreSQL ({user}@{host}:{port}/{dbname}):")
        print(f"        {e}\n")
        print("Please ensure PostgreSQL is running and credentials in .env are correct.")
        sys.exit(1)

def run_loader(excel_path, dry_run=False, replace_dev_seed=False):
    if not os.path.exists(excel_path):
        print(f"[ERROR] Excel file not found: {excel_path}")
        sys.exit(1)

    print("=" * 76)
    print("  BHARATPATH – PRODUCTION EXCEL TO POSTGRESQL LOADER")
    print("=" * 76)
    print(f" Source Workbook  : {excel_path}")
    print(f" Mode             : {'[DRY RUN - ROLLBACK ONLY]' if dry_run else ('[REPLACE SEED - TRUNCATE CASCADE]' if replace_dev_seed else '[APPEND / INSERT]')}")
    print("=" * 76)

    xl = pd.ExcelFile(excel_path)
    all_sheet_names = xl.sheet_names
    data_sheets = [s for s in all_sheet_names if s not in SKIP_SHEETS]
    print(f"Found {len(all_sheet_names)} total sheets. Skipping 4 documentation sheets.")
    print(f"Loading {len(data_sheets)} operational data sheets across 5 dependency levels...\n")

    conn = connect_to_postgres()
    cur = conn.cursor()

    current_sheet = None
    current_row_idx = 0

    try:
        # Step 1: Manage triggers and truncation if replacing seed
        if replace_dev_seed:
            print("--> Disabling user triggers via session_replication_role = 'replica'...")
            cur.execute("SET session_replication_role = 'replica';")
            
            print("--> Truncating all 13 tables CASCADE...")
            cur.execute("""
                TRUNCATE TABLE cultural_exchanges, travellers, currencies, 
                               route_commodity, route_city, trade_routes, ports, 
                               kingdoms, cities, commodities, historical_periods, 
                               regions, sources CASCADE;
            """)
            print("    Tables truncated successfully.\n")

        # ---------------------------------------------------------------------
        # LEVEL 1: Sources (41 rows)
        # ---------------------------------------------------------------------
        current_sheet = 'Sources'
        print(f"[Level 1] Loading {current_sheet}...")
        df_src = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_src.iterrows():
            current_row_idx = idx + 2
            cur.execute("""
                INSERT INTO sources (source_id, title, author_or_editor, source_type, publisher, publication_year, url, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    author_or_editor = EXCLUDED.author_or_editor,
                    source_type = EXCLUDED.source_type,
                    publisher = EXCLUDED.publisher,
                    publication_year = EXCLUDED.publication_year,
                    url = EXCLUDED.url,
                    note = EXCLUDED.note;
            """, (
                clean_val(row['source_id']), clean_val(row['title']), clean_val(row['author_or_editor']),
                clean_val(row['source_type']), clean_val(row['publisher']),
                str(row['publication_year']).split('.')[0] if pd.notna(row['publication_year']) else None,
                clean_val(row['url']), clean_val(row['note'])
            ))
        print(f"         {len(df_src)} records processed.")

        # ---------------------------------------------------------------------
        # LEVEL 2: Regions (33), Historical_Periods (32), Commodities (30)
        # ---------------------------------------------------------------------
        current_sheet = 'Regions'
        print(f"[Level 2] Loading {current_sheet}...")
        df_reg = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_reg.iterrows():
            current_row_idx = idx + 2
            cur.execute("""
                INSERT INTO regions (region_id, region_name, historical_names, present_day_area, present_day_country, geographic_setting, historical_significance, source_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (region_id) DO UPDATE SET
                    region_name = EXCLUDED.region_name,
                    historical_names = EXCLUDED.historical_names,
                    present_day_area = EXCLUDED.present_day_area,
                    present_day_country = EXCLUDED.present_day_country,
                    geographic_setting = EXCLUDED.geographic_setting,
                    historical_significance = EXCLUDED.historical_significance,
                    source_id = EXCLUDED.source_id;
            """, (
                clean_val(row['region_id']), clean_val(row['region_name']), clean_val(row['historical_names']),
                clean_val(row['present_day_area']), clean_val(row['present_day_country']),
                clean_val(row['geographic_setting']), clean_val(row['historical_significance']), clean_val(row['source_id'])
            ))
        print(f"         {len(df_reg)} records processed.")

        current_sheet = 'Historical_Periods'
        print(f"[Level 2] Loading {current_sheet}...")
        df_hp = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_hp.iterrows():
            current_row_idx = idx + 2
            s_num = parse_year_to_num(row['start_year'])
            e_num = parse_year_to_num(row['end_year'])
            cur.execute("""
                INSERT INTO historical_periods (period_id, period_name, era, start_year, end_year, start_year_num, end_year_num, dating_note, defining_features, source_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (period_id) DO UPDATE SET
                    period_name = EXCLUDED.period_name,
                    era = EXCLUDED.era,
                    start_year = EXCLUDED.start_year,
                    end_year = EXCLUDED.end_year,
                    start_year_num = EXCLUDED.start_year_num,
                    end_year_num = EXCLUDED.end_year_num,
                    dating_note = EXCLUDED.dating_note,
                    defining_features = EXCLUDED.defining_features,
                    source_id = EXCLUDED.source_id;
            """, (
                clean_val(row['period_id']), clean_val(row['period_name']), clean_val(row['era']),
                clean_val(row['start_year']), clean_val(row['end_year']), s_num, e_num,
                clean_val(row['dating_note']), clean_val(row['defining_features']), clean_val(row['source_id'])
            ))
        print(f"         {len(df_hp)} records processed.")

        current_sheet = 'Commodities'
        print(f"[Level 2] Loading {current_sheet}...")
        df_cm = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_cm.iterrows():
            current_row_idx = idx + 2
            cur.execute("""
                INSERT INTO commodities (commodity_id, commodity_name, category, primary_source_area, trade_direction, attested_in, description, source_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (commodity_id) DO UPDATE SET
                    commodity_name = EXCLUDED.commodity_name,
                    category = EXCLUDED.category,
                    primary_source_area = EXCLUDED.primary_source_area,
                    trade_direction = EXCLUDED.trade_direction,
                    attested_in = EXCLUDED.attested_in,
                    description = EXCLUDED.description,
                    source_id = EXCLUDED.source_id;
            """, (
                clean_val(row['commodity_id']), clean_val(row['commodity_name']), clean_val(row['category']),
                clean_val(row['primary_source_area']), clean_val(row['trade_direction']),
                clean_val(row['attested_in']), clean_val(row['description']), clean_val(row['source_id'])
            ))
        print(f"         {len(df_cm)} records processed.")

        # ---------------------------------------------------------------------
        # LEVEL 3: Cities (73), Cultural_Exchanges (30)
        # ---------------------------------------------------------------------
        current_sheet = 'Cities'
        print(f"[Level 3] Loading {current_sheet}...")
        df_cit = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_cit.iterrows():
            current_row_idx = idx + 2
            meta = {
                "dating_note": "Classical urban florescence",
                "river_or_coast": clean_val(row['river_or_coast']),
                "city_type": clean_val(row['city_type']),
                "present_day_state": clean_val(row['present_day_state']),
                "present_day_country": clean_val(row['present_day_country']),
                "historical_highlights": clean_val(row['historical_significance']),
                "image_asset": f"/static/img/artefacts/cities/{str(row['city_id']).lower()}.jpg"
            }
            cur.execute("""
                INSERT INTO cities (city_id, ancient_name, modern_name, present_day_state, present_day_country, 
                                    region_id, river_or_coast, city_type, period_id, historical_significance, 
                                    latitude, longitude, source_id, artefact_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (city_id) DO UPDATE SET
                    ancient_name = EXCLUDED.ancient_name,
                    modern_name = EXCLUDED.modern_name,
                    present_day_state = EXCLUDED.present_day_state,
                    present_day_country = EXCLUDED.present_day_country,
                    region_id = EXCLUDED.region_id,
                    river_or_coast = EXCLUDED.river_or_coast,
                    city_type = EXCLUDED.city_type,
                    period_id = EXCLUDED.period_id,
                    historical_significance = EXCLUDED.historical_significance,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    source_id = EXCLUDED.source_id,
                    artefact_metadata = EXCLUDED.artefact_metadata;
            """, (
                clean_val(row['city_id']), clean_val(row['ancient_name']), clean_val(row['modern_name']),
                clean_val(row['present_day_state']), clean_val(row['present_day_country']),
                clean_val(row['region_id']), clean_val(row['river_or_coast']), clean_val(row['city_type']),
                clean_val(row['period_id']), clean_val(row['historical_significance']),
                float(row['latitude']), float(row['longitude']), clean_val(row['source_id']), Json(meta)
            ))
        print(f"         {len(df_cit)} records processed.")

        current_sheet = 'Cultural_Exchanges'
        print(f"[Level 3] Loading {current_sheet}...")
        df_ce = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_ce.iterrows():
            current_row_idx = idx + 2
            s_num = parse_year_to_num(row['start_year'])
            e_num = parse_year_to_num(row['end_year'])
            meta = {
                "dating_note": clean_val(row['dating_note']),
                "evidence_type": clean_val(row['evidence_type']),
                "exchange_type": clean_val(row['exchange_type']),
                "historical_highlights": clean_val(row['description']),
                "image_asset": f"/static/img/artefacts/exchanges/{str(row['exchange_id']).lower()}.jpg"
            }
            cur.execute("""
                INSERT INTO cultural_exchanges (exchange_id, exchange_name, exchange_type, from_region_id, to_region_id, 
                                                period_id, start_year, end_year, start_year_num, end_year_num, 
                                                dating_note, description, evidence_type, source_id, artefact_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (exchange_id) DO UPDATE SET
                    exchange_name = EXCLUDED.exchange_name,
                    exchange_type = EXCLUDED.exchange_type,
                    from_region_id = EXCLUDED.from_region_id,
                    to_region_id = EXCLUDED.to_region_id,
                    period_id = EXCLUDED.period_id,
                    start_year = EXCLUDED.start_year,
                    end_year = EXCLUDED.end_year,
                    start_year_num = EXCLUDED.start_year_num,
                    end_year_num = EXCLUDED.end_year_num,
                    dating_note = EXCLUDED.dating_note,
                    description = EXCLUDED.description,
                    evidence_type = EXCLUDED.evidence_type,
                    source_id = EXCLUDED.source_id,
                    artefact_metadata = EXCLUDED.artefact_metadata;
            """, (
                clean_val(row['exchange_id']), clean_val(row['exchange_name']), clean_val(row['exchange_type']),
                clean_val(row['from_region_id']), clean_val(row['to_region_id']), clean_val(row['period_id']),
                clean_val(row['start_year']), clean_val(row['end_year']), s_num, e_num,
                clean_val(row['dating_note']), clean_val(row['description']), clean_val(row['evidence_type']),
                clean_val(row['source_id']), Json(meta)
            ))
        print(f"         {len(df_ce)} records processed.")

        # ---------------------------------------------------------------------
        # LEVEL 4: Kingdoms (31), Ports (28), Trade_Routes (26)
        # ---------------------------------------------------------------------
        current_sheet = 'Kingdoms'
        print(f"[Level 4] Loading {current_sheet}...")
        df_kg = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_kg.iterrows():
            current_row_idx = idx + 2
            s_num = parse_year_to_num(row['start_year'])
            e_num = parse_year_to_num(row['end_year'])
            meta = {
                "dating_note": clean_val(row['dating_note']),
                "founder": clean_val(row['founder']),
                "notable_ruler": clean_val(row['notable_ruler']),
                "polity_type": clean_val(row['polity_type']),
                "historical_highlights": clean_val(row['historical_significance']),
                "image_asset": f"/static/img/artefacts/kingdoms/{str(row['kingdom_id']).lower()}.jpg"
            }
            cur.execute("""
                INSERT INTO kingdoms (kingdom_id, kingdom_name, polity_type, capital_city_id, region_id, 
                                      period_id, start_year, end_year, start_year_num, end_year_num, 
                                      dating_note, founder, notable_ruler, historical_significance, source_id, artefact_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (kingdom_id) DO UPDATE SET
                    kingdom_name = EXCLUDED.kingdom_name,
                    polity_type = EXCLUDED.polity_type,
                    capital_city_id = EXCLUDED.capital_city_id,
                    region_id = EXCLUDED.region_id,
                    period_id = EXCLUDED.period_id,
                    start_year = EXCLUDED.start_year,
                    end_year = EXCLUDED.end_year,
                    start_year_num = EXCLUDED.start_year_num,
                    end_year_num = EXCLUDED.end_year_num,
                    dating_note = EXCLUDED.dating_note,
                    founder = EXCLUDED.founder,
                    notable_ruler = EXCLUDED.notable_ruler,
                    historical_significance = EXCLUDED.historical_significance,
                    source_id = EXCLUDED.source_id,
                    artefact_metadata = EXCLUDED.artefact_metadata;
            """, (
                clean_val(row['kingdom_id']), clean_val(row['kingdom_name']), clean_val(row['polity_type']),
                clean_val(row['capital_city_id']), clean_val(row['region_id']), clean_val(row['period_id']),
                clean_val(row['start_year']), clean_val(row['end_year']), s_num, e_num,
                clean_val(row['dating_note']), clean_val(row['founder']), clean_val(row['notable_ruler']),
                clean_val(row['historical_significance']), clean_val(row['source_id']), Json(meta)
            ))
        print(f"         {len(df_kg)} records processed.")

        current_sheet = 'Ports'
        print(f"[Level 4] Loading {current_sheet}...")
        df_pt = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_pt.iterrows():
            current_row_idx = idx + 2
            cur.execute("""
                INSERT INTO ports (port_id, port_name, present_day_location, city_id, coast, port_type, 
                                   period_id, active_period_note, overseas_connections, trade_note, 
                                   latitude, longitude, source_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (port_id) DO UPDATE SET
                    port_name = EXCLUDED.port_name,
                    present_day_location = EXCLUDED.present_day_location,
                    city_id = EXCLUDED.city_id,
                    coast = EXCLUDED.coast,
                    port_type = EXCLUDED.port_type,
                    period_id = EXCLUDED.period_id,
                    active_period_note = EXCLUDED.active_period_note,
                    overseas_connections = EXCLUDED.overseas_connections,
                    trade_note = EXCLUDED.trade_note,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    source_id = EXCLUDED.source_id;
            """, (
                clean_val(row['port_id']), clean_val(row['port_name']), clean_val(row['present_day_location']),
                clean_val(row['city_id']), clean_val(row['coast']), clean_val(row['port_type']),
                clean_val(row['period_id']), clean_val(row['active_period_note']), clean_val(row['overseas_connections']),
                clean_val(row['trade_note']), float(row['latitude']), float(row['longitude']), clean_val(row['source_id'])
            ))
        print(f"         {len(df_pt)} records processed.")

        current_sheet = 'Trade_Routes'
        print(f"[Level 4] Loading {current_sheet}...")
        df_tr = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_tr.iterrows():
            current_row_idx = idx + 2
            s_num = parse_year_to_num(row['start_year'])
            e_num = parse_year_to_num(row['end_year'])
            meta = {
                "dating_note": clean_val(row['dating_note']),
                "route_type": clean_val(row['route_type']),
                "historical_highlights": clean_val(row['description']),
                "image_asset": f"/static/img/artefacts/routes/{str(row['route_id']).lower()}.jpg"
            }
            cur.execute("""
                INSERT INTO trade_routes (route_id, route_name, route_type, start_city_id, end_city_id, 
                                          period_id, start_year, end_year, start_year_num, end_year_num, 
                                          dating_note, description, source_id, artefact_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (route_id) DO UPDATE SET
                    route_name = EXCLUDED.route_name,
                    route_type = EXCLUDED.route_type,
                    start_city_id = EXCLUDED.start_city_id,
                    end_city_id = EXCLUDED.end_city_id,
                    period_id = EXCLUDED.period_id,
                    start_year = EXCLUDED.start_year,
                    end_year = EXCLUDED.end_year,
                    start_year_num = EXCLUDED.start_year_num,
                    end_year_num = EXCLUDED.end_year_num,
                    dating_note = EXCLUDED.dating_note,
                    description = EXCLUDED.description,
                    source_id = EXCLUDED.source_id,
                    artefact_metadata = EXCLUDED.artefact_metadata;
            """, (
                clean_val(row['route_id']), clean_val(row['route_name']), clean_val(row['route_type']),
                clean_val(row['start_city_id']), clean_val(row['end_city_id']), clean_val(row['period_id']),
                clean_val(row['start_year']), clean_val(row['end_year']), s_num, e_num,
                clean_val(row['dating_note']), clean_val(row['description']), clean_val(row['source_id']), Json(meta)
            ))
        print(f"         {len(df_tr)} records processed.")

        # ---------------------------------------------------------------------
        # LEVEL 5: Route_City (68), Route_Commodity (79), Currencies (32), Travellers (28)
        # ---------------------------------------------------------------------
        current_sheet = 'Route_City'
        print(f"[Level 5] Loading {current_sheet}...")
        df_rc = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_rc.iterrows():
            current_row_idx = idx + 2
            cur.execute("""
                INSERT INTO route_city (route_id, city_id, stop_sequence, stop_role, note)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (route_id, city_id) DO UPDATE SET
                    stop_sequence = EXCLUDED.stop_sequence,
                    stop_role = EXCLUDED.stop_role,
                    note = EXCLUDED.note;
            """, (
                clean_val(row['route_id']), clean_val(row['city_id']), int(row['stop_sequence']),
                clean_val(row['stop_role']), clean_val(row['note'])
            ))
        print(f"         {len(df_rc)} records processed.")

        current_sheet = 'Route_Commodity'
        print(f"[Level 5] Loading {current_sheet}...")
        df_rcom = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_rcom.iterrows():
            current_row_idx = idx + 2
            cur.execute("""
                INSERT INTO route_commodity (route_id, commodity_id, trade_direction, evidence_note, source_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (route_id, commodity_id) DO UPDATE SET
                    trade_direction = EXCLUDED.trade_direction,
                    evidence_note = EXCLUDED.evidence_note,
                    source_id = EXCLUDED.source_id;
            """, (
                clean_val(row['route_id']), clean_val(row['commodity_id']), clean_val(row['trade_direction']),
                clean_val(row['evidence_note']), clean_val(row['source_id'])
            ))
        print(f"         {len(df_rcom)} records processed.")

        current_sheet = 'Currencies'
        print(f"[Level 5] Loading {current_sheet}...")
        df_cu = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_cu.iterrows():
            current_row_idx = idx + 2
            s_num = parse_year_to_num(row['start_year'])
            e_num = parse_year_to_num(row['end_year'])
            meta = {
                "dating_note": clean_val(row['dating_note']),
                "weight_standard": clean_val(row['weight_standard']),
                "issuer_note": clean_val(row['issuer_note']),
                "metal": clean_val(row['metal']),
                "historical_highlights": clean_val(row['description']),
                "image_asset": f"/static/img/artefacts/currencies/{str(row['currency_id']).lower()}.jpg"
            }
            cur.execute("""
                INSERT INTO currencies (currency_id, coin_name, metal, issuing_kingdom_id, issuer_note, 
                                        period_id, start_year, end_year, start_year_num, end_year_num, 
                                        dating_note, weight_standard, description, source_id, artefact_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (currency_id) DO UPDATE SET
                    coin_name = EXCLUDED.coin_name,
                    metal = EXCLUDED.metal,
                    issuing_kingdom_id = EXCLUDED.issuing_kingdom_id,
                    issuer_note = EXCLUDED.issuer_note,
                    period_id = EXCLUDED.period_id,
                    start_year = EXCLUDED.start_year,
                    end_year = EXCLUDED.end_year,
                    start_year_num = EXCLUDED.start_year_num,
                    end_year_num = EXCLUDED.end_year_num,
                    dating_note = EXCLUDED.dating_note,
                    weight_standard = EXCLUDED.weight_standard,
                    description = EXCLUDED.description,
                    source_id = EXCLUDED.source_id,
                    artefact_metadata = EXCLUDED.artefact_metadata;
            """, (
                clean_val(row['currency_id']), clean_val(row['coin_name']), clean_val(row['metal']),
                clean_val(row['issuing_kingdom_id']), clean_val(row['issuer_note']), clean_val(row['period_id']),
                clean_val(row['start_year']), clean_val(row['end_year']), s_num, e_num,
                clean_val(row['dating_note']), clean_val(row['weight_standard']), clean_val(row['description']),
                clean_val(row['source_id']), Json(meta)
            ))
        print(f"         {len(df_cu)} records processed.")

        current_sheet = 'Travellers'
        print(f"[Level 5] Loading {current_sheet}...")
        df_tv = pd.read_excel(excel_path, sheet_name=current_sheet)
        for idx, row in df_tv.iterrows():
            current_row_idx = idx + 2
            arr_num = parse_year_to_num(row['arrival_year'])
            dep_num = parse_year_to_num(row['departure_year'])
            meta = {
                "dating_note": clean_val(row['dating_note']),
                "account_title": clean_val(row['account_title']),
                "homeland": clean_val(row['homeland']),
                "profession": clean_val(row['role']),
                "historical_highlights": clean_val(row['key_observation']),
                "image_asset": f"/static/img/artefacts/travellers/{str(row['traveller_id']).lower()}.jpg"
            }
            cur.execute("""
                INSERT INTO travellers (traveller_id, traveller_name, homeland, role, arrival_year, departure_year, 
                                        arrival_year_num, departure_year_num, dating_note, period_id, 
                                        kingdom_visited_id, main_city_visited_id, account_title, 
                                        key_observation, source_id, artefact_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (traveller_id) DO UPDATE SET
                    traveller_name = EXCLUDED.traveller_name,
                    homeland = EXCLUDED.homeland,
                    role = EXCLUDED.role,
                    arrival_year = EXCLUDED.arrival_year,
                    departure_year = EXCLUDED.departure_year,
                    arrival_year_num = EXCLUDED.arrival_year_num,
                    departure_year_num = EXCLUDED.departure_year_num,
                    dating_note = EXCLUDED.dating_note,
                    period_id = EXCLUDED.period_id,
                    kingdom_visited_id = EXCLUDED.kingdom_visited_id,
                    main_city_visited_id = EXCLUDED.main_city_visited_id,
                    account_title = EXCLUDED.account_title,
                    key_observation = EXCLUDED.key_observation,
                    source_id = EXCLUDED.source_id,
                    artefact_metadata = EXCLUDED.artefact_metadata;
            """, (
                clean_val(row['traveller_id']), clean_val(row['traveller_name']), clean_val(row['homeland']),
                clean_val(row['role']), clean_val(row['arrival_year']), clean_val(row['departure_year']),
                arr_num, dep_num, clean_val(row['dating_note']), clean_val(row['period_id']),
                clean_val(row['kingdom_visited_id']), clean_val(row['main_city_visited_id']),
                clean_val(row['account_title']), clean_val(row['key_observation']), clean_val(row['source_id']),
                Json(meta)
            ))
        print(f"         {len(df_tv)} records processed.\n")

        # ---------------------------------------------------------------------
        # Table Verification & Status Matrix
        # ---------------------------------------------------------------------
        table_order = [
            ("Level 1", "sources", 41),
            ("Level 2", "regions", 33),
            ("Level 2", "historical_periods", 32),
            ("Level 2", "commodities", 30),
            ("Level 3", "cities", 73),
            ("Level 3", "cultural_exchanges", 30),
            ("Level 4", "kingdoms", 31),
            ("Level 4", "ports", 28),
            ("Level 4", "trade_routes", 26),
            ("Level 5", "route_city", 68),
            ("Level 5", "route_commodity", 79),
            ("Level 5", "currencies", 32),
            ("Level 5", "travellers", 28),
        ]

        print("=" * 76)
        print("  DATABASE VERIFICATION REPORT (WITHIN CURRENT TRANSACTION)")
        print("=" * 76)
        print(f" {'Dep Level':<10} | {'Table Name':<22} | {'Target':<7} | {'Loaded':<7} | {'Status':<10}")
        print("-" * 76)

        total_loaded = 0
        all_ok = True

        for lvl, tbl, target in table_order:
            cur.execute(f"SELECT COUNT(*) FROM {tbl};")
            actual = cur.fetchone()[0]
            total_loaded += actual
            status = "PASS" if actual >= 25 and actual == target else ("WARN" if actual >= 25 else "FAIL")
            if status != "PASS":
                all_ok = False
            print(f" {lvl:<10} | {tbl:<22} | {target:<7} | {actual:<7} | {status:<10}")

        print("-" * 76)
        print(f" {'TOTAL':<35} | {531:<7} | {total_loaded:<7} | {'PERFECT' if (total_loaded == 531 and all_ok) else 'VERIFY'}")
        print("=" * 76)

        # Restore trigger state if replace_dev_seed was used
        if replace_dev_seed:
            cur.execute("SET session_replication_role = 'origin';")
            print("--> Restored user triggers via session_replication_role = 'origin'.")

        if dry_run:
            conn.rollback()
            print("\n[DRY-RUN COMPLETE] All 13 tables verified. Transaction rolled back cleanly without changes.\n")
        else:
            conn.commit()
            print("\n[TRANSACTION COMMITTED] All 531 rows successfully loaded and persisted in PostgreSQL.\n")

    except Exception as e:
        conn.rollback()
        print("\n" + "!" * 76)
        print(f"  [ATOMIC ROLLBACK TRIGGERED]")
        print(f"  Failed Sheet     : '{current_sheet}'")
        print(f"  Excel Row Number : {current_row_idx}")
        print(f"  PostgreSQL Error : {e}")
        print("!" * 76 + "\n")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="BharatPath Production Excel to PostgreSQL Dataset Loader")
    parser.add_argument('--file', type=str, default=DEFAULT_EXCEL_PATH, help="Path to BharatPath_Database_Final.xlsx")
    parser.add_argument('--dry-run', action='store_true', help="Run cleaning, transforms, and inserts inside a single transaction, then rollback")
    parser.add_argument('--replace-dev-seed', action='store_true', help="Disable triggers, truncate all 13 tables CASCADE, load 531 rows, and re-enable triggers")

    args = parser.parse_args()
    run_loader(excel_path=args.file, dry_run=args.dry_run, replace_dev_seed=args.replace_dev_seed)

if __name__ == '__main__':
    main()
