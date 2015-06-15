#!/bin/env python
import sys

from PIL import Image

base = Image.new('RGBA', (1200, 1800))
areas = ((0, 0), (600, 0))
i = Image.open(sys.argv[1])
for area in areas:
    base.paste(i, area, mask=i)
base.save(sys.argv[-1])
