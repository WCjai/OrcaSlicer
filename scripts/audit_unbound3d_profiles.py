"""Audit Unbound3D profiles against original Lynx-320.orca_printer bundle."""
import json, os, sys

# Application-specific metadata fields (allowed to differ between original/app)
META = {
    'type','name','inherits','from','instantiation','setting_id','filament_id',
    'print_settings_id','filament_settings_id','printer_settings_id',
    'compatible_printers','compatible_prints','compatible_printers_condition',
    'compatible_prints_condition','version','is_custom_defined',
    'default_print_profile','default_filament_profile',
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIG_BASE = os.path.join(ROOT, 'Lynx-320.orca_printer')
APP_BASE  = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D')

def load(p):
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        return json.load(f)

# Mapping (original filename without ext -> app filename without ext)
proc_map = {
    '0.20mm Standard @MyKlipper - Copy': '0.20mm Standard @Unbound3D',
    'Bambulab petg cf lynx320':           '0.20mm PETG-CF Bambu @Unbound3D',
    'Fibreel PA CF lynx 320':             '0.20mm PA-CF Fibreel @Unbound3D',
    'Numaker PLA+':                       '0.20mm PLA+ Numaker @Unbound3D',
    'Numakers petg hs lynx 320':          '0.20mm PETG-HS Numaker @Unbound3D',
    'TPU 95A':                            '0.20mm TPU 95A @Unbound3D',
    'TPU 95A lynx320':                    '0.20mm TPU 95A Alt @Unbound3D',
    'esun pa-cf lynx320':                 '0.20mm PA-CF eSUN @Unbound3D',
    'esun pla+':                          '0.20mm PLA+ eSUN @Unbound3D',
    'fibreel pa-cf lynx320':              '0.20mm PA-CF Fibreel Alt @Unbound3D',
    'flex 3d pla+':                       '0.20mm PLA+ Flex3D @Unbound3D',
}

fil_map = {
    'Bambu PETG-CF Lynx 320':                  'Bambu PETG-CF @Unbound3D',
    'Fibreel PA-CF black ':                    'Fibreel PA-CF black @Unbound3D',
    'Fibreel PA-CF black lynx 320':            'Fibreel PA-CF Lynx @Unbound3D',
    'Fibreel PA12-CF black ':                  'Fibreel PA12-CF @Unbound3D',
    'Generic TPU @System - Copy':              'Generic TPU @Unbound3D',
    'Make3d.in':                               'Make3D PLA @Unbound3D',
    'Numaker PLA+':                            'Numaker PLA+ @Unbound3D',
    'Numakers petg hs lynx 320':               'Numakers PETG-HS @Unbound3D',
    'TPU lynx 230':                            'TPU Lynx @Unbound3D',
    'eSUN PA-CF':                              'eSUN PA-CF @Unbound3D',
    'eSUN PA-CF black ':                       'eSUN PA-CF black @Unbound3D',
    'eSUN PA-CF black @MyKlipper 0.4 nozzle':  'eSUN PA-CF Lynx @Unbound3D',
    'eSUN PA-CF blck @MyKlipper 0.4 nozzle':   None,  # typo dup
    'eSUN PA-CF lynx320':                      'eSUN PA-CF @Unbound3D Lynx 320',
    'eSUN PETG-CF':                            'eSUN PETG-CF @Unbound3D',
    'eSUN PLA+ @System - Copy':                'eSUN PLA+ @Unbound3D',
    'flex3d PLA+ @System - Copy':              'Flex3D PLA+ @Unbound3D',
    'nfill pla + glass':                       'NFill PLA Glass @Unbound3D',
}

def hdr(t):
    print('\n' + '='*72)
    print(t)
    print('='*72)

def audit(orig_dir, app_dir, mapping, kind):
    hdr(f'AUDIT: {kind.upper()}  (original count={len(mapping)})')
    for orig_name, app_name in mapping.items():
        orig_path = os.path.join(orig_dir, orig_name + '.json')
        print('\n-- ORIG: ' + orig_name)
        if not os.path.exists(orig_path):
            print('   [!] original file missing on disk')
            continue
        orig = load(orig_path)
        if app_name is None:
            print('   APP : (none mapped) -> appears to be intentional drop (typo duplicate)')
            continue
        print('   APP : ' + app_name)
        app_path = os.path.join(app_dir, app_name + '.json')
        if not os.path.exists(app_path):
            print('   [!] APP FILE NOT FOUND: ' + app_path)
            continue
        app = load(app_path)
        orig_keys = set(orig.keys()) - META
        app_keys  = set(app.keys())  - META
        missing = sorted(orig_keys - app_keys)
        extra   = sorted(app_keys - orig_keys)
        mism    = []
        for k in sorted(orig_keys & app_keys):
            if orig[k] != app[k]:
                mism.append((k, orig[k], app[k]))
        if not missing and not mism:
            print('   OK (all original parameters present and values match)')
            if extra:
                # extras are normal (app uses inheritance / extras)
                pass
        else:
            if missing:
                print('   [MISSING IN APP] (' + str(len(missing)) + '):')
                for k in missing:
                    print('      ' + k + ' = ' + repr(orig[k]))
            if mism:
                print('   [VALUE MISMATCH] (' + str(len(mism)) + '):')
                for k, o, a in mism:
                    print('      ' + k + ':')
                    print('         orig = ' + repr(o))
                    print('         app  = ' + repr(a))

audit(os.path.join(ORIG_BASE, 'process'),  os.path.join(APP_BASE, 'process'),  proc_map, 'process')
audit(os.path.join(ORIG_BASE, 'filament'), os.path.join(APP_BASE, 'filament'), fil_map,  'filament')

# Identify app-only extras (not mapped from any original)
hdr('APP FILES WITHOUT ORIGINAL COUNTERPART (potential extras)')
COMMON = {
    'fdm_process_common.json','fdm_process_unbound3d_common.json',
    'fdm_filament_common.json',
    'fdm_machine_common.json','fdm_unbound3d_common.json',
    'Unbound3D Lynx 320.json','Unbound3D Lynx 320 0.4 nozzle.json',
}

for sub, mapping in (('process', proc_map), ('filament', fil_map)):
    mapped = {v + '.json' for v in mapping.values() if v}
    have   = set(os.listdir(os.path.join(APP_BASE, sub)))
    extras = sorted(have - mapped - COMMON)
    print('\n[' + sub + ']  extras = ' + str(extras))

# Machine folder
print('\n[machine] files:')
for f in sorted(os.listdir(os.path.join(APP_BASE, 'machine'))):
    print('  ' + f)
