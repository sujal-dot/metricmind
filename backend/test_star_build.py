#!/usr/bin/env python3
print("Testing Star Schema Build...")

import sys
sys.path.insert(0, '/Users/sujal/Downloads/metricmind/backend')

from scripts.build_star_schema import build_star_schema

build_star_schema()
