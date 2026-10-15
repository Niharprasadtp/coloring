"""Generate color-by-number PDF books.

    python colorbynumber.py -i input -o output --difficulty intermediate
"""

import sys

from cbn.cli import main

if __name__ == "__main__":
    sys.exit(main())
