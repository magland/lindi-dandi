import hashlib
import lindi
from lindi_dandi import create_asset
from lindi.LindiStagingStore import StagingArea
from helpers.add_autocorrelograms import add_autocorrelograms

# This script downloads an NWB file from DANDI, adds autocorrelograms, and
# uploads the modified NWB file back to DANDI as a .nwb.json file.


lindi_tests_dandiset_id = '213569'
lindi_tests_dandiset_version = 'draft'


def lindi_test_2():
    # path = '000946/sub-BH494/sub-BH494_ses-20230817T132836_ecephys.nwb'
    download_url = 'https://api-staging.dandiarchive.org/api/assets/11b45116-807e-4ba0-82cd-95530c3b095f/download/'

    with StagingArea.create(base_dir='lindi_staging') as staging_area:
        client = lindi.LindiH5pyFile.from_reference_file_system(download_url, mode='r+', staging_area=staging_area)
        add_autocorrelograms(client)
        upload_nwb_to_dandi(
            nwb_client=client,
            dandiset_id=lindi_tests_dandiset_id,
            dandiset_version=lindi_tests_dandiset_version,
            path='000946/sub-BH494/sub-BH494_ses-20230817T132836_desc-autocorrelograms_ecephys.nwb.json'
        )


def upload_nwb_to_dandi(
    nwb_client: lindi.LindiH5pyFile,
    dandiset_id: str,
    dandiset_version: str,
    path: str
):
    staging_store = nwb_client.staging_store
    if staging_store is None:
        raise ValueError("NWB client does not have a staging store")

    def on_store_blob(filename: str):
        sha1 = _compute_sha1_of_file(filename)
        a = create_asset(
            dandiset_id=dandiset_id,
            dandiset_version=dandiset_version,
            local_filename=filename,
            asset_path=f'sha1/{sha1}',
            leave_existing=True
        )
        assert isinstance(a, dict)
        return a['download_url']

    def on_store_main(filename: str):
        a = create_asset(
            dandiset_id=dandiset_id,
            dandiset_version=dandiset_version,
            local_filename=filename,
            asset_path=path,
            replace_existing=True
        )
        assert isinstance(a, dict)
        return a['download_url']

    staging_store.upload(
        on_store_blob=on_store_blob,
        on_store_main=on_store_main,
        consolidate_chunks=True
    )


def _compute_sha1_of_file(filename: str):
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


if __name__ == '__main__':
    lindi_test_2()
