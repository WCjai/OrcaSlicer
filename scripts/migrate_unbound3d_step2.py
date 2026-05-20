"""Resume migration: filament files + index + machine refs.

Processes were already migrated by migrate_unbound3d_profiles.py.
This script:
  - Iterates rename maps directly (avoids picking up `fdm_*_common.json`)
  - Renames filament files (resolves the eSUN PA-CF swap via rename)
  - Updates internal name/inherits/settings_id/compatible_printers
  - Rewrites the Unbound3D.json index
  - Patches machine files (default_print_profile, default_filament_profile,
    default_materials)
"""
import json, os

ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_BASE   = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D')
INDEX_PATH = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D.json')

proc_renames = {
    '0.20mm Standard @Unbound3D':           '0.20mm Standard @Unbound3D',
    '0.20mm PETG-CF Bambu @Unbound3D':      '0.20mm Bambulab petg cf lynx320 @Unbound3D',
    '0.20mm PA-CF Fibreel @Unbound3D':      '0.20mm Fibreel PA CF lynx 320 @Unbound3D',
    '0.20mm PLA+ Numaker @Unbound3D':       '0.20mm Numaker PLA+ @Unbound3D',
    '0.20mm PETG-HS Numaker @Unbound3D':    '0.20mm Numakers petg hs lynx 320 @Unbound3D',
    '0.20mm TPU 95A Alt @Unbound3D':        '0.20mm TPU 95A @Unbound3D',
    '0.20mm TPU 95A @Unbound3D':            '0.20mm TPU 95A lynx320 @Unbound3D',
    '0.20mm PA-CF eSUN @Unbound3D':         '0.20mm esun pa-cf lynx320 @Unbound3D',
    '0.20mm PLA+ eSUN @Unbound3D':          '0.20mm esun pla+ @Unbound3D',
    '0.20mm PA-CF Fibreel Alt @Unbound3D':  '0.20mm fibreel pa-cf lynx320 @Unbound3D',
    '0.20mm PLA+ Flex3D @Unbound3D':        '0.20mm flex 3d pla+ @Unbound3D',
}
proc_delete = ['0.20mm Standard Alt @Unbound3D']

fil_renames = {
    'Bambu PETG-CF @Unbound3D':           'Bambu PETG-CF Lynx 320 @Unbound3D',
    'Fibreel PA-CF black @Unbound3D':     'Fibreel PA-CF black @Unbound3D',
    'Fibreel PA-CF Lynx @Unbound3D':      'Fibreel PA-CF black lynx 320 @Unbound3D',
    'Fibreel PA12-CF @Unbound3D':         'Fibreel PA12-CF black @Unbound3D',
    'Generic TPU @Unbound3D':             'Generic TPU @Unbound3D',
    'Make3D PLA @Unbound3D':              'Make3d.in @Unbound3D',
    'Numaker PLA+ @Unbound3D':            'Numaker PLA+ @Unbound3D',
    'Numakers PETG-HS @Unbound3D':        'Numakers petg hs lynx 320 @Unbound3D',
    'TPU Lynx @Unbound3D':                'TPU lynx 230 @Unbound3D',
    'eSUN PA-CF @Unbound3D':              'eSUN PA-CF @Unbound3D',
    'eSUN PA-CF black @Unbound3D':        'eSUN PA-CF black @Unbound3D',
    'eSUN PA-CF Lynx @Unbound3D':         'eSUN PA-CF lynx320 @Unbound3D',
    'eSUN PA-CF @Unbound3D Lynx 320':     'eSUN PA-CF black @MyKlipper 0.4 nozzle @Unbound3D',
    'eSUN PETG-CF @Unbound3D':            'eSUN PETG-CF @Unbound3D',
    'eSUN PLA+ @Unbound3D':               'eSUN PLA+ @Unbound3D',
    'Flex3D PLA+ @Unbound3D':             'flex3d PLA+ @Unbound3D',
    'NFill PLA Glass @Unbound3D':         'nfill pla + glass @Unbound3D',
}

name_translation = {**proc_renames, **fil_renames}


def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(p, obj):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
        f.write('\n')


def update_internal(obj, new_name):
    obj['name'] = new_name
    if 'inherits' in obj:
        obj['inherits'] = name_translation.get(obj['inherits'], obj['inherits'])
    for k in ('print_settings_id', 'filament_settings_id', 'printer_settings_id'):
        if k in obj:
            obj[k] = [new_name]
    if 'compatible_printers' in obj:
        obj['compatible_printers'] = [name_translation.get(x, x) for x in obj['compatible_printers']]
    if 'compatible_prints' in obj:
        obj['compatible_prints'] = [name_translation.get(x, x) for x in obj['compatible_prints']]
    return obj


# -------- FILAMENT migration (load -> rename -> write) ----------
print('=== filament migration ===')
fil_dir = os.path.join(APP_BASE, 'filament')
# Phase 1: read everything we need into memory
loaded = {}
for old in fil_renames:
    p = os.path.join(fil_dir, old + '.json')
    if not os.path.exists(p):
        print('  [!] missing source:', p)
        continue
    loaded[old] = load(p)

# Phase 2: delete old files that won't be reused (only the ones being renamed)
for old, new in fil_renames.items():
    if old == new:
        continue
    src = os.path.join(fil_dir, old + '.json')
    if os.path.exists(src):
        os.remove(src)

# Phase 3: write new files
for old, body in loaded.items():
    new = fil_renames[old]
    update_internal(body, new)
    save(os.path.join(fil_dir, new + '.json'), body)
    print(f'  {old} -> {new}')

# -------- INDEX update ----------
print('\n=== index Unbound3D.json ===')
idx = load(INDEX_PATH)

def rebuild(old_list, renames, deletes, subdir):
    out = []
    for entry in old_list:
        nm = entry['name']
        if nm in deletes:
            print(f'  removed: {nm}')
            continue
        if nm in renames:
            new = renames[nm]
            out.append({'name': new, 'sub_path': f'{subdir}/{new}.json'})
            if new != nm:
                print(f'  rename: {nm} -> {new}')
        else:
            out.append(entry)
    return out

idx['process_list']  = rebuild(idx['process_list'],  proc_renames, proc_delete, 'process')
idx['filament_list'] = rebuild(idx['filament_list'], fil_renames,  [],          'filament')
save(INDEX_PATH, idx)

# -------- MACHINE refs ----------
print('\n=== machine refs ===')
def patch(path, transforms):
    obj = load(path)
    for k, fn in transforms.items():
        if k in obj:
            obj[k] = fn(obj[k])
    save(path, obj)
    print('  patched:', os.path.relpath(path, ROOT))

patch(os.path.join(APP_BASE, 'machine', 'fdm_unbound3d_common.json'),
      {'default_print_profile': lambda v: name_translation.get(v, v)})

patch(os.path.join(APP_BASE, 'machine', 'Unbound3D Lynx 320 0.4 nozzle.json'),
      {'default_print_profile':    lambda v: name_translation.get(v, v),
       'default_filament_profile': lambda v: [name_translation.get(x, x) for x in v]})

def semi(v):
    return ';'.join(name_translation.get(p.strip(), p.strip()) for p in v.split(';'))

patch(os.path.join(APP_BASE, 'machine', 'Unbound3D Lynx 320.json'),
      {'default_materials': semi})

print('\nDONE.')
