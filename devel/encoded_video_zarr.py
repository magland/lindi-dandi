import hashlib
import numpy as np
import lindi
from lindi_dandi import create_asset
from neurosift.codecs import MP4AVCCodec

MP4AVCCodec.register_codec()


lindi_tests_dandiset_id = '213569'
lindi_tests_dandiset_version = 'draft'


def encoded_video_zarr():
    # url = 'https://api.dandiarchive.org/api/assets/9278ecc2-3d95-4757-b681-f6a44c19ebab/download/'
    fname = '/home/magland/Downloads/60d277d6-24fd-4817-bb02-41382db59172_external_file_0.avi'

    mp4avc_codec = MP4AVCCodec(fps=30)  # note: I actually don't know the fps of the video

    # Read the video into a huge numpy array
    print('Decoding video...')
    with open(fname, 'rb') as f:
        buf = f.read()
        big_array = mp4avc_codec.decode(buf)

    with lindi.StagingArea.create(base_dir='lindi_staging') as staging_area:
        empty_rfs = {
            'refs': {
                '.zgroup': {
                    'zarr_format': 2
                }
            },
            'version': 1
        }
        client = lindi.LindiH5pyFile.from_reference_file_system(empty_rfs, mode='r+', staging_area=staging_area)

        print('Creating group...')
        group1 = client.create_group('group1')

        print('Creating test_video...')
        test_video_group = group1.create_group('test_video')
        chunk_size = 2000
        test_video_group.create_dataset_with_zarr_compressor(
            'data',
            shape=big_array.shape,
            dtype=np.uint8,
            compressor=mp4avc_codec,
            chunks=(chunk_size, big_array.shape[1], big_array.shape[2], big_array.shape[3])
        )
        for ii in range(0, big_array.shape[0], chunk_size):
            print(f'Writing chunk {ii}...')
            test_video_group['data'][ii:ii + chunk_size] = big_array[ii:ii + chunk_size]
        test_video_group.attrs['neurodata_type'] = 'test_video'

        print('Uploading to DANDI...')
        upload_nwb_to_dandi(
            nwb_client=client,
            dandiset_id=lindi_tests_dandiset_id,
            dandiset_version=lindi_tests_dandiset_version,
            path='test_video/video1.nwb.json'
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


if __name__ == "__main__":
    encoded_video_zarr()
