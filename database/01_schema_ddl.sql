-- ============================================================================
-- BharatPath – Ancient Indian Routes, Trade and Geographical Heritage
-- File: 01_schema_ddl.sql
-- Description: Production PostgreSQL 3NF Relational Schema (13 Tables)
--              Aligned with data/BharatPath_Database_Final.xlsx (531 Rows)
-- Key Features: VARCHAR(6) natural keys, strict FKs (CASCADE/RESTRICT),
--               companion numeric year columns for chronological sorting,
--               and JSONB artefact_metadata hybrid NoSQL document layer.
-- ============================================================================

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS cultural_exchanges CASCADE;
DROP TABLE IF EXISTS travellers CASCADE;
DROP TABLE IF EXISTS currencies CASCADE;
DROP TABLE IF EXISTS route_commodity CASCADE;
DROP TABLE IF EXISTS commodities CASCADE;
DROP TABLE IF EXISTS route_city CASCADE;
DROP TABLE IF EXISTS trade_routes CASCADE;
DROP TABLE IF EXISTS ports CASCADE;
DROP TABLE IF EXISTS kingdoms CASCADE;
DROP TABLE IF EXISTS cities CASCADE;
DROP TABLE IF EXISTS historical_periods CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS sources CASCADE;

-- ----------------------------------------------------------------------------
-- 1. Sources (Primary Literature, Epigraphy & Reference Corpora)
-- ----------------------------------------------------------------------------
CREATE TABLE sources (
    source_id VARCHAR(6) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author_or_editor VARCHAR(120) NOT NULL,
    source_type VARCHAR(60) NOT NULL,
    publisher VARCHAR(120),
    publication_year VARCHAR(12),
    url VARCHAR(200),
    note VARCHAR(300),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Regions (Geographical Context & Terran Basins)
-- ----------------------------------------------------------------------------
CREATE TABLE regions (
    region_id VARCHAR(6) PRIMARY KEY,
    region_name VARCHAR(80) NOT NULL UNIQUE,
    historical_names VARCHAR(120),
    present_day_area VARCHAR(120) NOT NULL,
    present_day_country VARCHAR(60) NOT NULL,
    geographic_setting VARCHAR(80),
    historical_significance VARCHAR(300) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. Historical Periods (Standardized Chronological Epochs)
-- ----------------------------------------------------------------------------
CREATE TABLE historical_periods (
    period_id VARCHAR(6) PRIMARY KEY,
    period_name VARCHAR(100) NOT NULL UNIQUE,
    era VARCHAR(20) NOT NULL,
    start_year VARCHAR(10) NOT NULL,
    end_year VARCHAR(10) NOT NULL,
    start_year_num SMALLINT,         -- Negative for BC, positive for AD
    end_year_num SMALLINT,           -- Negative for BC, positive for AD
    dating_note VARCHAR(80) NOT NULL,
    defining_features VARCHAR(300) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_period_era CHECK (era IN ('Ancient', 'Early Medieval', 'Medieval'))
);

-- ----------------------------------------------------------------------------
-- 4. Cities (Urban Centers, Trade Emporiums & Pilgrimage Waypoints)
-- ----------------------------------------------------------------------------
CREATE TABLE cities (
    city_id VARCHAR(6) PRIMARY KEY,
    ancient_name VARCHAR(80) NOT NULL,
    modern_name VARCHAR(80) NOT NULL,
    present_day_state VARCHAR(80) NOT NULL,
    present_day_country VARCHAR(40) NOT NULL,
    region_id VARCHAR(6) NOT NULL REFERENCES regions(region_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    river_or_coast VARCHAR(80),
    city_type VARCHAR(60) NOT NULL,
    period_id VARCHAR(6) NOT NULL REFERENCES historical_periods(period_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    historical_significance VARCHAR(300) NOT NULL,
    latitude DECIMAL(8,4) NOT NULL CHECK (latitude BETWEEN -90.0000 AND 90.0000),
    longitude DECIMAL(8,4) NOT NULL CHECK (longitude BETWEEN -180.0000 AND 180.0000),
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    artefact_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. Kingdoms (Dynasties, Empires & Polities)
-- ----------------------------------------------------------------------------
CREATE TABLE kingdoms (
    kingdom_id VARCHAR(6) PRIMARY KEY,
    kingdom_name VARCHAR(80) NOT NULL UNIQUE,
    polity_type VARCHAR(30) NOT NULL,
    capital_city_id VARCHAR(6) REFERENCES cities(city_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    region_id VARCHAR(6) NOT NULL REFERENCES regions(region_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    period_id VARCHAR(6) NOT NULL REFERENCES historical_periods(period_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    start_year VARCHAR(10) NOT NULL,
    end_year VARCHAR(10) NOT NULL,
    start_year_num SMALLINT,         -- Negative for BC, positive for AD
    end_year_num SMALLINT,           -- Negative for BC, positive for AD
    dating_note VARCHAR(80) NOT NULL,
    founder VARCHAR(80),
    notable_ruler VARCHAR(80),
    historical_significance VARCHAR(300) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    artefact_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 6. Ports (Maritime, Riverine & Estuarine Gateways)
-- ----------------------------------------------------------------------------
CREATE TABLE ports (
    port_id VARCHAR(6) PRIMARY KEY,
    port_name VARCHAR(80) NOT NULL,
    present_day_location VARCHAR(120) NOT NULL,
    city_id VARCHAR(6) REFERENCES cities(city_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    coast VARCHAR(60) NOT NULL,
    port_type VARCHAR(80) NOT NULL,
    period_id VARCHAR(6) NOT NULL REFERENCES historical_periods(period_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    active_period_note VARCHAR(60) NOT NULL,
    overseas_connections VARCHAR(120),
    trade_note VARCHAR(300) NOT NULL,
    latitude DECIMAL(8,4) NOT NULL CHECK (latitude BETWEEN -90.0000 AND 90.0000),
    longitude DECIMAL(8,4) NOT NULL CHECK (longitude BETWEEN -180.0000 AND 180.0000),
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 7. Trade Routes (Trans-Continental Highways & Sea Lanes)
-- ----------------------------------------------------------------------------
CREATE TABLE trade_routes (
    route_id VARCHAR(6) PRIMARY KEY,
    route_name VARCHAR(100) NOT NULL UNIQUE,
    route_type VARCHAR(40) NOT NULL,
    start_city_id VARCHAR(6) NOT NULL REFERENCES cities(city_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    end_city_id VARCHAR(6) NOT NULL REFERENCES cities(city_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    period_id VARCHAR(6) NOT NULL REFERENCES historical_periods(period_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    start_year VARCHAR(10) NOT NULL,
    end_year VARCHAR(10) NOT NULL,
    start_year_num SMALLINT,         -- Negative for BC, positive for AD
    end_year_num SMALLINT,           -- Negative for BC, positive for AD
    dating_note VARCHAR(80) NOT NULL,
    description VARCHAR(300) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    artefact_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 8. Route City (Junction: Ordered Waypoints along Routes)
-- ----------------------------------------------------------------------------
CREATE TABLE route_city (
    route_id VARCHAR(6) NOT NULL REFERENCES trade_routes(route_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    city_id VARCHAR(6) NOT NULL REFERENCES cities(city_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    stop_sequence SMALLINT NOT NULL CHECK (stop_sequence > 0),
    stop_role VARCHAR(20) NOT NULL,
    note VARCHAR(120),
    PRIMARY KEY (route_id, city_id)
);

-- ----------------------------------------------------------------------------
-- 9. Commodities (Spices, Textiles, Gems, Metals & Bulk Cargo)
-- ----------------------------------------------------------------------------
CREATE TABLE commodities (
    commodity_id VARCHAR(6) PRIMARY KEY,
    commodity_name VARCHAR(80) NOT NULL UNIQUE,
    category VARCHAR(40) NOT NULL,
    primary_source_area VARCHAR(120) NOT NULL,
    trade_direction VARCHAR(20) NOT NULL,
    attested_in VARCHAR(120) NOT NULL,
    description VARCHAR(300) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 10. Route Commodity (Junction: Commodities Flowing on Corridors)
-- ----------------------------------------------------------------------------
CREATE TABLE route_commodity (
    route_id VARCHAR(6) NOT NULL REFERENCES trade_routes(route_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    commodity_id VARCHAR(6) NOT NULL REFERENCES commodities(commodity_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    trade_direction VARCHAR(20) NOT NULL,
    evidence_note VARCHAR(160) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    PRIMARY KEY (route_id, commodity_id)
);

-- ----------------------------------------------------------------------------
-- 11. Currencies (Coinage, Weights & Numismatic Standards)
-- ----------------------------------------------------------------------------
CREATE TABLE currencies (
    currency_id VARCHAR(6) PRIMARY KEY,
    coin_name VARCHAR(80) NOT NULL UNIQUE,
    metal VARCHAR(40) NOT NULL,
    issuing_kingdom_id VARCHAR(6) REFERENCES kingdoms(kingdom_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    issuer_note VARCHAR(120),
    period_id VARCHAR(6) NOT NULL REFERENCES historical_periods(period_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    start_year VARCHAR(10) NOT NULL,
    end_year VARCHAR(10) NOT NULL,
    start_year_num SMALLINT,         -- Negative for BC, positive for AD
    end_year_num SMALLINT,           -- Negative for BC, positive for AD
    dating_note VARCHAR(80) NOT NULL,
    weight_standard VARCHAR(80),
    description VARCHAR(300) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    artefact_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 12. Travellers (Pilgrims, Envoys, Geographers & Accounts)
-- ----------------------------------------------------------------------------
CREATE TABLE travellers (
    traveller_id VARCHAR(6) PRIMARY KEY,
    traveller_name VARCHAR(80) NOT NULL,
    homeland VARCHAR(60) NOT NULL,
    role VARCHAR(60) NOT NULL,
    arrival_year VARCHAR(10) NOT NULL,
    departure_year VARCHAR(10),
    arrival_year_num SMALLINT,       -- Negative for BC, positive for AD
    departure_year_num SMALLINT,     -- Negative for BC, positive for AD
    dating_note VARCHAR(80) NOT NULL,
    period_id VARCHAR(6) NOT NULL REFERENCES historical_periods(period_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    kingdom_visited_id VARCHAR(6) REFERENCES kingdoms(kingdom_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    main_city_visited_id VARCHAR(6) REFERENCES cities(city_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    account_title VARCHAR(120) NOT NULL,
    key_observation VARCHAR(300) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    artefact_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 13. Cultural Exchanges (Diffusions of Thought, Art, Architecture & Scripts)
-- ----------------------------------------------------------------------------
CREATE TABLE cultural_exchanges (
    exchange_id VARCHAR(6) PRIMARY KEY,
    exchange_name VARCHAR(100) NOT NULL,
    exchange_type VARCHAR(40) NOT NULL,
    from_region_id VARCHAR(6) NOT NULL REFERENCES regions(region_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    to_region_id VARCHAR(6) NOT NULL REFERENCES regions(region_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    period_id VARCHAR(6) NOT NULL REFERENCES historical_periods(period_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    start_year VARCHAR(10) NOT NULL,
    end_year VARCHAR(10) NOT NULL,
    start_year_num SMALLINT,         -- Negative for BC, positive for AD
    end_year_num SMALLINT,           -- Negative for BC, positive for AD
    dating_note VARCHAR(80) NOT NULL,
    description VARCHAR(300) NOT NULL,
    evidence_type VARCHAR(60) NOT NULL,
    source_id VARCHAR(6) REFERENCES sources(source_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    artefact_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance & Lookup Indexes
CREATE INDEX idx_cities_coords ON cities(latitude, longitude);
CREATE INDEX idx_cities_region ON cities(region_id);
CREATE INDEX idx_cities_period ON cities(period_id);
CREATE INDEX idx_ports_city ON ports(city_id);
CREATE INDEX idx_ports_coast ON ports(coast);
CREATE INDEX idx_trade_routes_type ON trade_routes(route_type);
CREATE INDEX idx_trade_routes_years ON trade_routes(start_year_num, end_year_num);
CREATE INDEX idx_kingdoms_years ON kingdoms(start_year_num, end_year_num);
CREATE INDEX idx_currencies_kingdom ON currencies(issuing_kingdom_id);
CREATE INDEX idx_currencies_metal ON currencies(metal);
CREATE INDEX idx_route_city_city ON route_city(city_id);
CREATE INDEX idx_route_commodity_comm ON route_commodity(commodity_id);
CREATE INDEX idx_travellers_years ON travellers(arrival_year_num);
