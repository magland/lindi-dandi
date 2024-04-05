# lindi-dandi

Provides the needed functionality for uploading LINDI .nwb.json files to DANDI.

See: https://github.com/NeurodataWithoutBorders/lindi/pull/42

NOTE: Everything is hard-coded to work with the DANDI staging instance.

NOTE: Any destructive operations (e.g., deleting a dandiset) will prompt you to confirm.

You'll need to set the DANDI_STAGING_API_KEY environment variable.

## Installation

```
pip install -e .
```

## Usage

See the scripts in the devel/ folder.
