#!/usr/bin/env python

from pathlib import Path
import json
import os
import hashlib
from tempfile import mkdtemp
from lib import get_download_url
from urllib import parse as urlparse, request as urlrequest


def main():
    cwd = Path(os.getcwd())
    mod_cache = cwd / 'cache' / 'mods'

    with (cwd / 'manifest.json').open() as f:
        manifest = json.load(f)

    if not mod_cache.exists():
        mod_cache.mkdir(parents=True, exist_ok=True)

    manifest_files = []
    for mod in manifest['files']:

        file_path = (mod_cache / f"{mod['projectID']}_{mod['fileID']}.jar")
        if 'md5' in mod:
            if file_path.exists():
                with file_path.open('rb') as f:
                    md5sum = hashlib.md5(f.read()).hexdigest()
                if md5sum == mod['md5']:
                    pass
            print(f"{mod['projectID']}/{mod['fileID']} found in cache. Skipping...")
            continue

        download_url, md5sum = get_download_url(mod['projectID'], mod['fileID'])
        mod['md5'] = md5sum
        mod['downloadUrl'] = download_url
        manifest_files.append(mod)

        print(f"Processed {mod['projectID']}/{mod['fileID']}.")
        print(f"  md5: {md5sum}")
        print(f"  url: {download_url}")

        #file_name = os.path.basename(urlparse.urlparse(download_url).path)
        # print(f"Downloading {mod['projectID']}/{mod['fileID']} from {download_url}...")
        # urlrequest.urlretrieve(download_url, file_path)


        # with
        # md5sum = hashlib.md5

    manifest['files'] = manifest_files
    with (cwd / 'manifest.json').open('w') as f:
        json.dump(manifest, f)


if __name__ == '__main__':
    main()
