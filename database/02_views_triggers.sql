-- ============================================================================
-- BharatPath – Ancient Indian Routes, Trade and Geographical Heritage
-- File: 02_views_triggers.sql
-- Description: Audit Triggers, Stored Procedures, Analytical Views, and
--              Recursive CTE Function aligned with the 13-table Excel Schema.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Real-Time Audit Log Table & Trigger Function
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS audit_log CASCADE;

CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id VARCHAR(50),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    old_data JSONB,
    new_data JSONB
);

CREATE OR REPLACE FUNCTION fn_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    v_record_id VARCHAR(50);
BEGIN
    IF (TG_OP = 'DELETE') THEN
        IF TG_TABLE_NAME = 'kingdoms' THEN v_record_id := OLD.kingdom_id;
        ELSIF TG_TABLE_NAME = 'cities' THEN v_record_id := OLD.city_id;
        ELSIF TG_TABLE_NAME = 'trade_routes' THEN v_record_id := OLD.route_id;
        ELSIF TG_TABLE_NAME = 'currencies' THEN v_record_id := OLD.currency_id;
        ELSE v_record_id := 'UNKNOWN';
        END IF;

        INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, v_record_id, to_jsonb(OLD), NULL);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        IF TG_TABLE_NAME = 'kingdoms' THEN v_record_id := NEW.kingdom_id;
        ELSIF TG_TABLE_NAME = 'cities' THEN v_record_id := NEW.city_id;
        ELSIF TG_TABLE_NAME = 'trade_routes' THEN v_record_id := NEW.route_id;
        ELSIF TG_TABLE_NAME = 'currencies' THEN v_record_id := NEW.currency_id;
        ELSE v_record_id := 'UNKNOWN';
        END IF;

        INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, v_record_id, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        IF TG_TABLE_NAME = 'kingdoms' THEN v_record_id := NEW.kingdom_id;
        ELSIF TG_TABLE_NAME = 'cities' THEN v_record_id := NEW.city_id;
        ELSIF TG_TABLE_NAME = 'trade_routes' THEN v_record_id := NEW.route_id;
        ELSIF TG_TABLE_NAME = 'currencies' THEN v_record_id := NEW.currency_id;
        ELSE v_record_id := 'UNKNOWN';
        END IF;

        INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, v_record_id, NULL, to_jsonb(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach Audit Triggers to Core Tables
DROP TRIGGER IF EXISTS trg_audit_kingdoms ON kingdoms;
CREATE TRIGGER trg_audit_kingdoms
AFTER INSERT OR UPDATE OR DELETE ON kingdoms
FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

DROP TRIGGER IF EXISTS trg_audit_cities ON cities;
CREATE TRIGGER trg_audit_cities
AFTER INSERT OR UPDATE OR DELETE ON cities
FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

DROP TRIGGER IF EXISTS trg_audit_trade_routes ON trade_routes;
CREATE TRIGGER trg_audit_trade_routes
AFTER INSERT OR UPDATE OR DELETE ON trade_routes
FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

DROP TRIGGER IF EXISTS trg_audit_currencies ON currencies;
CREATE TRIGGER trg_audit_currencies
AFTER INSERT OR UPDATE OR DELETE ON currencies
FOR EACH ROW EXECUTE FUNCTION fn_audit_log();

-- ----------------------------------------------------------------------------
-- 2. Stored Procedure: add_validated_route_stop
-- ----------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE add_validated_route_stop(
    p_route_id VARCHAR(6),
    p_city_id VARCHAR(6),
    p_stop_sequence INT,
    p_stop_role VARCHAR(20) DEFAULT 'Intermediate',
    p_note VARCHAR(120) DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_route_exists BOOLEAN;
    v_city_exists BOOLEAN;
BEGIN
    SELECT EXISTS (SELECT 1 FROM trade_routes WHERE route_id = p_route_id) INTO v_route_exists;
    IF NOT v_route_exists THEN
        RAISE EXCEPTION 'Route ID % does not exist in trade_routes', p_route_id USING ERRCODE = '23503';
    END IF;

    SELECT EXISTS (SELECT 1 FROM cities WHERE city_id = p_city_id) INTO v_city_exists;
    IF NOT v_city_exists THEN
        RAISE EXCEPTION 'City ID % does not exist in cities', p_city_id USING ERRCODE = '23503';
    END IF;

    IF p_stop_sequence <= 0 THEN
        RAISE EXCEPTION 'Stop sequence must be a positive integer greater than 0' USING ERRCODE = '23514';
    END IF;

    IF EXISTS (SELECT 1 FROM route_city WHERE route_id = p_route_id AND city_id = p_city_id) THEN
        RAISE EXCEPTION 'City % already exists on Route %', p_city_id, p_route_id USING ERRCODE = '23505';
    END IF;

    INSERT INTO route_city (route_id, city_id, stop_sequence, stop_role, note)
    VALUES (p_route_id, p_city_id, p_stop_sequence, p_stop_role, p_note);

    RAISE NOTICE 'Added stop % (City %, Route %)', p_stop_sequence, p_city_id, p_route_id;
END;
$$;

-- ----------------------------------------------------------------------------
-- 3. Analytical Views
-- ----------------------------------------------------------------------------

-- View A: Summary of Route Networks with terminal cities and commodity counts
CREATE OR REPLACE VIEW vw_route_network_summary AS
SELECT 
    tr.route_id,
    tr.route_name,
    tr.route_type,
    tr.start_year,
    tr.end_year,
    tr.start_year_num,
    tr.end_year_num,
    COUNT(DISTINCT rc.city_id) AS total_stops,
    c_start.ancient_name AS start_city_name,
    c_end.ancient_name AS end_city_name,
    COUNT(DISTINCT rcom.commodity_id) AS commodities_count,
    STRING_AGG(DISTINCT comm.commodity_name, ', ') AS sample_commodities
FROM trade_routes tr
LEFT JOIN cities c_start ON tr.start_city_id = c_start.city_id
LEFT JOIN cities c_end ON tr.end_city_id = c_end.city_id
LEFT JOIN route_city rc ON tr.route_id = rc.route_id
LEFT JOIN route_commodity rcom ON tr.route_id = rcom.route_id
LEFT JOIN commodities comm ON rcom.commodity_id = comm.commodity_id
GROUP BY tr.route_id, tr.route_name, tr.route_type, tr.start_year, tr.end_year, 
         tr.start_year_num, tr.end_year_num, c_start.ancient_name, c_end.ancient_name;

-- View B: Coinage by Kingdom / Dynasty
CREATE OR REPLACE VIEW vw_coinage_by_kingdom AS
SELECT 
    k.kingdom_id,
    k.kingdom_name,
    k.polity_type,
    COUNT(c.currency_id) AS total_coin_types,
    STRING_AGG(DISTINCT c.metal, ', ') AS metals_minted,
    STRING_AGG(DISTINCT c.coin_name, '; ') AS sample_coins,
    STRING_AGG(DISTINCT c.start_year || ' to ' || c.end_year, '; ') AS circulation_eras
FROM kingdoms k
LEFT JOIN currencies c ON k.kingdom_id = c.issuing_kingdom_id
GROUP BY k.kingdom_id, k.kingdom_name, k.polity_type;

-- View C: Source / Pramana Linked Heritage
CREATE OR REPLACE VIEW vw_source_linked_heritage AS
SELECT 
    s.source_id,
    s.title,
    s.author_or_editor,
    s.source_type,
    COUNT(DISTINCT c.city_id) AS cited_cities,
    COUNT(DISTINCT k.kingdom_id) AS cited_kingdoms,
    COUNT(DISTINCT tr.route_id) AS cited_routes,
    COUNT(DISTINCT tv.traveller_id) AS cited_travellers
FROM sources s
LEFT JOIN cities c ON s.source_id = c.source_id
LEFT JOIN kingdoms k ON s.source_id = k.source_id
LEFT JOIN trade_routes tr ON s.source_id = tr.source_id
LEFT JOIN travellers tv ON s.source_id = tv.source_id
GROUP BY s.source_id, s.title, s.author_or_editor, s.source_type;

-- ----------------------------------------------------------------------------
-- 4. Recursive CTE Function: find_trade_paths
-- Computes multi-hop connected trade corridors between two cities
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION find_trade_paths(
    p_start_city_id VARCHAR(6),
    p_end_city_id VARCHAR(6),
    p_max_hops INT DEFAULT 6
)
RETURNS TABLE (
    path_hops INT,
    city_path VARCHAR(6)[],
    city_names TEXT[],
    route_ids VARCHAR(6)[],
    route_names TEXT[],
    total_distance NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE trade_corridor AS (
        -- Anchor Member: direct single segment between two cities sharing any route
        SELECT 
            1 AS hops,
            ARRAY[rc1.city_id, rc2.city_id] AS c_path,
            ARRAY[c1.ancient_name::text, c2.ancient_name::text] AS c_names,
            ARRAY[tr.route_id] AS r_ids,
            ARRAY[tr.route_name::text] AS r_names,
            ABS(rc2.stop_sequence - rc1.stop_sequence)::numeric * 150.00 AS dist_km,
            rc2.city_id AS current_city
        FROM route_city rc1
        JOIN route_city rc2 ON rc1.route_id = rc2.route_id AND rc1.city_id <> rc2.city_id
        JOIN trade_routes tr ON rc1.route_id = tr.route_id
        JOIN cities c1 ON rc1.city_id = c1.city_id
        JOIN cities c2 ON rc2.city_id = c2.city_id
        WHERE rc1.city_id = p_start_city_id

        UNION ALL

        -- Recursive Member: transition from current_city to next adjacent city on any route
        SELECT 
            tc.hops + 1,
            tc.c_path || rc_next.city_id,
            tc.c_names || c_next.ancient_name::text,
            tc.r_ids || tr_next.route_id,
            tc.r_names || tr_next.route_name::text,
            tc.dist_km + (ABS(rc_next.stop_sequence - rc_curr.stop_sequence)::numeric * 150.00),
            rc_next.city_id
        FROM trade_corridor tc
        JOIN route_city rc_curr ON rc_curr.city_id = tc.current_city
        JOIN route_city rc_next ON rc_curr.route_id = rc_next.route_id AND rc_curr.city_id <> rc_next.city_id
        JOIN trade_routes tr_next ON rc_next.route_id = tr_next.route_id
        JOIN cities c_next ON rc_next.city_id = c_next.city_id
        WHERE tc.hops < p_max_hops
          AND NOT (rc_next.city_id = ANY(tc.c_path))
          AND tc.current_city <> p_end_city_id
    )
    SELECT 
        hops AS path_hops,
        c_path AS city_path,
        c_names AS city_names,
        r_ids AS route_ids,
        r_names AS route_names,
        ROUND(dist_km, 2) AS total_distance
    FROM trade_corridor
    WHERE current_city = p_end_city_id
    ORDER BY hops ASC, total_distance ASC;
END;
$$ LANGUAGE plpgsql;
