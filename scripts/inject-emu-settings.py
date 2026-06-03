#!/usr/bin/env python3
"""
Injects Clay settings into the Pebble emulator's localStorage.

Usage: python3 scripts/inject-emu-settings.py [settings-file] [platform]
Default settings file: emu-settings.json
Default platform: emery

pypkjs uses Python's dbm.dumb format for localStorage, stored in:
~/.pebble-emu/<platform>/localstorage/<app-uuid>
"""

import dbm.dumb
import json
import os
import sys
from pathlib import Path

def main():
    settings_file = sys.argv[1] if len(sys.argv) > 1 else 'emu-settings.json'
    platform = sys.argv[2] if len(sys.argv) > 2 else 'emery'

    # Read the app's UUID from package.json
    with open('package.json', 'r') as f:
        package_json = json.load(f)
    app_uuid = package_json['pebble']['uuid']

    # Path to emulator's localStorage (dbm.dumb format)
    # pypkjs uses: ~/Library/Application Support/Pebble SDK/<version>/<platform>/localstorage/
    pebble_sdk_dir = Path.home() / 'Library' / 'Application Support' / 'Pebble SDK'

    # Find the current SDK version by checking which one is linked
    current_sdk = pebble_sdk_dir / 'SDKs' / 'current'
    if current_sdk.is_symlink():
        sdk_version = current_sdk.resolve().name
    else:
        # Fall back to finding the latest version
        versions = [d.name for d in (pebble_sdk_dir).iterdir() if d.is_dir() and d.name[0].isdigit()]
        sdk_version = sorted(versions)[-1] if versions else None
        if not sdk_version:
            print("Could not find Pebble SDK version", file=sys.stderr)
            sys.exit(1)

    emu_dir = pebble_sdk_dir / sdk_version / platform / 'localstorage'
    db_path = emu_dir / app_uuid

    print(f"SDK version: {sdk_version}")

    # Read settings to inject
    if not os.path.exists(settings_file):
        print(f"Settings file not found: {settings_file}", file=sys.stderr)
        print("\nCreate emu-settings.json with your Clay settings, e.g.:", file=sys.stderr)
        print(json.dumps({
            "accountName": "your_dexcom_username",
            "password": "your_dexcom_password",
            "server": "us",
            "unit": "mgdl",
            "reversed": False,
            "lowThreshold": 70,
            "highThreshold": 180,
            "vibeLowSoonEnabled": False,
            "vibeLowSoonThreshold": 80,
            "vibeLowSoonRepeatMinutes": 30,
            "vibeEnabled": False,
            "vibeHighThreshold": 250,
            "vibeDelayMinutes": 60,
            "vibeRepeatMinutes": 60,
            "saltieApiToken": ""
        }, indent=2), file=sys.stderr)
        sys.exit(1)

    with open(settings_file, 'r') as f:
        settings = json.load(f)

    # Ensure emulator directory exists
    emu_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing db files if they exist
    for ext in ['', '.dat', '.dir', '.bak']:
        try:
            os.remove(str(db_path) + ext)
        except FileNotFoundError:
            pass

    # Create new db with settings
    db = dbm.dumb.open(str(db_path), 'c')
    db['clay-settings'] = json.dumps(settings)
    db.close()

    print(f"Injected settings into {db_path}")
    print(f"App UUID: {app_uuid}")
    print(f"Settings: {json.dumps(settings, indent=2)}")

if __name__ == '__main__':
    main()
