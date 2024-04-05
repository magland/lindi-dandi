import json
import tempfile
import lindi
from lindi_dandi import create_asset


# Create a .nwb.json file for the given dandiset and asset path


lindi_tests_dandiset_id = '213569'
lindi_tests_dandiset_version = 'draft'


def lindi_test_1():
    dandiset_id = '000946'
    # dandiset_version = 'draft'
    path = 'sub-BH494/sub-BH494_ses-20230817T132836_ecephys.nwb'
    download_url = 'https://api.dandiarchive.org/api/assets/3764f5c5-0d06-4f24-9bf2-d2849b1e9d0c/download/'

    # Create a read-only Zarr store as a wrapper for the h5 file
    store = lindi.LindiH5ZarrStore.from_file(download_url)

    # Generate a reference file system
    rfs = store.to_reference_file_system()

    # # Create an h5py-like client from the reference file system
    # client = lindi.LindiH5pyFile.from_reference_file_system(rfs)

    with tempfile.TemporaryDirectory() as tmpdir:
        fname = f'{tmpdir}/nwb.json'
        with open(fname, 'w') as f:
            json.dump(rfs, f, indent=2)
        create_asset(
            dandiset_id=lindi_tests_dandiset_id,
            dandiset_version=lindi_tests_dandiset_version,
            local_filename=fname,
            asset_path=f'{dandiset_id}/{path}.json',
            replace_existing=True
        )


if __name__ == '__main__':
    lindi_test_1()
