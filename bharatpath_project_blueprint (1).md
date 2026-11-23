# BharatPath – Ancient Indian Routes, Trade and Geographical Heritage

> **Course:** Database Management Systems (CD252IA)
>
> **Theme:** Indian Knowledge Systems (IKS) & Historical Trade Networks
>
> **Stack:** PostgreSQL · Python (Flask, pandas, psycopg2) · Tailwind CSS · Leaflet.js · Vis.js

---

## 1. Decoupled System Architecture

**BharatPath** is split into two independent tracks so development and testing can proceed immediately without waiting for the final Excel dataset:

* **Track A — Core Platform (Build & Run Now):** PostgreSQL 3NF schema (13 tables + `JSONB` hybrid document layer), triggers, views, a lightweight placeholder dev seed (`03_dev_seed_sample.sql`), a 15-query Viva SQL pack, Flask REST APIs, NLP modules, and the full IKS-themed web UI. The web application reads *exclusively* from PostgreSQL.
* **Track B — Excel-to-PostgreSQL ETL Module (Plug In Later):** A standalone CLI utility with a JSON mapping config (`column_mapping.json`). When your Excel workbook is ready, this module inspects, validates, transforms, and bulk-loads all 13 sheets (at least 25 records per table) into PostgreSQL, cleanly replacing the dev seed with zero changes to backend or frontend code.

```text
TRACK A: CORE PLATFORM (Build & Test Now)
┌─────────────────────────────────────────────────────────────────────────┐
│ [ 03_dev_seed_sample.sql ] (Temporary 4-5 rows/table for UI/API testing)│
│             │                                                           │
│             ▼                                                           │
│ [ PostgreSQL 3NF Database (13 Tables + JSONB Hybrid NoSQL Layer) ]      │
│             │                                                           │
│             ▼  (Flask APIs + Live SQL Drawer + Vāk-to-SQL + Entity NLP) │
│ [ IKS-Themed Web UI (Tailwind CSS + Leaflet.js + Vis.js) ]              │
└─────────────────────────────────────────────────────────────────────────┘
              ▲
              │  (Swap in later via CLI: --replace-dev-seed)
┌─────────────┴───────────────────────────────────────────────────────────┐
│ TRACK B: STANDALONE EXCEL ETL MODULE (Integrate Later)                  │
│ [ Excel Workbook (13 Sheets) ] ──► [ column_mapping.json ]              │
│                                              │                          │
│                                              ▼                          │
│                                [ load_excel_to_postgres.py ]            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete Feature Set

### A. IKS & Cultural Heritage Modules
* **Bharata-Manchitra (Interactive Historical Map):** Plots ancient land routes (*Uttarapatha*, *Dakshinapatha*) and maritime spice routes alongside ancient cities and ports (*Lothal, Muziris, Tamralipti, Bhrigukachchha*) with an **Era/Dynasty Timeline Slider (600 BCE – 1200 CE)**.
* **Ancient-to-Modern Geography Bridge:** Displays classical Sanskrit/Prakrit names alongside modern locations (e.g., *Pataliputra → Patna*, *Ujjayini → Ujjain*, *Kaveripattinam → Poompuhar*).
* **Mudra-Kosha (Ancient Coinage & Currency Explorer):** Filterable catalog of Indian coinage (*Karshapanas*, Gupta gold *Dinars*, Satavahana lead coins, Chola *Kasu*) by metal, dynasty, and era, with obverse/reverse inspection modals and linked trade routes.
* **Yatri-Path (Traveller & Pilgrim Chronicles):** Chronological step-by-step journey timelines for classical travellers, pilgrims, and merchant guilds showing visited stops, ruling kingdoms at the time, and recorded cultural exchanges.
* **Pramana (Primary IKS Source Citations):** Clickable source badges on city, route, coin, and cultural cards linking records to classical texts (*Kautilya's Arthashastra*, *Indica*, *Periplus of the Erythraean Sea*, Ashokan Edicts).

### B. DBMS Viva & Evaluation Highlights
* **Multi-Hop Trade Route Finder (Recursive CTEs):** Computes connected trade paths between any two ancient cities (e.g., *Taxila* to *Muziris*), listing intermediate stops, kingdoms crossed, currency transitions, and traded commodities.
* **Live "Under-the-Hood SQL" Drawer:** Collapsible drawer available across all pages displaying the exact executed PostgreSQL query, execution time (ms), and row count behind every UI interaction.
* **Viva SQL Query Lab (15 Preset Analytical Queries):** Dedicated evaluation tab to run and inspect viva-ready queries (multi-table joins, nested/correlated subqueries, `GROUP BY`/`HAVING`, window functions, set operations, `JSONB` queries, and Recursive CTEs) with live tabular results.
* **3NF Integrity & Trigger Admin Dashboard:** Full CRUD interface across all 13 tables demonstrating live `FOREIGN KEY` and `CHECK` constraint protection, stored procedure execution, and a real-time `audit_log` viewer populated by database triggers.

### C. Hybrid RDBMS + NoSQL Extension
* **Artefact & Manuscript Vault (`JSONB`):** Structured relational facts stay in 13 normalized 3NF PostgreSQL tables as the single source of truth, while semi-structured content (long historical essays, coin obverse/reverse image paths, epigraphic transcripts, and bibliography metadata) is stored in PostgreSQL `JSONB` columns linked directly via primary keys (`route_id`, `city_id`, `kingdom_id`, `currency_id`).

### D. Innovative Experiments (NLP & Network Analytics)
* **Vāk-to-SQL (Natural Language Querying):** Translates plain-English questions (e.g., *"Which ports under the Chola dynasty exported black pepper?"*) into read-only PostgreSQL `SELECT` queries, blocks mutating keywords, displays the SQL, and renders results.
* **Historical Text-to-Entity Extractor:** Allows users to paste a paragraph from a historical passage; detects mentioned ancient cities, ports, kingdoms, routes, and commodities, highlights them inline, and cross-links each matched entity to its live PostgreSQL record.
* **Trade & Cultural Diffusion Network Graph:** Interactive Vis.js hub-and-spoke graph visualizing major ancient trade hubs and how commodities, currencies, scripts, art forms, and philosophical traditions spread across regions.

### E. Visual Design System (IKS Manuscript Theme)

| Element | Color Hex | Purpose |
| :--- | :--- | :--- |
| **Parchment Background** | `#FAF3E0` | Warm manuscript/sandstone canvas |
| **Card Surface** | `#FFFDF7` | Subtle elevated parchment cards |
| **Indigo Ink** | `#1E293B` | High-contrast readable primary typography |
| **Terracotta / Vermilion** | `#B45309` | Primary buttons, active routes, heritage accents |
| **Temple Gold** | `#D97706` | Borders, Pramana badges, timeline markers, coin highlights |

---

## 3. Project Directory Structure

```text
BharatPath/
├── database/                        # [TRACK A] Core PostgreSQL Layer
│   ├── 01_schema_ddl.sql            # 13 normalized (3NF) tables, PK/FK/CHECK constraints, JSONB
│   ├── 02_views_triggers.sql        # Audit triggers, analytical views, stored procedures, Recursive CTE
│   ├── 03_dev_seed_sample.sql       # Lightweight dummy data (4-5 rows/table) to test app without Excel
│   └── 04_analytical_queries.sql    # 15 viva-ready DQL queries (Joins, Nested, Group By, Window, CTE)
│
├── app/                             # [TRACK A] Flask Backend & IKS Frontend (DB-only, Excel-agnostic)
│   ├── __init__.py                  # Flask application factory & Blueprint registration
│   ├── db.py                        # psycopg2 helper + "Under-the-Hood SQL" telemetry logger
│   ├── routes/
│   │   ├── main_routes.py           # Bharata-Manchitra map API, Era filter & Multi-hop Path Finder
│   │   ├── explorer_routes.py       # Mudra-Kosha, Yatri-Path, Pramana Citations & Analytics APIs
│   │   ├── admin_routes.py          # 3NF CRUD, Constraint Demo, Audit Log & Viva Preset Query Runner
│   │   └── nlp_routes.py            # Vāk-to-SQL & Historical Text-to-Entity Extractor endpoints
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── iks_theme.css        # Parchment palette, terracotta/indigo accents & classical fonts
│   │   ├── js/
│   │   │   ├── map_manchitra.js     # Leaflet.js routes, ports, cities, era slider & pathfinder
│   │   │   ├── network_graph.js     # Vis.js commodity & cultural diffusion network graph
│   │   │   ├── nlp_workbench.js     # Vāk-to-SQL UI & inline Historical Text-to-Entity highlighter
│   │   │   └── sql_inspector.js     # Global Under-the-Hood SQL drawer & Pramana citation modal
│   │   └── images/                  # Coinage plates, artefact thumbnails & BharatPath emblems
│   │
│   └── templates/
│       ├── base.html                # Tailwind CSS shell, IKS header, nav tabs, SQL drawer & citation modal
│       ├── index.html               # Bharata-Manchitra map + Route Path Finder
│       ├── mudra_kosha.html         # Ancient coinage catalog with filters & obverse/reverse modal
│       ├── yatri_sangam.html        # Chronological traveller timelines & cultural exchanges
│       ├── analytics.html           # Vis.js diffusion graph + aggregated commodity/cultural charts
│       ├── viva_nlp_lab.html        # 15-Query Viva Runner + Vāk-to-SQL + Text-to-Entity Extractor
│       └── admin_crud.html          # Full 3NF CRUD dashboard, integrity demo & live Audit Log table
│
├── etl/                             # [TRACK B] Standalone Excel Integration (Plug in Later)
│   ├── data/
│   │   └── BharatPath_Master.xlsx   # Place your final 13-sheet Excel workbook here later
│   ├── inspect_excel.py             # Reads Excel sheets/columns & checks compatibility with SQL schema
│   ├── column_mapping.json          # Maps Excel sheet/column names to PostgreSQL tables/columns
│   └── load_excel_to_postgres.py    # Standalone CLI loader (replaces dev seed with real Excel data)
│
├── .env                             # PostgreSQL credentials (DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT)
├── requirements.txt                 # flask, psycopg2-binary, pandas, openpyxl, python-dotenv
└── run.py                           # Application entry point
```

---

## 4. Complete Decoupled Implementation Prompts

Execute **Track A (Prompts A1–A6)** sequentially in your IDE right now to build and test the complete platform without needing the Excel file. Execute **Track B (Prompts B1–B2)** later when your Excel workbook is finalized.

---

### Track A: Core Database, Backend & IKS Web Application (Build Now)

#### Prompt A1: PostgreSQL 3NF Schema, Triggers, Stored Procedures & Hybrid JSONB Layer
> **Prompt:**
> Act as a PostgreSQL database architect. Create `database/01_schema_ddl.sql` and `database/02_views_triggers.sql` for **BharatPath – Ancient Indian Routes, Trade and Geographical Heritage**.
>
> 1. In `01_schema_ddl.sql`, define **13 interconnected tables normalized to Third Normal Form (3NF)** using clean `snake_case` naming:
>    - **Core Entity Tables (9):** `kingdoms`, `ancient_cities` (with `classical_name`, `modern_name`, `region`, `latitude`, `longitude`, `era_start_year`, `era_end_year`), `ports` (linked to `ancient_cities` with `water_body`, `port_type`), `trade_routes` (`route_name`, `route_type` CHECK IN `'Land'`, `'Maritime'`, `'Riverine'`, `active_era_start`, `active_era_end`), `commodities` (`commodity_name`, `category`, `origin_region`), `currencies` (`currency_name`, `metal_type`, `kingdom_id`, `weight_grams`, `circulation_era`), `travellers` (`traveller_name`, `origin_country`, `travel_period`, `profession`), `cultural_exchanges` (`exchange_title`, `category` e.g. Language/Religion/Art/Science, `origin_city_id`, `destination_city_id`, `period`), and `pramana_sources` (`source_title`, `author_or_tradition`, `language`, `approximate_century`, `source_type`).
>    - **Junction Tables (4):** `route_cities` (`route_id`, `city_id`, `stop_order`, `distance_from_prev_km`), `route_commodities` (`route_id`, `commodity_id`, `trade_direction`, `primary_source_id`), `kingdom_city_control` (`kingdom_id`, `city_id`, `control_start_year`, `control_end_year`), and `traveller_stops` (`traveller_id`, `city_id`, `route_id`, `visit_order`, `recorded_observation`, `pramana_source_id`).
> 2. Enforce strict `PRIMARY KEY`, `FOREIGN KEY` (`ON UPDATE CASCADE`, `ON DELETE RESTRICT`), `UNIQUE`, and `CHECK` constraints (e.g., valid latitude/longitude bounds, positive weight/distance, `era_start_year <= era_end_year` using negative integers for BCE).
> 3. Add a `JSONB` column named `artefact_metadata` (default `'{}'::jsonb`) on `ancient_cities`, `trade_routes`, `currencies`, `travellers`, and `cultural_exchanges` to act as a hybrid RDBMS/NoSQL document store for long historical essays, coin obverse/reverse image URLs, epigraphic transcripts, and extra source citations.
> 4. In `02_views_triggers.sql`:
>    - Create an `audit_log` table (`log_id`, `table_name`, `operation`, `record_id`, `changed_at`, `old_data JSONB`, `new_data JSONB`) and attach an `AFTER INSERT OR UPDATE OR DELETE` PostgreSQL trigger function to `kingdoms`, `ancient_cities`, `trade_routes`, and `currencies`.
>    - Create a stored procedure `add_validated_route_stop(...)` that validates stop ordering and inserts a new `route_cities` entry safely.
>    - Create analytical views (`vw_route_network_summary`, `vw_coinage_by_kingdom`, `vw_pramana_linked_heritage`) and a **Recursive CTE SQL function** `find_trade_paths(start_city_id INT, end_city_id INT, max_hops INT DEFAULT 6)` that returns multi-hop connected routes without cycles, listing the path of city IDs, total distance, and routes used.

---

#### Prompt A2: Lightweight Dev Sample Seed & 15-Query Viva DQL Pack
> **Prompt:**
> Using the exact 13-table schema from `database/01_schema_ddl.sql`, create `database/03_dev_seed_sample.sql` and `database/04_analytical_queries.sql`.
>
> 1. In `03_dev_seed_sample.sql`, insert a compact, historically authentic development dataset (4 to 6 rows per table across all 13 tables) covering:
>    - Kingdoms: Maurya, Gupta, Chola, Satavahana, Kushan.
>    - Cities & Ports with real coordinates: Taxila, Pataliputra (Patna), Ujjayini (Ujjain), Bhrigukachchha (Bharuch), Muziris (Kodungallur), Tamralipti (Tamluk), Kaveripattinam (Poompuhar).
>    - Routes: *Uttarapatha*, *Dakshinapatha*, Western Maritime Spice Route, Bay of Bengal Maritime Route.
>    - Commodities: Black Pepper, Muslin Cotton, Silk, Spices, Gold Bullion, Pearls.
>    - Currencies: Punch-marked *Karshapana*, Gupta Gold *Dinar*, Chola *Kasu*, Satavahana Lead Coin.
>    - Travellers: Megasthenes, Faxian, Xuanzang, Adi Shankaracharya.
>    - Pramana Sources: *Kautilya's Arthashastra*, *Indica*, *Periplus of the Erythraean Sea*, *Si-Yu-Ki*, Ashokan Edicts.
>    - Populate realistic `artefact_metadata` `JSONB` objects (historical summary, coin obverse/reverse descriptions, epigraphic notes) so every UI feature renders richly right away. Add a top comment marking this as a temporary dev seed to be replaced later by Track B.
> 2. In `04_analytical_queries.sql`, write **15 clearly titled, viva-ready DQL queries** with descriptive `-- @name:` and `-- @category:` headers covering:
>    - Multi-table inner and outer `JOIN`s (e.g., routes + cities + controlling kingdoms + commodities + currencies).
>    - Nested & correlated subqueries (e.g., cities traded on more routes than the average city; kingdoms controlling both inland hubs and maritime ports).
>    - `GROUP BY` + `HAVING` aggregations (e.g., top trade hubs by commodity diversity, total coinage types per metal and dynasty).
>    - Window functions (`RANK()`, `DENSE_RANK()`, running totals along route stops).
>    - Set operations (`UNION` / `INTERSECT` comparing land-only vs. maritime cities).
>    - `JSONB` hybrid document queries (extracting keys and filtering inside `artefact_metadata`).
>    - Recursive CTE invocation calling `find_trade_paths(...)` between Taxila and Muziris.

---

#### Prompt A3: Flask Backend, Live SQL Telemetry, Explorer APIs, Viva Runner & 3NF Admin
> **Prompt:**
> Build the Flask backend inside `app/` (`__init__.py`, `db.py`, `routes/main_routes.py`, `routes/explorer_routes.py`, `routes/admin_routes.py`) plus `run.py`, `.env.example`, and `requirements.txt`. The backend must be completely Excel-agnostic and communicate strictly with PostgreSQL via `psycopg2`.
>
> 1. In `app/db.py`, implement a connection helper and `execute_query(sql, params=None, fetch=True)` that:
>    - Executes parameterized PostgreSQL queries safely.
>    - Captures exact rendered SQL (safe preview), execution duration in milliseconds, and row count.
>    - Returns `{ "data": rows, "sql_meta": { "query": ..., "execution_ms": ..., "row_count": ... } }` so every API response powers the frontend's **Under-the-Hood SQL** drawer.
> 2. In `main_routes.py`:
>    - Page route `/` rendering `index.html`.
>    - `GET /api/map-data?year=<int>&route_type=<str>` returning cities (with ancient + modern names, coordinates, port flag, Pramana source count, and `artefact_metadata`), ordered route polylines, and active kingdoms for the selected year.
>    - `GET /api/route-finder?from_city=<id>&to_city=<id>` calling the PostgreSQL Recursive CTE `find_trade_paths`, enriching each hop with controlling kingdoms, circulating currencies, and traded commodities.
> 3. In `explorer_routes.py`:
>    - Page routes `/mudra-kosha`, `/yatri-sangam`, `/analytics` and JSON APIs:
>    - `GET /api/currencies?metal=&kingdom_id=&era=` returning coinage details, kingdom info, circulating routes, `artefact_metadata` (obverse/reverse notes), and Pramana citations.
>    - `GET /api/travellers` and `GET /api/travellers/<id>/journey` returning ordered chronological stops, ruling kingdom at each stop, observations, cultural exchanges, and Pramana citations.
>    - `GET /api/pramana/<entity_type>/<entity_id>` returning all classical IKS source citations linked to a specific city, route, currency, or traveller.
>    - `GET /api/analytics/network` returning Vis.js `nodes` and `edges` (hubs, kingdoms, commodities, cultural exchanges) plus aggregated KPI stats for charts.
> 4. In `admin_routes.py`:
>    - Page routes `/admin` and `/viva-lab`.
>    - Full CRUD JSON endpoints (`/api/admin/<table_name>`) for core tables that explicitly catch `psycopg2.IntegrityError` (foreign key, unique, check violations) and return a structured JSON explanation (`constraint_name`, `pg_error`, `human_explanation`) for live 3NF viva demonstrations.
>    - `GET /api/admin/audit-log` returning the latest trigger-populated rows from `audit_log`.
>    - `GET /api/viva/queries` and `POST /api/viva/run/<query_id>` that parse the 15 preset queries from `database/04_analytical_queries.sql` and execute any selected query live, returning columns, rows, and `sql_meta`.

---

#### Prompt A4: Innovative NLP Module — Vāk-to-SQL & Historical Text-to-Entity Extractor
> **Prompt:**
> Create `app/routes/nlp_routes.py` implementing the two NLP innovative experiments from the project architecture, registered as a Flask Blueprint:
>
> 1. **Vāk-to-SQL (`POST /api/nlp/vak-to-sql`):**
>    - Accepts `{ "question": "..." }` in plain English (e.g., *"Which ports under the Chola dynasty exported black pepper?"*, *"List all gold coins issued by the Gupta kingdom"*, *"Show cities along the Uttarapatha route"*).
>    - Implements a clean, deterministic schema-aware intent & template SQL translator (with optional pluggable LLM API fallback via `.env` if an API key is configured, so it works 100% offline during viva demos without internet dependency).
>    - Enforces a strict read-only SQL sanitizer that **blocks** any query not starting with `SELECT` or `WITH`, and rejects any mutating/DDL keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `;`).
>    - Executes the generated query via `app/db.py` and returns `{ "question": ..., "generated_sql": ..., "columns": [...], "rows": [...], "sql_meta": ... }`.
> 2. **Historical Text-to-Entity Extractor (`POST /api/nlp/extract-entities`):**
>    - Accepts `{ "text": "..." }` containing any historical paragraph or excerpt (also expose `GET /api/nlp/sample-passages` with 3 pre-loaded classical excerpts about Indian trade for one-click viva demos).
>    - Fetches canonical entity dictionaries (classical names, modern names, aliases) from PostgreSQL (`ancient_cities`, `ports`, `kingdoms`, `trade_routes`, `commodities`, `currencies`, `travellers`).
>    - Uses case-insensitive boundary-aware pattern matching (and optional lightweight tokenization) to extract every matching entity with character offsets (`start`, `end`), entity category, database ID, and a brief DB summary snippet.
>    - Returns `{ "entities": [...], "counts_by_type": {...}, "highlighted_segments": [...], "sql_meta": ... }` so the frontend can color-code entities inline and link them directly to database records.

---

#### Prompt A5: IKS-Themed Frontend Core — Shell, Bharata-Manchitra Map, Pramana Modal & Live SQL Drawer
> **Prompt:**
> Build the core frontend shell and interactive map in `app/templates/base.html`, `app/templates/index.html`, `app/static/css/iks_theme.css`, `app/static/js/sql_inspector.js`, and `app/static/js/map_manchitra.js` using Tailwind CSS (CDN) and Leaflet.js.
>
> 1. **IKS Manuscript Aesthetic (`iks_theme.css` & `base.html`):**
>    - Use warm parchment background (`#FAF3E0`), elevated cream cards (`#FFFDF7`), deep indigo ink text (`#1E293B`), terracotta/vermilion accents (`#B45309`), and temple gold borders (`#D97706`) with classical serif headings (`Cinzel` or `Playfair Display` via Google Fonts) and clean sans-serif body text (`Inter`).
>    - Top navigation bar with tabs: **Bharata-Manchitra (Map)**, **Mudra-Kosha (Coinage)**, **Yatri-Sangam (Travellers)**, **Trade Analytics**, **Viva & NLP Lab**, and **3NF Admin**.
>    - **Global Under-the-Hood SQL Drawer (`sql_inspector.js`):** A persistent bottom/side collapsible drawer with a live badge showing the count of queries run; every `fetch()` call to `/api/*` automatically appends its `sql_meta` (formatted SQL, execution time in ms, row count) with a copy-SQL button.
>    - **Global Pramana Citation Modal (`sql_inspector.js`):** Reusable modal triggered whenever a user clicks a gold **Pramana Source** badge anywhere in the app, fetching `/api/pramana/<type>/<id>` to display the classical text title, author/tradition, century, and `JSONB` epigraphic/manuscript notes.
> 2. **Bharata-Manchitra Interactive Map (`index.html` & `map_manchitra.js`):**
>    - Full-width Leaflet.js map centered on the Indian subcontinent with muted warm/vintage map tiles.
>    - Distinct markers for **Ancient Cities** vs. **Maritime Ports**, showing both Classical Sanskrit/Prakrit and Modern names in popups alongside a clickable **Pramana Citation** badge and `JSONB` historical summary.
>    - Color-coded polylines for **Land Routes** (terracotta solid), **Maritime Routes** (indigo dashed), and **Riverine Routes** (teal dotted), with route-type filter toggles.
>    - Interactive **Era Timeline Slider (600 BCE – 1200 CE)** that dynamically filters active cities, routes, and ruling kingdoms via `/api/map-data`.
>    - **Multi-Hop Route Pathfinder Panel:** Source & Destination city dropdowns calling `/api/route-finder`, highlighting the computed Recursive CTE path on the map and displaying a step-by-step hop breakdown (city → kingdom → currency → commodities → distance).

---

#### Prompt A6: Dedicated Heritage, Analytics, Viva Lab, NLP Workbench & 3NF Admin Pages
> **Prompt:**
> Build the remaining five pages and scripts (`mudra_kosha.html`, `yatri_sangam.html`, `analytics.html`, `viva_nlp_lab.html`, `admin_crud.html`, and `app/static/js/network_graph.js`, `app/static/js/nlp_workbench.js`) extending `base.html` and wired to the global `sql_inspector.js` drawer and Pramana citation modal.
>
> 1. **Mudra-Kosha (`mudra_kosha.html`):**
>    - Filter bar for **Metal Type** (Gold, Silver, Copper, Lead), **Issuing Dynasty/Kingdom**, and **Search**.
>    - Responsive card grid displaying coin name, issuing kingdom, weight, era, linked trade routes, and a **Pramana** badge.
>    - Clicking a coin opens an **Obverse / Reverse Coin Inspection Modal** displaying structured PostgreSQL attributes alongside the `JSONB` `artefact_metadata` (obverse/reverse motifs, inscriptions, image or clean SVG placeholder fallback).
> 2. **Yatri-Sangam (`yatri_sangam.html`):**
>    - Selector sidebar/tabs for historical travellers (Megasthenes, Faxian, Xuanzang, Adi Shankaracharya, etc.).
>    - Renders a **Chronological Step-by-Step Journey Timeline** showing each stop in `visit_order`, classical-to-modern city name, ruling kingdom during that visit, recorded observations, linked **Cultural Exchanges** (language, art, philosophy, scripts), and **Pramana** citation badges.
> 3. **Trade & Cultural Diffusion Analytics (`analytics.html` & `network_graph.js`):**
>    - Interactive **Vis.js Network Graph** with color-coded node clusters (Cities/Ports, Kingdoms, Commodities, Cultural Exchanges) and toggleable edge filters so users can visually inspect major trade hubs and cultural diffusion corridors.
>    - Companion KPI summary cards and clean bar/distribution breakdown of top trade hubs and most widely traded commodities.
> 4. **Viva SQL Lab & NLP Workbench (`viva_nlp_lab.html` & `nlp_workbench.js`):**
>    - **Tab 1 — 15-Query Viva SQL Runner:** Lists all 15 preset queries grouped by SQL category (Joins, Nested Subqueries, Group By/Having, Window Functions, JSONB, Recursive CTE). Clicking **Run Query** displays the formatted SQL and renders the live result table.
>    - **Tab 2 — Vāk-to-SQL:** Plain-English search bar with 4 clickable example chips; displays the generated read-only SQL, safety-check badge, and tabular output.
>    - **Tab 3 — Historical Text-to-Entity Extractor:** Textarea with 3 one-click sample historical passages and an **Extract Entities** button. Displays the passage with color-coded inline highlights (City, Kingdom, Route, Commodity, Currency), summary entity counts, and clickable side cards linked to the live database records.
> 5. **3NF Integrity & Trigger Admin Dashboard (`admin_crud.html`):**
>    - Table selector supporting Create, Read, Update, and Delete across core tables.
>    - Dedicated **"Test 3NF Integrity" Quick Demo Buttons** (e.g., *Attempt to delete a Kingdom referenced by Currencies* or *Insert invalid Era Range*) that trigger live PostgreSQL `IntegrityError` responses and display a clear amber alert showing the exact PostgreSQL constraint that protected data integrity.
>    - Live **Trigger Audit Log Table** at the bottom displaying automatic `INSERT/UPDATE/DELETE` audit entries captured by PostgreSQL triggers.

---

### Track B: Standalone Excel-to-PostgreSQL ETL Module (Integrate Later)

Run **Prompts B1–B2** only when your 13-sheet Excel workbook is finalized. This module lives entirely inside `etl/` and populates the existing PostgreSQL tables without modifying any Track A application code.

#### Prompt B1: Excel Schema Inspector & Mapping Config Generator
> **Prompt:**
> Create a standalone utility `etl/inspect_excel.py` and a template `etl/column_mapping.json` using `pandas` and `openpyxl`.
>
> 1. Read the Excel workbook at `etl/data/BharatPath_Master.xlsx` and list every worksheet name, row count, detected column headers, null counts, and inferred data types.
> 2. Parse the 13 table and column definitions from `database/01_schema_ddl.sql` and output a compatibility report identifying:
>    - Matched vs. unmatched sheet names.
>    - Renamed or missing columns.
>    - Extra descriptive/image/source columns that should be packed into PostgreSQL `JSONB` (`artefact_metadata`).
>    - Any worksheet containing fewer than 25 records (flagging synopsis requirement compliance).
> 3. Auto-generate `etl/column_mapping.json` so aligning Excel headers to PostgreSQL columns requires editing only the JSON mapping file—never altering the SQL schema or Flask app.

---

#### Prompt B2: Transactional Excel-to-PostgreSQL Bulk Loader
> **Prompt:**
> Write a standalone CLI script `etl/load_excel_to_postgres.py` using `pandas`, `openpyxl`, `psycopg2`, `argparse`, and `python-dotenv`.
>
> 1. Load sheet-to-table and column-to-column mapping rules from `etl/column_mapping.json` and read data from `etl/data/BharatPath_Master.xlsx`.
> 2. Support two CLI flags:
>    - `--dry-run`: Validates all rows, data types, JSONB serialization, and foreign-key references inside a transaction and rolls back without modifying the database.
>    - `--replace-dev-seed`: Safely truncates the temporary sample data (`TRUNCATE ... RESTART IDENTITY CASCADE`) inside the same transaction before bulk-loading the full Excel dataset.
> 3. Clean all values (trim strings, convert `NaN`/`NaT` to `None`, cast BCE/CE integer years and numeric coordinates accurately) and pack all designated semi-structured columns into valid JSON strings for PostgreSQL `JSONB` columns.
> 4. Insert tables in strict foreign-key dependency order:
>    - **Level 1 (Parents):** `kingdoms`, `ancient_cities`, `trade_routes`, `commodities`, `travellers`, `pramana_sources`
>    - **Level 2 (Dependent Entities):** `ports`, `currencies`, `cultural_exchanges`
>    - **Level 3 (Junction Tables):** `route_cities`, `route_commodities`, `kingdom_city_control`, `traveller_stops`
> 5. Synchronize all PostgreSQL `SERIAL` / `IDENTITY` sequences (`setval`) after bulk loading, print a clean terminal verification table showing final row counts per table (confirming 25+ rows each), and rollback atomically with exact sheet name, Excel row number, and constraint error details if any row fails.

---

## 5. Phased Setup & Viva Demo Checklist

### Stage 1: Build & Test Immediately (Without Excel)
1. **Create Database:** `CREATE DATABASE bharatpath_db;`
2. **Apply Core Schema & Triggers:** Execute `database/01_schema_ddl.sql`, then `database/02_views_triggers.sql`.
3. **Load Dev Sample Seed:** Execute `database/03_dev_seed_sample.sql`.
4. **Configure Environment:** Copy `.env.example` to `.env`, add PostgreSQL credentials, and run `pip install -r requirements.txt`.
5. **Launch & Verify:** Run `python run.py` and verify all 6 modules:
   - Bharata-Manchitra map, Era slider, and Recursive CTE Route Finder.
   - Mudra-Kosha coin filters, obverse/reverse modal, and Pramana citation popups.
   - Yatri-Sangam chronological traveller timeline.
   - Vis.js Trade & Cultural Diffusion Network Graph.
   - Viva Lab (15 preset SQL queries), Vāk-to-SQL, and Historical Text-to-Entity Extractor.
   - 3NF Admin CRUD, live `IntegrityError` protection demo, and Trigger Audit Log.

### Stage 2: Plug In Your Excel Dataset (Later)
1. **Place Workbook:** Copy your finalized 13-sheet Excel file to `etl/data/BharatPath_Master.xlsx`.
2. **Inspect & Map:** Run `python etl/inspect_excel.py` and review `etl/column_mapping.json`.
3. **Dry Run Validation:** Run `python etl/load_excel_to_postgres.py --dry-run`.
4. **Load Production Data:** Run `python etl/load_excel_to_postgres.py --replace-dev-seed`.
5. **Refresh Browser:** Reload the Flask app—every map marker, route, coin, traveller timeline, graph node, and viva query automatically reflects your full Excel dataset.