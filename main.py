#!/usr/bin/env python
import json
import time
from pathlib import Path
import urllib.request as urlrequest
from urllib.error import HTTPError
import urllib.parse as urlparse
from tempfile import mkdtemp
import zipfile
import sys
import os
import shutil


class FileDeletionException(Exception):
    def __init__(self, path: Path, msg=None):
        self.path = path
        self.msg = msg

    def __str__(self):
        return f"ERROR deleting {self.path} {self.msg if self.msg is not None else ''}"


def is_instance_directory(path: Path):
    return (path / 'minecraft').exists()


def main():
    instance_path = Path(os.getcwd())
    if not is_instance_directory(instance_path):
        print("ERROR: multimc-updater must be executed from within a MultiMC instance directory! Exiting")
        sys.exit(1)

    with (instance_path / "pack_url").open('r') as f:
        pack_url = f.read().strip()
    download_dir = Path(mkdtemp())
    print("=== Downloading update package ===")
    try:
        urlrequest.urlretrieve(pack_url, download_dir / "modpack.zip")
    except HTTPError as e:
        print(f"ERROR: Could not download update package ({pack_url})")
        print(e)
        sys.exit(1)
    extract_dir = (download_dir / 'extract')
    extract_dir.mkdir()
    print("=== Extracting ===")
    with zipfile.ZipFile(download_dir / "modpack.zip", 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    if (extract_dir / 'update.json').exists():
        update_config = json.load((extract_dir / 'update.json').open())
        print("=== Removing files ===")
        for path in update_config['delete']:
            if (instance_path / path).exists():
                print(f"Removing {path}...")
                if (instance_path / path).is_file():
                    (instance_path / path).unlink()
                else:
                    shutil.rmtree(instance_path / path)
        print("=== Copying new files ===")
        for path in update_config['copy']:
            if not (instance_path / path).exists():
                print(f"Copying {path}...")
                if (extract_dir / path).is_file():
                    shutil.copy(extract_dir / path, instance_path / path)
                else:
                    shutil.copytree(extract_dir / path, (instance_path / path))

    if (extract_dir / 'manifest.json').exists():
        print("=== Updating mods ===")
        manifest = json.load((extract_dir / 'manifest.json').open())
        cf_base_url = "https://addons-ecs.forgesvc.net"

        if (instance_path / 'minecraft' / 'mods').exists():
            shutil.move(instance_path / 'minecraft' / 'mods', download_dir / 'mods_old')
        else:
            (download_dir / 'mods_old').mkdir(parents=True, exist_ok=True)
        (instance_path / 'minecraft' / 'mods').mkdir(parents=True, exist_ok=True)
        for mod in manifest['files']:
            api_url = f"{cf_base_url}" \
                f"/api/v2/addon/{mod['projectID']}" \
                f"/file/{mod['fileID']}/download-url"
            error = None
            for i in range(0, 3):
                try:
                    print(f"Requesting {api_url}")
                    with urlrequest.urlopen(api_url) as conn:
                        url = urlparse.urlparse(conn.read().decode('utf-8'))
                        download_url = urlparse.urlunparse((url.scheme,
                                                            url.netloc,
                                                            urlparse.quote(url.path),
                                                            url.params,
                                                            url.query,
                                                            url.fragment))
                        break
                except HTTPError as e:
                    error = e
                    print(f"WARN: {e}")
                    print("Retrying...")
                    time.sleep(3)
            if download_url is None:
                raise error

            file_name = os.path.basename(urlparse.urlparse(download_url).path)
            if (download_dir / 'mods_old' / file_name).exists():
                print(f"{file_name} already exists.")
                shutil.copy(download_dir / 'mods_old' / file_name, instance_path / 'minecraft' / 'mods' / file_name)
            else:
                print(f"Downloading from {download_url}...")
                urlrequest.urlretrieve(download_url, instance_path / 'minecraft' / 'mods' / file_name)

    if (extract_dir / 'modlist.html').exists():
        shutil.copy(extract_dir / 'modlist.html', instance_path / 'modlist.html')

    shutil.rmtree(download_dir)

    print("\nUpdate succesfully installed!")

    input("\nPress ENTER to exit")


if __name__ == '__main__':
    main()
