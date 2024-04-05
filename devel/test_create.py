from lindi_dandi import create_dandiset, delete_dandiset, create_asset, remove_asset

# This test script creates a dandiset, adds an asset, removes the asset, and
# deletes the dandiset.


def test_create():
    dandiset_id = create_dandiset(name="test_dandiset", embargo=False)
    print(f"Created dandiset {dandiset_id}")
    create_asset(
        dandiset_id=dandiset_id,
        dandiset_version="draft",
        local_filename="test_file.txt",
        asset_path="test_file.txt"
    )
    remove_asset(dandiset_id=dandiset_id, dandi_version="draft", path="test_file.txt")
    delete_dandiset(dandiset_id)
    print(f"Deleted dandiset {dandiset_id}")


if __name__ == '__main__':
    test_create()
