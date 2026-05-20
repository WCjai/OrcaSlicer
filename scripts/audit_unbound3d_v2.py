"""Re-audit after migration. App names now derived from originals."""
import json, os

META = {
    'type','name','inherits','from','instantiation','setting_id','filament_id',
    'print_settings_id','filament_settings_id','printer_settings_id',
    'compatible_printers','compatible_prints','compatible_printers_condition',
    'compatible_prints_condition','version','is_custom_defined',
    'default_print_profile','default_filament_profile',
}

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_BASE = os.path.join(ROOT, 'Lynx-320.orca_printer')
APP_BASE  = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D')

def load(p):
    with open(p, 'rb') as f:
        return json.loads(f.read().decode('utf-8-sig'))

# Original-name (filename) -> new app filename (no extension)
proc_map = {
    '0.20mm Standard @MyKlipper - Copy': '0.20mm Standard @Unbound3D',
    'Bambulab petg cf lynx320':           '0.20mm Bambulab petg cf lynx320 @Unbound3D',
    'Fibreel PA CF lynx 320':             '0.20mm Fibreel PA CF lynx 320 @Unbound3D',
    'Numaker PLA+':                       '0.20mm Numaker PLA+ @Unbound3D',
    'Numakers petg hs lynx 320':          '0.20mm Numakers petg hs lynx 320 @Unbound3D',
    'TPU 95A':                            '0.20mm TPU 95A @Unbound3D',
    'TPU 95A lynx320':                    '0.20mm TPU 95A lynx320 @Unbound3D',
    'esun pa-cf lynx320':                 '0.20mm esun pa-cf lynx320 @Unbound3D',
    'esun pla+':                          '0.20mm esun pla+ @Unbound3D',
    'fibreel pa-cf lynx320':              '0.20mm fibreel pa-cf lynx320 @Unbound3D',
    'flex 3d pla+':                       '0.20mm flex 3d pla+ @Unbound3D',
}

fil_map = {
    'Bambu PETG-CF Lynx 320':                  'Bambu PETG-CF Lynx 320 @Unbound3D',
    'Fibreel PA-CF black ':                    'Fibreel PA-CF black @Unbound3D',
    'Fibreel PA-CF black lynx 320':            'Fibreel PA-CF black lynx 320 @Unbound3D',
    'Fibreel PA12-CF black ':                  'Fibreel PA12-CF black @Unbound3D',
    'Generic TPU @System - Copy':              'Generic TPU @Unbound3D',
    'Make3d.in':                               'Make3d.in @Unbound3D',
    'Numaker PLA+':                            'Numaker PLA+ @Unbound3D',
    'Numakers petg hs lynx 320':               'Numakers petg hs lynx 320 @Unbound3D',
    'TPU lynx 230':                            'TPU lynx 230 @Unbound3D',
    'eSUN PA-CF':                              'eSUN PA-CF @Unbound3D',
    'eSUN PA-CF black ':                       'eSUN PA-CF black @Unbound3D',
    'eSUN PA-CF black @MyKlipper 0.4 nozzle':  'eSUN PA-CF black @MyKlipper 0.4 nozzle @Unbound3D',
    'eSUN PA-CF blck @MyKlipper 0.4 nozzle':   None,  # typo dup
    'eSUN PA-CF lynx320':                      'eSUN PA-CF lynx320 @Unbound3D',
    'eSUN PETG-CF':                            'eSUN PETG-CF @Unbound3D',
    'eSUN PLA+ @System - Copy':                'eSUN PLA+ @Unbound3D',
    'flex3d PLA+ @System - Copy':              'flex3d PLA+ @Unbound3D',
    'nfill pla + glass':                       'nfill pla + glass @Unbound3D',
}

def hdr(t):
    print('\n' + '='*72)
    print(t)
    print('='*72)

issues_total = 0
extras_total = 0

def audit(orig_dir, app_dir, mapping, kind):
    global issues_total
    hdr(f'AUDIT: {kind.upper()}  (originals={len(mapping)})')
    ok_count = 0
    for orig_name, app_name in mapping.items():
        orig_path = os.path.join(orig_dir, orig_name + '.json')
        if not os.path.exists(orig_path):
            print(f'  [!] orig missing: {orig_name}')
            continue
        orig = load(orig_path)
        if app_name is None:
            continue  # intentional drop
        app_path = os.path.join(app_dir, app_name + '.json')
        if not os.path.exists(app_path):
            print(f'  [!] APP MISSING: {app_name}')
            issues_total += 1
            continue
        app = load(app_path)
        orig_keys = set(orig.keys()) - META
        app_keys  = set(app.keys()) - META
        missing = sorted(orig_keys - app_keys)
        mism = [(k, orig[k], app[k]) for k in sorted(orig_keys & app_keys)
                if orig[k] != app[k]]
        if not missing and not mism:
            ok_count += 1
        else:
            issues_total += 1
            print(f'\n[ISSUE] {orig_name!r} -> {app_name!r}')
            if missing:
                print('   MISSING (' + str(len(missing)) + '):')
                for k in missing:
                    print(f'      {k} = {orig[k]!r}')
            if mism:
                print('   MISMATCH (' + str(len(mism)) + '):')
                for k, o, a in mism:
                    print(f'      {k}: orig={o!r}  app={a!r}')
    print(f'\n   {kind}: {ok_count} OK,  ' +
          f'{len(mapping) - ok_count - sum(1 for v in mapping.values() if v is None)} with issues' +
          f',  {sum(1 for v in mapping.values() if v is None)} intentionally dropped')

audit(os.path.join(ORIG_BASE, 'process'),  os.path.join(APP_BASE, 'process'),  proc_map, 'process')
audit(os.path.join(ORIG_BASE, 'filament'), os.path.join(APP_BASE, 'filament'), fil_map,  'filament')

# Extras check
hdr('APP-ONLY EXTRAS (files in app without an original counterpart)')
COMMON = {
    'fdm_process_common.json', 'fdm_process_unbound3d_common.json',
    'fdm_filament_common.json',
    'fdm_machine_common.json', 'fdm_unbound3d_common.json',
    'Unbound3D Lynx 320.json', 'Unbound3D Lynx 320 0.4 nozzle.json',
}
for sub, mapping in (('process', proc_map), ('filament', fil_map)):
    mapped = {v + '.json' for v in mapping.values() if v}
    have   = set(os.listdir(os.path.join(APP_BASE, sub)))
    extras = sorted(have - mapped - COMMON)
    print(f'[{sub}] extras = {extras}')
    extras_total += len(extras)

# Index sanity check
hdr('INDEX (Unbound3D.json) CONSISTENCY')
idx = load(os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D.json'))
def check_index(lst, subdir, label):
    bad = 0
    for entry in lst:
        nm = entry['name']
        sp = entry['sub_path']
        if not sp.startswith(subdir + '/'):
            print(f'  [!] {label}: wrong subdir: {entry}')
            bad += 1
            continue
        fname = sp[len(subdir)+1:]
        full = os.path.join(APP_BASE, subdir, fname)
        if not os.path.exists(full):
            print(f'  [!] {label}: file missing: {sp}')
            bad += 1
        else:
            body = load(full)
            if body.get('name') != nm:
                print(f'  [!] {label}: name mismatch index={nm!r} vs file name={body.get("name")!r}')
                bad += 1
    if bad == 0:
        print(f'  {label}: all {len(lst)} entries resolve & match.')

check_index(idx['process_list'],  'process',  'process_list')
check_index(idx['filament_list'], 'filament', 'filament_list')
check_index(idx['machine_list'],  'machine',  'machine_list')

# Machine default refs
hdr('MACHINE DEFAULT REFERENCES')
def field_in_file(rel, key):
    obj = load(os.path.join(APP_BASE, rel))
    return obj.get(key)

for rel, key in [
    ('machine/fdm_unbound3d_common.json',          'default_print_profile'),
    ('machine/Unbound3D Lynx 320 0.4 nozzle.json', 'default_print_profile'),
    ('machine/Unbound3D Lynx 320 0.4 nozzle.json', 'default_filament_profile'),
    ('machine/Unbound3D Lynx 320.json',            'default_materials'),
]:
    print(f'  {rel}::{key} = {field_in_file(rel, key)!r}')

# Inherits-resolution check
hdr('INHERITS CHAIN RESOLUTION')
def collect_names(subdir):
    out = set()
    for f in os.listdir(os.path.join(APP_BASE, subdir)):
        if f.endswith('.json'):
            out.add(f[:-5])
    return out

proc_names = collect_names('process')
fil_names  = collect_names('filament')
mach_names = collect_names('machine')
ALL_NAMES  = proc_names | fil_names | mach_names | {
    'fdm_process_common', 'fdm_process_unbound3d_common', 'fdm_filament_common',
    'fdm_machine_common', 'fdm_unbound3d_common',
}

unresolved = 0
for sub in ('process', 'filament', 'machine'):
    for fname in os.listdir(os.path.join(APP_BASE, sub)):
        if not fname.endswith('.json'):
            continue
        body = load(os.path.join(APP_BASE, sub, fname))
        inh = body.get('inherits')
        if inh and inh not in ALL_NAMES:
            print(f'  [!] {sub}/{fname}: inherits {inh!r} -> not found in profile tree')
            unresolved += 1
if unresolved == 0:
    print('  all inherits resolve.')

hdr('SUMMARY')
print(f'  parameter issues = {issues_total}')
print(f'  app-only extras  = {extras_total}')
print(f'  inherit unresolved = {unresolved}')
