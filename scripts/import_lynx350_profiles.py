"""Import Lynx-350 original profiles into the Unbound3D system profile bundle.

What this script does:
- Reads every filament/process JSON from Lynx-350.orca_printer/
- Creates properly formatted system-profile JSONs in resources/profiles/Unbound3D/
- Merges: keeps any parameters already in current Lynx 350 files and ADDS
  anything from the originals that is missing
- Updates resources/profiles/Unbound3D.json index
- Also patches Unbound3D Lynx 350 0.4 nozzle.json with params that were in
  the original printer JSON but are missing from the current machine config

Run from the repo root:
    python3 scripts/import_lynx350_profiles.py
"""

import json
import os
import sys
import shutil

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_BASE   = os.path.join(ROOT, 'Lynx-350.orca_printer')
APP_BASE    = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D')
INDEX_PATH  = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D.json')
SUFFIX      = ' @Unbound3D'

# Machine name used throughout
LYNX350_MACHINE = 'Unbound3D Lynx 350 0.4 nozzle'
LYNX320_MACHINE = 'Unbound3D Lynx 320 0.4 nozzle'

# Fields that are metadata, not print-parameters
META = {
    'type', 'name', 'inherits', 'from', 'instantiation',
    'setting_id', 'filament_id',
    'print_settings_id', 'filament_settings_id', 'printer_settings_id',
    'compatible_printers', 'compatible_prints',
    'compatible_printers_condition', 'compatible_prints_condition',
    'version', 'is_custom_defined',
    'default_print_profile', 'default_filament_profile',
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load(path):
    with open(path, 'rb') as f:
        return json.loads(f.read().decode('utf-8-sig'))


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
        f.write('\n')


def orig_path(kind, fname):
    return os.path.join(ORIG_BASE, kind, fname)


def app_path(kind, fname):
    return os.path.join(APP_BASE, kind, fname)

# ---------------------------------------------------------------------------
# inherits-name translation: original -> Unbound3D system name
# "X @MyKlipper" -> "X @Unbound3D" equivalents, and "@System" stays as-is
# ---------------------------------------------------------------------------
INHERITS_MAP = {
    '0.20mm Standard @MyKlipper':                   '0.20mm Standard @Unbound3D',
    '0.20mm Standard @MyKlipper - Copy':             '0.20mm Standard @Unbound3D',
    'eSUN PA-CF black @MyKlipper 0.4 nozzle':       'eSUN PA-CF black @MyKlipper 0.4 nozzle @Unbound3D',
    'MyKlipper 0.4 nozzle':                         'Unbound3D Lynx 350 0.4 nozzle',
    # "@System" presets are global and stay as-is
}


def translate_inherits(val):
    return INHERITS_MAP.get(val, val)

# ---------------------------------------------------------------------------
# New filament profiles
# Mapping: (orig_filename_base, new_app_name, filament_id, inherits_override)
#   inherits_override=None  -> use original inherits (translated)
#   inherits_override=str   -> force this inherits value
# ---------------------------------------------------------------------------
NEW_FILAMENTS = [
    # orig base name (without .json)                  new app name                          fid       inherits override
    ('eSUN PA-CF Lynx-350',                           'eSUN PA-CF Lynx-350 @Unbound3D',     'GFL18',  None),
    ('Lynx 350 JAMG HE PLA+',                         'Lynx 350 JAMG HE PLA+ @Unbound3D',   'GFL19',  None),
    ('Lynx 350 Numaker PLA+',                         'Lynx 350 Numaker PLA+ @Unbound3D',   'GFL20',  None),
    ('Lynx 350 PPS CF ( Bambu)',                      'Lynx 350 PPS CF (Bambu) @Unbound3D', 'GFL21',  None),
    ('Lynx350 ASA',                                   'Lynx350 ASA @Unbound3D',             'GFL22',  None),
    ('Lynx350 Numaker ASA',                           'Lynx350 Numaker ASA @Unbound3D',     'GFL23',  None),
    ('Numaker PETG HS Lynx 350',                      'Numaker PETG HS Lynx 350 @Unbound3D','GFL24',  None),
]

# New process profiles
# Mapping: (orig_filename_base, new_app_name, setting_id)
NEW_PROCESSES = [
    # orig base name (without .json)              new app name                                     sid
    ('Numaker PLA+ Lynx 350',                     '0.20mm Numaker PLA+ Lynx 350 @Unbound3D',       'GP016'),
    ('High speed profile JAMG HE PLA 0.4mm',      'High speed profile JAMG HE PLA 0.4mm @Unbound3D','GP017'),
    ('High speed profile Numaker PLA 0.4mm',      'High speed profile Numaker PLA 0.4mm @Unbound3D','GP018'),
    ('High speed profile PETG 0.4mm',             'High speed profile PETG 0.4mm @Unbound3D',      'GP019'),
    ('High speed profile PLA 0.4mm',              'High speed profile PLA 0.4mm @Unbound3D',       'GP020'),
    ('Numaker ASA',                               '0.20mm Numaker ASA @Unbound3D',                 'GP021'),
    ('PPS CF Lynx350',                            '0.20mm PPS CF Lynx350 @Unbound3D',              'GP022'),
    ('esun PACF Lynx350',                         '0.20mm esun PACF Lynx350 @Unbound3D',           'GP023'),
    ('Vtol profile PLA 0.4mm',                    'Vtol profile PLA 0.4mm @Unbound3D',             'GP024'),
]

# Filament files that already exist in the app but also appear in the Lynx-350
# bundle. We verify their parameters match and patch any missing ones.
EXISTING_FILAMENT_CHECK = [
    ('Bambu PETG-CF Lynx 320',        'Bambu PETG-CF Lynx 320 @Unbound3D'),
    ('Fibreel PA-CF black ',          'Fibreel PA-CF black @Unbound3D'),
    ('Fibreel PA-CF black lynx 320',  'Fibreel PA-CF black lynx 320 @Unbound3D'),
    ('Fibreel PA12-CF black ',        'Fibreel PA12-CF black @Unbound3D'),
    ('Generic TPU @System - Copy',    'Generic TPU @Unbound3D'),
    ('Make3d.in',                     'Make3d.in @Unbound3D'),
    ('Numaker PLA+',                  'Numaker PLA+ @Unbound3D'),
    ('Numakers petg hs lynx 320',     'Numakers petg hs lynx 320 @Unbound3D'),
    ('TPU lynx 230',                  'TPU lynx 230 @Unbound3D'),
    ('eSUN PA-CF',                    'eSUN PA-CF @Unbound3D'),
    ('eSUN PA-CF black ',             'eSUN PA-CF black @Unbound3D'),
    ('eSUN PA-CF black @MyKlipper 0.4 nozzle', 'eSUN PA-CF black @MyKlipper 0.4 nozzle @Unbound3D'),
    ('eSUN PA-CF lynx320',            'eSUN PA-CF lynx320 @Unbound3D'),
    ('eSUN PETG-CF',                  'eSUN PETG-CF @Unbound3D'),
    ('eSUN PLA+ @System - Copy',      'eSUN PLA+ @Unbound3D'),
    ('flex3d PLA+ @System - Copy',    'flex3d PLA+ @Unbound3D'),
    ('nfill pla + glass',             'nfill pla + glass @Unbound3D'),
]

EXISTING_PROCESS_CHECK = [
    ('0.20mm Standard @MyKlipper - Copy', '0.20mm Standard @Unbound3D'),
    ('Bambulab petg cf lynx320',           '0.20mm Bambulab petg cf lynx320 @Unbound3D'),
    ('Fibreel PA CF lynx 320',             '0.20mm Fibreel PA CF lynx 320 @Unbound3D'),
    ('Numaker PLA+',                       '0.20mm Numaker PLA+ @Unbound3D'),
    ('Numakers petg hs lynx 320',          '0.20mm Numakers petg hs lynx 320 @Unbound3D'),
    ('TPU 95A',                            '0.20mm TPU 95A @Unbound3D'),
    ('TPU 95A lynx320',                    '0.20mm TPU 95A lynx320 @Unbound3D'),
    ('esun pa-cf lynx320',                 '0.20mm esun pa-cf lynx320 @Unbound3D'),
    ('esun pla+',                          '0.20mm esun pla+ @Unbound3D'),
    ('fibreel pa-cf lynx320',              '0.20mm fibreel pa-cf lynx320 @Unbound3D'),
    ('flex 3d pla+',                       '0.20mm flex 3d pla+ @Unbound3D'),
]

# ---------------------------------------------------------------------------
# Extra params added by us that are NOT in the original (preserve these)
# ---------------------------------------------------------------------------
OUR_EXTRA_FILAMENT_FIELDS = {'filament_id', 'filament_settings_id', 'type',
                              'from', 'instantiation', 'compatible_printers'}
OUR_EXTRA_PROCESS_FIELDS  = {'setting_id', 'type', 'from', 'instantiation',
                              'compatible_printers'}

# ---------------------------------------------------------------------------
# Machine config params from original Lynx-350.json that are missing in
# current Unbound3D Lynx 350 0.4 nozzle.json
# ---------------------------------------------------------------------------
MACHINE_PARAMS_TO_ADD = {
    'auxiliary_fan':               '1',
    'machine_max_junction_deviation': ['0.3'],
    'purge_in_prime_tower':        '1',
    'resonance_avoidance':         '0',
    'min_resonance_avoidance_speed': '70',
    'max_resonance_avoidance_speed': '120',
}


# ===========================================================================
# STEP 1 – Create new filament profiles
# ===========================================================================
print('\n' + '='*72)
print('STEP 1 – Creating new Lynx-350 filament profiles')
print('='*72)

for orig_base, app_name, fid, inherits_override in NEW_FILAMENTS:
    src = orig_path('filament', orig_base + '.json')
    dst = app_path('filament', app_name + '.json')

    if not os.path.exists(src):
        print(f'  [!] Source missing: {src}')
        continue

    orig = load(src)

    # Start from original data
    out = {}

    # Copy all non-meta print parameters from the original
    for k, v in orig.items():
        if k not in META:
            out[k] = v

    # Set system-profile metadata
    out['type']        = 'filament'
    out['name']        = app_name
    out['from']        = 'system'
    out['instantiation'] = 'true'
    out['filament_id'] = fid
    out['filament_settings_id'] = [app_name]

    # Inherits
    if inherits_override:
        out['inherits'] = inherits_override
    elif orig.get('inherits'):
        out['inherits'] = translate_inherits(orig['inherits'])

    # compatible_printers – Lynx 350 specific new profiles only go to Lynx 350
    orig_compat = orig.get('compatible_printers', [])
    # If original has empty list, means it was not assigned – assign to Lynx 350
    if not orig_compat or orig_compat == ['MyKlipper 0.4 nozzle']:
        out['compatible_printers'] = [LYNX350_MACHINE]
    else:
        # translate any MyKlipper references
        new_compat = []
        for cp in orig_compat:
            if cp == 'MyKlipper 0.4 nozzle':
                new_compat.append(LYNX350_MACHINE)
            else:
                new_compat.append(cp)
        out['compatible_printers'] = new_compat

    # If file already exists, MERGE: keep our existing fields, add new ones
    if os.path.exists(dst):
        existing = load(dst)
        # Keep our metadata exactly
        for k in ('filament_id', 'filament_settings_id', 'type', 'from',
                  'instantiation', 'name', 'compatible_printers', 'inherits'):
            if k in existing:
                out[k] = existing[k]
        # Keep any of our extra params that aren't in orig
        for k, v in existing.items():
            if k not in out and k not in META:
                out[k] = v
        print(f'  MERGE  {orig_base!r:45s} -> {app_name!r}')
    else:
        print(f'  CREATE {orig_base!r:45s} -> {app_name!r}')

    save(dst, out)

print()


# ===========================================================================
# STEP 2 – Create new process profiles
# ===========================================================================
print('='*72)
print('STEP 2 – Creating new Lynx-350 process profiles')
print('='*72)

for orig_base, app_name, sid in NEW_PROCESSES:
    src = orig_path('process', orig_base + '.json')
    dst = app_path('process', app_name + '.json')

    if not os.path.exists(src):
        print(f'  [!] Source missing: {src}')
        continue

    orig = load(src)

    out = {}

    # Copy all non-meta print parameters
    for k, v in orig.items():
        if k not in META:
            out[k] = v

    # Remove print_settings_id from params (it's meta)
    out.pop('print_settings_id', None)

    # Set system-profile metadata
    out['type']        = 'process'
    out['name']        = app_name
    out['from']        = 'system'
    out['instantiation'] = 'true'
    out['setting_id']  = sid

    # Inherits: always 0.20mm Standard @Unbound3D for process profiles
    orig_inh = orig.get('inherits', '')
    out['inherits'] = translate_inherits(orig_inh) if orig_inh else '0.20mm Standard @Unbound3D'

    # compatible_printers – Lynx 350 specific
    out['compatible_printers'] = [LYNX350_MACHINE]

    # If file already exists, merge
    if os.path.exists(dst):
        existing = load(dst)
        for k in ('setting_id', 'type', 'from', 'instantiation', 'name',
                  'compatible_printers', 'inherits'):
            if k in existing:
                out[k] = existing[k]
        for k, v in existing.items():
            if k not in out and k not in META:
                out[k] = v
        print(f'  MERGE  {orig_base!r:45s} -> {app_name!r}')
    else:
        print(f'  CREATE {orig_base!r:45s} -> {app_name!r}')

    save(dst, out)

print()


# ===========================================================================
# STEP 3 – Patch existing filament profiles: merge any missing params from
#           the Lynx-350 bundle version
# ===========================================================================
print('='*72)
print('STEP 3 – Patching existing filament profiles from Lynx-350 bundle')
print('='*72)

for orig_base, app_name in EXISTING_FILAMENT_CHECK:
    src = orig_path('filament', orig_base + '.json')
    dst = app_path('filament', app_name + '.json')

    if not os.path.exists(src):
        continue  # not all originals are present
    if not os.path.exists(dst):
        print(f'  [!] App file missing: {dst}')
        continue

    orig = load(src)
    app  = load(dst)

    added = []
    for k, v in orig.items():
        if k in META:
            continue
        if k not in app:
            app[k] = v
            added.append(k)

    if added:
        save(dst, app)
        print(f'  PATCHED {app_name!r}: added {added}')
    else:
        print(f'  OK      {app_name!r}')

print()


# ===========================================================================
# STEP 4 – Patch existing process profiles: merge any missing params
# ===========================================================================
print('='*72)
print('STEP 4 – Patching existing process profiles from Lynx-350 bundle')
print('='*72)

for orig_base, app_name in EXISTING_PROCESS_CHECK:
    src = orig_path('process', orig_base + '.json')
    dst = app_path('process', app_name + '.json')

    if not os.path.exists(src):
        continue
    if not os.path.exists(dst):
        print(f'  [!] App file missing: {dst}')
        continue

    orig = load(src)
    app  = load(dst)

    added = []
    for k, v in orig.items():
        if k in META or k == 'print_settings_id':
            continue
        if k not in app:
            app[k] = v
            added.append(k)

    if added:
        save(dst, app)
        print(f'  PATCHED {app_name!r}: added {added}')
    else:
        print(f'  OK      {app_name!r}')

print()


# ===========================================================================
# STEP 5 – Patch machine config: add missing params from original Lynx-350.json
# ===========================================================================
print('='*72)
print('STEP 5 – Patching Unbound3D Lynx 350 0.4 nozzle.json')
print('='*72)

machine_path = app_path('machine', 'Unbound3D Lynx 350 0.4 nozzle.json')
if os.path.exists(machine_path):
    mach = load(machine_path)
    added = []
    for k, v in MACHINE_PARAMS_TO_ADD.items():
        if k not in mach:
            mach[k] = v
            added.append(k)
    if added:
        save(machine_path, mach)
        print(f'  Added to machine config: {added}')
    else:
        print('  Machine config already has all params.')
else:
    print(f'  [!] Machine config not found: {machine_path}')

print()


# ===========================================================================
# STEP 6 – Update Unbound3D.json index
# ===========================================================================
print('='*72)
print('STEP 6 – Updating Unbound3D.json index')
print('='*72)

idx = load(INDEX_PATH)

# Helpers to check/add entries
def index_has(lst, name):
    return any(e['name'] == name for e in lst)

def add_index_entry(lst, name, sub_path):
    if not index_has(lst, name):
        lst.append({'name': name, 'sub_path': sub_path})
        print(f'  + {name}')
        return True
    return False

fil_list  = idx['filament_list']
proc_list = idx['process_list']

# New filaments
for _, app_name, _, _ in NEW_FILAMENTS:
    fname = app_name + '.json'
    add_index_entry(fil_list, app_name, f'filament/{fname}')

# New processes
for _, app_name, _ in NEW_PROCESSES:
    fname = app_name + '.json'
    add_index_entry(proc_list, app_name, f'process/{fname}')

save(INDEX_PATH, idx)
print(f'  Index updated: {len(fil_list)} filaments, {len(proc_list)} processes')
print()


# ===========================================================================
# STEP 7 – Verify index consistency
# ===========================================================================
print('='*72)
print('STEP 7 – Index verification')
print('='*72)

issues = 0
for entry in idx['filament_list'] + idx['process_list'] + idx['machine_list']:
    nm = entry['name']
    sp = entry['sub_path']
    full = os.path.join(APP_BASE, sp)
    if not os.path.exists(full):
        print(f'  [!] Index entry file missing: {sp}')
        issues += 1
        continue
    body = load(full)
    if body.get('name') != nm:
        print(f'  [!] Name mismatch: index={nm!r} vs file={body.get("name")!r}')
        issues += 1

if issues == 0:
    print('  All index entries valid.')
else:
    print(f'  {issues} issues found.')

print()

# ===========================================================================
# Summary
# ===========================================================================
print('='*72)
print('DONE')
print(f'  New filament profiles created/merged: {len(NEW_FILAMENTS)}')
print(f'  New process profiles created/merged:  {len(NEW_PROCESSES)}')
print(f'  Total filament_list entries: {len(idx["filament_list"])}')
print(f'  Total process_list entries:  {len(idx["process_list"])}')
print('='*72)
