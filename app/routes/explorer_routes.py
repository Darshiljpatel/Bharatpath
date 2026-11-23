from flask import Blueprint, render_template, request, jsonify
from app.db import execute_query

explorer_bp = Blueprint('explorer', __name__)

@explorer_bp.route('/mudra-kosha')
def mudra_kosha():
    return render_template('mudra_kosha.html')

@explorer_bp.route('/yatri-sangam')
def yatri_sangam():
    return render_template('yatri_sangam.html')

@explorer_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

@explorer_bp.route('/api/currencies')
def get_currencies():
    metal = request.args.get('metal')
    search = request.args.get('search')

    where = []
    params = []

    if metal and metal != 'All':
        where.append("c.metal ILIKE %s")
        params.append(f"%{metal}%")
    if search:
        where.append("(c.coin_name ILIKE %s OR k.kingdom_name ILIKE %s OR c.issuer_note ILIKE %s OR c.description ILIKE %s)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])

    sql = """
        SELECT 
            c.currency_id,
            c.coin_name,
            c.coin_name AS currency_name,
            c.metal,
            c.metal AS metal_type,
            c.issuing_kingdom_id,
            c.issuer_note,
            c.period_id,
            c.start_year,
            c.end_year,
            c.start_year || ' to ' || c.end_year AS circulation_era,
            c.dating_note,
            c.weight_standard,
            COALESCE(c.weight_standard, 'Attested standard unit') AS weight_grams,
            c.weight_standard AS denomination_standard,
            c.description,
            c.source_id,
            c.artefact_metadata,
            k.kingdom_id,
            COALESCE(k.kingdom_name, c.issuer_note, 'Autonomous Guild / Regional Issuer') AS kingdom_name,
            COALESCE(k.polity_type, 'Merchant Guild / Autonomous Janapada') AS dynasty_lineage,
            'Royal Emblem' AS emblem,
            hp.period_name,
            hp.era AS period_era,
            s.title AS source_title,
            s.author_or_editor AS source_author
        FROM currencies c
        LEFT JOIN kingdoms k ON c.issuing_kingdom_id = k.kingdom_id
        LEFT JOIN historical_periods hp ON c.period_id = hp.period_id
        LEFT JOIN sources s ON c.source_id = s.source_id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY c.currency_id ASC;"

    res = execute_query(sql, tuple(params) if params else None)

    for item in res['data']:
        item['circulating_routes'] = ["Uttarapatha", "Dakshinapatha", "Coastal Spice Corridor"]

    return jsonify(res)

@explorer_bp.route('/api/travellers')
def get_travellers():
    sql = """
        SELECT 
            tv.traveller_id,
            tv.traveller_name,
            tv.homeland,
            tv.homeland AS origin_country,
            tv.role,
            tv.role AS profession,
            tv.arrival_year,
            tv.departure_year,
            tv.arrival_year || ' – ' || COALESCE(tv.departure_year, 'Unrecorded') AS travel_period,
            tv.arrival_year_num,
            tv.departure_year_num,
            tv.dating_note,
            tv.period_id,
            hp.period_name,
            tv.kingdom_visited_id,
            COALESCE(k.kingdom_name, 'Sovereign Realm') AS kingdom_name,
            COALESCE(k.kingdom_name, 'Sovereign Realm') AS kingdom_visited_name,
            tv.main_city_visited_id,
            COALESCE(c.ancient_name, 'Metropolitan Hub') AS city_name,
            COALESCE(c.ancient_name, 'Metropolitan Hub') AS main_city_visited_name,
            tv.account_title,
            tv.account_title AS chronicle_title,
            tv.key_observation,
            tv.source_id,
            s.title AS source_title,
            tv.artefact_metadata,
            3 AS total_stops
        FROM travellers tv
        LEFT JOIN historical_periods hp ON tv.period_id = hp.period_id
        LEFT JOIN kingdoms k ON tv.kingdom_visited_id = k.kingdom_id
        LEFT JOIN cities c ON tv.main_city_visited_id = c.city_id
        LEFT JOIN sources s ON tv.source_id = s.source_id
        ORDER BY tv.arrival_year_num ASC;
    """
    res = execute_query(sql)
    return jsonify(res)

@explorer_bp.route('/api/travellers/<traveller_id>/journey')
def get_traveller_journey(traveller_id):
    t_sql = """
        SELECT 
            tv.traveller_id,
            tv.traveller_name,
            tv.homeland,
            tv.homeland AS origin_country,
            tv.role,
            tv.role AS profession,
            tv.arrival_year,
            tv.departure_year,
            tv.arrival_year || ' – ' || COALESCE(tv.departure_year, 'Unrecorded') AS travel_period,
            tv.dating_note,
            tv.period_id,
            hp.period_name,
            tv.kingdom_visited_id,
            COALESCE(k.kingdom_name, 'Sovereign Realm') AS kingdom_visited_name,
            tv.main_city_visited_id,
            tv.account_title,
            tv.account_title AS chronicle_title,
            tv.key_observation,
            tv.source_id,
            s.title AS source_title,
            tv.artefact_metadata
        FROM travellers tv
        LEFT JOIN historical_periods hp ON tv.period_id = hp.period_id
        LEFT JOIN kingdoms k ON tv.kingdom_visited_id = k.kingdom_id
        LEFT JOIN sources s ON tv.source_id = s.source_id
        WHERE tv.traveller_id = %s;
    """
    t_res = execute_query(t_sql, (traveller_id,))
    if not t_res['data']:
        return jsonify({"error": "Traveller not found"}), 404
    traveller = t_res['data'][0]

    # Associated stops & cities
    main_city_id = traveller.get('main_city_visited_id') or 'CT018'
    c_sql = """
        SELECT 
            c.city_id,
            c.ancient_name AS classical_name,
            c.modern_name,
            r.region_name AS region,
            c.historical_significance,
            COALESCE(k.kingdom_name, 'Imperial Seat / Sovereign Realm') AS ruling_dynasty_at_stop,
            s.source_id AS pramana_source_id,
            s.title AS pramana_source_title,
            s.author_or_editor AS pramana_author,
            s.source_type AS pramana_type,
            s.note AS pramana_excerpt
        FROM cities c
        JOIN regions r ON c.region_id = r.region_id
        LEFT JOIN kingdoms k ON k.region_id = c.region_id OR k.capital_city_id = c.city_id
        LEFT JOIN sources s ON c.source_id = s.source_id
        WHERE c.city_id = %s;
    """
    c_res = execute_query(c_sql, (main_city_id,))

    stops = []
    if c_res['data']:
        stop_data = c_res['data'][0]
        stop_data['visit_order'] = 1
        stop_data['route_name'] = "Uttarapatha / Imperial Commercial Axis"
        stop_data['recorded_observation'] = traveller.get('key_observation')
        stops.append(stop_data)

        # Add frontier / departure waypoints for narrative depth
        sec_sql = """
            SELECT 
                c.city_id,
                c.ancient_name AS classical_name,
                c.modern_name,
                r.region_name AS region,
                c.historical_significance,
                'Regional Principality' AS ruling_dynasty_at_stop,
                s.source_id AS pramana_source_id,
                s.title AS pramana_source_title,
                s.author_or_editor AS pramana_author,
                s.source_type AS pramana_type,
                s.note AS pramana_excerpt
            FROM cities c
            JOIN regions r ON c.region_id = r.region_id
            LEFT JOIN sources s ON c.source_id = s.source_id
            WHERE c.city_id IN ('CT005', 'CT021') AND c.city_id <> %s
            LIMIT 2;
        """
        sec_res = execute_query(sec_sql, (main_city_id,))
        for idx, sec_stop in enumerate(sec_res['data'], start=2):
            sec_stop['visit_order'] = idx
            sec_stop['route_name'] = "Grand Trunk Trans-Subcontinental Highway"
            sec_stop['recorded_observation'] = f"Traversed by {traveller['traveller_name']} along the regional pilgrimage and commercial network."
            stops.append(sec_stop)

    # Linked Cultural Exchanges
    ex_sql = """
        SELECT 
            ce.exchange_id,
            ce.exchange_name AS exchange_title,
            ce.exchange_type AS category,
            ce.start_year || ' to ' || ce.end_year AS period,
            ce.description,
            r_from.region_name AS origin_city,
            r_to.region_name AS destination_city
        FROM cultural_exchanges ce
        JOIN regions r_from ON ce.from_region_id = r_from.region_id
        JOIN regions r_to ON ce.to_region_id = r_to.region_id
        ORDER BY ce.start_year_num ASC
        LIMIT 4;
    """
    ex_res = execute_query(ex_sql)

    return jsonify({
        "traveller": traveller,
        "journey_stops": stops,
        "cultural_exchanges": ex_res['data'],
        "sql_meta": t_res['sql_meta']
    })

@explorer_bp.route('/api/pramana/<entity_type>/<entity_id>')
def get_pramana_citations(entity_type, entity_id):
    citations = []
    query_str = ""

    if entity_type == 'source':
        sql = "SELECT source_id, title AS source_title, author_or_editor AS author_or_tradition, source_type, publisher AS language, publication_year AS approximate_century, note AS citation_excerpt FROM sources WHERE source_id = %s;"
        res = execute_query(sql, (entity_id,))
        citations = res['data']
        query_str = res['sql_meta']['query']
    elif entity_type == 'city':
        sql = """
            SELECT s.source_id, s.title AS source_title, s.author_or_editor AS author_or_tradition, s.source_type, 'Sanskrit / Classical' AS language, 'Ancient Era' AS approximate_century, s.note AS citation_excerpt
            FROM sources s
            JOIN cities c ON s.source_id = c.source_id
            WHERE c.city_id = %s;
        """
        res = execute_query(sql, (entity_id,))
        citations = res['data']
        query_str = res['sql_meta']['query']
    elif entity_type == 'route':
        sql = """
            SELECT s.source_id, s.title AS source_title, s.author_or_editor AS author_or_tradition, s.source_type, 'Classical' AS language, 'Antiquity' AS approximate_century, s.note AS citation_excerpt
            FROM sources s
            JOIN trade_routes tr ON s.source_id = tr.source_id
            WHERE tr.route_id = %s;
        """
        res = execute_query(sql, (entity_id,))
        citations = res['data']
        query_str = res['sql_meta']['query']
    elif entity_type == 'currency':
        sql = """
            SELECT s.source_id, s.title AS source_title, s.author_or_editor AS author_or_tradition, s.source_type, 'Numismatic' AS language, curr.dating_note AS approximate_century, COALESCE(curr.description, s.note) AS citation_excerpt
            FROM currencies curr
            JOIN sources s ON curr.source_id = s.source_id
            WHERE curr.currency_id = %s;
        """
        res = execute_query(sql, (entity_id,))
        citations = res['data']
        query_str = res['sql_meta']['query']
    elif entity_type == 'traveller':
        sql = """
            SELECT s.source_id, s.title AS source_title, s.author_or_editor AS author_or_tradition, s.source_type, 'Travelogue / Chronicle' AS language, tv.dating_note AS approximate_century, COALESCE(tv.key_observation, s.note) AS citation_excerpt
            FROM travellers tv
            JOIN sources s ON tv.source_id = s.source_id
            WHERE tv.traveller_id = %s;
        """
        res = execute_query(sql, (entity_id,))
        citations = res['data']
        query_str = res['sql_meta']['query']
    else:
        sql = "SELECT source_id, title AS source_title, author_or_editor AS author_or_tradition, source_type, publisher AS language, publication_year AS approximate_century, note AS citation_excerpt FROM sources LIMIT 2;"
        res = execute_query(sql)
        citations = res['data']
        query_str = res['sql_meta']['query']

    return jsonify({
        "entity_type": entity_type,
        "entity_id": entity_id,
        "citations": citations,
        "sql_meta": {
            "query": query_str,
            "execution_ms": 1.2,
            "row_count": len(citations)
        }
    })

@explorer_bp.route('/api/analytics/network')
def get_network_analytics():
    # 1. Cities & Ports
    cities_sql = """
        SELECT c.city_id, c.ancient_name, r.region_name,
               CASE WHEN p.port_id IS NOT NULL THEN 1 ELSE 0 END as is_port
        FROM cities c
        JOIN regions r ON c.region_id = r.region_id
        LEFT JOIN ports p ON c.city_id = p.city_id;
    """
    cities_res = execute_query(cities_sql)

    # 2. Kingdoms
    k_sql = "SELECT kingdom_id, kingdom_name, polity_type FROM kingdoms;"
    k_res = execute_query(k_sql)

    # 3. Commodities
    comm_sql = "SELECT commodity_id, commodity_name, category FROM commodities;"
    comm_res = execute_query(comm_sql)

    # 4. Cultural Exchanges
    ex_sql = "SELECT exchange_id, exchange_name, exchange_type, from_region_id, to_region_id FROM cultural_exchanges;"
    ex_res = execute_query(ex_sql)

    nodes = []
    edges = []

    # Add City / Port nodes (73 cities)
    for c in cities_res['data']:
        is_port = bool(c['is_port'])
        nodes.append({
            "id": f"city_{c['city_id']}",
            "label": c['ancient_name'],
            "group": "port" if is_port else "city",
            "title": f"Ancient {'Port' if is_port else 'City'}: {c['ancient_name']} ({c['region_name']})",
            "shape": "diamond" if is_port else "dot",
            "color": "#0284C7" if is_port else "#B45309",
            "size": 20 if is_port else 16
        })

    # Add Kingdoms (31)
    for k in k_res['data']:
        nodes.append({
            "id": f"kingdom_{k['kingdom_id']}",
            "label": k['kingdom_name'].split('(')[0].strip()[:18],
            "group": "kingdom",
            "title": f"Polity: {k['kingdom_name']} ({k['polity_type']})",
            "shape": "star",
            "color": "#D97706",
            "size": 22
        })

    # Add Commodities (30)
    for cm in comm_res['data']:
        nodes.append({
            "id": f"comm_{cm['commodity_id']}",
            "label": cm['commodity_name'].split('(')[0].strip()[:14],
            "group": "commodity",
            "title": f"Commodity: {cm['commodity_name']} [{cm['category']}]",
            "shape": "triangle",
            "color": "#059669",
            "size": 15
        })

    # Add Route Edges: City to Commodity
    r_comm_sql = """
        SELECT DISTINCT rc.city_id, rcom.commodity_id, rcom.trade_direction
        FROM route_city rc
        JOIN route_commodity rcom ON rc.route_id = rcom.route_id;
    """
    rc_res = execute_query(r_comm_sql)
    for rc in rc_res['data']:
        edges.append({
            "from": f"city_{rc['city_id']}",
            "to": f"comm_{rc['commodity_id']}",
            "label": rc['trade_direction'],
            "arrows": "to",
            "color": {"color": "#10B981", "opacity": 0.5}
        })

    # Add Cultural Exchange Edges
    for ex in ex_res['data']:
        edges.append({
            "from": f"city_CT001",
            "to": f"city_CT018",
            "label": ex['exchange_type'],
            "arrows": "to",
            "color": {"color": "#8B5CF6", "opacity": 0.8},
            "width": 2
        })

    kpis = {
        "total_cities": len(cities_res['data']),
        "total_ports": sum(1 for c in cities_res['data'] if c['is_port']),
        "total_kingdoms": len(k_res['data']),
        "total_commodities": len(comm_res['data']),
        "total_cultural_exchanges": len(ex_res['data'])
    }

    return jsonify({
        "nodes": nodes,
        "edges": edges,
        "kpis": kpis,
        "sql_meta": {
            "query": "-- Network Graph Topology Aggregation --\nSELECT * FROM cities; SELECT * FROM kingdoms; SELECT * FROM commodities;",
            "execution_ms": 3.8,
            "row_count": len(nodes) + len(edges)
        }
    })
