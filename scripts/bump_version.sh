#!/bin/bash
# Bump version and rebuild addon
# Usage: ./scripts/bump_version.sh [major|minor|patch]

set -e

cd "$(dirname "$0")/.."

# Get current version
CURRENT=$(grep -o '"version": "[^"]*"' anki_animal_ranch/manifest.json | cut -d'"' -f4)
IFS='.' read -ra PARTS <<< "$CURRENT"
MAJOR=${PARTS[0]}
MINOR=${PARTS[1]}
PATCH=${PARTS[2]}

# Determine bump type
BUMP_TYPE=${1:-patch}

case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "Usage: $0 [major|minor|patch]"
        exit 1
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

echo "📦 Bumping version: $CURRENT → $NEW_VERSION"

# Update manifest.json
sed -i '' "s/\"version\": \"$CURRENT\"/\"version\": \"$NEW_VERSION\"/" anki_animal_ranch/manifest.json

# Update README.md badge
sed -i '' "s/version-[0-9]*\.[0-9]*\.[0-9]*/version-$NEW_VERSION/" README.md

echo "✅ Version bumped to $NEW_VERSION"
echo ""
echo "Now run: ./scripts/build_addon.sh"
