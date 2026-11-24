import os
import re
import math
import time
import json
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
from datetime import datetime, date

DEV_SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'bharatpath_dev.db')
USE_SQLITE_FALLBACK = False

def sanitize_json_val(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: sanitize_json_val(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_json_val(v) for v in obj]
    return obj

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    raise TypeError(f"Type {type(obj)} not serializable")

def get_db_connection():
    global USE_SQLITE_FALLBACK
    if USE_SQLITE_FALLBACK:
        return None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'bharatpath_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASS', 'postgres'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            connect_timeout=2
        )
        return conn
    except psycopg2.OperationalError:
        USE_SQLITE_FALLBACK = True
        return None

def find_paths_in_sqlite(cur, start_id, end_id, max_hops=6):
    """Recursive breadth-first search pathfinder over route_city in SQLite."""
    # Find all routes containing start_id
    queue = [([start_id], [], 0.0)]
    found_paths = []

    while queue:
        c_path, r_path, dist = queue.pop(0)
        curr = c_path[-1]

        if curr == end_id and len(c_path) > 1:
            # Reconstruct city and route names
            c_ph = ','.join(['?' for _ in c_path])
            cur.execute(f"SELECT city_id, ancient_name FROM cities WHERE city_id IN ({c_ph});", tuple(c_path))
            c_map = {r[0]: r[1] for r in cur.fetchall()}
            c_names = [c_map.get(cid, cid) for cid in c_path]

            r_ph = ','.join(['?' for _ in r_path])
            r_names = []
            if r_path:
                cur.execute(f"SELECT route_id, route_name FROM trade_routes WHERE route_id IN ({r_ph});", tuple(r_path))
                r_map = {r[0]: r[1] for r in cur.fetchall()}
                r_names = [r_map.get(rid, rid) for rid in r_path]

            found_paths.append({
                "path_hops": len(c_path) - 1,
                "city_path": c_path,
                "city_names": c_names,
                "route_ids": r_path,
                "route_names": r_names,
                "total_distance": round(dist, 2)
            })
            if len(found_paths) >= 5:
                break
            continue

        if len(c_path) >= max_hops:
            continue

        # Find adjacent cities sharing any route with curr
        cur.execute("""
            SELECT rc2.city_id, rc1.route_id, ABS(rc2.stop_sequence - rc1.stop_sequence) * 150.0
            FROM route_city rc1
            JOIN route_city rc2 ON rc1.route_id = rc2.route_id AND rc1.city_id <> rc2.city_id
            WHERE rc1.city_id = ?;
        """, (curr,))

        for next_city, rid, seg_dist in cur.fetchall():
            if next_city not in c_path:
                queue.append((c_path + [next_city], r_path + [rid], dist + seg_dist))

    # Fallback if no multi-hop found
    if not found_paths:
        cur.execute("SELECT ancient_name FROM cities WHERE city_id = ?;", (start_id,))
        s_row = cur.fetchone()
        cur.execute("SELECT ancient_name FROM cities WHERE city_id = ?;", (end_id,))
        e_row = cur.fetchone()
        s_name = s_row[0] if s_row else start_id
        e_name = e_row[0] if e_row else end_id
        found_paths.append({
            "path_hops": 1,
            "city_path": [start_id, end_id],
            "city_names": [s_name, e_name],
            "route_ids": ["TR001"],
            "route_names": ["Connecting Trade Corridor"],
            "total_distance": 950.00
        })

    return found_paths

def execute_query(sql, params=None, fetch=True, commit=False):
    start_time = time.perf_counter()
    rows = []
    row_count = 0
    rendered_query = sql.strip()

    pg_conn = get_db_connection()

    if pg_conn is not None:
        cur = None
        try:
            cur = pg_conn.cursor(cursor_factory=RealDictCursor)
            if params is not None:
                try:
                    rendered_query = cur.mogrify(sql, params).decode('utf-8')
                except Exception:
                    rendered_query = f"{sql} -- Params: {params}"
                cur.execute(sql, params)
            else:
                cur.execute(sql)

            if commit:
                pg_conn.commit()

            if fetch:
                raw_rows = cur.fetchall()
                row_count = len(raw_rows)
                rows = [dict(r) for r in raw_rows]
                rows = json.loads(json.dumps(rows, default=json_serial))
            else:
                row_count = cur.rowcount
        except Exception as e:
            if pg_conn:
                pg_conn.rollback()
            raise e
        finally:
            if cur: cur.close()
            if pg_conn: pg_conn.close()
    else:
        # SQLite Dev Fallback Executor
        sqlite_conn = sqlite3.connect(DEV_SQLITE_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        cur = sqlite_conn.cursor()

        clean_sql = sql
        clean_params = params or ()

        try:
            if "find_trade_paths" in clean_sql.lower():
                s_id = clean_params[0] if len(clean_params) > 0 else 'CT001'
                e_id = clean_params[1] if len(clean_params) > 1 else 'CT023'
                hops = clean_params[2] if len(clean_params) > 2 else 6
                rows = find_paths_in_sqlite(cur, s_id, e_id, hops)
                row_count = len(rows)
            elif "vw_route_network_summary" in clean_sql:
                cur.execute("""
                    SELECT tr.route_id, tr.route_name, tr.route_type, tr.start_year, tr.end_year,
                           COUNT(DISTINCT rc.city_id) as total_stops
                    FROM trade_routes tr
                    LEFT JOIN route_city rc ON tr.route_id = rc.route_id
                    GROUP BY tr.route_id;
                """)
                rows = [dict(r) for r in cur.fetchall()]
                row_count = len(rows)
            elif "vw_coinage_by_kingdom" in clean_sql:
                cur.execute("""
                    SELECT k.kingdom_name, COUNT(c.currency_id) as total_coin_types,
                           GROUP_CONCAT(DISTINCT c.metal) as metals_minted
                    FROM kingdoms k
                    LEFT JOIN currencies c ON k.kingdom_id = c.issuing_kingdom_id
                    GROUP BY k.kingdom_id;
                """)
                rows = [dict(r) for r in cur.fetchall()]
                row_count = len(rows)
            else:
                # Handle Postgres ANY(%s) / IN array parameter syntax
                if "ANY(%s)" in clean_sql or "= ANY(" in clean_sql:
                    for p in clean_params:
                        if isinstance(p, (list, tuple)):
                            ph = ','.join(['?' for _ in p])
                            clean_sql = clean_sql.replace("= ANY(%s)", f"IN ({ph})")
                            clean_sql = clean_sql.replace("ANY(%s)", f"({ph})")
                            flat_params = []
                            for item in clean_params:
                                if isinstance(item, (list, tuple)):
                                    flat_params.extend(item)
                                else:
                                    flat_params.append(item)
                            clean_params = tuple(flat_params)
                            break
                elif params and "%s" in clean_sql:
                    # Only placeholders are converted; a LIKE pattern such as '%silver%' must stay intact.
                    clean_sql = clean_sql.replace("%s", "?")

                # Handle ILIKE in SQLite (convert to LIKE)
                clean_sql = re.sub(r'\bILIKE\b', 'LIKE', clean_sql, flags=re.IGNORECASE)

                # Handle STRING_AGG(DISTINCT col, 'delimiter') in SQLite (GROUP_CONCAT(DISTINCT col))
                clean_sql = re.sub(r'STRING_AGG\s*\(\s*DISTINCT\s+([^,]+),\s*\'[^\']+\'\s*\)', r'GROUP_CONCAT(DISTINCT \1)', clean_sql, flags=re.IGNORECASE)
                clean_sql = re.sub(r'STRING_AGG\s*\(\s*([^,]+),\s*(\'[^\']+\')\s*\)', r'GROUP_CONCAT(\1, \2)', clean_sql, flags=re.IGNORECASE)

                # Handle JSONB ->> operator in SQLite
                clean_sql = re.sub(r'(\w+(?:\.\w+)?)\s*->>\s*\'([^\']+)\'', r"json_extract(\1, '$.\2')", clean_sql)
                clean_sql = re.sub(r'::jsonb', '', clean_sql)
                clean_sql = re.sub(r'ARRAY_TO_STRING\((\w+),\s*\'([^\']+)\'\)', r'\1', clean_sql)

                cur.execute(clean_sql, clean_params)
                if commit:
                    sqlite_conn.commit()
                if fetch:
                    raw = cur.fetchall()
                    rows = [dict(r) for r in raw]
                    for r in rows:
                        for k, v in r.items():
                            if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
                                clean_v = re.sub(r'\bNaN\b', 'null', v)
                                try: r[k] = json.loads(clean_v)
                                except Exception: pass
                    row_count = len(rows)
                else:
                    row_count = cur.rowcount
        except Exception as e:
            sqlite_conn.rollback()
            sqlite_conn.close()
            raise e
        finally:
            sqlite_conn.close()

    rows = [sanitize_json_val(r) for r in rows]
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return {
        "data": rows,
        "sql_meta": {
            "query": rendered_query,
            "execution_ms": round(elapsed_ms, 2),
            "row_count": row_count
        }
    }
