import sys
from lindi_dandi import create_dandiset

# This script creates a dandiset with the given name.


def create_dandiset_f(name: str):
    dandiset_id = create_dandiset(name=name, embargo=False)
    print(f"Created dandiset {dandiset_id}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python create_dandiset.py \"<name>\"")
        sys.exit(1)
    name = sys.argv[1]
    create_dandiset_f(name=name)
