#!/bin/bash
# Build script for Anki Animal Ranch addon
# Creates a .ankiaddon file ready for distribution

set -e

# Configuration
ADDON_NAME="anki_animal_ranch"
VERSION=$(grep -o '"version": "[^"]*"' anki_animal_ranch/manifest.json | cut -d'"' -f4)
OUTPUT_FILE="${ADDON_NAME}_v${VERSION}.ankiaddon"

echo "🐄 Building Anki Animal Ranch v${VERSION}..."
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Clean up old builds
rm -f *.ankiaddon

# Create the .ankiaddon file
# AnkiWeb expects files at the ROOT of the zip, not in a subfolder
cd "$ADDON_NAME"
zip -r "../$OUTPUT_FILE" . \
    -x "*.pyc" \
    -x "*__pycache__*" \
    -x "*.log" \
    -x "*.tmp" \
    -x ".DS_Store" \
    -x ".*"
cd ..

# Show result
echo ""
echo "✅ Build complete!"
echo "   Output: $OUTPUT_FILE"
echo "   Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""

# Verify zip structure
echo "📁 Zip contents (should show files at root, not in folder):"
unzip -l "$OUTPUT_FILE" | head -20
echo ""

echo "📤 To publish on AnkiWeb:"
echo "   1. Go to https://ankiweb.net/shared/upload"
echo "   2. Upload: $OUTPUT_FILE"
echo "   3. Fill in title, description, tags"
echo "   4. Submit for review"
echo ""
echo "🔄 To update an existing addon:"
echo "   1. Increment version in manifest.json"
echo "   2. Run this script again"
echo "   3. Upload new .ankiaddon to same addon page"
