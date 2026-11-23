from flask import Blueprint, render_template, request, jsonify
from app.db import execute_query

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api/cities/list')
def get_cities_list():
    sql = """
        SELECT 
            c.city_id, 
            c.ancient_name AS classical_name, 
            c.modern_name, 
            r.region_name AS region,
            c.present_day_state,
            c.present_day_country
        FROM cities c
        JOIN regions r ON c.region_id = r.region_id
        ORDER BY c.ancient_name ASC;
    """
    res = execute_query(sql)
    return jsonify(res)

@main_bp.route('/api/map-data')
def get_map_data():
    year_str = request.args.get('year')
    route_type = request.args.get('route_type')

    city_params = []
    city_where = []

    if year_str:
        try:
            year = int(year_str)
            city_where.append("hp.start_year_num <= %s AND hp.end_year_num >= %s")
            city_params.extend([year, year])
        except ValueError:
            pass

    city_sql = """
        SELECT 
            c.city_id,
            c.ancient_name AS classical_name,
            c.modern_name,
            r.region_name AS region,
            c.latitude,
            c.longitude,
            COALESCE(hp.start_year_num, -2600) AS era_start_year,
            COALESCE(hp.end_year_num, 1200) AS era_end_year,
            c.historical_significance,
            c.artefact_metadata,
            CASE WHEN p.port_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_port,
            p.port_type,
            p.coast AS water_body,
            TRUE AS tidal_dock_present,
            3 AS pramana_citation_count
        FROM cities c
        JOIN regions r ON c.region_id = r.region_id
        JOIN historical_periods hp ON c.period_id = hp.period_id
        LEFT JOIN ports p ON c.city_id = p.city_id
    """
    if city_where:
        city_sql += " WHERE " + " AND ".join(city_where)
    city_sql += " ORDER BY c.ancient_name ASC;"

    cities_res = execute_query(city_sql, tuple(city_params) if city_params else None)

    # Fetch Routes
    route_params = []
    route_where = []
    if year_str:
        try:
            year = int(year_str)
            route_where.append("tr.start_year_num <= %s AND tr.end_year_num >= %s")
            route_params.extend([year, year])
        except ValueError:
            pass
    if route_type and route_type != 'All':
        route_where.append("tr.route_type = %s")
        route_params.append(route_type)

    routes_sql = """
        SELECT 
            tr.route_id,
            tr.route_name,
            tr.route_type,
            COALESCE(tr.start_year_num, -600) AS active_era_start,
            COALESCE(tr.end_year_num, 1200) AS active_era_end,
            tr.description AS terrain_description,
            'Caravan / Galleys' AS primary_transport_mode,
            tr.artefact_metadata
        FROM trade_routes tr
    """
    if route_where:
        routes_sql += " WHERE " + " AND ".join(route_where)
    routes_sql += " ORDER BY tr.route_id ASC;"

    routes_res = execute_query(routes_sql, tuple(route_params) if route_params else None)

    # Attach ordered stops and commodities to each route
    enriched_routes = []
    for rt in routes_res['data']:
        r_id = rt['route_id']
        stops_sql = """
            SELECT 
                rc.stop_sequence AS stop_order,
                c.city_id,
                c.ancient_name AS classical_name,
                c.latitude,
                c.longitude
            FROM route_city rc
            JOIN cities c ON rc.city_id = c.city_id
            WHERE rc.route_id = %s
            ORDER BY rc.stop_sequence ASC;
        """
        s_res = execute_query(stops_sql, (r_id,))

        comm_sql = """
            SELECT 
                comm.commodity_id,
                comm.commodity_name,
                comm.category,
                rcom.trade_direction
            FROM route_commodity rcom
            JOIN commodities comm ON rcom.commodity_id = comm.commodity_id
            WHERE rcom.route_id = %s;
        """
        c_res = execute_query(comm_sql, (r_id,))

        rt['stops'] = s_res['data']
        rt['commodities'] = c_res['data']
        enriched_routes.append(rt)

    # Active Kingdoms
    k_params = []
    k_sql = """
        SELECT 
            k.kingdom_id, 
            k.kingdom_name, 
            k.capital_city_id AS capital_city, 
            COALESCE(k.start_year_num, -600) AS founded_year, 
            COALESCE(k.end_year_num, 1200) AS dissolved_year, 
            k.polity_type AS dynasty_lineage, 
            'Royal Emblem' AS emblem, 
            k.artefact_metadata
        FROM kingdoms k
    """
    if year_str:
        try:
            year = int(year_str)
            k_sql += " WHERE k.start_year_num <= %s AND k.end_year_num >= %s"
            k_params.append(year)
            k_params.append(year)
        except ValueError:
            pass
    k_sql += " ORDER BY k.start_year_num ASC;"
    kingdoms_res = execute_query(k_sql, tuple(k_params) if k_params else None)

    combined_meta = {
        "query": f"-- Cities Query:\n{cities_res['sql_meta']['query']}\n\n-- Routes Query:\n{routes_res['sql_meta']['query']}",
        "execution_ms": round(cities_res['sql_meta']['execution_ms'] + routes_res['sql_meta']['execution_ms'], 2),
        "row_count": len(cities_res['data']) + len(enriched_routes)
    }

    return jsonify({
        "cities": cities_res['data'],
        "routes": enriched_routes,
        "kingdoms": kingdoms_res['data'],
        "sql_meta": combined_meta
    })

@main_bp.route('/api/route-finder')
def find_trade_corridor():
    from_city_id = request.args.get('from_city')
    to_city_id = request.args.get('to_city')
    max_hops = request.args.get('max_hops', 6)

    if not from_city_id or not to_city_id:
        return jsonify({"error": "from_city and to_city parameters required"}), 400

    try:
        hops = int(max_hops)
    except ValueError:
        hops = 6

    sql = """
        SELECT 
            path_hops,
            city_path,
            city_names,
            route_ids,
            route_names,
            total_distance
        FROM find_trade_paths(%s, %s, %s);
    """
    result = execute_query(sql, (from_city_id, to_city_id, hops))

    enriched_paths = []
    for path in result['data']:
        city_ids = path['city_path']
        route_ids = path['route_ids']

        city_details_sql = """
            SELECT 
                c.city_id,
                c.ancient_name AS classical_name,
                c.modern_name,
                c.latitude,
                c.longitude,
                p.port_type,
                r.region_name,
                c.present_day_state,
                COALESCE(
                    (SELECT k.kingdom_name FROM kingdoms k WHERE k.capital_city_id = c.city_id OR k.region_id = c.region_id LIMIT 1),
                    'Regional Chieftaincy'
                ) AS ruling_kingdoms,
                COALESCE(
                    (SELECT string_agg(curr.coin_name || ' (' || curr.metal || ')', '; ')
                     FROM currencies curr
                     JOIN kingdoms k ON curr.issuing_kingdom_id = k.kingdom_id
                     WHERE k.region_id = c.region_id), 'Regional Coinage Standard'
                ) AS circulating_currencies
            FROM cities c
            JOIN regions r ON c.region_id = r.region_id
            LEFT JOIN ports p ON c.city_id = p.city_id
            WHERE c.city_id = ANY(%s);
        """
        c_res = execute_query(city_details_sql, (city_ids,))
        city_dict = {c['city_id']: c for c in c_res['data']}
        ordered_cities = [city_dict.get(cid) for cid in city_ids if cid in city_dict]

        comm_sql = """
            SELECT DISTINCT comm.commodity_name, comm.category, rcom.trade_direction, tr.route_name
            FROM route_commodity rcom
            JOIN commodities comm ON rcom.commodity_id = comm.commodity_id
            JOIN trade_routes tr ON rcom.route_id = tr.route_id
            WHERE rcom.route_id = ANY(%s);
        """
        comm_res = execute_query(comm_sql, (route_ids,))

        enriched_paths.append({
            "path_hops": path['path_hops'],
            "city_ids": path['city_path'],
            "city_names": path['city_names'],
            "route_ids": path['route_ids'],
            "route_names": path['route_names'],
            "total_distance_km": float(path['total_distance']),
            "ordered_stops": ordered_cities,
            "commodities": comm_res['data']
        })

    return jsonify({
        "paths": enriched_paths,
        "count": len(enriched_paths),
        "sql_meta": result['sql_meta']
    })
