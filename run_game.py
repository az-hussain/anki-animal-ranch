#!/usr/bin/env python3
"""
Standalone runner for Anki Animal Ranch.

Use this to test the game without Anki.
"""

import sys
import os

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anki_animal_ranch import main

if __name__ == "__main__":
    main()
