-- ============================================================================
-- BharatPath – Ancient Indian Routes, Trade and Geographical Heritage
-- File: 04_analytical_queries.sql
-- Description: 15 Viva-Ready Analytical DQL Queries for 13-Table Schema
-- Features: Multi-Table Joins, Nested Subqueries, Correlated EXISTS,
--           GROUP BY/HAVING, Window Functions, Set Operations, JSONB, and CTE
-- ============================================================================

-- ============================================================================
-- QUERY 1
-- @name: Comprehensive Route Trade Matrix
-- @category: Multi-Table Joins (Inner)
-- @description: Connects routes, ordered cities, region settings, traded commodities,
--               and source citations into an end-to-end commercial trade matrix.
-- ============================================================================
SELECT 
    tr.route_id,
    tr.route_name,
    tr.route_type,
    rc.stop_sequence,
    c.ancient_name AS city_ancient,
    c.modern_name AS city_modern,
    r.region_name,
    comm.commodity_name AS traded_good,
    rcomm.trade_direction,
    s.title AS primary_source
FROM trade_routes tr
JOIN route_city rc ON tr.route_id = rc.route_id
JOIN cities c ON rc.city_id = c.city_id
JOIN regions r ON c.region_id = r.region_id
LEFT JOIN route_commodity rcomm ON tr.route_id = rcomm.route_id
LEFT JOIN commodities comm ON rcomm.commodity_id = comm.commodity_id
LEFT JOIN sources s ON tr.source_id = s.source_id
ORDER BY tr.route_id, rc.stop_sequence, comm.commodity_name;


-- ============================================================================
-- QUERY 2
-- @name: Comprehensive Port & Coinage Endowment Matrix
-- @category: Multi-Table Joins (Outer)
-- @description: Lists cities alongside their port status and all currencies issued by
--               kingdoms situated within the same geographic region.
-- ============================================================================
SELECT 
    c.city_id,
    c.ancient_name,
    c.modern_name,
    r.region_name,
    COALESCE(p.port_type, 'Inland Hub') AS maritime_facility,
    p.coast,
    k.kingdom_name AS regional_kingdom,
    curr.coin_name,
    curr.metal,
    curr.start_year || ' to ' || curr.end_year AS circulation_era
FROM cities c
JOIN regions r ON c.region_id = r.region_id
LEFT JOIN ports p ON c.city_id = p.city_id
LEFT JOIN kingdoms k ON r.region_id = k.region_id
LEFT JOIN currencies curr ON k.kingdom_id = curr.issuing_kingdom_id
ORDER BY c.city_id, curr.metal;


-- ============================================================================
-- QUERY 3
-- @name: Traveller Chronicles & Cross-Dynasty Waypoints
-- @category: Three-Way Joins
-- @description: Reconstructs each historical traveller's journey connecting their
--               visited cities, kingdoms encountered, and chronicle titles.
-- ============================================================================
SELECT 
    tv.traveller_id,
    tv.traveller_name,
    tv.homeland,
    tv.arrival_year,
    tv.departure_year,
    c.ancient_name AS main_city_visited,
    c.modern_name AS modern_location,
    k.kingdom_name AS kingdom_visited,
    tv.account_title,
    tv.key_observation,
    s.title AS source_citation
FROM travellers tv
LEFT JOIN cities c ON tv.main_city_visited_id = c.city_id
LEFT JOIN kingdoms k ON tv.kingdom_visited_id = k.kingdom_id
LEFT JOIN sources s ON tv.source_id = s.source_id
ORDER BY tv.arrival_year_num ASC, tv.traveller_name;


-- ============================================================================
-- QUERY 4
-- @name: Cities Trading in High-Value Luxury Commodities
-- @category: Nested Subqueries (IN clause)
-- @description: Identifies ancient cities situated on trade routes handling spices,
--               precious metals, or minerals & gems.
-- ============================================================================
SELECT 
    c.city_id,
    c.ancient_name,
    c.modern_name,
    c.present_day_state,
    c.historical_significance
FROM cities c
WHERE c.city_id IN (
    SELECT rc.city_id
    FROM route_city rc
    WHERE rc.route_id IN (
        SELECT rcomm.route_id
        FROM route_commodity rcomm
        JOIN commodities comm ON rcomm.commodity_id = comm.commodity_id
        WHERE comm.category IN ('Spice', 'Precious metal', 'Mineral / stone', 'Textile')
    )
)
ORDER BY c.ancient_name;


-- ============================================================================
-- QUERY 5
-- @name: Imperial Dynasties Controlling Maritime Gateways
-- @category: Correlated Subqueries (EXISTS)
-- @description: Finds kingdoms that governed geographic regions endowed with
--               at least one verified maritime or estuarine port.
-- ============================================================================
SELECT 
    k.kingdom_id,
    k.kingdom_name,
    k.polity_type,
    k.start_year || ' to ' || k.end_year AS ruling_era,
    r.region_name
FROM kingdoms k
JOIN regions r ON k.region_id = r.region_id
WHERE EXISTS (
    SELECT 1 
    FROM cities c
    JOIN ports p ON c.city_id = p.city_id
    WHERE c.region_id = k.region_id
)
ORDER BY k.start_year_num ASC;


-- ============================================================================
-- QUERY 6
-- @name: Strategic Cities with Route Density Exceeding Average
-- @category: Scalar Subquery in SELECT / WHERE
-- @description: Compares each city's route memberships against the average route
--               connectivity across the subcontinental network.
-- ============================================================================
SELECT 
    c.city_id,
    c.ancient_name,
    c.modern_name,
    COUNT(rc.route_id) AS routes_served_count,
    ROUND((SELECT AVG(route_cnt) 
           FROM (SELECT COUNT(route_id) AS route_cnt 
                 FROM route_city 
                 GROUP BY city_id) sub), 2) AS national_avg_routes
FROM cities c
JOIN route_city rc ON c.city_id = rc.city_id
GROUP BY c.city_id, c.ancient_name, c.modern_name
HAVING COUNT(rc.route_id) >= (
    SELECT AVG(route_cnt) 
    FROM (SELECT COUNT(route_id) AS route_cnt 
          FROM route_city 
          GROUP BY city_id) sub
)
ORDER BY routes_served_count DESC, c.ancient_name;


-- ============================================================================
-- QUERY 7
-- @name: Top Ancient Trade Hubs by Commodity Diversity
-- @category: GROUP BY Aggregations
-- @description: Ranks ancient cities by the distinct number of commodities flowing
--               through all routes connecting that city.
-- ============================================================================
SELECT 
    c.city_id,
    c.ancient_name,
    c.modern_name,
    r.region_name,
    COUNT(DISTINCT rcomm.commodity_id) AS distinct_commodities_count,
    STRING_AGG(DISTINCT comm.commodity_name, ', ') AS sample_commodities
FROM cities c
JOIN regions r ON c.region_id = r.region_id
JOIN route_city rc ON c.city_id = rc.city_id
JOIN route_commodity rcomm ON rc.route_id = rcomm.route_id
JOIN commodities comm ON rcomm.commodity_id = comm.commodity_id
GROUP BY c.city_id, c.ancient_name, c.modern_name, r.region_name
ORDER BY distinct_commodities_count DESC, c.ancient_name;


-- ============================================================================
-- QUERY 8
-- @name: Major Imperial Dynasties Minting Multi-Metal Coinage
-- @category: GROUP BY with HAVING
-- @description: Filters for kingdoms that minted multiple coinages across different
--               metals (Gold, Silver, Copper, Lead, etc.).
-- ============================================================================
SELECT 
    k.kingdom_name,
    k.polity_type,
    COUNT(curr.currency_id) AS total_currencies_minted,
    STRING_AGG(DISTINCT curr.metal, ', ') AS metals_minted,
    STRING_AGG(DISTINCT curr.coin_name, '; ') AS coinage_titles
FROM kingdoms k
JOIN currencies curr ON k.kingdom_id = curr.issuing_kingdom_id
GROUP BY k.kingdom_id, k.kingdom_name, k.polity_type
HAVING COUNT(curr.currency_id) >= 1
ORDER BY total_currencies_minted DESC, k.kingdom_name;


-- ============================================================================
-- QUERY 9
-- @name: Corridor Modality Breakdown (Land vs Maritime vs Riverine)
-- @category: Conditional Aggregations (FILTER / CASE)
-- @description: Compares Land, Maritime, and Riverine corridors across total stops,
--               unique commodities carried, and era duration.
-- ============================================================================
SELECT 
    tr.route_type,
    COUNT(DISTINCT tr.route_id) AS total_corridors,
    COUNT(DISTINCT rc.city_id) AS total_cities_served,
    COUNT(DISTINCT rcomm.commodity_id) AS total_commodities_carried,
    ROUND(AVG(COALESCE(tr.end_year_num, 1200) - COALESCE(tr.start_year_num, -600)), 1) AS avg_corridor_lifespan_years
FROM trade_routes tr
LEFT JOIN route_city rc ON tr.route_id = rc.route_id
LEFT JOIN route_commodity rcomm ON tr.route_id = rcomm.route_id
GROUP BY tr.route_type
ORDER BY total_corridors DESC;


-- ============================================================================
-- QUERY 10
-- @name: Route Stop Sequence & Waypoint Ranking
-- @category: Window Functions (RANK)
-- @description: Ranks waypoints along each trade corridor by stop sequence,
--               identifying terminal hubs versus intermediate halts.
-- ============================================================================
SELECT 
    tr.route_name,
    rc.stop_sequence,
    rc.stop_role,
    c.ancient_name,
    c.modern_name,
    RANK() OVER (
        PARTITION BY tr.route_id 
        ORDER BY rc.stop_sequence ASC
    ) AS forward_rank,
    RANK() OVER (
        PARTITION BY tr.route_id 
        ORDER BY rc.stop_sequence DESC
    ) AS reverse_rank
FROM trade_routes tr
JOIN route_city rc ON tr.route_id = rc.route_id
JOIN cities c ON rc.city_id = c.city_id
ORDER BY tr.route_name, rc.stop_sequence;


-- ============================================================================
-- QUERY 11
-- @name: Ancient Currencies Ranked by Duration of Circulation
-- @category: Window Functions (DENSE_RANK)
-- @description: Calculates lifespan and ranks minted coinages by longevity within
--               their metal classification.
-- ============================================================================
SELECT 
    curr.coin_name,
    curr.metal,
    k.kingdom_name,
    curr.start_year,
    curr.end_year,
    (curr.end_year_num - curr.start_year_num) AS circulation_years,
    DENSE_RANK() OVER (
        PARTITION BY curr.metal 
        ORDER BY (curr.end_year_num - curr.start_year_num) DESC
    ) AS longevity_rank_in_metal
FROM currencies curr
JOIN kingdoms k ON curr.issuing_kingdom_id = k.kingdom_id
WHERE curr.start_year_num IS NOT NULL AND curr.end_year_num IS NOT NULL
ORDER BY curr.metal, longevity_rank_in_metal;


-- ============================================================================
-- QUERY 12
-- @name: Unified Master Commercial Registry of Ancient Urban Centers
-- @category: Set Operations (UNION)
-- @description: Combines maritime ports and inland caravan nodes into a single
--               master registry with categorized trade roles.
-- ============================================================================
SELECT 
    c.city_id,
    c.ancient_name,
    c.modern_name,
    'Maritime / Estuarine Port' AS settlement_category,
    p.coast AS geographic_attribute
FROM cities c
JOIN ports p ON c.city_id = p.city_id

UNION

SELECT 
    c.city_id,
    c.ancient_name,
    c.modern_name,
    'Inland Trading Metropolis' AS settlement_category,
    r.region_name AS geographic_attribute
FROM cities c
JOIN regions r ON c.region_id = r.region_id
WHERE c.city_id NOT IN (SELECT city_id FROM ports WHERE city_id IS NOT NULL)
ORDER BY settlement_category, ancient_name;


-- ============================================================================
-- QUERY 13
-- @name: Strategic Junction Cities Serving Both Land and Maritime Routes
-- @category: Set Operations (INTERSECT)
-- @description: Discovers trans-shipment nodes that served as waypoints on both
--               Land highways and Maritime sea lanes.
-- ============================================================================
SELECT c.city_id, c.ancient_name, c.modern_name
FROM cities c
JOIN route_city rc ON c.city_id = rc.city_id
JOIN trade_routes tr ON rc.route_id = tr.route_id
WHERE tr.route_type = 'Land'

INTERSECT

SELECT c.city_id, c.ancient_name, c.modern_name
FROM cities c
JOIN route_city rc ON c.city_id = rc.city_id
JOIN trade_routes tr ON rc.route_id = tr.route_id
WHERE tr.route_type IN ('Maritime', 'Riverine')

ORDER BY ancient_name;


-- ============================================================================
-- QUERY 14
-- @name: Hybrid JSONB Document Querying: Excavation & Epigraphic Metadata
-- @category: JSONB Hybrid Document Layer
-- @description: Queries semi-structured archaeological attributes, excavation notes,
--               and epigraphic records inside PostgreSQL JSONB document columns.
-- ============================================================================
SELECT 
    c.city_id,
    c.ancient_name,
    c.modern_name,
    c.present_day_state,
    c.artefact_metadata->>'unesco_site_id' AS unesco_id,
    c.artefact_metadata->>'excavator' AS archaeological_excavator,
    c.artefact_metadata->>'river_system' AS river_system
FROM cities c
WHERE c.artefact_metadata->>'unesco_site_id' IS NOT NULL
   OR c.artefact_metadata->>'excavator' IS NOT NULL
   OR c.artefact_metadata IS NOT NULL
ORDER BY c.ancient_name;


-- ============================================================================
-- QUERY 15
-- @name: Multi-Hop Trade Route Pathfinder Execution (Harappa to Muziris)
-- @category: Recursive CTE Function Invocation
-- @description: Executes the recursive SQL function find_trade_paths() across
--               connected corridors from Harappa (CT001) to Pattanam/Muziris (CT023).
-- ============================================================================
SELECT 
    path_hops,
    ARRAY_TO_STRING(city_names, ' ➔ ') AS routing_corridor,
    ARRAY_TO_STRING(route_names, ' | ') AS routes_traversed,
    total_distance AS total_route_km
FROM find_trade_paths('CT001', 'CT023', 6)
ORDER BY path_hops ASC, total_distance ASC;
