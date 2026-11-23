-- ============================================================================
-- BharatPath – Ancient Indian Routes, Trade and Geographical Heritage
-- File: 03_dev_seed_sample.sql
-- Description: Lightweight Development Dataset (4-6 rows per table across all 13 tables)
-- NOTE: This is a TEMPORARY dev seed for Track A testing. It will be replaced
--       by Track B (load_excel_to_postgres.py --replace-dev-seed) when Excel data is ready.
-- ============================================================================

-- Clean existing data
TRUNCATE TABLE 
    traveller_stops,
    kingdom_city_control,
    route_commodities,
    route_cities,
    cultural_exchanges,
    currencies,
    ports,
    travellers,
    commodities,
    trade_routes,
    ancient_cities,
    kingdoms,
    pramana_sources,
    audit_log
RESTART IDENTITY CASCADE;

-- ----------------------------------------------------------------------------
-- 1. Pramana Sources (5 rows)
-- ----------------------------------------------------------------------------
INSERT INTO pramana_sources (source_id, source_title, author_or_tradition, language, approximate_century, source_type, citation_excerpt, artefact_metadata)
VALUES
(1, 'Arthashastra', 'Kautilya (Chanakya)', 'Sanskrit', '4th Century BCE', 'Text', 
 'Trade routes (vanikpatha) through land and water are the lifelines of the state treasury; water routes yield greater volume but land routes provide safer transit.',
 '{"text_category": "Statecraft & Political Economy", "adhyaya": "Book VII, Chapter 12", "epigraphic_parallel": "Edicts of Ashoka at Girnar", "modern_translation": "R.P. Kangle, University of Bombay"}'),

(2, 'Indica', 'Megasthenes', 'Ancient Greek', '3rd Century BCE', 'Foreign Chronicle', 
 'The royal road spanning from the northwest frontier to Pataliputra is measured with milestones, guarded with military outposts, and shaded with banyan groves.',
 '{"text_category": "Diplomatic Observation", "fragment_source": "Fragments preserved in Arrian and Strabo", "route_reference": "Great Royal Highway (Uttarapatha)", "modern_translation": "J.W. McCrindle"}'),

(3, 'Periplus of the Erythraean Sea', 'Anonymous Alexandrian Navigator', 'Koine Greek', '1st Century CE', 'Foreign Chronicle', 
 'From Barygaza the navigation is dangerous due to the fierce bore tides; inland from here lies Ozene, whence are brought onyx, porcelain, fine muslins and spikenard.',
 '{"text_category": "Maritime Guide & Cabotage Log", "maritime_ports": ["Barygaza", "Muziris", "Poduke"], "monsoon_winds": "Hippalus South-West Trade Wind", "modern_translation": "Lionel Casson, Princeton University"}'),

(4, 'Si-Yu-Ki (Records of the Western Regions)', 'Xuanzang (Hiuen Tsang)', 'Classical Chinese', '7th Century CE', 'Foreign Chronicle', 
 'The kingdom of Magadha produces abundant rice, and the city of Pataliputra, though largely ruined, maintains monastic learning centers along the holy Ganga.',
 '{"text_category": "Pilgrimage Chronicle", "monastic_sites": ["Nalanda", "Pataliputra", "Varanasi"], "preservation_era": "Tang Dynasty Court Records", "modern_translation": "Samuel Beal / Thomas Watters"}'),

(5, 'Major Rock Edict II & XIII', 'Emperor Ashoka Maurya', 'Prakrit (Brahmi Script)', '3rd Century BCE', 'Edict', 
 'Everywhere in the empire and among frontier neighbors—Cholas, Pandyas, Satiyaputras, Keralaputras—medicinal herbs for humans and beasts have been planted along roads and wells dug.',
 '{"text_category": "Imperial Epigraphy", "inscribed_locations": ["Girnar", "Kalsi", "Shahbazgarhi", "Dhauli"], "script": "Mauryan Brahmi", "modern_translation": "E. Hultzsch, Corpus Inscriptionum Indicarum"}');

-- ----------------------------------------------------------------------------
-- 2. Kingdoms (5 rows)
-- ----------------------------------------------------------------------------
INSERT INTO kingdoms (kingdom_id, kingdom_name, capital_city, founded_year, dissolved_year, dynasty_lineage, emblem, artefact_metadata)
VALUES
(1, 'Mauryan Empire', 'Pataliputra', -322, -185, 'Solar Kshatriya / Mauryan Lineage', 'Lion Capital & Ashoka Chakra',
 '{"imperial_extent": "Khyber Pass to Bay of Bengal, Mysore to Assam", "monetary_standard": "Punch-Marked Silver Karshapana", "royal_highway": "Uttarapatha", "epigraphy": "Brahmi & Kharosthi Edicts"}'),

(2, 'Gupta Empire', 'Pataliputra / Ujjayini', 320, 550, 'Gupta Dynasty (Golden Age)', 'Garuda Standard',
 '{"imperial_extent": "Northern & Central India, Western littoral protectorates", "monetary_standard": "Archer-type & Ashvamedha Gold Dinara", "literary_patronage": "Kalidasa, Aryabhata", "architectural_style": "Gupta Classical Temple Architecture"}'),

(3, 'Satavahana Dynasty', 'Pratishthana / Amaravati', -230, 220, 'Andhra / Satavahana Lineage', 'Ship with Double Masts',
 '{"imperial_extent": "Deccan Plateau, Konkan & Coromandel Coastlines", "monetary_standard": "Lead & Potin Ship-type Coins", "trade_dominance": "Greco-Roman Maritime Pepper Trade via Barygaza and Kalyan", "monuments": "Karle, Kanheri, Amaravati Stupa"}'),

(4, 'Kushan Empire', 'Purushapura / Mathura', 30, 375, 'Da Yuezhi / Kushan Dynasty', 'Tamga & Sacred Fire Altar',
 '{"imperial_extent": "Bactria, Gandhara, Punjab through Gangetic Plain to Varanasi", "monetary_standard": "High-purity Gold Dinars & Tetradrachms (Kanishka / Huvishka)", "cultural_syncretism": "Greco-Buddhist Gandhara Art & Mathura Sculpture", "trade_role": "Northern Silk Road connector to Gangetic India"}'),

(5, 'Chola Dynasty', 'Uraiyur / Thanjavur / Kaveripattinam', 848, 1279, 'Solar Chola Dynasty (Imperial Cholas)', 'Tiger Emblem',
 '{"imperial_extent": "Tamilakam, Sri Lanka, Malayan Archipelago expeditions (Kadaram)", "monetary_standard": "Gold and Copper Kasu / Madai", "maritime_command": "Bay of Bengal (Chola Lake) Naval Fleet", "trade_guilds": "Manigramam and Ayyavole 500"}');

-- ----------------------------------------------------------------------------
-- 3. Ancient Cities (8 rows)
-- ----------------------------------------------------------------------------
INSERT INTO ancient_cities (city_id, classical_name, modern_name, region, latitude, longitude, era_start_year, era_end_year, historical_significance, artefact_metadata)
VALUES
(1, 'Taxila', 'Taxila (Rawalpindi)', 'Gandhara (Northwestern Gateway)', 33.746000, 72.827000, -600, 500, 
 'Premier university hub of antiquity, junction of Uttarapatha and Silk Road, center of Gandhara art and Vedic learning.',
 '{"unesco_site_id": "139", "archaeological_mounds": ["Bhir Mound", "Sirkap", "Sirsukh"], "famous_scholars": ["Chanakya", "Panini", "Jivaka"], "excavator": "Sir John Marshall"}'),

(2, 'Pataliputra', 'Patna', 'Magadha (Bihar)', 25.610000, 85.141000, -500, 600, 
 'Imperial capital of the Mauryas and Guptas, confluence of Ganga and Son rivers, grand palisaded metropolis described by Megasthenes.',
 '{"palisade_excavation": "Kumrahar wooden pillar hypostyle hall", "recorded_dimensions": "80 stadia length, 15 stadia breadth (Megasthenes)", "monastic_institutions": ["Asokarama", "Kukkutarama"]}'),

(3, 'Ujjayini', 'Ujjain', 'Malwa (Madhya Pradesh)', 23.176500, 75.788500, -600, 1200, 
 'Prime meridian of ancient Indian astronomy, premier inland trade nexus connecting Gangetic plains with Gujarat ports.',
 '{"astronomy_meridian": "Zero Meridian in Surya Siddhanta", "sacred_temple": "Mahakaleshwar Jyotirlinga", "trade_junction": "Meeting point of Dakshinapatha and Western Sea Route"}'),

(4, 'Bhrigukachchha', 'Bharuch', 'Lata / Gujarat Coast', 21.705100, 72.995900, -500, 1000, 
 'Renowned port of Barygaza in Greco-Roman records, estuarine gateway on the Narmada exporting cotton, agate, and spices to the Roman Empire.',
 '{"greek_name": "Barygaza", "river": "Narmada River Estuary", "tides": "Famous high-velocity bore tides noted in Periplus", "major_exports": ["Onyx", "Fine Muslin", "Spikenard", "Bdellium"]}'),

(5, 'Muziris', 'Kodungallur / Pattanam', 'Malabar Coast (Kerala)', 10.221000, 76.196000, -300, 500, 
 'Legendary black pepper emporium of the ancient maritime world; Roman trading station handling massive annual bullion inflows for Malabar spices.',
 '{"tamil_sangam_reference": "Muchiri where the beautiful vessels of the Yavanas come with gold and return with pepper", "archaeological_site": "Pattanam excavations", "roman_temple": "Temple of Augustus (Tabula Peutingeriana)"}'),

(6, 'Tamralipti', 'Tamluk', 'Vanga (West Bengal)', 22.289000, 87.925000, -400, 800, 
 'Premier eastern maritime terminus on the Rupnarayan river sending monks, pilgrims, and silks to Southeast Asia, Sri Lanka, and China.',
 '{"terracotta_art": "Famous Yakshi terracotta plaques (Tamluk Museum)", "pilgrim_embarkation": "Faxian embarked here for Ceylon in 411 CE", "river_estuary": "Rupnarayan-Hooghly confluence"}'),

(7, 'Kaveripattinam', 'Poompuhar', 'Chola Nadu (Tamil Nadu Coast)', 11.144000, 79.855000, -300, 1100, 
 'Ancient Chola port city celebrated in the Tamil epic Silappadikaram; bustling foreign merchant colonies and active docks at the Kaveri delta.',
 '{"sangam_epic": "Silappadikaram by Ilango Adigal", "submerged_structures": "Underwater marine archaeology brick wharves", "foreign_quarters": "Yavana settlements and customs houses described in Pattinappalai"}'),

(8, 'Mathura', 'Mathura', 'Surasena (Uttar Pradesh)', 27.492400, 77.673700, -600, 1000, 
 'Major sacred and mercantile city on the Yamuna, southern capital of Kushans, famed for spotted red sandstone sculpture and junction of Uttarapatha.',
 '{"art_school": "Mathura School of Sculpture (red Sikri sandstone)", "kushan_shrine": "Mat Royal Sanctuary with Kanishka statue", "yamuna_navigation": "Riverine trade junction towards Pataliputra"}');

-- ----------------------------------------------------------------------------
-- 4. Ports (4 rows)
-- ----------------------------------------------------------------------------
INSERT INTO ports (port_id, city_id, water_body, port_type, tidal_dock_present, anchorage_depth_meters, artefact_metadata)
VALUES
(1, 4, 'Arabian Sea / Narmada Gulf of Khambhat', 'Estuarine', true, 11.50,
 '{"pilot_boats": "Local fishermen government pilots guided foreign Yavana galleys past sandbanks", "classical_source": "Periplus, Section 44"}'),

(2, 5, 'Arabian Sea / Periyar River Lagoon', 'Maritime', false, 8.20,
 '{"anchorage_method": "Roadstead anchorage; cargo unloaded via light river craft called lighters", "classical_source": "Pliny Natural History 6.26"}'),

(3, 6, 'Bay of Bengal / Rupnarayan River', 'Estuarine', true, 9.80,
 '{"monsoon_sailings": "Winter northeast monsoon sailings to Suvarnabhumi (Southeast Asia)", "classical_source": "Records of Faxian"}'),

(4, 7, 'Bay of Bengal / Kaveri River Delta', 'Maritime', true, 12.00,
 '{"harbour_features": "Stone pier lighthouses (Kalan-karai-vilakku) and timber cargo warehouses", "classical_source": "Pattinappalai & Manimekalai"}');

-- ----------------------------------------------------------------------------
-- 5. Trade Routes (4 rows)
-- ----------------------------------------------------------------------------
INSERT INTO trade_routes (route_id, route_name, route_type, active_era_start, active_era_end, terrain_description, primary_transport_mode, artefact_metadata)
VALUES
(1, 'Uttarapatha (Great Northern Trans-Continental Highway)', 'Land', -600, 1200, 
 'Stretches across Indo-Gangetic alluvium from Gandharan mountain passes through fertile plains along Yamuna and Ganga to the Bay of Bengal.', 
 'Ox-cart Caravans, Pack-horses & River Barges',
 '{"historical_predecessor": "Proto-historic Vedic trail transformed by Chandragupta Maurya and later modernized as Grand Trunk Road", "rest_houses": "Sarai network, distance markers (kos minars)"}'),

(2, 'Dakshinapatha (Great Southern Imperial Trade Highway)', 'Land', -500, 1000, 
 'Traverses Vindhya and Satpura mountain defiles into the Deccan plateau basalt plains, connecting northern Gangetic cities with peninsular peninsulas and western ports.',
 'Pack-bullocks, Hand-drawn litters & Caravan Carts',
 '{"mountain_passes": "Narmada river crossings and Thal/Bhor Ghat trails", "patronage": "Satavahana and Vakataka epigraphs"}'),

(3, 'Western Maritime Spice Route (Malabar-Gujarat Sea Lane)', 'Maritime', -300, 1100, 
 'Coastal navigation corridor along the Arabian Sea connecting Malabar pepper ports (Muziris) northward to Barygaza and western Persian Gulf/Red Sea networks.',
 'Sewn-plank Timber Galleys (Dhows / Kattu-maram)',
 '{"wind_dependence": "Hippalus South-West Monsoon (Summer) and North-East Monsoon (Winter)", "patronage": "Satavahana, Western Kshatrapas and Roman merchants"}'),

(4, 'Bay of Bengal Maritime Route (Kalinga-Chola Sea Corridor)', 'Maritime', -300, 1200, 
 'High-seas maritime circuit connecting Tamil and Bengali ports (Kaveripattinam, Tamralipti) to Sri Lanka and eastward to the Straits of Malacca.',
 'Multi-decked Ocean Galleys (Sangara and Colandia)',
 '{"naval_expeditions": "Rajendra Chola maritime campaigns", "trade_guilds": "Ayyavole 500, Manigramam, Nanadesi"}');

-- ----------------------------------------------------------------------------
-- 6. Commodities (8 rows)
-- ----------------------------------------------------------------------------
INSERT INTO commodities (commodity_id, commodity_name, category, origin_region, perishability, standard_trade_unit, artefact_metadata)
VALUES
(1, 'Malabar Black Pepper (Black Gold)', 'Spices', 'Malabar Coast (Kerala)', 'Low', 'Sack (approx. 50 kg)', 
 '{"latin_name": "Piper nigrum", "roman_valuation": "Worth its weight in silver; demanded as ransom by Alaric the Visigoth during the sack of Rome"}'),

(2, 'Bengal Muslin (Gangetica)', 'Textiles', 'Gangetic Delta (Vanga / Bengal)', 'Low', 'Bolt / Roll of gossamer fabric',
 '{"classical_praise": "Described in Periplus as so light that whole dresses could pass through a signet ring", "greek_term": "Gangitikon"}'),

(3, 'Gandhara Lapis Lazuli', 'Minerals & Gems', 'Badakhshan / Hindu Kush Foothills', 'Low', 'Rough stone talent',
 '{"pigment_use": "Raw pigment for ultramarine temple frescoes in Ajanta and Buddhist manuscripts"}'),

(4, 'Silk (Kauseya / Chinapatta)', 'Textiles', 'Trans-Himalayan / Gangetic weaving centers', 'Low', 'Standard Silk Bolt',
 '{"sanskrit_etymology": "Kauseya (wild tussar silk) and Chinapatta (imported Chinese raw yarn woven in Varanasi)"}'),

(5, 'Roman Gold Bullion & Denarii', 'Precious Metals', 'Mediterranean / Roman Empire', 'Low', 'Denarius / Aureus coin sacks',
 '{"hoards": "Dozens of hoards discovered across Tamil Nadu, Karnataka and Kerala with defaced imperial busts to prevent re-export"}'),

(6, 'Gulf of Mannar Pearls', 'Minerals & Gems', 'Coromandel / Gulf of Mannar Coast', 'Low', 'String / Carat pouch',
 '{"pliny_lament": "Pliny lamented Rome draining over 50 million sesterces annually for Indian pearls and luxury spices"}'),

(7, 'Malabar Cardamom & Cinnamon', 'Spices', 'Western Ghats Cardamom Hills', 'Medium', 'Woven cane hamper',
 '{"ayurvedic_classification": "Tridosha balancing spice, key pharmaceutical export to Alexandria"}'),

(8, 'Gujarat Agate & Carnelian Beads', 'Minerals & Gems', 'Ratanpur (Narmada Basin, Gujarat)', 'Low', 'Polished bead strings',
 '{"manufacturing_hub": "Specialized workshops at Vallabhi and Barygaza exported beads as far as Egypt and Mesopotamia"}');

-- ----------------------------------------------------------------------------
-- 7. Currencies (5 rows)
-- ----------------------------------------------------------------------------
INSERT INTO currencies (currency_id, currency_name, metal_type, kingdom_id, weight_grams, circulation_era, denomination_standard, artefact_metadata)
VALUES
(1, 'Silver Punch-Marked Karshapana (Pana)', 'Silver', 1, 3.40, '4th - 2nd Century BCE', 'Vimshatika / Karshapana standard (32 rattis)',
 '{"obverse_symbols": ["Sun", "Six-arm symbol (Shadarachakra)", "Hill with crescent", "Peacock on hill"], "reverse_symbols": ["Taxila mark", "Caduceus-like mark"], "manufacturing_technique": "Hammered planchet with multiple punches", "image_url": "/static/images/coins/karshapana.svg"}'),

(2, 'Gupta Gold Dinar (Archer Type of Chandragupta II)', 'Gold', 2, 8.10, '4th - 5th Century CE', 'Suvarna standard (approx. 120-124 grains)',
 '{"obverse_symbols": ["King standing left holding bow and arrow", "Garuda banner (Garudadhvaja) on left", "Brahmi legend: Deva Sri Maharajadhiraja"], "reverse_symbols": ["Goddess Lakshmi seated on lotus holding pasham and lotus", "Brahmi legend: Sri Vikramah"], "image_url": "/static/images/coins/gupta_dinar.svg"}'),

(3, 'Satavahana Lead Ship Coin (Vasisthiputra Pulumavi)', 'Lead', 3, 7.80, '2nd Century CE', 'Karshapana unit',
 '{"obverse_symbols": ["Two-masted sailing ship rigged with oars and anchor", "Brahmi legend: Siri Pulumavisa"], "reverse_symbols": ["Ujjain four-orbed symbol", "Swastika and taurine emblems"], "image_url": "/static/images/coins/satavahana_lead.svg"}'),

(4, 'Kushan Gold Dinar (Kanishka I - Buddha Type)', 'Gold', 4, 7.95, '2nd Century CE', 'Attic / Kushan Gold Dinar',
 '{"obverse_symbols": ["King Kanishka standing left sacrificing at altar", "Bactrian script legend: Shaonanoshao Kanishki Koshano"], "reverse_symbols": ["Buddha standing facing forward with right hand in Abhaya Mudra", "Greek/Bactrian legend: BODDO"], "image_url": "/static/images/coins/kushan_dinar.svg"}'),

(5, 'Imperial Chola Gold Kasu (Rajaraja I)', 'Gold', 5, 4.30, '10th - 11th Century CE', 'Kalanju / Kasu standard',
 '{"obverse_symbols": ["King standing right holding flower above fire altar", "Crescent moon and solar disc"], "reverse_symbols": ["Seated king holding conch shell", "Nagari legend: Sri Raja Raja"], "image_url": "/static/images/coins/chola_kasu.svg"}');

-- ----------------------------------------------------------------------------
-- 8. Travellers (4 rows)
-- ----------------------------------------------------------------------------
INSERT INTO travellers (traveller_id, traveller_name, origin_country, travel_period, profession, chronicle_title, artefact_metadata)
VALUES
(1, 'Megasthenes', 'Seleucid Empire (Ionia / Greece)', '302 BCE – 298 BCE', 'Diplomatic Ambassador & Geographer', 'Indica',
 '{"embassy_to": "Court of Chandragupta Maurya at Pataliputra", "observations": ["Description of seven caste-like classes", "Absence of chattel slavery", "Organization of Pataliputra city municipal boards"]}'),

(2, 'Faxian (Fa-Hien)', 'Jin Dynasty (China)', '399 CE – 412 CE', 'Buddhist Monk & Vinaya Scholar', 'A Record of Buddhist Kingdoms (Gaoseng Faxian Zhuan)',
 '{"mission": "Procure authentic copies of the Buddhist Monastic Code (Vinaya Pitaka)", "travel_mode": "Overland via Gobi desert and Khyber Pass, return by sea via Tamralipti and Java", "impressions": "Praised peace and security under Chandragupta II Vikramaditya"}'),

(3, 'Xuanzang (Hiuen Tsang)', 'Tang Dynasty (China)', '629 CE – 645 CE', 'Buddhist Scholar, Pilgrim & Translator', 'Great Tang Records on the Western Regions (Da Tang Xi You Ji)',
 '{"mission": "Deep study at Nalanda Mahavihara under Abbot Silabhadra", "patronage": "King Harshavardhana of Kannauj and King Bhaskaravarman of Kamarupa", "translation_legacy": "Brought back 657 Sanskrit texts in 520 bundles on 22 horses"}'),

(4, 'Adi Shankaracharya', 'Kalady (Kerala, India)', 'c. 788 CE – 820 CE', 'Philosopher, Reformer & Sanatana Dharma Acharya', 'Brahmasutra Bhashya & Upadeshasahasri',
 '{"mission": "Advaita Vedanta digvijaya (all-India philosophical discourse) establishing four Amnaya Mathas", "four_mathas": ["Sringeri (South)", "Dvaraka (West)", "Puri (East)", "Joshimath (North)"], "unification": "Unified Indian sacred geography and pilgrim circuits"}');

-- ----------------------------------------------------------------------------
-- 9. Cultural Exchanges (5 rows)
-- ----------------------------------------------------------------------------
INSERT INTO cultural_exchanges (exchange_id, exchange_title, category, origin_city_id, destination_city_id, period, description, artefact_metadata)
VALUES
(1, 'Transmission of Buddhist Philosophical Texts to China', 'Philosophy', 2, 1, '4th - 7th Century CE',
 'Nalanda and Pataliputra scholars copied Mahayana and Yogachara manuscripts on birch bark and palm leaf, carried across Taxila to Chang''an.',
 '{"key_texts": ["Madhyamaka Karika", "Yogacharabhumi", "Prajnaparamita"], "script": "Siddham / Brahmi", "translator": "Kumarajiva & Xuanzang"}'),

(2, 'Greco-Buddhist Hybrid Sculptural Style (Gandhara Art)', 'Art', 1, 8, '1st - 3rd Century CE',
 'Gandharan artists synthesized Hellenistic drapery, wavy hair, and realistic musculature with Indian Buddhist iconography, diffusing through Mathura.',
 '{"medium": "Grey schist in Taxila, transitioned to red Sikri sandstone in Mathura", "canonical_form": "Emergence of anthropomorphic Buddha representation"}'),

(3, 'Maritime Dissemination of Grantha Script & Temple Architecture', 'Architecture', 7, 6, '7th - 10th Century CE',
 'Pallava and Chola architectural canons (Shilpa Shastras) and Grantha scripts diffused to Southeast Asia and Bengal coastlines.',
 '{"epigraphy": "Origin of Old Javanese and Khmer scripts from Southern Brahmi/Grantha", "temple_models": "Dravidian vimana prototypes"}'),

(4, 'Surya Siddhanta Astronomical Computations & Prime Meridian', 'Science', 3, 2, '5th - 6th Century CE',
 'Astronomical calculations developed at Ujjayini (zero meridian) integrated into Aryabhata''s work at Kusumapura (Pataliputra).',
 '{"discoveries": ["Heliocentric hints", "Calculation of Earth circumference", "Decimal place value with zero"], "author": "Aryabhata & Varahamihira"}'),

(5, 'Ayurvedic Botanical Knowledge Exchange & Herb Trade', 'Science', 5, 4, '1st - 4th Century CE',
 'Malabar spice gatherers and physicians documented herbal remedies that were systematized into Charaka Samhita and exported through Barygaza.',
 '{"herbs": ["Black Pepper (Maricha)", "Cardamom (Ela)", "Ginger (Ardraka)", "Long Pepper (Pippali)"], "pharmacopoeia": "Exported to Roman Alexandria"}');

-- ----------------------------------------------------------------------------
-- 10. Route Cities (Junction - 15 stops across 4 routes)
-- ----------------------------------------------------------------------------
-- Route 1: Uttarapatha (Taxila -> Mathura -> Pataliputra -> Tamralipti)
INSERT INTO route_cities (route_id, city_id, stop_order, distance_from_prev_km, estimated_travel_days) VALUES
(1, 1, 1, 0.00, 0),        -- Taxila
(1, 8, 2, 780.00, 26),     -- Mathura
(1, 2, 3, 620.00, 21),     -- Pataliputra
(1, 6, 4, 480.00, 16);     -- Tamralipti

-- Route 2: Dakshinapatha (Pataliputra -> Ujjayini -> Bhrigukachchha -> Muziris)
INSERT INTO route_cities (route_id, city_id, stop_order, distance_from_prev_km, estimated_travel_days) VALUES
(2, 2, 1, 0.00, 0),        -- Pataliputra
(2, 3, 2, 850.00, 28),     -- Ujjayini
(2, 4, 3, 340.00, 11),     -- Bhrigukachchha
(2, 5, 4, 1290.00, 43);    -- Muziris

-- Route 3: Western Maritime Spice Route (Bhrigukachchha -> Muziris -> Kaveripattinam)
INSERT INTO route_cities (route_id, city_id, stop_order, distance_from_prev_km, estimated_travel_days) VALUES
(3, 4, 1, 0.00, 0),        -- Bhrigukachchha
(3, 5, 2, 1350.00, 18),    -- Muziris
(3, 7, 3, 560.00, 8);      -- Kaveripattinam (Rounding Cape Comorin)

-- Route 4: Bay of Bengal Maritime Route (Kaveripattinam -> Tamralipti)
INSERT INTO route_cities (route_id, city_id, stop_order, distance_from_prev_km, estimated_travel_days) VALUES
(4, 7, 1, 0.00, 0),        -- Kaveripattinam
(4, 6, 2, 1420.00, 20);    -- Tamralipti

-- ----------------------------------------------------------------------------
-- 11. Route Commodities (Junction - 10 rows)
-- ----------------------------------------------------------------------------
INSERT INTO route_commodities (route_id, commodity_id, trade_direction, primary_source_id) VALUES
(1, 2, 'Export', 2),        -- Uttarapatha -> Muslin Cotton (Indica)
(1, 3, 'Import', 1),        -- Uttarapatha -> Lapis Lazuli (Arthashastra)
(1, 4, 'Transit', 4),       -- Uttarapatha -> Silk (Si-Yu-Ki)
(2, 8, 'Export', 1),        -- Dakshinapatha -> Agate & Carnelian Beads (Arthashastra)
(2, 1, 'Transit', 3),       -- Dakshinapatha -> Black Pepper (Periplus)
(3, 1, 'Export', 3),        -- Western Maritime -> Black Pepper (Periplus)
(3, 5, 'Import', 3),        -- Western Maritime -> Roman Gold Bullion (Periplus)
(3, 7, 'Export', 3),        -- Western Maritime -> Cardamom (Periplus)
(4, 6, 'Export', 5),        -- Bay of Bengal -> Pearls (Ashokan Edicts)
(4, 2, 'Transit', 4);       -- Bay of Bengal -> Muslin (Si-Yu-Ki)

-- ----------------------------------------------------------------------------
-- 12. Kingdom City Control (Junction - 10 rows)
-- ----------------------------------------------------------------------------
INSERT INTO kingdom_city_control (kingdom_id, city_id, control_start_year, control_end_year, tribute_details) VALUES
(1, 2, -322, -185, 'Imperial capital seat with direct imperial council administration'),
(1, 1, -320, -190, 'Administered by Royal Kumara (Princes such as Ashoka as Viceroy)'),
(1, 3, -315, -185, 'Viceroyalty seat of Avantiratha under Prince Ashoka'),
(2, 2, 320, 500, 'Imperial seat of Chandragupta I and Samudragupta'),
(2, 3, 380, 520, 'Second imperial capital under Chandragupta II Vikramaditya'),
(3, 4, -100, 150, 'Major western gateway customs house under Gautamiputra Satakarni'),
(4, 1, 60, 240, 'Winter administrative center and mint city of Kushan Emperors'),
(4, 8, 70, 250, 'Southern imperial capital and primary sculptural center of Kushans'),
(5, 7, 850, 1250, 'Principal Chola naval port and custom toll station'),
(3, 5, -50, 180, 'Allied maritime trading enclave under Chera-Satavahana pact');

-- ----------------------------------------------------------------------------
-- 13. Traveller Stops (Junction - 12 rows)
-- ----------------------------------------------------------------------------
-- Megasthenes
INSERT INTO traveller_stops (traveller_id, visit_order, city_id, route_id, recorded_observation, pramana_source_id) VALUES
(1, 1, 1, 1, 'Entered Punjab through Gandhara, recorded the fortified Greek and Indian settlements at Taxila.', 2),
(1, 2, 8, 1, 'Witnessed flourishing Krishna-Herakles worship along the Yamuna at Mathura.', 2),
(1, 3, 2, 1, 'Arrived at the Mauryan court in Pataliputra; described the royal audience and elephant processions.', 2);

-- Faxian
INSERT INTO traveller_stops (traveller_id, visit_order, city_id, route_id, recorded_observation, pramana_source_id) VALUES
(2, 1, 8, 1, 'Observed numerous Buddhist monasteries with thousands of resident sangha members on the Yamuna.', 4),
(2, 2, 2, 1, 'Spent three years in Pataliputra transcribing Vinaya rules; visited Ashoka’s legendary stone palace.', 4),
(2, 3, 6, 1, 'Spent two years at Tamralipti painting Buddhist images and copying sacred sutras before embarking by sea.', 4);

-- Xuanzang
INSERT INTO traveller_stops (traveller_id, visit_order, city_id, route_id, recorded_observation, pramana_source_id) VALUES
(3, 1, 1, 1, 'Explored Taxila stupas and lamented the decline of monasteries since the Hephthalite incursions.', 4),
(3, 2, 8, 1, 'Recorded five or six stupas built by Ashoka and observed five hundred monks of Mahayana & Hinayana.', 4),
(3, 3, 2, 1, 'Visited the ruins of ancient Pataliputra and proceeded to Nalanda Mahavihara for advanced dialectics.', 4);

-- Adi Shankaracharya
INSERT INTO traveller_stops (traveller_id, visit_order, city_id, route_id, recorded_observation, pramana_source_id) VALUES
(4, 1, 5, 3, 'Began digvijaya from Kalady near Muziris, expounding Advaita non-duality.', 1),
(4, 2, 3, 2, 'Debated scholars at Ujjayini, establishing the supremacy of Vedic non-dual philosophy.', 1),
(4, 3, 2, 2, 'Visited Magadha centers of learning, revitalizing temple traditions and establishing monastic orders.', 1);
