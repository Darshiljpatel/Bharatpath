import os
import sqlite3
import json

DB_FILE = os.path.join(os.path.dirname(__file__), 'bharatpath_dev.db')

def init_dev_db():
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # 1. Pramana Sources
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pramana_sources (
        source_id INTEGER PRIMARY KEY,
        source_title TEXT NOT NULL,
        author_or_tradition TEXT NOT NULL,
        language TEXT NOT NULL,
        approximate_century TEXT NOT NULL,
        source_type TEXT NOT NULL,
        citation_excerpt TEXT,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 2. Kingdoms
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kingdoms (
        kingdom_id INTEGER PRIMARY KEY,
        kingdom_name TEXT UNIQUE NOT NULL,
        capital_city TEXT,
        founded_year INTEGER NOT NULL,
        dissolved_year INTEGER NOT NULL,
        dynasty_lineage TEXT,
        emblem TEXT,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 3. Ancient Cities
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ancient_cities (
        city_id INTEGER PRIMARY KEY,
        classical_name TEXT UNIQUE NOT NULL,
        modern_name TEXT NOT NULL,
        region TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        era_start_year INTEGER NOT NULL,
        era_end_year INTEGER NOT NULL,
        historical_significance TEXT,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 4. Ports
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ports (
        port_id INTEGER PRIMARY KEY,
        city_id INTEGER UNIQUE NOT NULL,
        water_body TEXT NOT NULL,
        port_type TEXT NOT NULL,
        tidal_dock_present INTEGER DEFAULT 0,
        anchorage_depth_meters REAL,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 5. Trade Routes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trade_routes (
        route_id INTEGER PRIMARY KEY,
        route_name TEXT UNIQUE NOT NULL,
        route_type TEXT NOT NULL,
        active_era_start INTEGER NOT NULL,
        active_era_end INTEGER NOT NULL,
        terrain_description TEXT,
        primary_transport_mode TEXT DEFAULT 'Caravan/Pack-Animal',
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 6. Commodities
    cur.execute("""
    CREATE TABLE IF NOT EXISTS commodities (
        commodity_id INTEGER PRIMARY KEY,
        commodity_name TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        origin_region TEXT,
        perishability TEXT DEFAULT 'Low',
        standard_trade_unit TEXT,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 7. Currencies
    cur.execute("""
    CREATE TABLE IF NOT EXISTS currencies (
        currency_id INTEGER PRIMARY KEY,
        currency_name TEXT NOT NULL,
        metal_type TEXT NOT NULL,
        kingdom_id INTEGER,
        weight_grams REAL NOT NULL,
        circulation_era TEXT NOT NULL,
        denomination_standard TEXT,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 8. Travellers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS travellers (
        traveller_id INTEGER PRIMARY KEY,
        traveller_name TEXT NOT NULL,
        origin_country TEXT NOT NULL,
        travel_period TEXT NOT NULL,
        profession TEXT NOT NULL,
        chronicle_title TEXT,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 9. Cultural Exchanges
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cultural_exchanges (
        exchange_id INTEGER PRIMARY KEY,
        exchange_title TEXT NOT NULL,
        category TEXT NOT NULL,
        origin_city_id INTEGER NOT NULL,
        destination_city_id INTEGER NOT NULL,
        period TEXT NOT NULL,
        description TEXT,
        artefact_metadata TEXT DEFAULT '{}'
    );
    """)

    # 10. Route Cities
    cur.execute("""
    CREATE TABLE IF NOT EXISTS route_cities (
        route_id INTEGER NOT NULL,
        city_id INTEGER NOT NULL,
        stop_order INTEGER NOT NULL,
        distance_from_prev_km REAL DEFAULT 0.0,
        estimated_travel_days INTEGER DEFAULT 0,
        PRIMARY KEY (route_id, stop_order)
    );
    """)

    # 11. Route Commodities
    cur.execute("""
    CREATE TABLE IF NOT EXISTS route_commodities (
        route_id INTEGER NOT NULL,
        commodity_id INTEGER NOT NULL,
        trade_direction TEXT DEFAULT 'Bidirectional',
        primary_source_id INTEGER,
        PRIMARY KEY (route_id, commodity_id)
    );
    """)

    # 12. Kingdom City Control
    cur.execute("""
    CREATE TABLE IF NOT EXISTS kingdom_city_control (
        kingdom_id INTEGER NOT NULL,
        city_id INTEGER NOT NULL,
        control_start_year INTEGER NOT NULL,
        control_end_year INTEGER NOT NULL,
        tribute_details TEXT,
        PRIMARY KEY (kingdom_id, city_id, control_start_year)
    );
    """)

    # 13. Traveller Stops
    cur.execute("""
    CREATE TABLE IF NOT EXISTS traveller_stops (
        traveller_id INTEGER NOT NULL,
        visit_order INTEGER NOT NULL,
        city_id INTEGER NOT NULL,
        route_id INTEGER,
        recorded_observation TEXT,
        pramana_source_id INTEGER,
        PRIMARY KEY (traveller_id, visit_order)
    );
    """)

    # Audit log
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        operation TEXT NOT NULL,
        record_id TEXT,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        old_data TEXT,
        new_data TEXT
    );
    """)

    # Insert Sample Data
    # Pramana sources
    cur.executemany("INSERT INTO pramana_sources VALUES (?,?,?,?,?,?,?,?)", [
        (1, 'Arthashastra', 'Kautilya (Chanakya)', 'Sanskrit', '4th Century BCE', 'Text', 'Trade routes (vanikpatha) through land and water are the lifelines of the state treasury.', json.dumps({"text_category": "Statecraft & Political Economy"})),
        (2, 'Indica', 'Megasthenes', 'Ancient Greek', '3rd Century BCE', 'Foreign Chronicle', 'The royal road spanning from the northwest frontier to Pataliputra is measured with milestones.', json.dumps({"text_category": "Diplomatic Observation"})),
        (3, 'Periplus of the Erythraean Sea', 'Anonymous Navigator', 'Koine Greek', '1st Century CE', 'Foreign Chronicle', 'From Barygaza the navigation is dangerous due to the fierce bore tides; inland lies Ozene.', json.dumps({"text_category": "Maritime Guide & Cabotage Log"})),
        (4, 'Si-Yu-Ki', 'Xuanzang (Hiuen Tsang)', 'Classical Chinese', '7th Century CE', 'Foreign Chronicle', 'The city of Pataliputra maintains monastic learning centers along the holy Ganga.', json.dumps({"text_category": "Pilgrimage Chronicle"})),
        (5, 'Major Rock Edict II & XIII', 'Emperor Ashoka Maurya', 'Prakrit (Brahmi Script)', '3rd Century BCE', 'Edict', 'Medicinal herbs for humans and beasts have been planted along roads and wells dug.', json.dumps({"text_category": "Imperial Epigraphy"}))
    ])

    # Kingdoms
    cur.executemany("INSERT INTO kingdoms VALUES (?,?,?,?,?,?,?,?)", [
        (1, 'Mauryan Empire', 'Pataliputra', -322, -185, 'Solar Kshatriya Lineage', 'Lion Capital & Ashoka Chakra', json.dumps({"monetary_standard": "Punch-Marked Silver Karshapana"})),
        (2, 'Gupta Empire', 'Pataliputra / Ujjayini', 320, 550, 'Gupta Dynasty (Golden Age)', 'Garuda Standard', json.dumps({"monetary_standard": "Archer-type Gold Dinara"})),
        (3, 'Satavahana Dynasty', 'Pratishthana / Amaravati', -230, 220, 'Andhra Lineage', 'Ship with Double Masts', json.dumps({"monetary_standard": "Lead & Potin Ship-type Coins"})),
        (4, 'Kushan Empire', 'Purushapura / Mathura', 30, 375, 'Da Yuezhi Lineage', 'Tamga & Sacred Fire Altar', json.dumps({"monetary_standard": "High-purity Gold Dinars"})),
        (5, 'Chola Dynasty', 'Thanjavur / Kaveripattinam', 848, 1279, 'Solar Chola Dynasty', 'Tiger Emblem', json.dumps({"monetary_standard": "Gold and Copper Kasu"}))
    ])

    # Ancient Cities
    cur.executemany("INSERT INTO ancient_cities VALUES (?,?,?,?,?,?,?,?,?,?)", [
        (1, 'Taxila', 'Taxila (Rawalpindi)', 'Gandhara', 33.7460, 72.8270, -600, 500, 'Premier university hub of antiquity, junction of Uttarapatha and Silk Road.', json.dumps({"unesco_site_id": "139"})),
        (2, 'Pataliputra', 'Patna', 'Magadha (Bihar)', 25.6100, 85.1410, -500, 600, 'Imperial capital of the Mauryas and Guptas, grand palisaded metropolis.', json.dumps({"palisade": "Kumrahar hall"})),
        (3, 'Ujjayini', 'Ujjain', 'Malwa (Madhya Pradesh)', 23.1765, 75.7885, -600, 1200, 'Prime meridian of ancient Indian astronomy, inland trade nexus.', json.dumps({"meridian": "Surya Siddhanta"})),
        (4, 'Bhrigukachchha', 'Bharuch', 'Lata (Gujarat Coast)', 21.7051, 72.9959, -500, 1000, 'Renowned port of Barygaza in Greco-Roman records on the Narmada.', json.dumps({"greek_name": "Barygaza"})),
        (5, 'Muziris', 'Kodungallur / Pattanam', 'Malabar Coast (Kerala)', 10.2210, 76.1960, -300, 500, 'Legendary black pepper emporium of the ancient maritime world.', json.dumps({"roman_trade": "Temple of Augustus"})),
        (6, 'Tamralipti', 'Tamluk', 'Vanga (West Bengal)', 22.2890, 87.9250, -400, 800, 'Premier eastern maritime terminus on the Rupnarayan river.', json.dumps({"pilgrim_embark": "Faxian 411 CE"})),
        (7, 'Kaveripattinam', 'Poompuhar', 'Chola Nadu (Tamil Nadu Coast)', 11.1440, 79.8550, -300, 1100, 'Ancient Chola port city celebrated in Silappadikaram.', json.dumps({"sangam_epic": "Silappadikaram"})),
        (8, 'Mathura', 'Mathura', 'Surasena (Uttar Pradesh)', 27.4924, 77.6737, -600, 1000, 'Major mercantile city on the Yamuna, southern capital of Kushans.', json.dumps({"art_school": "Mathura School"}))
    ])

    # Ports
    cur.executemany("INSERT INTO ports VALUES (?,?,?,?,?,?,?)", [
        (1, 4, 'Arabian Sea / Narmada Gulf of Khambhat', 'Estuarine', 1, 11.5, json.dumps({"pilot_boats": "Guided foreign galleys"})),
        (2, 5, 'Arabian Sea / Periyar River Lagoon', 'Maritime', 0, 8.2, json.dumps({"anchorage": "Roadstead"})),
        (3, 6, 'Bay of Bengal / Rupnarayan River', 'Estuarine', 1, 9.8, json.dumps({"monsoon": "Winter northeast"})),
        (4, 7, 'Bay of Bengal / Kaveri River Delta', 'Maritime', 1, 12.0, json.dumps({"harbour": "Lighthouses and docks"}))
    ])

    # Trade Routes
    cur.executemany("INSERT INTO trade_routes VALUES (?,?,?,?,?,?,?,?)", [
        (1, 'Uttarapatha (Great Northern Highway)', 'Land', -600, 1200, 'Indo-Gangetic alluvium from Gandhara through Yamuna/Ganga.', 'Ox-cart Caravans & Pack-horses', json.dumps({"predecessor": "Grand Trunk predecessor"})),
        (2, 'Dakshinapatha (Great Southern Highway)', 'Land', -500, 1000, 'Traverses Vindhyas into Deccan plateau connecting northern cities to south.', 'Pack-bullocks & Caravan Carts', json.dumps({"mountain_passes": "Narmada crossings"})),
        (3, 'Western Maritime Spice Route', 'Maritime', -300, 1100, 'Coastal navigation corridor along Arabian Sea connecting Muziris to Barygaza.', 'Timber Galleys (Dhows)', json.dumps({"wind": "Hippalus monsoon"})),
        (4, 'Bay of Bengal Maritime Route', 'Maritime', -300, 1200, 'High-seas maritime circuit connecting Kaveripattinam to Tamralipti.', 'Multi-decked Ocean Galleys', json.dumps({"expeditions": "Chola naval fleets"}))
    ])

    # Commodities
    cur.executemany("INSERT INTO commodities VALUES (?,?,?,?,?,?,?)", [
        (1, 'Malabar Black Pepper (Black Gold)', 'Spices', 'Malabar Coast (Kerala)', 'Low', 'Sack (50 kg)', json.dumps({"roman_valuation": "Worth weight in silver"})),
        (2, 'Bengal Muslin (Gangetica)', 'Textiles', 'Gangetic Delta (Bengal)', 'Low', 'Bolt of gossamer fabric', json.dumps({"greek_term": "Gangitikon"})),
        (3, 'Gandhara Lapis Lazuli', 'Minerals & Gems', 'Badakhshan / Hindu Kush', 'Low', 'Rough stone talent', json.dumps({"pigment": "Ultramarine Ajanta fresco pigment"})),
        (4, 'Silk (Kauseya / Chinapatta)', 'Textiles', 'Gangetic weaving centers', 'Low', 'Standard Silk Bolt', json.dumps({"etymology": "Kauseya"})),
        (5, 'Roman Gold Bullion & Denarii', 'Precious Metals', 'Roman Empire', 'Low', 'Denarius coin sacks', json.dumps({"hoards": "Dozens of hoards in South India"})),
        (6, 'Gulf of Mannar Pearls', 'Minerals & Gems', 'Coromandel / Gulf of Mannar', 'Low', 'String / Carat pouch', json.dumps({"pliny": "Pliny 50M sesterces drain"})),
        (7, 'Malabar Cardamom & Cinnamon', 'Spices', 'Western Ghats', 'Medium', 'Woven cane hamper', json.dumps({"ayurveda": "Tridosha balancing"})),
        (8, 'Gujarat Agate & Carnelian Beads', 'Minerals & Gems', 'Ratanpur (Gujarat)', 'Low', 'Polished bead strings', json.dumps({"manufacturing": "Vallabhi/Barygaza"}))
    ])

    # Currencies
    cur.executemany("INSERT INTO currencies VALUES (?,?,?,?,?,?,?,?)", [
        (1, 'Silver Punch-Marked Karshapana (Pana)', 'Silver', 1, 3.40, '4th - 2nd Century BCE', 'Vimshatika standard', json.dumps({"obverse_symbols": ["Sun", "Six-arm", "Hill with crescent"], "reverse_symbols": ["Taxila mark"], "image_url": "/static/images/coins/karshapana.svg"})),
        (2, 'Gupta Gold Dinar (Archer Type)', 'Gold', 2, 8.10, '4th - 5th Century CE', 'Suvarna standard', json.dumps({"obverse_symbols": ["King holding bow and arrow", "Garuda banner"], "reverse_symbols": ["Goddess Lakshmi on lotus"], "image_url": "/static/images/coins/gupta_dinar.svg"})),
        (3, 'Satavahana Lead Ship Coin', 'Lead', 3, 7.80, '2nd Century CE', 'Karshapana unit', json.dumps({"obverse_symbols": ["Two-masted sailing ship"], "reverse_symbols": ["Ujjain four-orbed symbol"], "image_url": "/static/images/coins/satavahana_lead.svg"})),
        (4, 'Kushan Gold Dinar (Kanishka I)', 'Gold', 4, 7.95, '2nd Century CE', 'Kushan Gold Dinar', json.dumps({"obverse_symbols": ["King sacrificing at fire altar"], "reverse_symbols": ["Buddha in Abhaya Mudra"], "image_url": "/static/images/coins/kushan_dinar.svg"})),
        (5, 'Imperial Chola Gold Kasu', 'Gold', 5, 4.30, '10th - 11th Century CE', 'Kasu standard', json.dumps({"obverse_symbols": ["King holding flower above altar"], "reverse_symbols": ["Seated king holding conch"], "image_url": "/static/images/coins/chola_kasu.svg"}))
    ])

    # Travellers
    cur.executemany("INSERT INTO travellers VALUES (?,?,?,?,?,?,?)", [
        (1, 'Megasthenes', 'Seleucid Empire (Greece)', '302 BCE – 298 BCE', 'Ambassador & Geographer', 'Indica', json.dumps({"mission": "Embassy to court of Chandragupta Maurya at Pataliputra"})),
        (2, 'Faxian (Fa-Hien)', 'Jin Dynasty (China)', '399 CE – 412 CE', 'Buddhist Monk & Scholar', 'A Record of Buddhist Kingdoms', json.dumps({"mission": "Procure authentic copies of the Vinaya Pitaka"})),
        (3, 'Xuanzang (Hiuen Tsang)', 'Tang Dynasty (China)', '629 CE – 645 CE', 'Buddhist Scholar & Translator', 'Si-Yu-Ki', json.dumps({"mission": "Study at Nalanda under Abbot Silabhadra"})),
        (4, 'Adi Shankaracharya', 'Kalady (Kerala, India)', 'c. 788 CE – 820 CE', 'Philosopher & Acharya', 'Brahmasutra Bhashya', json.dumps({"mission": "Advaita Vedanta digvijaya establishing four Amnaya Mathas"}))
    ])

    # Cultural Exchanges
    cur.executemany("INSERT INTO cultural_exchanges VALUES (?,?,?,?,?,?,?,?)", [
        (1, 'Transmission of Buddhist Philosophical Texts to China', 'Philosophy', 2, 1, '4th - 7th Century CE', 'Manuscripts copied on palm leaf and carried to China.', json.dumps({"script": "Siddham / Brahmi"})),
        (2, 'Greco-Buddhist Hybrid Sculptural Style (Gandhara Art)', 'Art', 1, 8, '1st - 3rd Century CE', 'Synthesis of Hellenistic drapery with Buddhist iconography.', json.dumps({"medium": "Grey schist to red sandstone"})),
        (3, 'Maritime Dissemination of Grantha Script & Architecture', 'Architecture', 7, 6, '7th - 10th Century CE', 'Dravidian architectural canons diffused to Bengal and Southeast Asia.', json.dumps({"script": "Grantha"})),
        (4, 'Surya Siddhanta Astronomical Computations', 'Science', 3, 2, '5th - 6th Century CE', 'Zero meridian astronomical calculations at Ujjayini.', json.dumps({"author": "Aryabhata & Varahamihira"})),
        (5, 'Ayurvedic Botanical Knowledge Exchange & Herb Trade', 'Science', 5, 4, '1st - 4th Century CE', 'Malabar herbs systematized and exported via Barygaza.', json.dumps({"herbs": ["Maricha", "Ela", "Pippali"]}))
    ])

    # Route Cities
    cur.executemany("INSERT INTO route_cities VALUES (?,?,?,?,?)", [
        (1, 1, 1, 0.0, 0), (1, 8, 2, 780.0, 26), (1, 2, 3, 620.0, 21), (1, 6, 4, 480.0, 16),
        (2, 2, 1, 0.0, 0), (2, 3, 2, 850.0, 28), (2, 4, 3, 340.0, 11), (2, 5, 4, 1290.0, 43),
        (3, 4, 1, 0.0, 0), (3, 5, 2, 1350.0, 18), (3, 7, 3, 560.0, 8),
        (4, 7, 1, 0.0, 0), (4, 6, 2, 1420.0, 20)
    ])

    # Route Commodities
    cur.executemany("INSERT INTO route_commodities VALUES (?,?,?,?)", [
        (1, 2, 'Export', 2), (1, 3, 'Import', 1), (1, 4, 'Transit', 4),
        (2, 8, 'Export', 1), (2, 1, 'Transit', 3),
        (3, 1, 'Export', 3), (3, 5, 'Import', 3), (3, 7, 'Export', 3),
        (4, 6, 'Export', 5), (4, 2, 'Transit', 4)
    ])

    # Kingdom City Control
    cur.executemany("INSERT INTO kingdom_city_control VALUES (?,?,?,?,?)", [
        (1, 2, -322, -185, 'Imperial capital seat'),
        (1, 1, -320, -190, 'Administered by Royal Kumara Viceroy'),
        (1, 3, -315, -185, 'Viceroyalty seat under Prince Ashoka'),
        (2, 2, 320, 500, 'Imperial seat of Chandragupta I'),
        (2, 3, 380, 520, 'Second imperial capital under Vikramaditya'),
        (3, 4, -100, 150, 'Western gateway customs house'),
        (4, 1, 60, 240, 'Winter administrative center and mint'),
        (4, 8, 70, 250, 'Southern imperial capital of Kushans'),
        (5, 7, 850, 1250, 'Principal Chola naval port and custom station'),
        (3, 5, -50, 180, 'Allied maritime trading enclave')
    ])

    # Traveller Stops
    cur.executemany("INSERT INTO traveller_stops VALUES (?,?,?,?,?,?)", [
        (1, 1, 1, 1, 'Entered Punjab through Gandhara, recorded the fortified Greek and Indian settlements at Taxila.', 2),
        (1, 2, 8, 1, 'Witnessed flourishing Krishna-Herakles worship along the Yamuna at Mathura.', 2),
        (1, 3, 2, 1, 'Arrived at the Mauryan court in Pataliputra; described the royal audience and elephant processions.', 2),
        (2, 1, 8, 1, 'Observed numerous Buddhist monasteries with thousands of resident sangha members on the Yamuna.', 4),
        (2, 2, 2, 1, 'Spent three years in Pataliputra transcribing Vinaya rules; visited Ashoka’s legendary stone palace.', 4),
        (2, 3, 6, 1, 'Spent two years at Tamralipti painting Buddhist images and copying sacred sutras.', 4),
        (3, 1, 1, 1, 'Explored Taxila stupas and lamented the decline of monasteries since the Hephthalite incursions.', 4),
        (3, 2, 8, 1, 'Recorded five or six stupas built by Ashoka and observed five hundred monks of Mahayana & Hinayana.', 4),
        (3, 3, 2, 1, 'Visited the ruins of ancient Pataliputra and proceeded to Nalanda Mahavihara for advanced dialectics.', 4),
        (4, 1, 5, 3, 'Began digvijaya from Kalady near Muziris, expounding Advaita non-duality.', 1),
        (4, 2, 3, 2, 'Debated scholars at Ujjayini, establishing the supremacy of Vedic non-dual philosophy.', 1),
        (4, 3, 2, 2, 'Visited Magadha centers of learning, revitalizing temple traditions and establishing monastic orders.', 1)
    ])

    conn.commit()
    conn.close()
    print("Dev SQLite database initialized successfully at:", DB_FILE)

if __name__ == '__main__':
    init_dev_db()
