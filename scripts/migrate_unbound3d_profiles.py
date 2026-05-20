"""Migrate Unbound3D profiles to original-based names + apply parameter fixes.

Plan
----
1. Strategy for the two pairs of swapped-content profiles: rename the FILES so
   the content lands at the proper original-derived filename (no content
   editing required for the swap itself).
2. Add the 5 missing acceleration params to 0.20mm Standard.
3. Add the 5 missing speed params to the slow TPU profile (after rename).
4. Delete the extra 0.20mm Standard Alt file.
5. Rename remaining files to `0.20mm <orig> @Unbound3D` (processes) or
   `<orig> @Unbound3D` (filaments).
6. Update internal name / *_settings_id / inherits / compatible_printers in
   each file.
7. Update Unbound3D.json index, fdm_unbound3d_common.json default_print_profile,
   Unbound3D Lynx 320.json default_materials, and
   Unbound3D Lynx 320 0.4 nozzle.json default_print_profile / default_filament_profile.
"""
import json, os, shutil

ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_BASE   = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D')
INDEX_PATH = os.path.join(ROOT, 'resources', 'profiles', 'Unbound3D.json')
SUFFIX     = ' @Unbound3D'

# -----------------------------------------------------------------------------
# Process renames: current (in-app) base name -> new base name
# (file is base+'.json')
# After value-swap-via-rename, the file 'TPU 95A Alt' (fast content) becomes
# 'TPU 95A' and 'TPU 95A' (slow content) becomes 'TPU 95A lynx320'.
proc_renames = {
    '0.20mm Standard @Unbound3D':           '0.20mm Standard @Unbound3D',  # keep
    '0.20mm PETG-CF Bambu @Unbound3D':      '0.20mm Bambulab petg cf lynx320 @Unbound3D',
    '0.20mm PA-CF Fibreel @Unbound3D':      '0.20mm Fibreel PA CF lynx 320 @Unbound3D',
    '0.20mm PLA+ Numaker @Unbound3D':       '0.20mm Numaker PLA+ @Unbound3D',
    '0.20mm PETG-HS Numaker @Unbound3D':    '0.20mm Numakers petg hs lynx 320 @Unbound3D',
    # SWAP via rename: file with fast content (currently Alt) becomes 'TPU 95A'
    '0.20mm TPU 95A Alt @Unbound3D':        '0.20mm TPU 95A @Unbound3D',
    # file with slow content (currently named TPU 95A) becomes 'TPU 95A lynx320'
    '0.20mm TPU 95A @Unbound3D':            '0.20mm TPU 95A lynx320 @Unbound3D',
    '0.20mm PA-CF eSUN @Unbound3D':         '0.20mm esun pa-cf lynx320 @Unbound3D',
    '0.20mm PLA+ eSUN @Unbound3D':          '0.20mm esun pla+ @Unbound3D',
    '0.20mm PA-CF Fibreel Alt @Unbound3D':  '0.20mm fibreel pa-cf lynx320 @Unbound3D',
    '0.20mm PLA+ Flex3D @Unbound3D':        '0.20mm flex 3d pla+ @Unbound3D',
}
proc_delete = ['0.20mm Standard Alt @Unbound3D']  # extra, no original

# Filament renames: current -> new
# SWAP via rename: file 'eSUN PA-CF Lynx' has lynx320 content -> rename to 'eSUN PA-CF lynx320'
# file 'eSUN PA-CF @Unbound3D Lynx 320' has black@MyKlipper content -> rename to 'eSUN PA-CF black @MyKlipper 0.4 nozzle'
fil_renames = {
    'Bambu PETG-CF @Unbound3D':           'Bambu PETG-CF Lynx 320 @Unbound3D',
    'Fibreel PA-CF black @Unbound3D':     'Fibreel PA-CF black @Unbound3D',  # keep
    'Fibreel PA-CF Lynx @Unbound3D':      'Fibreel PA-CF black lynx 320 @Unbound3D',
    'Fibreel PA12-CF @Unbound3D':         'Fibreel PA12-CF black @Unbound3D',
    'Generic TPU @Unbound3D':             'Generic TPU @Unbound3D',  # keep
    'Make3D PLA @Unbound3D':              'Make3d.in @Unbound3D',
    'Numaker PLA+ @Unbound3D':            'Numaker PLA+ @Unbound3D',  # keep
    'Numakers PETG-HS @Unbound3D':        'Numakers petg hs lynx 320 @Unbound3D',
    'TPU Lynx @Unbound3D':                'TPU lynx 230 @Unbound3D',
    'eSUN PA-CF @Unbound3D':              'eSUN PA-CF @Unbound3D',  # keep
    'eSUN PA-CF black @Unbound3D':        'eSUN PA-CF black @Unbound3D',  # keep
    'eSUN PA-CF Lynx @Unbound3D':         'eSUN PA-CF lynx320 @Unbound3D',
    'eSUN PA-CF @Unbound3D Lynx 320':     'eSUN PA-CF black @MyKlipper 0.4 nozzle @Unbound3D',
    'eSUN PETG-CF @Unbound3D':            'eSUN PETG-CF @Unbound3D',  # keep
    'eSUN PLA+ @Unbound3D':               'eSUN PLA+ @Unbound3D',  # keep
    'Flex3D PLA+ @Unbound3D':             'flex3d PLA+ @Unbound3D',
    'NFill PLA Glass @Unbound3D':         'nfill pla + glass @Unbound3D',
}

# -----------------------------------------------------------------------------
# Parameter additions
PROC_PARAM_ADDS = {
    # by NEW name
    '0.20mm Standard @Unbound3D': {
        'default_acceleration':     '3000',
        'inner_wall_acceleration':  '1500',
        'outer_wall_acceleration':  '1500',
        'top_surface_acceleration': '800',
        'travel_acceleration':      '3000',
    },
    '0.20mm TPU 95A lynx320 @Unbound3D': {
        'initial_layer_infill_speed': '35',
        'initial_layer_speed':        '35',
        'small_perimeter_speed':      '100%',
        'sparse_infill_speed':        '35',
        'support_speed':              '35',
    },
}

# -----------------------------------------------------------------------------
# Build name-translation tables for inherits/compat-printer/etc.
# Old reference name -> new reference name (without .json)
name_translation = {}
name_translation.update(proc_renames)
name_translation.update(fil_renames)


def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(p, obj):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
        f.write('\n')


def translate_list_field(val, mapping):
    """Replace any matching name found inside a list-of-strings."""
    if isinstance(val, list):
        return [mapping.get(x, x) for x in val]
    return mapping.get(val, val)


def translate_semicolon_field(val, mapping):
    """Replace names inside a 'A;B;C' string."""
    if isinstance(val, str) and ';' in val:
        parts = val.split(';')
        return ';'.join(mapping.get(p.strip(), p.strip()) for p in parts)
    return mapping.get(val, val)


def update_internal_refs(obj, new_name):
    """Update name + any cross-reference fields inside a profile JSON to use
    the new naming scheme."""
    obj['name'] = new_name
    # inherits
    if 'inherits' in obj:
        obj['inherits'] = name_translation.get(obj['inherits'], obj['inherits'])
    # *_settings_id (always list)
    for k in ('print_settings_id', 'filament_settings_id', 'printer_settings_id'):
        if k in obj:
            # The settings_id should match the new profile name
            obj[k] = [new_name]
    # compatible_printers
    if 'compatible_printers' in obj:
        obj['compatible_printers'] = [
            name_translation.get(x, x) for x in obj['compatible_printers']
        ]
    # compatible_prints
    if 'compatible_prints' in obj:
        obj['compatible_prints'] = [
            name_translation.get(x, x) for x in obj['compatible_prints']
        ]
    return obj


# =============================================================================
# 1. Load every profile into memory, keyed by OLD base name
# =============================================================================
def load_dir(subdir, renames, deletes):
    data = {}
    for fname in os.listdir(os.path.join(APP_BASE, subdir)):
        if not fname.endswith('.json'):
            continue
        base = fname[:-5]
        if base in deletes:
            continue
        data[base] = load(os.path.join(APP_BASE, subdir, fname))
    return data

proc_data = load_dir('process',  proc_renames, proc_delete)
fil_data  = load_dir('filament', fil_renames,  [])

# =============================================================================
# 2. Wipe out old process/filament files (we'll re-emit under new names)
#    Keep base/common files (those not in our rename map).
# =============================================================================
def cleanup_dir(subdir, renames, deletes):
    targets = set(renames.keys()) | set(deletes)
    for fname in os.listdir(os.path.join(APP_BASE, subdir)):
        if not fname.endswith('.json'):
            continue
        base = fname[:-5]
        if base in targets:
            os.remove(os.path.join(APP_BASE, subdir, fname))
            print('  deleted:', subdir + '/' + fname)

print('\n=== removing old files ===')
cleanup_dir('process',  proc_renames, proc_delete)
cleanup_dir('filament', fil_renames,  [])

# =============================================================================
# 3. Emit each profile under its NEW name, with updated internal refs.
# =============================================================================
print('\n=== writing process files ===')
for old, body in proc_data.items():
    new = proc_renames[old]
    update_internal_refs(body, new)
    # Apply param additions for NEW name
    if new in PROC_PARAM_ADDS:
        body.update(PROC_PARAM_ADDS[new])
    save(os.path.join(APP_BASE, 'process', new + '.json'), body)
    print(f'  {old}.json -> {new}.json')

print('\n=== writing filament files ===')
for old, body in fil_data.items():
    new = fil_renames[old]
    update_internal_refs(body, new)
    save(os.path.join(APP_BASE, 'filament', new + '.json'), body)
    print(f'  {old}.json -> {new}.json')

# =============================================================================
# 4. Update Unbound3D.json index
# =============================================================================
print('\n=== updating Unbound3D.json index ===')
idx = load(INDEX_PATH)

def rebuild_list(old_list, renames, deletes, subdir):
    out = []
    for entry in old_list:
        nm = entry['name']
        if nm in deletes:
            print(f'  removed from index: {nm}')
            continue
        if nm in renames:
            new = renames[nm]
            out.append({'name': new, 'sub_path': f'{subdir}/{new}.json'})
            if new != nm:
                print(f'  index: {nm} -> {new}')
        else:
            out.append(entry)  # preserve commons (fdm_process_common etc.)
    return out

idx['process_list']  = rebuild_list(idx['process_list'],  proc_renames, proc_delete, 'process')
idx['filament_list'] = rebuild_list(idx['filament_list'], fil_renames,  [],          'filament')
save(INDEX_PATH, idx)

# =============================================================================
# 5. Update machine files for new default refs
# =============================================================================
print('\n=== updating machine refs ===')
def patch_json(path, transforms):
    obj = load(path)
    for key, fn in transforms.items():
        if key in obj:
            obj[key] = fn(obj[key])
    save(path, obj)
    print('  patched:', os.path.relpath(path, ROOT))

patch_json(
    os.path.join(APP_BASE, 'machine', 'fdm_unbound3d_common.json'),
    {'default_print_profile': lambda v: name_translation.get(v, v)},
)
patch_json(
    os.path.join(APP_BASE, 'machine', 'Unbound3D Lynx 320 0.4 nozzle.json'),
    {
        'default_print_profile':    lambda v: name_translation.get(v, v),
        'default_filament_profile': lambda v: [name_translation.get(x, x) for x in v],
    },
)
patch_json(
    os.path.join(APP_BASE, 'machine', 'Unbound3D Lynx 320.json'),
    {
        'default_materials': lambda v: translate_semicolon_field(v, name_translation),
    },
)

print('\nDONE.')
