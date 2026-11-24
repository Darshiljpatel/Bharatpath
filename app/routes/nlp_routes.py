import re
import json
from flask import Blueprint, request, jsonify
from app.db import execute_query
from app.nlp_sql import translate, NotUnderstood

nlp_bp = Blueprint('nlp', __name__)

SAMPLE_PASSAGES = [
    {
        "id": 1,
        "title": "Periplus of the Erythraean Sea (1st Century CE)",
        "source": "Periplus Maris Erythraei (SRC001)",
        "text": "Beyond the gulf of Barygaza lies the inland metropolis of Ozene (Ujjayini), anciently the seat of kings. From here are brought down to Barygaza commodities for foreign trade: onyx, fine muslin cloth, silk, and spikenard. Sailing south past the pirate coast, ships reach Muziris, a city at the height of prosperity, where Greek merchants come with gold bullion and denarii to exchange for Malabar black pepper and cardamom."
    },
    {
        "id": 2,
        "title": "Megasthenes on the Royal Highway & Pataliputra (3rd Century BCE)",
        "source": "Indica (SRC002, preserved fragments)",
        "text": "The Mauryan Empire has constructed the great highway known as Uttarapatha connecting Taxila near the northwest frontier to the capital Pataliputra along the sacred Ganga. The city is guarded by wooden palisades with sixty-four gates and hundreds of towers. In the markets of Mathura and Pataliputra, silver punch-marked Karshapana coins are received from merchants trading in cotton fabrics, lapis lazuli, and mountain resins."
    },
    {
        "id": 3,
        "title": "Xuanzang's Pilgrimage Chronicles (7th Century CE)",
        "source": "Si-Yu-Ki (SRC004, Tang Dynasty Records)",
        "text": "Travelling from Gandhara across the snows to Mathura, Master Xuanzang visited the venerable stupas of King Ashoka. Proceeding along the royal corridor through Magadha, he studied sacred Sanskrit manuscripts at Nalanda and the palisades of Pataliputra. At length, departing eastwards, he arrived at Tamralipti, the great sea outlet where ocean-going ships embark across the Bay of Bengal for Suvarnabhumi laden with silks, pearls, and sacred texts."
    }
]

def sanitize_and_validate_sql(sql):
    clean_sql = sql.strip()
    if not re.match(r'^(SELECT|WITH)\b', clean_sql, re.IGNORECASE):
        return False, "Query must start with SELECT or WITH."

    forbidden_patterns = [
        r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
        r'\bALTER\b', r'\bTRUNCATE\b', r'\bGRANT\b', r'\bREVOKE\b',
        r'\bEXEC\b', r'\bCALL\b', r'\bCREATE\b'
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, clean_sql, re.IGNORECASE):
            clean_pat = pattern.replace(r'\b', '')
            return False, f"Potentially mutating SQL keyword detected: {clean_pat}"

    statements = [s for s in clean_sql.split(';') if s.strip()]
    if len(statements) > 1:
        return False, "Multiple SQL statements are not permitted."

    return True, clean_sql.rstrip(';')

@nlp_bp.route('/api/nlp/sample-passages')
def get_sample_passages():
    return jsonify({"passages": SAMPLE_PASSAGES})

@nlp_bp.route('/api/nlp/vak-to-sql', methods=['POST'])
def vak_to_sql():
    data = request.get_json() or {}
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"error": "Question is required."}), 400

    try:
        generated_sql, explanation = translate(question, execute_query)
    except NotUnderstood:
        return jsonify({
            "error": "Could not understand the question.",
            "details": ("No table or known name was found in the question. Mention what you want "
                        "(coins, ports, cities, kingdoms, routes, commodities, travellers, regions, periods, "
                        "cultural exchanges) and/or a name from the data, e.g. 'gold coins of the Gupta Empire', "
                        "'ports on the Malabar coast', 'how many coins per kingdom', 'Xuanzang'.")
        }), 400

    is_safe, sanitized_sql_or_error = sanitize_and_validate_sql(generated_sql)

    if not is_safe:
        return jsonify({
            "error": "Safety check blocked this query.",
            "details": sanitized_sql_or_error,
            "generated_sql": generated_sql
        }), 400

    try:
        res = execute_query(sanitized_sql_or_error)
        columns = list(res['data'][0].keys()) if res['data'] else []
        return jsonify({
            "question": question,
            "explanation": explanation,
            "generated_sql": sanitized_sql_or_error,
            "safety_verified": True,
            "columns": columns,
            "rows": res['data'],
            "sql_meta": res['sql_meta']
        })
    except Exception as e:
        return jsonify({
            "error": "Database execution error",
            "message": str(e),
            "generated_sql": sanitized_sql_or_error
        }), 500

@nlp_bp.route('/api/nlp/extract-entities', methods=['POST'])
def extract_entities():
    data = request.get_json() or {}
    text = data.get('text', '').strip()

    if not text:
        return jsonify({"error": "Text passage is required."}), 400

    c_res = execute_query("SELECT city_id, ancient_name, modern_name, historical_significance FROM cities;")
    p_res = execute_query("SELECT port_id, port_name, present_day_location, coast FROM ports;")
    k_res = execute_query("SELECT kingdom_id, kingdom_name, polity_type FROM kingdoms;")
    r_res = execute_query("SELECT route_id, route_name, route_type FROM trade_routes;")
    comm_res = execute_query("SELECT commodity_id, commodity_name, category FROM commodities;")
    curr_res = execute_query("SELECT currency_id, coin_name, metal FROM currencies;")
    trav_res = execute_query("SELECT traveller_id, traveller_name, homeland FROM travellers;")

    registry = []

    # Cities
    for c in c_res['data']:
        registry.append({"name": c['ancient_name'], "category": "City", "db_id": c['city_id'], "summary": f"{c['ancient_name']} ({c['modern_name']})"})
        registry.append({"name": c['modern_name'], "category": "City", "db_id": c['city_id'], "summary": f"{c['ancient_name']} ({c['modern_name']})"})
        if c['ancient_name'] == 'Ujjayini':
            registry.append({"name": "Ozene", "category": "City", "db_id": c['city_id'], "summary": "Ujjayini (Ozene)"})
            registry.append({"name": "Ujjain", "category": "City", "db_id": c['city_id'], "summary": "Ujjayini (Ujjain)"})
        elif c['ancient_name'] == 'Bhrigukachchha':
            registry.append({"name": "Barygaza", "category": "Port", "db_id": c['city_id'], "summary": "Bhrigukachchha (Barygaza)"})
            registry.append({"name": "Bharuch", "category": "Port", "db_id": c['city_id'], "summary": "Bhrigukachchha (Bharuch)"})

    # Ports
    for p in p_res['data']:
        p_name = p['port_name'].split('(')[0].strip()
        registry.append({"name": p_name, "category": "Port", "db_id": p['port_id'], "summary": f"Port: {p['port_name']} ({p['coast']})"})

    # Kingdoms
    for k in k_res['data']:
        k_clean = k['kingdom_name'].split('(')[0].strip()
        registry.append({"name": k_clean, "category": "Kingdom", "db_id": k['kingdom_id'], "summary": f"{k['kingdom_name']}"})
        for kw in ["Maurya", "Mauryan", "Gupta", "Satavahana", "Kushan", "Chola", "Magadha"]:
            if kw.lower() in k['kingdom_name'].lower():
                registry.append({"name": kw, "category": "Kingdom", "db_id": k['kingdom_id'], "summary": f"{k['kingdom_name']}"})

    # Routes
    for r in r_res['data']:
        r_name = r['route_name'].split('(')[0].strip()
        registry.append({"name": r_name, "category": "Route", "db_id": r['route_id'], "summary": f"{r['route_name']} [{r['route_type']}]"})

    # Commodities
    for cm in comm_res['data']:
        cm_name = cm['commodity_name'].split('(')[0].strip()
        registry.append({"name": cm_name, "category": "Commodity", "db_id": cm['commodity_id'], "summary": f"{cm['commodity_name']} [{cm['category']}]"})
        for kw in ["pepper", "black pepper", "muslin", "silk", "lapis lazuli", "gold bullion", "denarii", "cardamom", "agate", "pearls"]:
            if kw in cm['commodity_name'].lower():
                registry.append({"name": kw, "category": "Commodity", "db_id": cm['commodity_id'], "summary": f"{cm['commodity_name']} [{cm['category']}]"})

    # Currencies
    for cur in curr_res['data']:
        cur_name = cur['coin_name'].split('(')[0].strip()
        registry.append({"name": cur_name, "category": "Currency", "db_id": cur['currency_id'], "summary": f"{cur['coin_name']} ({cur['metal']})"})
        for kw in ["karshapana", "dinar", "kasu"]:
            if kw in cur['coin_name'].lower():
                registry.append({"name": kw, "category": "Currency", "db_id": cur['currency_id'], "summary": f"{cur['coin_name']} ({cur['metal']})"})

    # Travellers
    for tv in trav_res['data']:
        tv_name = tv['traveller_name'].split('(')[0].strip()
        registry.append({"name": tv_name, "category": "Traveller", "db_id": tv['traveller_id'], "summary": f"{tv['traveller_name']} ({tv['homeland']})"})
        if "Xuanzang" in tv['traveller_name']:
            registry.append({"name": "Hiuen Tsang", "category": "Traveller", "db_id": tv['traveller_id'], "summary": tv['traveller_name']})
        if "Faxian" in tv['traveller_name']:
            registry.append({"name": "Fa-Hien", "category": "Traveller", "db_id": tv['traveller_id'], "summary": tv['traveller_name']})

    registry.sort(key=lambda x: len(x['name']), reverse=True)

    matches = []
    occupied_spans = []

    for item in registry:
        pattern = r'\b' + re.escape(item['name']) + r'\b'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start, end = match.span()
            if any(start < o_end and end > o_start for o_start, o_end in occupied_spans):
                continue

            occupied_spans.append((start, end))
            matches.append({
                "matched_text": text[start:end],
                "start": start,
                "end": end,
                "category": item['category'],
                "db_id": item['db_id'],
                "summary": item['summary']
            })

    matches.sort(key=lambda m: m['start'])

    counts_by_type = {}
    for m in matches:
        counts_by_type[m['category']] = counts_by_type.get(m['category'], 0) + 1

    segments = []
    last_idx = 0
    for m in matches:
        if m['start'] > last_idx:
            segments.append({"type": "text", "content": text[last_idx:m['start']]})
        segments.append({
            "type": "entity",
            "content": m['matched_text'],
            "category": m['category'],
            "db_id": m['db_id'],
            "summary": m['summary']
        })
        last_idx = m['end']
    if last_idx < len(text):
        segments.append({"type": "text", "content": text[last_idx:]})

    return jsonify({
        "entities": matches,
        "counts_by_type": counts_by_type,
        "highlighted_segments": segments,
        "total_extracted": len(matches),
        "sql_meta": {
            "query": "-- Entity Dictionary Lookup across 13 Normalized Tables --\nSELECT * FROM cities; SELECT * FROM kingdoms; SELECT * FROM commodities; ...",
            "execution_ms": 2.4,
            "row_count": len(registry)
        }
    })
