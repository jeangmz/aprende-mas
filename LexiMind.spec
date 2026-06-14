# -*- mode: python ; coding: utf-8 -*-
import os
import llama_cpp

basedir = os.path.dirname(os.path.abspath('main.py'))

def walk_rel(src_dir, target_prefix=None):
    entries = []
    if os.path.isdir(src_dir):
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                full_path = os.path.join(root, f)
                if target_prefix is not None:
                    rel_dir = target_prefix
                else:
                    rel_dir = os.path.dirname(os.path.relpath(full_path, basedir))
                entries.append((full_path, rel_dir))
    return entries

extra_datas = []

extra_datas += walk_rel(os.path.join(basedir, 'chat', 'dist'))
extra_datas += walk_rel(os.path.join(basedir, 'config'))
llama_lib = os.path.join(os.path.dirname(llama_cpp.__file__), 'lib')
if os.path.isdir(llama_lib):
    for f in os.listdir(llama_lib):
        full = os.path.join(llama_lib, f)
        if os.path.isfile(full):
            extra_datas.append((full, 'llama_cpp/lib'))

a = Analysis(
    ['main.py'],
    pathex=[basedir],
    binaries=[],
    datas=extra_datas,
    hiddenimports=[
        'fastapi',
        'uvicorn',
        'sqlite3',
        'llama_cpp',
        'sse_starlette',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Aprende+',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
