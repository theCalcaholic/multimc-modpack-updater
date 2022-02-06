from urllib import request as urlrequest, parse as urlparse
from urllib.error import HTTPError
import json
import time


CURSE_FORGE_BASE_URL = "https://addons-ecs.forgesvc.net"


def get_download_url(project_id, file_id):
    api_url = f"{CURSE_FORGE_BASE_URL}/api/v2/addon/{project_id}/file/{file_id}"
    error = None
    for i in range(0, 3):
        try:
            print(f"Requesting {api_url}")
            with urlrequest.urlopen(api_url) as conn:
                resp = json.loads(conn.read().decode('utf-8'))
                url = urlparse.urlparse(resp['downloadUrl'])
                md5sum = next((h['value'] for h in resp['hashes'] if h['algorithm'] == 2), None)
                download_url = urlparse.urlunparse((url.scheme,
                                                    url.netloc,
                                                    urlparse.quote(url.path),
                                                    url.params,
                                                    url.query,
                                                    url.fragment))
                return download_url, md5sum
        except HTTPError as e:
            error = e
            print(f"WARN: {e}")
            print("Retrying...")
            time.sleep(3)

    raise error
