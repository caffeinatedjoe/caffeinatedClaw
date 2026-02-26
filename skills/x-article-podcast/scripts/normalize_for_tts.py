#!/usr/bin/env python3
import re
import sys

text = sys.stdin.read()

# Remove long divider lines common in X articles
text = re.sub(r"\n\s*[-—]{4,}\s*\n", "\n\n", text)

# Normalize URLs for listening (source is preserved in RSS description)
text = re.sub(r"https?://\S+", "[source link in description]", text)

# Normalize ranges like $2,000-$5,000
text = re.sub(r"\$\s?([0-9][0-9,]*)\s*[-–]\s*\$\s?([0-9][0-9,]*)", r"\1 to \2 dollars", text)

# Normalize monthly pricing like $297/month
text = re.sub(r"\$\s?([0-9][0-9,]*)\s*/\s*month", r"\1 dollars per month", text, flags=re.I)

# Normalize standalone currency
text = re.sub(r"\$\s?([0-9][0-9,]*)", r"\1 dollars", text)

# Normalize remaining dollars/month variants
text = re.sub(r"dollars\s*/\s*month", "dollars per month", text, flags=re.I)

# Normalize percentages
text = re.sub(r"\b([0-9]+)\s?%", r"\1 percent", text)

# Make numbering pauses friendlier: "1)" -> "1."
text = re.sub(r"\b([0-9]+)\)", r"\1.", text)

# Clean spacing
text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"

sys.stdout.write(text)
