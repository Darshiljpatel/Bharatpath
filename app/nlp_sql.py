"""
Vak-to-SQL: a rule-based English-to-SQL translator for the BharatPath schema.

No AI model and no internet are used. The translation works in five steps:

1. TARGET   - words such as "coins", "ports" or "kingdoms" decide which table is listed.
2. NAMES    - every other word is looked up in the real data (kingdom names, city names,
              commodities, routes, travellers, ...). Matches become WHERE ... IN (...) filters.
3. ATTRIBUTES - descriptive words (gold, maritime, spice, western, buddhist, religious, ...)
              become WHERE column LIKE '%value%' filters.
4. JOINS    - for every filter the cheapest foreign-key path from the target table is found
              in a join graph that mirrors the ER diagram (Dijkstra), and the JOINs are added.
5. MODIFIERS - "how many", "per <entity>", "before/after <year>", "oldest", "latest", "top N".

The generated SQL is plain, read-only SELECT that runs on PostgreSQL and (via the existing
ILIKE -> LIKE conversion in app/db.py) on the SQLite development database.
"""
import re
import time
import heapq

# --------------------------------------------------------------------------- schema metadata
TABLES = {
    'currencies': dict(alias='cur', pk='currency_id', label='coins (currencies)',
                       cols=['currency_id', 'coin_name', 'metal', 'start_year', 'end_year', 'weight_standard'],
                       name_cols=['coin_name'], year='start_year_num',
                       words=['coin', 'coins', 'currency', 'currencies', 'coinage', 'money']),
    'ports': dict(alias='p', pk='port_id', label='ports',
                  cols=['port_id', 'port_name', 'present_day_location', 'coast', 'port_type'],
                  name_cols=['port_name'], year=None,
                  words=['port', 'ports', 'harbour', 'harbours', 'harbor', 'harbors', 'seaport', 'seaports']),
    'cities': dict(alias='c', pk='city_id', label='cities',
                   cols=['city_id', 'ancient_name', 'modern_name', 'present_day_state', 'city_type'],
                   name_cols=['ancient_name', 'modern_name'], year=None,
                   words=['city', 'cities', 'town', 'towns', 'place', 'places']),
    'kingdoms': dict(alias='k', pk='kingdom_id', label='kingdoms',
                     cols=['kingdom_id', 'kingdom_name', 'polity_type', 'start_year', 'end_year', 'notable_ruler'],
                     name_cols=['kingdom_name'], year='start_year_num',
                     words=['kingdom', 'kingdoms', 'dynasty', 'dynasties', 'empire', 'empires', 'ruler',
                            'rulers', 'sultanate', 'sultanates', 'polity', 'polities']),
    'trade_routes': dict(alias='tr', pk='route_id', label='trade routes',
                         cols=['route_id', 'route_name', 'route_type', 'start_year', 'end_year'],
                         name_cols=['route_name'], year='start_year_num',
                         words=['route', 'routes', 'road', 'roads', 'highway', 'highways', 'corridor', 'corridors']),
    'commodities': dict(alias='cm', pk='commodity_id', label='commodities',
                        cols=['commodity_id', 'commodity_name', 'category', 'primary_source_area', 'trade_direction'],
                        name_cols=['commodity_name'], year=None,
                        words=['commodity', 'commodities', 'goods', 'good', 'item', 'items', 'product', 'products']),
    'travellers': dict(alias='tv', pk='traveller_id', label='travellers',
                       cols=['traveller_id', 'traveller_name', 'homeland', 'role', 'arrival_year', 'account_title'],
                       name_cols=['traveller_name'], year='arrival_year_num',
                       words=['traveller', 'travellers', 'traveler', 'travelers', 'visitor', 'visitors',
                              'pilgrim', 'pilgrims', 'chronicler', 'chroniclers']),
    'regions': dict(alias='r', pk='region_id', label='regions',
                    cols=['region_id', 'region_name', 'present_day_area', 'present_day_country'],
                    name_cols=['region_name'], year=None,
                    words=['region', 'regions', 'area', 'areas']),
    'historical_periods': dict(alias='hp', pk='period_id', label='historical periods',
                               cols=['period_id', 'period_name', 'era', 'start_year', 'end_year'],
                               name_cols=['period_name'], year='start_year_num',
                               words=['period', 'periods', 'era', 'eras', 'epoch', 'epochs']),
    'cultural_exchanges': dict(alias='ce', pk='exchange_id', label='cultural exchanges',
                               cols=['exchange_id', 'exchange_name', 'exchange_type', 'start_year', 'end_year'],
                               name_cols=['exchange_name'], year='start_year_num',
                               words=['exchange', 'exchanges', 'cultural', 'culture', 'influence', 'influences']),
    'sources': dict(alias='src', pk='source_id', label='sources',
                    cols=['source_id', 'title', 'author_or_editor', 'source_type', 'publication_year'],
                    name_cols=[], year=None,
                    words=['source', 'sources', 'book', 'books', 'reference', 'references', 'bibliography']),
}
JUNCTIONS = {'route_city': 'rc', 'route_commodity': 'rcm'}
ALIAS_TABLE = {m['alias']: t for t, m in TABLES.items()}
ALIAS_TABLE.update({a: t for t, a in JUNCTIONS.items()})

# Tie-break when one word matches names in several tables (lower = preferred).
PRIORITY = ['kingdoms', 'cities', 'ports', 'commodities', 'trade_routes', 'travellers',
            'regions', 'cultural_exchanges', 'historical_periods', 'currencies', 'sources']

# Foreign-key join graph (mirrors the ER diagram). Cost decides which path is preferred:
# joins through historical_periods only mean "same era", so they are made expensive.
EDGES = [
    ('c', 'r', 'c.region_id = r.region_id', 1),                          # LOCATED_IN
    ('k', 'r', 'k.region_id = r.region_id', 1),                          # RULED_IN
    ('p', 'c', 'p.city_id = c.city_id', 1),                              # SERVES
    ('cur', 'k', 'cur.issuing_kingdom_id = k.kingdom_id', 1),            # ISSUED_BY
    ('tv', 'k', 'tv.kingdom_visited_id = k.kingdom_id', 1),              # VISITED_KINGDOM
    ('tv', 'c', 'tv.main_city_visited_id = c.city_id', 1),               # VISITED_CITY
    ('tr', 'rc', 'rc.route_id = tr.route_id', 0.5),                      # PASSES_THROUGH (M:N)
    ('rc', 'c', 'rc.city_id = c.city_id', 0.5),
    ('tr', 'rcm', 'rcm.route_id = tr.route_id', 0.5),                    # CARRIES (M:N)
    ('rcm', 'cm', 'rcm.commodity_id = cm.commodity_id', 0.5),
    ('ce', 'r', '(ce.from_region_id = r.region_id OR ce.to_region_id = r.region_id)', 1),  # ORIGINATES_IN / REACHES
    ('c', 'hp', 'c.period_id = hp.period_id', 3),                        # FLOURISHED_IN
    ('k', 'hp', 'k.period_id = hp.period_id', 3),                        # BELONGS_TO
    ('p', 'hp', 'p.period_id = hp.period_id', 3),                        # ACTIVE_IN
    ('tr', 'hp', 'tr.period_id = hp.period_id', 3),                      # DATED_TO
    ('cur', 'hp', 'cur.period_id = hp.period_id', 3),                    # CIRCULATED_IN
    ('tv', 'hp', 'tv.period_id = hp.period_id', 3),                      # TRAVELLED_IN
    ('ce', 'hp', 'ce.period_id = hp.period_id', 3),                      # OCCURRED_IN
]
CAPITAL_EDGE = ('c', 'k', 'k.capital_city_id = c.city_id', 0.1)         # HAS_CAPITAL (only on "capital")

# Descriptive words -> (table, column, LIKE pattern, required context)
# context 'coin' / 'port': only applied when coins / ports are part of the question,
# otherwise the word is treated as a name (e.g. "copper" the commodity).
ATTRIBUTES = {}
def _attr(words, table, column, pattern, context=None):
    for w in words:
        ATTRIBUTES[w] = (table, column, pattern, context)

_attr(['gold', 'golden'], 'currencies', 'metal', 'gold', 'coin')
_attr(['silver'], 'currencies', 'metal', 'silver', 'coin')
_attr(['copper'], 'currencies', 'metal', 'copper', 'coin')
_attr(['lead', 'potin'], 'currencies', 'metal', 'lead', 'coin')
_attr(['billon'], 'currencies', 'metal', 'billon', 'coin')
_attr(['brass'], 'currencies', 'metal', 'brass', 'coin')
_attr(['shell', 'cowrie'], 'currencies', 'metal', 'shell', 'coin')
_attr(['maritime', 'sea', 'ocean', 'naval', 'oceanic'], 'trade_routes', 'route_type', 'maritime')
_attr(['overland', 'land'], 'trade_routes', 'route_type', 'overland')
_attr(['riverine', 'river'], 'trade_routes', 'route_type', 'riverine')
_attr(['mountain'], 'trade_routes', 'route_type', 'mountain')
_attr(['west', 'western'], 'ports', 'coast', 'west', 'port')
_attr(['east', 'eastern'], 'ports', 'coast', 'east', 'port')
_attr(['southwest', 'southwestern'], 'ports', 'coast', 'southwest', 'port')
_attr(['southeast', 'southeastern'], 'ports', 'coast', 'southeast', 'port')
_attr(['malabar'], 'ports', 'coast', 'malabar', 'port')
_attr(['coromandel'], 'ports', 'coast', 'coromandel', 'port')
_attr(['konkan'], 'ports', 'coast', 'konkan', 'port')
_attr(['spice', 'spices', 'spicy'], 'commodities', 'category', 'spice')
_attr(['textile', 'textiles', 'cloth', 'fabric', 'fabrics'], 'commodities', 'category', 'textile')
_attr(['gem', 'gems', 'gemstone', 'gemstones', 'jewel', 'jewels'], 'commodities', 'category', 'gem')
_attr(['aromatic', 'aromatics', 'perfume', 'perfumes', 'incense'], 'commodities', 'category', 'aromatic')
_attr(['food', 'foods', 'grain', 'grains'], 'commodities', 'category', 'food')
_attr(['dye', 'dyes'], 'commodities', 'category', 'dye')
_attr(['ceramic', 'ceramics', 'pottery'], 'commodities', 'category', 'ceramic')
_attr(['metal', 'metals'], 'commodities', 'category', 'metal')
_attr(['export', 'exports', 'exported', 'exporting'], 'commodities', 'trade_direction', 'export')
_attr(['import', 'imports', 'imported', 'importing'], 'commodities', 'trade_direction', 'import')
_attr(['religious', 'religion'], 'cultural_exchanges', 'exchange_type', 'religious')
_attr(['artistic', 'art'], 'cultural_exchanges', 'exchange_type', 'artistic')
_attr(['architectural', 'architecture'], 'cultural_exchanges', 'exchange_type', 'architectural')
_attr(['scientific', 'science'], 'cultural_exchanges', 'exchange_type', 'scientific')
_attr(['commercial'], 'cultural_exchanges', 'exchange_type', 'commercial')
_attr(['linguistic', 'language', 'languages', 'script'], 'cultural_exchanges', 'exchange_type', 'linguistic')
_attr(['philosophical', 'philosophy'], 'cultural_exchanges', 'exchange_type', 'philosophical')
_attr(['diplomatic', 'diplomacy'], 'cultural_exchanges', 'exchange_type', 'diplomatic')
_attr(['educational', 'education'], 'cultural_exchanges', 'exchange_type', 'educational')
_attr(['technological', 'technology'], 'cultural_exchanges', 'exchange_type', 'technological')
_attr(['literary', 'literature', 'music', 'musical'], 'cultural_exchanges', 'exchange_type', 'literary')
_attr(['military'], 'cultural_exchanges', 'exchange_type', 'military')
_attr(['agricultural', 'agriculture', 'crop', 'crops'], 'cultural_exchanges', 'exchange_type', 'agricultural')
_attr(['buddhist', 'monk', 'monks'], 'travellers', 'role', 'buddhist')
_attr(['merchant', 'merchants'], 'travellers', 'role', 'merchant')
_attr(['ambassador', 'ambassadors'], 'travellers', 'role', 'ambassador')
_attr(['envoy', 'envoys'], 'travellers', 'role', 'envoy')
_attr(['scholar', 'scholars'], 'travellers', 'role', 'scholar')
_attr(['ancient'], 'historical_periods', 'era', 'ancient')
_attr(['medieval'], 'historical_periods', 'era', 'medieval')

STOPWORDS = set("""
a an the of in on at by from to for with and or not no is are was were be been being do does did
which what who whom whose where when why how show list give get find display fetch tell me us about
all any some each every per many much more most less few one this that these those their there its it
under along through via between during within into onto over across near around than then also only
please name names details detail info information data record records table rows
issued issue issues ruled rule rules traded trade trading trades visited visit visits located lie lies
passing passes pass passed connected connect connects carried carry carries carrying linked link
start starts started starting end ends ended ending have has had made make used use known famous
major main important biggest big large small old new early later imperial great age dynasty empire
kingdom period road route sea river corridor valley country coast delta plateau doab state india indian
identification debated historical historic count total number oldest earliest latest newest recent first last top before after
since until till
""".split())

# --------------------------------------------------------------------------- helpers
def _norm(word):
    w = word.lower()
    if w.endswith("'s"):
        w = w[:-2]
    if len(w) > 4 and w.endswith('ies'):
        return w[:-3] + 'y'
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'):
        return w[:-1]
    return w

def _tokens(text):
    return [t for t in re.split(r"[^a-z0-9']+", text.lower()) if t]

def _words_match(a, b):
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 5 and long_.startswith(short)

def _q(value):
    return "'" + str(value).replace("'", "''") + "'"

TARGET_WORDS = {}
for _t, _m in TABLES.items():
    for _w in _m['words']:
        TARGET_WORDS[_w] = _t
        TARGET_WORDS[_norm(_w)] = _t
IGNORED_NAME_WORDS = STOPWORDS | set(TARGET_WORDS) | {_norm(w) for w in STOPWORDS}

# --------------------------------------------------------------------------- vocabulary from the database
_VOCAB = {'rows': None, 'loaded_at': 0.0}

def _load_vocabulary(execute_query):
    """Read every name from the database once a minute: {table: [(display_name, set_of_words)]}."""
    if _VOCAB['rows'] is not None and time.time() - _VOCAB['loaded_at'] < 60:
        return _VOCAB['rows']
    vocab = {}
    for table, meta in TABLES.items():
        if not meta['name_cols']:
            continue
        res = execute_query(f"SELECT {', '.join(meta['name_cols'])} FROM {table};")
        entries = []
        for row in res['data']:
            words = set()
            for col in meta['name_cols']:
                for tok in _tokens(str(row.get(col) or '')):
                    n = _norm(tok)
                    if len(n) >= 3 and n not in IGNORED_NAME_WORDS and not n.isdigit():
                        words.add(n)
            entries.append((row[meta['name_cols'][0]], words))
        vocab[table] = entries
    _VOCAB.update(rows=vocab, loaded_at=time.time())
    return vocab

# --------------------------------------------------------------------------- join planning
def _shortest_paths(start, use_capital):
    edges = EDGES + ([CAPITAL_EDGE] if use_capital else [])
    graph = {}
    for a, b, cond, cost in edges:
        graph.setdefault(a, []).append((b, cond, cost))
        graph.setdefault(b, []).append((a, cond, cost))
    dist, parent = {start: 0}, {start: None}
    heap = [(0, start)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist[node]:
            continue
        for nxt, cond, cost in graph.get(node, []):
            nd = d + cost
            if nd < dist.get(nxt, 1e9):
                dist[nxt], parent[nxt] = nd, (node, cond)
                heapq.heappush(heap, (nd, nxt))
    return dist, parent

def _join_clauses(target_alias, needed_aliases, parent, dist):
    nodes = set()
    for alias in needed_aliases:
        while alias is not None and alias != target_alias:
            nodes.add(alias)
            alias = parent[alias][0] if parent.get(alias) else None
    clauses = []
    for alias in sorted(nodes, key=lambda a: dist[a]):
        clauses.append(f"JOIN {ALIAS_TABLE[alias]} {alias} ON {parent[alias][1]}")
    return clauses

# --------------------------------------------------------------------------- main entry point
class NotUnderstood(Exception):
    pass

def translate(question, execute_query):
    """Return (sql, explanation). Raises NotUnderstood when no table/name could be recognised."""
    raw = question.lower()
    toks = _tokens(raw)
    norm_toks = [_norm(t) for t in toks]

    # ---- modifiers
    want_count = bool(re.search(r"\bhow many\b|\bcount\b|\bnumber of\b|\btotal\b", raw))
    limit = None
    m = re.search(r"\b(?:top|first|last)\s+(\d{1,3})\b", raw)
    if m:
        limit = int(m.group(1))
    order_dir = None
    if re.search(r"\b(oldest|earliest)\b", raw):
        order_dir = 'ASC'
    elif re.search(r"\b(latest|newest|most recent|recent)\b", raw):
        order_dir = 'DESC'
    year_filters = []
    for m in re.finditer(r"\b(before|after|since|until|till|by)\s+(\d{1,4})\s*(bce|bc|ce|ad)?\b", raw):
        year = int(m.group(2)) * (-1 if m.group(3) in ('bc', 'bce') else 1)
        year_filters.append(('<' if m.group(1) in ('before', 'until', 'till', 'by') else '>', year, m.group(0)))
    year_words = {w for _, _, phrase in year_filters for w in _tokens(phrase)}

    # ---- target table(s): first table word wins, later ones are "related" tables
    target_order = []
    for t in toks:
        table = TARGET_WORDS.get(t) or TARGET_WORDS.get(_norm(t))
        if table and table not in target_order:
            target_order.append(table)
    coin_ctx = 'currencies' in target_order
    port_ctx = 'ports' in target_order
    use_capital = 'capital' in norm_toks

    # ---- attribute words
    attr_filters = {}          # table -> list of (column, pattern, word)
    used = set()
    for t, n in zip(toks, norm_toks):
        spec = ATTRIBUTES.get(t) or ATTRIBUTES.get(n)
        if not spec or t in year_words:
            continue
        table, column, pattern, ctx = spec
        if (ctx == 'coin' and not coin_ctx) or (ctx == 'port' and not port_ctx):
            continue
        if table == 'cities' and use_capital:
            continue
        attr_filters.setdefault(table, [])
        if (column, pattern) not in [(c, p) for c, p, _ in attr_filters[table]]:
            attr_filters[table].append((column, pattern, t))
        used.add(t)

    # ---- name words matched against the real data
    vocab = _load_vocabulary(execute_query)
    name_tokens = []
    for t, n in zip(toks, norm_toks):
        if t in used or t in year_words or n in IGNORED_NAME_WORDS or t in IGNORED_NAME_WORDS:
            continue
        if len(n) < 3 or n.isdigit() or t == 'capital':
            continue
        name_tokens.append(n)

    token_tables = {}          # token -> {table: True}
    for tok in name_tokens:
        for table, entries in vocab.items():
            if any(any(_words_match(tok, w) for w in words) for _, words in entries):
                token_tables.setdefault(tok, set()).add(table)

    # ---- a table word right after a name is part of that name ("Delhi Sultanate coins",
    # "Gupta Empire coins"), so it should not decide what is listed.
    demoted = set()
    for i, t in enumerate(toks):
        table = TARGET_WORDS.get(t) or TARGET_WORDS.get(_norm(t))
        if table and i > 0 and norm_toks[i - 1] in token_tables:
            demoted.add(table)
    for i, t in enumerate(toks):
        table = TARGET_WORDS.get(t) or TARGET_WORDS.get(_norm(t))
        if table and not (i > 0 and norm_toks[i - 1] in token_tables):
            demoted.discard(table)
    target_order = [t for t in target_order if t not in demoted] + [t for t in target_order if t in demoted]

    # ---- "capital of the Maurya Empire": the answer is a city, linked through HAS_CAPITAL
    kingdom_named = any('kingdoms' in tbs for tbs in token_tables.values())
    if use_capital and kingdom_named:
        if 'cities' not in target_order:
            target_order = ['cities'] + [t for t in target_order if t != 'kingdoms']
        else:
            target_order = [t for t in target_order if t != 'kingdoms']
    elif use_capital:
        attr_filters.setdefault('cities', []).append(('city_type', 'capital', 'capital'))
        use_capital = False

    # ---- decide the target if the question named none
    if target_order:
        target = target_order[0]
    elif token_tables:
        counts = {}
        for tables in token_tables.values():
            for tb in tables:
                counts[tb] = counts.get(tb, 0) + 1
        target = sorted(counts, key=lambda tb: (-counts[tb], PRIORITY.index(tb)))[0]
    elif attr_filters:
        target = next(iter(attr_filters))
    else:
        raise NotUnderstood()

    meta = TABLES[target]
    ta = meta['alias']
    dist, parent = _shortest_paths(ta, use_capital and target == 'cities')

    # ---- assign each name word to one table: a table the question itself mentions wins
    # ("Chola dynasty" -> kingdoms), then the usual meaning (PRIORITY), then the shortest join.
    assigned = {}
    for tok, tables in token_tables.items():
        best = sorted(tables, key=lambda tb: (tb not in target_order[1:], PRIORITY.index(tb),
                                              dist.get(TABLES[tb]['alias'], 99)))[0]
        assigned.setdefault(best, []).append(tok)
    name_filters = {}
    for table, toks_for_table in assigned.items():
        scored = []
        for display, words in vocab[table]:
            score = sum(1 for tok in toks_for_table if any(_words_match(tok, w) for w in words))
            if score:
                scored.append((score, display))
        top = max(s for s, _ in scored)
        name_filters[table] = sorted({d for s, d in scored if s == top})

    # ---- related tables mentioned by a second table word ("kingdoms that issued coins")
    group_table = None
    related = [t for t in target_order[1:] if t not in name_filters and t not in attr_filters]
    if want_count and related and re.search(r"\b(per|each|every|by|wise)\b", raw):
        group_table = related[0]

    # ---- build SQL
    filter_tables = set(name_filters) | set(attr_filters) | set(related)
    needed = [TABLES[t]['alias'] for t in filter_tables if t != target]
    joins = _join_clauses(ta, needed, parent, dist)
    where, explain = [], []
    for table, names in name_filters.items():
        alias = TABLES[table]['alias']
        col = TABLES[table]['name_cols'][0]
        where.append(f"{alias}.{col} IN ({', '.join(_q(n) for n in names)})")
        explain.append(f"{TABLES[table]['label']}: {', '.join(names)}")
    for table, specs in attr_filters.items():
        alias = TABLES[table]['alias']
        by_col = {}
        for column, pattern, word in specs:
            by_col.setdefault(column, []).append(pattern)
        for column, patterns in by_col.items():
            conds = [f"{alias}.{column} ILIKE {_q('%' + p + '%')}" for p in patterns]
            where.append(conds[0] if len(conds) == 1 else '(' + ' OR '.join(conds) + ')')
            explain.append(f"{table}.{column} contains {' / '.join(patterns)}")
    if year_filters:
        if meta['year']:
            for op, year, phrase in year_filters:
                where.append(f"{ta}.{meta['year']} {op} {year}")
                explain.append(f"year {phrase}")
        else:
            explain.append(f"(year filter ignored: {meta['label']} have no year column)")
    for t in related:
        if t != group_table:
            explain.append(f"linked to {TABLES[t]['label']}")

    distinct = bool(joins)
    from_sql = f"FROM {target} {ta}" + ''.join('\n' + j for j in joins)
    where_sql = ('\nWHERE ' + '\n  AND '.join(where)) if where else ''

    if group_table:
        g = TABLES[group_table]
        gcol = f"{g['alias']}.{g['name_cols'][0]}"
        sql = (f"SELECT {gcol}, COUNT(DISTINCT {ta}.{meta['pk']}) AS total_{target}\n{from_sql}{where_sql}"
               f"\nGROUP BY {gcol}\nORDER BY total_{target} DESC")
        explain.insert(0, f"count {meta['label']} per {g['label'][:-1] if g['label'].endswith('s') else g['label']}")
    elif want_count:
        sql = f"SELECT COUNT(DISTINCT {ta}.{meta['pk']}) AS total_{target}\n{from_sql}{where_sql}"
        explain.insert(0, f"count {meta['label']}")
    else:
        select = [f"{ta}.{c}" for c in meta['cols']]
        for table in list(name_filters) + list(attr_filters):
            if table != target and TABLES[table]['name_cols']:
                col = f"{TABLES[table]['alias']}.{TABLES[table]['name_cols'][0]}"
                if col not in select:
                    select.append(col)
        order = f"{ta}.{meta['name_cols'][0] if meta['name_cols'] else meta['cols'][1]}"
        if target == 'cities' and 'trade_routes' in name_filters and len(name_filters['trade_routes']) == 1:
            select.insert(0, 'rc.stop_sequence')
            order = 'rc.stop_sequence'
        if order_dir and meta['year']:
            year_col = f"{ta}.{meta['year']}"
            if year_col not in select:
                select.append(year_col)
            order = f"{year_col} {order_dir}"
            explain.append('oldest first' if order_dir == 'ASC' else 'latest first')
        elif order_dir:
            explain.append(f"(cannot sort {meta['label']} by date)")
        sql = (f"SELECT {'DISTINCT ' if distinct else ''}{', '.join(select)}\n{from_sql}{where_sql}"
               f"\nORDER BY {order}")
        explain.insert(0, f"list {meta['label']}")
    if limit:
        sql += f"\nLIMIT {limit}"
        explain.append(f"first {limit} rows")
    return sql + ';', ' | '.join(explain)
