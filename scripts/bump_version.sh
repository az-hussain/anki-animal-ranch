#!/bin/bash
# Sync version from changelog.py → manifest.json + README.md, then build.
#
# Usage: ./scripts/bump_version.sh
#
# The version is the first key in core/changelog.py CHANGELOG dict.
# To release: add the new version entry at the top of that dict, then run this.

set -e

cd "$(dirname "$0")/.."

# Read version from changelog.py (first key in CHANGELOG dict)
NEW_VERSION=$(python3 -c "
import sys
sys.path.insert(0, '.')
from anki_animal_ranch.core.changelog import CHANGELOG
print(next(iter(CHANGELOG)))
")

# Read what manifest.json currently has
CURRENT=$(python3 -c "
import json
with open('anki_animal_ranch/manifest.json') as f:
    print(json.load(f)['version'])
")

if [ "$NEW_VERSION" = "$CURRENT" ]; then
    echo "⚠️  Version is already $CURRENT — add a new entry to core/changelog.py first."
    exit 1
fi

echo "📦 Releasing: $CURRENT → $NEW_VERSION"

# Sync manifest.json
python3 -c "
import json
with open('anki_animal_ranch/manifest.json') as f:
    data = json.load(f)
data['version'] = '$NEW_VERSION'
with open('anki_animal_ranch/manifest.json', 'w') as f:
    json.dump(data, f, indent=4)
print('  ✅ manifest.json updated')
"

# Sync README.md version badge
sed -i '' "s/version-[0-9]*\.[0-9]*\.[0-9]*/version-$NEW_VERSION/" README.md
echo "  ✅ README.md updated"

echo ""
echo "Building addon..."
./scripts/build_addon.sh
