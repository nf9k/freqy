#!/usr/bin/env python3
"""
Generate demo seed data for freqy demo instance.
Run: python3 scripts/generate_demo_seed.py
Output: demo/seed.sql
Requires: bcrypt (pip install bcrypt)
"""

import os
import random
from datetime import date, timedelta

try:
    import bcrypt
except ImportError:
    raise SystemExit('pip install bcrypt')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH   = os.path.join(SCRIPT_DIR, '..', 'demo', 'seed.sql')

RNG = random.Random(42)

# ── Password hashes ──────────────────────────────────────────────
def hashpw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=10)).decode()

print('Hashing passwords...')
ADMIN_HASH        = hashpw('admin')
USER_HASH         = hashpw('user')
PLACEHOLDER_HASH  = hashpw(os.urandom(32).hex())  # fake users — not loginable

# ── Source data ──────────────────────────────────────────────────
FIRSTS = [
    'James','John','Robert','Michael','William','David','Richard','Joseph',
    'Thomas','Charles','Patricia','Linda','Barbara','Susan','Jessica','Karen',
    'Sarah','Lisa','Nancy','Betty','Mark','Donald','George','Kenneth','Steven',
    'Edward','Brian','Ronald','Anthony','Kevin','Jason','Matthew','Gary',
    'Timothy','Jose','Larry','Jeffrey','Frank','Scott','Eric','Andrew',
]

LASTS = [
    'Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis',
    'Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Wilson','Anderson',
    'Thomas','Taylor','Moore','Jackson','Martin','Lee','Perez','Thompson',
    'White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson','Walker',
    'Young','Allen','King','Wright','Torres','Nguyen','Hill','Flores','Green',
]

CITIES = [
    ('Indianapolis','IN',39.77,-86.16), ('Fort Wayne','IN',41.08,-85.14),
    ('Evansville','IN',37.97,-87.57),   ('South Bend','IN',41.68,-86.25),
    ('Carmel','IN',39.98,-86.12),       ('Fishers','IN',39.96,-85.97),
    ('Bloomington','IN',39.17,-86.53),  ('Hammond','IN',41.58,-87.50),
    ('Gary','IN',41.59,-87.35),         ('Muncie','IN',40.19,-85.39),
    ('Lafayette','IN',40.42,-86.88),    ('Terre Haute','IN',39.47,-87.41),
    ('Columbus','IN',39.20,-85.92),     ('Anderson','IN',40.11,-85.68),
    ('Kokomo','IN',40.49,-86.13),       ('Noblesville','IN',40.04,-86.01),
    ('Greenwood','IN',39.61,-86.11),    ('Elkhart','IN',41.68,-85.98),
    ('Mishawaka','IN',41.66,-86.16),    ('Lawrence','IN',39.84,-86.02),
    ('Jeffersonville','IN',38.28,-85.74),('New Albany','IN',38.29,-85.82),
    ('Portage','IN',41.58,-87.18),      ('Richmond','IN',39.83,-84.90),
    ('Madison','IN',38.74,-85.38),      ('Vincennes','IN',38.68,-87.53),
    ('Logansport','IN',40.75,-86.36),   ('Michigan City','IN',41.71,-86.90),
    ('Peru','IN',40.75,-86.07),         ('Jasper','IN',38.39,-86.93),
    ('New Castle','IN',39.93,-85.37),   ('Frankfort','IN',40.28,-86.51),
    ('Marion','IN',40.56,-85.66),       ('Connersville','IN',39.64,-85.14),
    ('Valparaiso','IN',41.47,-87.06),
]

STREETS = [
    'Main St','Oak Ave','Maple Dr','Cedar Ln','Pine St','Elm St',
    'Washington Blvd','Park Ave','Lake Dr','Hill Rd','River Rd',
    'Forest Dr','Valley Rd','Sunset Blvd','Highland Ave','Church St',
    'Ridgewood Dr','Lakeview Ave','Brookside Rd','Hillcrest Dr',
]

CTCSS = [
    '67.0','71.9','74.4','77.0','79.7','82.5','85.4','88.5','91.5',
    '94.8','97.4','100.0','103.5','107.2','110.9','114.8','118.8',
    '123.0','127.3','131.8','136.5','141.3','146.2','151.4','156.7',
    '162.2','167.9','173.8','179.9','186.2','192.8','203.5',
]

BAND_DATA = {
    '50':   dict(outputs=[51.760,52.525,51.080,52.010,52.340,51.500,52.875,52.180,
                          51.220,51.880,52.640,53.110],
                 offset=-1.0,    em='20K0F3E', bw='25kHz'),
    '144':  dict(outputs=[145.110,145.230,145.390,146.625,146.820,146.940,
                          147.000,147.105,147.195,147.315,145.470,146.760,
                          147.030,147.240,146.700,146.580,145.350,147.150,
                          146.520,145.170,146.490,147.060,147.270,147.390],
                 offset=-0.600,  em='11K2F3E', bw='12.5kHz'),
    '222':  dict(outputs=[224.040,224.100,224.160,224.460,224.660,224.760,
                          224.880,224.220,224.320,224.580,224.420,223.900],
                 offset=-1.600,  em='11K2F3E', bw='12.5kHz'),
    '440':  dict(outputs=[442.075,442.125,442.225,442.550,443.225,444.125,
                          444.625,444.975,448.225,449.625,442.700,443.050,
                          443.475,444.200,444.450,444.775,449.125,449.225,
                          449.500,449.875,443.800,444.350,442.300,442.925,
                          443.650,444.875,448.575,449.350,442.450,443.100],
                 offset=-5.0,    em='11K2F3E', bw='12.5kHz'),
    '902':  dict(outputs=[927.1125,927.2875,927.4625,927.6375,927.8125,
                          926.9375,927.0625,927.5500,927.7250],
                 offset=-25.0,   em='11K2F3E', bw='12.5kHz'),
    '1296': dict(outputs=[1282.000,1282.100,1282.200,1282.300,1283.000,
                          1283.100,1283.200,1282.400,1282.600],
                 offset=-12.0,   em='11K2F3E', bw='12.5kHz'),
}

# Weighted pools
STATUSES  = (['Final']*55 + ['Construction Permit']*20 + ['New']*10 +
             ['On Hold']*5 + ['Cancelled']*5 + ['Expired']*3 + ['Audit']*2)
APP_TYPES = ['Repeater']*65 + ['Link']*15 + ['Control RX']*10 + ['Beacon']*7 + ['Other']*3
WILLBE    = ['Open']*60 + ['Closed']*25 + ['Private']*10 + ['Limited']*5
BANDS_W   = (['50']*5 + ['144']*28 + ['222']*10 +
             ['440']*42 + ['902']*8 + ['1296']*7)

# ── Helpers ──────────────────────────────────────────────────────
def sq(v):
    if v is None: return 'NULL'
    return "'" + str(v).replace('\\', '\\\\').replace("'", "''") + "'"

def sd(d):
    if d is None: return 'NULL'
    return f"'{d.isoformat()}'"

def gen_callsign(used):
    p2 = ['WA','WB','WC','WD','WF','KA','KB','KC','KD','KF',
          'KG','KI','KJ','KK','NA','NB','NC','ND','NF','NG',
          'AB','AC','AD','AE','AF','AG','AI','AK','AL','NI','KM',
          'KR','KS','KT','KU','KV','KW','KX','KY','KZ']
    L = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    while True:
        style = RNG.choice([1,2,3,4])
        # 95% area 9, 2.5% area 8, 2.5% area 4
        r = RNG.random()
        region = '9' if r < 0.95 else ('8' if r < 0.975 else '4')
        if style == 1:
            cs = f'{RNG.choice("WKN")}{region}{"".join(RNG.choices(L,k=2))}'
        elif style == 2:
            cs = f'{RNG.choice("WKN")}{region}{"".join(RNG.choices(L,k=3))}'
        elif style == 3:
            cs = f'{RNG.choice(p2)}{region}{"".join(RNG.choices(L,k=2))}'
        else:
            cs = f'{RNG.choice(p2)}{region}{"".join(RNG.choices(L,k=3))}'
        if cs not in used:
            used.add(cs)
            return cs

# ── Build users ──────────────────────────────────────────────────
TODAY    = date.today()
used_cs  = {'ADMIN', 'USER'}
fake_users = []

for i in range(100):
    cs  = gen_callsign(used_cs)
    city, state, lat, lng = RNG.choice(CITIES)
    fake_users.append({
        'id':      i + 3,
        'callsign': cs,
        'fname':   RNG.choice(FIRSTS),
        'lname':   RNG.choice(LASTS),
        'email':   f'{cs.lower()}@example.com',
        'address': f'{RNG.randint(100,9999)} {RNG.choice(STREETS)}',
        'city':    city,
        'state':   state,
        'zip':     f'{RNG.randint(10000,99999):05d}',
        'phone':   f'({RNG.randint(200,999)}) {RNG.randint(200,999)}-{RNG.randint(1000,9999)}',
        'lat':     round(lat + RNG.uniform(-0.5, 0.5), 6),
        'lng':     round(lng + RNG.uniform(-0.5, 0.5), 6),
    })

# ── Build records ────────────────────────────────────────────────
records = []
used_freqs = set()

def make_record(rec_id, user_id, system_id, city, state, lat, lng, status=None):
    band   = RNG.choice(BANDS_W)
    bd     = BAND_DATA[band]
    for _ in range(20):
        output = RNG.choice(bd['outputs'])
        if (band, output) not in used_freqs:
            break
    used_freqs.add((band, output))
    input_f = round(output + bd['offset'], 4)
    tone    = RNG.choice(CTCSS)
    status  = status or RNG.choice(STATUSES)
    atype   = RNG.choice(APP_TYPES)

    if status == 'Expired':
        expires = TODAY - timedelta(days=RNG.randint(1, 365))
        orig    = expires - timedelta(days=730)
    elif status in ('Final', 'Construction Permit', 'On Hold', 'Audit'):
        expires = TODAY + timedelta(days=RNG.randint(30, 730))
        orig    = TODAY - timedelta(days=RNG.randint(30, 730))
    else:
        expires = None
        orig    = TODAY - timedelta(days=RNG.randint(1, 180))

    return {
        'id':          rec_id,
        'subdir':      f'D{rec_id:05d}',
        'subdsc':      f'{system_id}/R {output:.4f} {city}',
        'user_id':     user_id,
        'system_id':   system_id,
        'app_type':    atype,
        'status':      status,
        'band':        band,
        'freq_output': output,
        'freq_input':  input_f,
        'bandwidth':   bd['bw'],
        'emission_des': bd['em'],
        'tx_pl':       tone,
        'rx_pl':       tone,
        'tx_power':    RNG.choice([5, 10, 25, 50, 100]),
        'loc_lat':     round(lat + RNG.uniform(-0.3, 0.3), 6),
        'loc_lng':     round(lng + RNG.uniform(-0.3, 0.3), 6),
        'loc_city':    city,
        'loc_state':   state,
        'willbe':      RNG.choice(WILLBE),
        'orig_date':   orig,
        'expires_date': expires,
    }

# 5 records for the demo user account
user_city, user_state, user_lat, user_lng = CITIES[0]  # Indianapolis
for i, forced_status in enumerate(['New', 'Construction Permit', 'Final', 'Final', 'On Hold']):
    records.append(make_record(i+1, 2, 'USER', user_city, user_state, user_lat, user_lng, forced_status))

# ~145 records for fake users
for i in range(145):
    u = fake_users[i % len(fake_users)]
    records.append(make_record(i+6, u['id'], u['callsign'],
                               u['city'], u['state'], u['lat'], u['lng']))

# ── Write SQL ────────────────────────────────────────────────────
lines = [
    '-- freqy demo seed data',
    '-- Generated by scripts/generate_demo_seed.py',
    '-- DO NOT EDIT — re-run the script to regenerate',
    '',
    'SET FOREIGN_KEY_CHECKS=0;',
    'TRUNCATE TABLE record_changelog;',
    'TRUNCATE TABLE expiration_notices;',
    'TRUNCATE TABLE coordination_records;',
    'TRUNCATE TABLE password_reset_tokens;',
    'TRUNCATE TABLE totp_backup_codes;',
    'TRUNCATE TABLE webauthn_credentials;',
    'TRUNCATE TABLE users;',
    'SET FOREIGN_KEY_CHECKS=1;',
    '',
    '-- ── Users ──────────────────────────────────────────────────',
    f"INSERT INTO users (id,callsign,password_hash,email,fname,lname,is_admin,created_at,updated_at) VALUES",
    f"  (1,'ADMIN',{sq(ADMIN_HASH)},'admin@demo.local','Demo','Admin',1,NOW(),NOW()),",
    f"  (2,'USER', {sq(USER_HASH)}, 'user@demo.local', 'Demo','User', 0,NOW(),NOW())",
    ';',
]

for u in fake_users:
    lines.append(
        f"INSERT INTO users (id,callsign,password_hash,email,fname,lname,"
        f"address,city,state,zip,phone_home,is_admin,created_at,updated_at) VALUES "
        f"({u['id']},{sq(u['callsign'])},{sq(PLACEHOLDER_HASH)},{sq(u['email'])},"
        f"{sq(u['fname'])},{sq(u['lname'])},"
        f"{sq(u['address'])},{sq(u['city'])},{sq(u['state'])},"
        f"{sq(u['zip'])},{sq(u['phone'])},0,NOW(),NOW());"
    )

lines += ['', '-- ── Coordination records ───────────────────────────────────']

for r in records:
    lines.append(
        f"INSERT INTO coordination_records "
        f"(id,subdir,subdsc,user_id,system_id,app_type,status,"
        f"band,freq_output,freq_input,bandwidth,emission_des,"
        f"tx_pl,rx_pl,tx_power,"
        f"loc_lat,loc_lng,loc_city,loc_state,"
        f"willbe,orig_date,expires_date,created_at,updated_at) VALUES ("
        f"{r['id']},{sq(r['subdir'])},{sq(r['subdsc'])},{r['user_id']},{sq(r['system_id'])},"
        f"{sq(r['app_type'])},{sq(r['status'])},"
        f"{sq(r['band'])},{r['freq_output']:.4f},{r['freq_input']:.4f},"
        f"{sq(r['bandwidth'])},{sq(r['emission_des'])},"
        f"{sq(r['tx_pl'])},{sq(r['rx_pl'])},{r['tx_power']},"
        f"{r['loc_lat']:.6f},{r['loc_lng']:.6f},{sq(r['loc_city'])},{sq(r['loc_state'])},"
        f"{sq(r['willbe'])},{sd(r['orig_date'])},{sd(r['expires_date'])},"
        f"NOW(),NOW());"
    )

sql = '\n'.join(lines) + '\n'
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, 'w') as f:
    f.write(sql)

print(f'Written {OUT_PATH}')
print(f'  {len(fake_users)+2} users, {len(records)} records')
