# BharatPath (भारतपथ)
### Ancient Indian Routes, Trade Networks, and Geographical Heritage Database System
*Course Project for Database Management Systems (CD252IA)*

---

## 🏛️ Project Overview
**BharatPath** is a comprehensive, full-stack database management and interactive geospatial visualization platform designed to model, query, and analyze ancient and medieval Indian trade routes, maritime networks, coinage standards, urban centers, foreign travellers, and cultural transmissions spanning from **600 BCE to 1600 CE**.

Built following rigorous relational database design principles (Boyce-Codd / 3NF Normalization), the platform integrates a classical **Indian Knowledge Systems (IKS)** aesthetic with modern data engineering, automated ETL pipelines, an interactive GIS map, network topology graph visualizations, and a natural language (Vāk-to-SQL) viva laboratory.

---

## 🏗️ Architecture & Technology Stack

- **Relational DBMS:** PostgreSQL 18 (Production) / SQLite 3 (Lightweight Dev / Demonstration)
- **Backend Framework:** Python 3.12 / Flask (Application Factory pattern, Blueprints)
- **Database Driver:** `psycopg2-binary` (PostgreSQL) / `sqlite3`
- **Data Engineering & ETL:** `pandas`, `openpyxl` with 5-tier foreign key topological dependency resolution
- **Frontend & UI Theme:** Custom IKS Manuscript theme (Chunar Sandstone `#F7F2E7`, Bhojpatra Parchment `#EBDDC3`, Temple Gold `#C68642`, Mauryan Ochre `#8B2500`, Ashokan Terracotta `#B2432F`)
- **GIS Mapping:** Leaflet.js (CartoDB Positron / OpenStreetMap base, custom geo-coordinates, polyline routes)
- **Graph & Charts:** Vis.js Network (route topology), Chart.js (temporal & commodity distributions)

---

## 📊 Database Schema (Strict 3NF)

The database consists of **13 core operational tables** structured across 5 strict topological dependency levels to ensure zero circular foreign keys and complete referential integrity (`ON UPDATE CASCADE`, restricted/nullified deletes):

```
Level 1 (Independent Roots):
  ├── sources (41 historical texts, epigraphs, numismatic catalogs)

Level 2 (Regional & Temporal Domains):
  ├── regions (33 macro-regions: Aryavarta, Dakshinapatha, etc.)
  ├── historical_periods (32 dynasties & eras: Mauryan, Gupta, Chola, etc.)
  └── commodities (30 luxury, spice, textile & metal trade items)

Level 3 (Geo-Spatial Entities):
  ├── cities (73 historic capitals, river ports, craft emporiums)
  └── cultural_exchanges (30 philosophical, religious, artistic transmissions)

Level 4 (Empires, Ports & Corridors):
  ├── kingdoms (31 empires and ruling dynasties)
  ├── ports (28 oceanic and estuarine harbor nodes)
  └── trade_routes (26 major terrestrial & maritime highways)

Level 5 (Junctions, Currencies & Chroniclers):
  ├── route_city (68 route-to-city traversal sequences)
  ├── route_commodity (79 transported commodities per trade route)
  ├── currencies (32 classical coins, standards, and metal specifications)
  └── travellers (28 historical chroniclers, ambassadors, and monks)
```

**Total Verified Records:** **531 authentic historical rows** across all tables.

### 🛡️ Triggers, Views & Procedures
- **Audit Logging Triggers (`audit_log`):** Automatically capture `OLD` and `NEW` JSON snapshots on `INSERT`, `UPDATE`, and `DELETE` for `kingdoms`, `cities`, `trade_routes`, and `currencies`.
- **Materialized Analytical Views:**
  - `vw_route_network_summary`: Denormalized highway lengths, start/end regions, and associated cities.
  - `vw_coinage_by_kingdom`: Imperial coin counts, metal breakdowns, and earliest/latest attestation dates.
  - `vw_source_linked_heritage`: Primary literary/epigraphic citation trails across all entities.
- **Stored Procedures:** `sp_recalculate_route_traffic()` and distance aggregation utilities.

---

## 🌟 Key Features & Modules

### 1. 🗺️ Bharata-Manchitra (Interactive GIS & Geo-Spatial Explorer)
- Interactive Leaflet map visualizing 73 historic cities, 28 maritime ports, and 26 overland & maritime corridors (e.g., *Uttarapatha*, *Dakshinapatha*, *Spice Route*).
- Filtering by historical era, empire, terrain type (terrestrial vs. maritime), and high-value commodity trade.

### 2. 🪙 Mudra-Kosha (Ancient Coinage & Currency Explorer)
- Comprehensive numismatic catalog of 32 classical currency records (Punch-marked *Karshapanas*, Gupta *Dināras*, Kushan gold staters, Satavahana lead maritime coins, Chola *Kasu*).
- Live case-insensitive search, filter by metal standard (Gold, Silver, Copper, Lead, Potin, Bronze), weight standards (Ratti, Masha), and epigraphic source popups.

### 3. 🚶 Yatri-Sangam (Chronicles of Foreign Travellers)
- Tracks 28 legendary historical chroniclers (Megasthenes, Xuanzang, Faxian, Al-Biruni, Ibn Battuta, Marco Polo, Niccolò de' Conti, etc.).
- Maps origin homelands (Greece, Tang China, Khorasan, Morocco, Venice) to visited Indian kingdoms, departure/arrival timelines, and primary citations.

### 4. 📈 Vanijya-Vyuha (Trade & Network Analytics)
- Interactive Vis.js network graph modeling topological centrality, trade bottlenecks, and trans-shipment hubs.
- Chart.js visual summaries of metal distribution, commodity flow volumes, and regional trade densities.

### 5. 🗣️ Vāk-to-SQL & Viva Lab (Natural Language to SQL Engine)
- Natural language query parser mapping conversational English queries (e.g., *"Show all gold coins issued during the Gupta Empire"*) into validated PostgreSQL / SQLite queries.
- SQL drawer with live query inspection, execution plan (`EXPLAIN ANALYZE`) viewers, and preloaded viva query templates.

### 6. 🛡️ 3NF Admin & Data Registry
- Full CRUD administration panel enforcing relational integrity, foreign key selectors, and automated audit logging.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Darshiljpatel/Bharatpath.git
cd Bharatpath
```

### 2. Set Up Python Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and set your database connection parameters:
```ini
FLASK_APP=run.py
FLASK_ENV=development
DB_ENGINE=postgres   # Or 'sqlite' for zero-dependency development

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bharatpath_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### 4. Database Setup & Production ETL Loader
To initialize PostgreSQL with the schema, triggers, and load the 531 rows from Excel:
```bash
# 1. Execute Schema & Triggers in PostgreSQL
psql -U postgres -d bharatpath_db -f "database/01_schema_ddl.sql"
psql -U postgres -d bharatpath_db -f "database/02_views_triggers.sql"

# 2. Run the Production ETL Pipeline
python etl/load_excel_to_postgres.py --replace-dev-seed
```

*(Alternatively, to run entirely on SQLite for standalone testing:)*
```bash
python etl/load_excel_to_db.py
```

### 5. Run the Application
```bash
python run.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 📑 Repository Structure

```
BharatPath/
├── app/
│   ├── __init__.py               # Flask application factory
│   ├── db.py                     # Dual-mode database abstraction (PostgreSQL / SQLite)
│   ├── routes/
│   │   ├── main_routes.py        # Map and core dashboard routes
│   │   ├── explorer_routes.py    # Mudra-Kosha, Yatri-Sangam, and API routes
│   │   ├── admin_routes.py       # 3NF CRUD admin interface
│   │   └── nlp_routes.py         # Vāk-to-SQL natural language parser & query lab
│   ├── static/
│   │   ├── css/iks_theme.css     # Classical IKS manuscript UI styling
│   │   ├── js/                   # Leaflet map, Vis.js graph, SQL inspector scripts
│   │   └── images/coins/         # SVG representations of classical coins
│   └── templates/                # Jinja2 templates (Manchitra, Mudra, Yatri, Admin)
├── data/
│   └── BharatPath_Database_Final.xlsx  # Master 17-sheet 531-row curated dataset
├── database/
│   ├── 01_schema_ddl.sql         # PostgreSQL 3NF DDL with foreign keys and indexes
│   ├── 02_views_triggers.sql     # Audit triggers, procedures, and analytical views
│   ├── 03_dev_seed_sample.sql    # Development seed sample
│   ├── 04_analytical_queries.sql # 15 comprehensive viva analytical queries
│   └── init_dev_sqlite.py        # SQLite schema initializer
├── etl/
│   ├── inspect_excel.py          # Automated schema audit and sheet validator
│   ├── load_excel_to_postgres.py # Production PostgreSQL multi-tier loader
│   └── load_excel_to_db.py       # SQLite development loader
├── bharatpath_project_blueprint (1).md # Comprehensive engineering blueprint
├── requirements.txt              # Python package dependencies
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore file for secrets and environments
└── run.py                        # Application entry point
```

---

## 🎓 Academic Viva Reference (CD252IA)
Key DBMS concepts demonstrated in this project:
1. **Normalization:** 1NF, 2NF, 3NF, and BCNF adherence with formal functional dependency validation.
2. **Referential Integrity:** Multi-level cascading foreign keys, surrogate primary keys (`UUID` / `VARCHAR`), domain check constraints.
3. **Database Security:** Parameterized prepared queries avoiding SQL injection, granular schema auditing.
4. **Advanced SQL:** Window functions (`DENSE_RANK()`, `LEAD()`, `LAG()`), Recursive CTEs for route graph traversal, JSON aggregation.
5. **ACID Transactions:** Full rollback isolation and `session_replication_role` safety during ETL ingestion.

---
*Developed with reverence for India's rich cultural, numismatic, and cartographic heritage.*
