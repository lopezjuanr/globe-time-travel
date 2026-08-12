"""Generate the compact country-boundary payload embedded in time-travel.html.

Source: Natural Earth 110m admin-0 countries (public domain).
Output: /tmp/country_data.js  -- a single `const COUNTRY_DATA = [...]` line.

Format per entry: ["Name", [ [ [ [lon,lat], ... outer ], [ ...hole ] ], ...polys ] ]
"""
import gzip
import json
import os

SRC = '/tmp/ne110.json'
OUT = '/tmp/country_data.js'
TOL = 0.12          # simplification tolerance in degrees
DECIMALS = 3        # coordinate rounding
MIN_AREA = 0.002    # drop outer rings smaller than this (sq. degrees)

# Natural Earth uses long formal names; prefer short readable ones.
RENAME = {
    'United States of America': 'United States',
    'United Kingdom': 'United Kingdom',
    'Russia': 'Russia',
    'Czechia': 'Czech Republic',
    'Republic of the Congo': 'Republic of the Congo',
    'Congo': 'Republic of the Congo',
    'Democratic Republic of the Congo': 'DR Congo',
    'Dem. Rep. Congo': 'DR Congo',
    'Central African Rep.': 'Central African Republic',
    'Dominican Rep.': 'Dominican Republic',
    'Bosnia and Herz.': 'Bosnia and Herzegovina',
    'N. Cyprus': 'Northern Cyprus',
    'Eq. Guinea': 'Equatorial Guinea',
    'S. Sudan': 'South Sudan',
    'Solomon Is.': 'Solomon Islands',
    'Falkland Is.': 'Falkland Islands',
    'Fr. S. Antarctic Lands': 'French Southern Territories',
    'Br. Indian Ocean Ter.': 'British Indian Ocean Territory',
    'Marshall Is.': 'Marshall Islands',
    'Cayman Is.': 'Cayman Islands',
    'Faeroe Is.': 'Faroe Islands',
    'Cook Is.': 'Cook Islands',
    'Turks and Caicos Is.': 'Turks and Caicos',
    'St. Vin. and Gren.': 'St. Vincent',
    'Antigua and Barb.': 'Antigua and Barbuda',
    'St. Kitts and Nevis': 'St. Kitts and Nevis',
    'Trinidad and Tob.': 'Trinidad and Tobago',
    'Sao Tome and Principe': 'Sao Tome and Principe',
    'S\u00e3o Tom\u00e9 and Principe': 'Sao Tome and Principe',
    'W. Sahara': 'Western Sahara',
    'Timor-Leste': 'East Timor',
    'Lao PDR': 'Laos',
    'Dem. Rep. Korea': 'North Korea',
    'Korea': 'South Korea',
    'Czech Rep.': 'Czech Republic',
    'Macedonia': 'North Macedonia',
    'C\u00f4te d\'Ivoire': 'Ivory Coast',
    'Swaziland': 'Eswatini',
    'Bahamas': 'Bahamas',
    'Gambia': 'Gambia',
    'Central African Republic': 'Central African Republic',
    'Dominican Republic': 'Dominican Republic',
    'Bosnia and Herzegovina': 'Bosnia and Herzegovina',
    'Northern Cyprus': 'Northern Cyprus',
    'Republic of Serbia': 'Serbia',
    'United Republic of Tanzania': 'Tanzania',
    'Solomon Islands': 'Solomon Islands',
    'South Sudan': 'South Sudan',
    'Equatorial Guinea': 'Equatorial Guinea',
    'Papua New Guinea': 'Papua New Guinea',
    'Trinidad and Tobago': 'Trinidad and Tobago',
    'Antigua and Barbuda': 'Antigua and Barbuda',
    'Saint Vincent and the Grenadines': 'St. Vincent',
    'Turkiye': 'Turkey',
    'Turkey': 'Turkey',
    'eSwatini': 'Eswatini',
    'Ivory Coast': 'Ivory Coast',
    'Falkland Islands': 'Falkland Islands',
    'French Southern and Antarctic Lands': 'French Southern Territories',
    'Heard Island and McDonald Islands': 'Heard Island',
    'Saint Helena': 'Saint Helena',
    'South Georgia and the Islands': 'South Georgia',
    'Federated States of Micronesia': 'Micronesia',
    'Northern Mariana Islands': 'Northern Marianas',
    'British Virgin Islands': 'British Virgin Islands',
    'United States Virgin Islands': 'U.S. Virgin Islands',
    'Turks and Caicos Islands': 'Turks and Caicos',
    'Sao Tome and Principe': 'Sao Tome and Principe',
    'Wallis and Futuna': 'Wallis and Futuna',
    'Saint Pierre and Miquelon': 'St. Pierre and Miquelon',
    'Saint Kitts and Nevis': 'St. Kitts and Nevis',
    'Bonaire, Sint Eustatius and Saba': 'Bonaire',
    'Sint Maarten': 'Sint Maarten',
    'Saint Barthelemy': 'St. Barthelemy',
    'Saint Martin': 'St. Martin',
    'Somaliland': 'Somaliland',
    'Western Sahara': 'Western Sahara',
    'Vatican': 'Vatican City',
    'Palestine': 'Palestine',
    'Hong Kong S.A.R.': 'Hong Kong',
    'Macao S.A.R': 'Macau',
    'Macao S.A.R.': 'Macau',
    'Republic of Korea': 'South Korea',
    'South Korea': 'South Korea',
    'North Korea': 'North Korea',
    'Laos': 'Laos',
    'Myanmar': 'Myanmar',
    'Brunei': 'Brunei',
    'East Timor': 'East Timor',
    'The Bahamas': 'Bahamas',
    'The Gambia': 'Gambia',
    'Cabo Verde': 'Cape Verde',
    'Cape Verde': 'Cape Verde',
    'North Macedonia': 'North Macedonia',
    'Republic of Moldova': 'Moldova',
    'Moldova': 'Moldova',
    'Marshall Islands': 'Marshall Islands',
    'New Caledonia': 'New Caledonia',
    'French Polynesia': 'French Polynesia',
    'Cayman Islands': 'Cayman Islands',
    'Faroe Islands': 'Faroe Islands',
    'Isle of Man': 'Isle of Man',
    'Aland Islands': 'Aland Islands',
    'Cook Islands': 'Cook Islands',
    'American Samoa': 'American Samoa',
    'Puerto Rico': 'Puerto Rico',
    'Greenland': 'Greenland',
    'Antarctica': 'Antarctica',
}


def _dp(pts, tol):
    """Iterative Douglas-Peucker on an OPEN polyline."""
    if len(pts) <= 2:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        x1, y1 = pts[a]
        x2, y2 = pts[b]
        dx, dy = x2 - x1, y2 - y1
        denom = (dx * dx + dy * dy) ** 0.5
        worst_i, worst_d = -1, -1.0
        for i in range(a + 1, b):
            px, py = pts[i]
            if denom < 1e-12:
                d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
            else:
                d = abs(dy * (px - x1) - dx * (py - y1)) / denom
            if d > worst_d:
                worst_i, worst_d = i, d
        if worst_d > tol and worst_i > 0:
            keep[worst_i] = True
            stack.append((a, worst_i))
            stack.append((worst_i, b))
    return [pts[i] for i in range(len(pts)) if keep[i]]


def simplify_ring(ring, tol):
    """Simplify a CLOSED ring by splitting it into two open halves first.

    Running Douglas-Peucker directly on a closed ring collapses it, because the
    two anchor endpoints are the same point and the baseline length is zero.

    The tolerance is scaled down for small rings: a fixed degree tolerance that
    is reasonable for a continent will erase a small island's shape entirely
    (e.g. Oahu is only ~0.6 deg across, so a 0.12 deg tolerance distorts it
    enough to push Honolulu outside the polygon).
    """
    if ring[0] == ring[-1]:
        ring = ring[:-1]
    n = len(ring)
    if n <= 4:
        return ring + [ring[0]]

    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    span = max(max(lons) - min(lons), max(lats) - min(lats))
    tol = min(tol, span / 40.0)

    mid = n // 2
    first = _dp(ring[:mid + 1], tol)
    second = _dp(ring[mid:] + [ring[0]], tol)
    out = first[:-1] + second[:-1]
    if len(out) < 3:
        out = ring[:3]
    return out + [out[0]]


def polys_of(geom):
    if geom['type'] == 'Polygon':
        return [geom['coordinates']]
    if geom['type'] == 'MultiPolygon':
        return geom['coordinates']
    return []


def ring_area(ring):
    """Absolute shoelace area, used to drop negligible slivers."""
    s = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def build():
    src = json.load(open(SRC))
    entries = []
    for feat in src['features']:
        props = feat['properties']
        raw_name = props.get('NAME') or props.get('ADMIN') or 'Unknown'
        name = RENAME.get(raw_name, raw_name)

        polys_out = []
        for poly in polys_of(feat['geometry']):
            rings_out = []
            for idx, ring in enumerate(poly):
                pts = [tuple(c[:2]) for c in ring]
                simp = simplify_ring(pts, TOL)
                if len(simp) < 4:
                    continue
                # Drop microscopic outer rings (invisible at click precision).
                if idx == 0 and ring_area(simp) < MIN_AREA:
                    rings_out = []
                    break
                rings_out.append([[round(x, DECIMALS), round(y, DECIMALS)] for x, y in simp])
            if rings_out:
                polys_out.append(rings_out)

        if polys_out:
            # Largest polygon first so common mainland hits match soonest.
            polys_out.sort(key=lambda p: ring_area(p[0]), reverse=True)
            entries.append([name, polys_out])

    # Sort countries by total area, descending: big landmasses are checked first.
    entries.sort(key=lambda e: sum(ring_area(p[0]) for p in e[1]), reverse=True)

    payload = json.dumps(entries, separators=(',', ':'))
    with open(OUT, 'w') as f:
        f.write('const COUNTRY_DATA = ' + payload + ';\n')

    raw = os.path.getsize(OUT)
    gz = len(gzip.compress(open(OUT, 'rb').read()))
    pts = sum(len(r) for _, polys in entries for poly in polys for r in poly)
    print(f'countries={len(entries)}')
    print(f'polygons={sum(len(p) for _, p in entries)}')
    print(f'points={pts}')
    print(f'raw={raw/1024:.0f} KB  gzipped={gz/1024:.0f} KB')
    return entries


def verify(entries):
    def point_in_ring(lon, lat, ring):
        inside = False
        n = len(ring)
        j = n - 1
        for i in range(n):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > lat) != (yj > lat):
                x_int = xi + (lat - yi) * (xj - xi) / ((yj - yi) or 1e-12)
                if lon < x_int:
                    inside = not inside
            j = i
        return inside

    def lookup(lon, lat):
        for name, polys in entries:
            for poly in polys:
                if point_in_ring(lon, lat, poly[0]):
                    if any(point_in_ring(lon, lat, h) for h in poly[1:]):
                        continue
                    return name
        return None

    tests = [
        ('New York', -74.01, 40.71, 'United States'),
        ('London', -0.13, 51.51, 'United Kingdom'),
        ('Cairo', 31.24, 30.04, 'Egypt'),
        ('Mumbai', 72.88, 19.08, 'India'),
        ('Sydney', 151.21, -33.87, 'Australia'),
        ('Sao Paulo', -46.63, -23.55, 'Brazil'),
        ('Beijing', 116.41, 39.90, 'China'),
        ('Cape Town', 18.42, -33.92, 'South Africa'),
        ('Moscow', 37.62, 55.75, 'Russia'),
        ('Toronto', -79.38, 43.65, 'Canada'),
        ('Denver', -104.99, 39.74, 'United States'),
        ('Anchorage', -149.90, 61.22, 'United States'),
        ('Honolulu', -157.86, 21.31, 'United States'),
        ('Tokyo', 139.69, 35.69, 'Japan'),
        ('Reykjavik', -21.94, 64.15, 'Iceland'),
        ('Nairobi', 36.82, -1.29, 'Kenya'),
        ('Buenos Aires', -58.38, -34.60, 'Argentina'),
        ('Berlin', 13.40, 52.52, 'Germany'),
        ('Madrid', -3.70, 40.42, 'Spain'),
        ('Paris', 2.35, 48.86, 'France'),
        ('Rome', 12.50, 41.90, 'Italy'),
        ('Cairo south', 32.90, 24.09, 'Egypt'),
        ('Ulaanbaatar', 106.92, 47.89, 'Mongolia'),
        ('Jakarta', 106.85, -6.21, 'Indonesia'),
        ('Lima', -77.04, -12.05, 'Peru'),
        ('Santiago', -70.65, -33.46, 'Chile'),
        ('Delhi', 77.21, 28.61, 'India'),
        ('Tehran', 51.39, 35.69, 'Iran'),
        ('Riyadh', 46.72, 24.71, 'Saudi Arabia'),
        ('Kinshasa', 15.27, -4.44, 'DR Congo'),
        ('Lagos', 3.38, 6.52, 'Nigeria'),
        ('Greenland interior', -42.0, 72.0, 'Greenland'),
        ('South Pole', 0.0, -89.0, 'Antarctica'),
        ('Mid-Atlantic', -30.0, 20.0, None),
        ('Mid-Pacific', -150.0, 0.0, None),
        ('Southern Ocean', 0.0, -60.0, None),
        ('Indian Ocean', 80.0, -20.0, None),
    ]

    print('\n--- verification ---')
    ok = 0
    for label, lon, lat, expect in tests:
        got = lookup(lon, lat)
        hit = (got == expect)
        ok += hit
        print(f'{"OK  " if hit else "MISS"} {label:20s} -> {got}')
    print(f'\n{ok}/{len(tests)} correct')
    return ok == len(tests)


if __name__ == '__main__':
    ents = build()
    verify(ents)
