import os
import re
import json
from flask import Blueprint, render_template, request, jsonify
import psycopg2
from app.db import execute_query

admin_bp = Blueprint('admin', __name__)

ALLOWED_TABLES = {
    'sources': 'source_id',
    'regions': 'region_id',
    'historical_periods': 'period_id',
    'cities': 'city_id',
    'kingdoms': 'kingdom_id',
    'ports': 'port_id',
    'trade_routes': 'route_id',
    'route_city': 'route_id',
    'commodities': 'commodity_id',
    'route_commodity': 'route_id',
    'currencies': 'currency_id',
    'travellers': 'traveller_id',
    'cultural_exchanges': 'exchange_id'
}

@admin_bp.route('/admin')
def admin_page():
    return render_template('admin_crud.html')

@admin_bp.route('/viva-lab')
def viva_lab_page():
    return render_template('viva_nlp_lab.html')

@admin_bp.route('/api/admin/tables')
def list_tables():
    return jsonify({
        "tables": list(ALLOWED_TABLES.keys()),
        "table_keys": ALLOWED_TABLES
    })

@admin_bp.route('/api/admin/<table_name>', methods=['GET'])
def get_table_data(table_name):
    if table_name not in ALLOWED_TABLES:
        return jsonify({"error": f"Invalid table name: {table_name}"}), 400

    pk = ALLOWED_TABLES[table_name]
    sql = f"SELECT * FROM {table_name} ORDER BY {pk} ASC LIMIT 100;"
    try:
        res = execute_query(sql)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/admin/<table_name>', methods=['POST'])
def insert_table_row(table_name):
    if table_name not in ALLOWED_TABLES:
        return jsonify({"error": f"Invalid table name: {table_name}"}), 400

    payload = request.get_json() or {}
    if not payload:
        return jsonify({"error": "Empty payload"}), 400

    cols = []
    vals = []
    placeholders = []

    for k, v in payload.items():
        if k == 'created_at':
            continue
        cols.append(k)
        placeholders.append("%s")
        if isinstance(v, (dict, list)):
            vals.append(json.dumps(v))
        else:
            vals.append(v)

    sql = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({', '.join(placeholders)}) RETURNING *;"

    try:
        res = execute_query(sql, tuple(vals), fetch=True, commit=True)
        return jsonify({
            "success": True,
            "message": f"Successfully inserted into {table_name}",
            "inserted_row": res['data'][0] if res['data'] else None,
            "sql_meta": res['sql_meta']
        })
    except psycopg2.IntegrityError as ie:
        err_msg = str(ie).strip()
        constraint_match = re.search(r'constraint "([^"]+)"', err_msg)
        constraint_name = constraint_match.group(1) if constraint_match else "Integrity Violation"

        explanation = "A relational 3NF constraint was violated."
        if 'foreign key' in err_msg.lower():
            explanation = f"Foreign Key constraint [{constraint_name}] blocked the operation because referenced parent record does not exist."
        elif 'unique' in err_msg.lower():
            explanation = f"Unique constraint [{constraint_name}] prevented duplicate record insertion."
        elif 'check' in err_msg.lower():
            explanation = f"Domain CHECK constraint [{constraint_name}] failed."

        return jsonify({
            "success": False,
            "error_type": "IntegrityError",
            "constraint_name": constraint_name,
            "pg_error": err_msg,
            "human_explanation": explanation
        }), 400
    except Exception as e:
        err_str = str(e)
        err_lower = err_str.lower()
        if "unique" in err_lower or "primary key" in err_lower:
            return jsonify({
                "success": False,
                "error_type": "IntegrityError",
                "constraint_name": "UNIQUE / PRIMARY KEY Constraint",
                "pg_error": err_str,
                "human_explanation": "Integrity Guard: Duplicate primary key or unique attribute detected."
            }), 400
        elif "check" in err_lower:
            return jsonify({
                "success": False,
                "error_type": "IntegrityError",
                "constraint_name": "Domain CHECK Guard",
                "pg_error": err_str,
                "human_explanation": "Domain CHECK Guard: Value falls outside the allowed relational domain constraints."
            }), 400
        elif "foreign key" in err_lower:
            return jsonify({
                "success": False,
                "error_type": "IntegrityError",
                "constraint_name": "Foreign Key Constraint",
                "pg_error": err_str,
                "human_explanation": "Foreign Key Violation: Referenced parent entity does not exist."
            }), 400
        return jsonify({"success": False, "error": err_str}), 500

@admin_bp.route('/api/admin/<table_name>/<record_id>', methods=['DELETE'])
def delete_table_row(table_name, record_id):
    if table_name not in ALLOWED_TABLES:
        return jsonify({"error": f"Invalid table name: {table_name}"}), 400

    pk = ALLOWED_TABLES[table_name]

    # Check for foreign key restriction in application layer if using SQLite fallback
    if table_name == 'kingdoms':
        check_res = execute_query("SELECT COUNT(*) as cnt FROM currencies WHERE issuing_kingdom_id = %s;", (record_id,))
        if check_res['data'] and check_res['data'][0].get('cnt', 0) > 0:
            return jsonify({
                "success": False,
                "error_type": "IntegrityError",
                "constraint_name": "fk_currencies_kingdom_restrict",
                "pg_error": f'update or delete on table "{table_name}" violates foreign key constraint on table "currencies"',
                "human_explanation": f"3NF RESTRICT Protection: Cannot delete Kingdom '{record_id}' because child records depend on it in table 'currencies' (ON DELETE RESTRICT)."
            }), 400

    sql = f"DELETE FROM {table_name} WHERE {pk} = %s;"
    try:
        res = execute_query(sql, (record_id,), fetch=False, commit=True)
        return jsonify({
            "success": True,
            "message": f"Deleted record {record_id} from {table_name}",
            "sql_meta": res['sql_meta']
        })
    except psycopg2.IntegrityError as ie:
        err_msg = str(ie).strip()
        return jsonify({
            "success": False,
            "error_type": "IntegrityError",
            "constraint_name": "ForeignKeyRestriction",
            "pg_error": err_msg,
            "human_explanation": f"Cannot delete record {record_id} from {table_name} due to active foreign key dependencies."
        }), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin_bp.route('/api/admin/audit-log')
def get_audit_log():
    sql = """
        SELECT log_id, table_name, operation, record_id, changed_at, old_data, new_data
        FROM audit_log
        ORDER BY changed_at DESC, log_id DESC
        LIMIT 50;
    """
    res = execute_query(sql)
    return jsonify(res)

def load_viva_queries():
    queries_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', '04_analytical_queries.sql')
    if not os.path.exists(queries_file):
        return []

    with open(queries_file, 'r', encoding='utf-8') as f:
        content = f.read()

    raw_blocks = content.split('-- ============================================================================')
    parsed_queries = []
    q_id = 1

    for i, block in enumerate(raw_blocks):
        if '-- @name:' not in block:
            continue

        name_m = re.search(r'-- @name:\s*(.+)', block)
        cat_m = re.search(r'-- @category:\s*(.+)', block)
        desc_m = re.search(r'-- @description:\s*([^\n]+(?:\n--\s+[^\n]+)*)', block)

        name = name_m.group(1).strip() if name_m else f"Query {q_id}"
        category = cat_m.group(1).strip() if cat_m else "General SQL"
        desc = ""
        if desc_m:
            raw_desc = desc_m.group(1)
            desc = " ".join([line.replace('--', '').strip() for line in raw_desc.split('\n')])

        sql_statement = ""
        if i + 1 < len(raw_blocks):
            sql_statement = raw_blocks[i + 1].strip()

        if sql_statement:
            parsed_queries.append({
                "query_id": q_id,
                "name": name,
                "category": category,
                "description": desc,
                "sql": sql_statement
            })
            q_id += 1

    return parsed_queries

@admin_bp.route('/api/viva/queries')
def get_viva_queries():
    queries = load_viva_queries()
    return jsonify({"queries": queries, "total": len(queries)})

@admin_bp.route('/api/viva/run/<int:query_id>', methods=['POST'])
def run_viva_query(query_id):
    queries = load_viva_queries()
    target_q = next((q for q in queries if q['query_id'] == query_id), None)
    if not target_q:
        return jsonify({"error": f"Query ID {query_id} not found"}), 404

    sql = target_q['sql']
    try:
        res = execute_query(sql)
        columns = list(res['data'][0].keys()) if res['data'] else []
        return jsonify({
            "query_id": query_id,
            "name": target_q['name'],
            "category": target_q['category'],
            "description": target_q['description'],
            "columns": columns,
            "rows": res['data'],
            "sql_meta": res['sql_meta']
        })
    except Exception as e:
        return jsonify({"error": str(e), "sql": sql}), 500
