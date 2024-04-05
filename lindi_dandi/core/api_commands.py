import os
import requests
from datetime import datetime


def create_dandiset(*, name: str, embargo: bool):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")
    url = "https://api-staging.dandiarchive.org/api/dandisets/?embargo=" + str(embargo).lower()
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {DANDI_STAGING_API_KEY}"
    }
    data = {
        "metadata": {},
        "name": name
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    dandiset_id = response.json()["identifier"]
    return dandiset_id


def delete_dandiset(dandiset_id: str):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")
    okay_to_delete = input(f"Are you sure you want to delete dandiset {dandiset_id}? (y/n) ")
    if okay_to_delete.lower() != "y":
        print("Aborting")
        return
    url = f"https://api-staging.dandiarchive.org/api/dandisets/{dandiset_id}/"
    headers = {
        "accept": "application/json",
        "Authorization": f"token {DANDI_STAGING_API_KEY}"
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def create_asset(*, dandiset_id: str, dandiset_version: str, local_filename: str, asset_path: str, replace_existing: bool = False, leave_existing: bool = False):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")

    blob_id = _upload_blob(dandiset_id=dandiset_id, dandiset_version=dandiset_version, local_filename=local_filename)

    # Now that we have a new blob, we can create the asset
    url = f"https://api-staging.dandiarchive.org/api/dandisets/{dandiset_id}/versions/{dandiset_version}/assets/"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {DANDI_STAGING_API_KEY}"
    }
    mtime = os.path.getmtime(local_filename)
    blob_data_modified = datetime.fromtimestamp(mtime).isoformat()  # e.g., 2024-03-19T12:45:23.897541-04:00
    data = {
        "metadata": {
            "path": asset_path,
            "blobDateModified": blob_data_modified,
        },
        "blob_id": blob_id
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 409:
        if replace_existing:
            remove_asset(dandiset_id=dandiset_id, dandi_version=dandiset_version, path=asset_path)
            response = requests.post(url, headers=headers, json=data)
        else:
            if leave_existing:
                # In this case we need to search for the asset so we can get the asset id (it would be nice if it was returned in the 409 response headers)
                asset_id = get_asset_id_for_path(dandiset_id=dandiset_id, dandiset_version=dandiset_version, path=asset_path)
                download_url = f'https://api-staging.dandiarchive.org/api/assets/{asset_id}/download/'
                return {
                    "asset_id": asset_id,
                    "download_url": download_url
                }
            raise ValueError(f"Asset {asset_path} already exists in dandiset {dandiset_id}")
    response.raise_for_status()
    asset_id = response.json()["asset_id"]
    # blob: str = response.json()["blob"]  # uuid
    # zarr: str = response.json()["zarr"]  # uuid
    # path: str = response.json()["path"]
    # size: int = response.json()["size"]
    # created: str = response.json()["created"]  # $date-time
    # modified: str = response.json()["modified"]  # $date-time
    # metadata: dict = response.json()["metadata"]
    return {
        "asset_id": asset_id,
        "download_url": f'https://api-staging.dandiarchive.org/api/assets/{asset_id}/download/'
    }


def remove_asset(*, dandiset_id: str, dandi_version: str, path: str):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")
    okay_to_delete = input(f"Are you sure you want to remove asset {path} from dandiset {dandiset_id}? (y/n) ")
    if okay_to_delete.lower() != "y":
        print("Aborting")
        return
    asset_id = get_asset_id_for_path(dandiset_id=dandiset_id, dandiset_version=dandi_version, path=path)
    url = f"https://api-staging.dandiarchive.org/api/dandisets/{dandiset_id}/versions/{dandi_version}/assets/{asset_id}/"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {DANDI_STAGING_API_KEY}"
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def get_asset_id_for_path(*, dandiset_id: str, dandiset_version: str, path: str):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")
    page_size = 1000
    page = 1  # should this be 1-indexed or 0-indexed?
    path_prefix = _get_path_prefix(path)
    url = f"https://api-staging.dandiarchive.org/api/dandisets/{dandiset_id}/versions/{dandiset_version}/assets/paths/?page={page}&page_size={page_size}&path_prefix={path_prefix}"
    while True:
        headers = {
            "accept": "application/json",
            "Authorization": f"token {DANDI_STAGING_API_KEY}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        rr = response.json()
        next = rr['next']
        results = rr['results']
        for result in results:
            if result["path"] == path:
                asset = result['asset']
                if not asset:
                    raise ValueError(f"Asset for {path} not found in dandiset {dandiset_id}")
                return asset['asset_id']
        if not next:
            raise ValueError(f"Asset {path} not found in dandiset {dandiset_id}")
        url = next


def _get_path_prefix(path: str):
    parts = path.split("/")
    if len(parts) == 1:
        return ""
    return "/".join(parts[:-1])


def _upload_blob(*, dandiset_id: str, dandiset_version: str, local_filename: str):
    from dandi.support.digests import get_dandietag
    etagger = get_dandietag(local_filename)
    print(f'Initializing multipart upload for {local_filename} with dandi-etag {etagger.as_str()}')
    upload_id, parts, blob_id = _initialize_multipart_upload(dandiset_id=dandiset_id, local_filename=local_filename, etagger=etagger)
    if blob_id is not None:
        # this means the blob already exists
        return blob_id
    assert upload_id is not None, "Unexpected error: upload_id is None"
    assert parts is not None, "Unexpected error: parts is None"
    processed_parts = []
    for part in parts:
        part_number = part["part_number"]
        etag_part = etagger.get_part(part["part_number"])
        part_size = part["size"]
        if etag_part.size != part_size:
            raise ValueError(f"Part {part_number} is not the expected size: {etag_part.size} != {part_size}")
        part_upload_url = part["upload_url"]
        with open(local_filename, "rb") as f:
            f.seek(etag_part.offset)
            part_data = f.read(etag_part.size)
        response = requests.put(part_upload_url, data=part_data)
        response.raise_for_status()
        processed_parts.append({
            "part_number": part_number,
            "size": part_size,
            "etag": response.headers["ETag"].strip('"')  # note that this is the server's ETag not the dandi-etag
        })
    print(f'Completing multipart upload for {local_filename}')
    complete_url, response_body = _complete_multipart_upload(upload_id=upload_id, processed_parts=processed_parts)
    # To actually perform the upload, we need to send a request to the complete_url
    response = requests.post(complete_url, data=response_body)
    response.raise_for_status()

    # Finally we validate to verify the upload and mint the new asset blob
    print(f'Validating multipart upload for {local_filename}')
    info = _validate_multipart_upload(upload_id=upload_id)
    blob_id = info["blob_id"]
    print(f'Created blob {blob_id} for {local_filename}')
    return blob_id


def _initialize_multipart_upload(*, dandiset_id: str, local_filename: str, etagger):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")
    url = "https://api-staging.dandiarchive.org/api/uploads/initialize/"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {DANDI_STAGING_API_KEY}"
    }
    filetag = etagger.as_str()
    data = {
        "contentSize": os.path.getsize(local_filename),
        "digest": {
            "algorithm": "dandi:dandi-etag",
            "value": filetag
        },
        "dandiset": dandiset_id
    }
    response = requests.post(url, headers=headers, json=data)
    # check if response code is 409, which means the blob already exists
    if response.status_code == 409:
        # get the blob_id from the Location header
        blob_id = response.headers["Location"]
        if not isinstance(blob_id, str):
            raise ValueError("Unexpected error: blob_id is not a string, from Location header")
        print(f'Blob {blob_id} already exists for {local_filename}')
        return None, None, blob_id
    response.raise_for_status()
    upload_id = response.json()["upload_id"]
    parts = response.json()["parts"]
    return upload_id, parts, None


def _complete_multipart_upload(*, upload_id: str, processed_parts: list):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")
    url = f"https://api-staging.dandiarchive.org/api/uploads/{upload_id}/complete/"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {DANDI_STAGING_API_KEY}"
    }
    data = {
        "parts": processed_parts
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    complete_url = response.json()["complete_url"]
    response_body = response.json()["body"]
    return complete_url, response_body


def _validate_multipart_upload(*, upload_id: str):
    DANDI_STAGING_API_KEY = os.getenv("DANDI_STAGING_API_KEY", None)
    if DANDI_STAGING_API_KEY is None:
        raise ValueError("DANDI_STAGING_API_KEY is not set")
    url = f"https://api-staging.dandiarchive.org/api/uploads/{upload_id}/validate/"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {DANDI_STAGING_API_KEY}"
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    blob_id = response.json()["blob_id"]
    etag = response.json()["etag"]
    sha256 = response.json()["sha256"]
    size = response.json()["size"]
    return {
        "blob_id": blob_id,
        "etag": etag,
        "sha256": sha256,
        "size": size
    }
