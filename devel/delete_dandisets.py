from lindi_dandi import delete_dandiset

# For convience, you can clean up the dandisets created by the test scripts.

# replace the dandiset_ids with the ids of the dandisets you want to delete
dandiset_ids = [
    '213568'
]

for dandiset_id in dandiset_ids:
    delete_dandiset(dandiset_id)
    print(f"Deleted dandiset {dandiset_id}")
