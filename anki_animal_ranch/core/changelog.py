"""
Changelog - Version history and changes.

Used to display what's new after updates.
"""

from typing import Final

# Changelog entries: version -> list of changes
# Add new versions at the TOP of this dict
CHANGELOG: Final[dict[str, list[str]]] = {
    "0.4.1": [
        "Added Settings menu with Reset Farm option — start fresh without reinstalling",
        "Major battery improvements: the game is now ~50% more efficient while you're playing, ~90% more efficient when you're studying with the farm open on the side, and nearly idle when minimized",
    ],
    "0.3.0": [
        "Season was stuck in Spring, time progression now fixed",
        "Fixed 'Sell All' bug: quality products now give correct money on sale (shout out to @adsharma and @Iloveanki67 for reporting)",
        "Fixed placement mode: can now place buildings near existing ones",
        "Added changelog feature to show what's new after updates",
    ],
    "0.2.4": [
        "Added seasonal visual effects (rain in spring, snow in winter)",
        "Tiles now show seasonal decorations (flowers, leaves, snow)",
        "Fixed version display in window title",
    ],
    "0.2.3": [
        "Added friend visit system - visit other players' farms",
        "Cloud sync for farm data",
        "Account creation with unique usernames",
    ],
    "0.2.2": [
        "Added decoration placement and rotation",
        "Decorations can be moved and removed",
        "Improved market dialog UI",
    ],
    "0.2.1": [
        "Log file rotation to prevent large files",
        "Locked tiles now show green with gray overlay",
        "Various bug fixes",
    ],
    "0.2.0": [
        "Initial public release",
        "Farm simulation with chickens, cows, and pigs",
        "Building placement and upgrades",
        "Product collection and selling",
    ],
}


def parse_version(version_str: str) -> tuple[int, int, int]:
    """
    Parse a version string into a tuple for comparison.
    
    Args:
        version_str: Version string like "0.2.4"
        
    Returns:
        Tuple of (major, minor, patch)
    """
    try:
        parts = version_str.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except (ValueError, IndexError):
        return (0, 0, 0)


def get_versions_between(old_version: str, new_version: str) -> list[str]:
    """
    Get all changelog versions between old and new (exclusive of old, inclusive of new).
    
    Args:
        old_version: The version the user last saw
        new_version: The current version
        
    Returns:
        List of version strings in descending order (newest first)
    """
    old_parsed = parse_version(old_version)
    new_parsed = parse_version(new_version)
    
    # Get all versions that are > old and <= new
    result = []
    for version in CHANGELOG.keys():
        v_parsed = parse_version(version)
        if old_parsed < v_parsed <= new_parsed:
            result.append(version)
    
    # Sort by version descending (newest first)
    result.sort(key=parse_version, reverse=True)
    return result


def get_changelog_for_versions(versions: list[str]) -> dict[str, list[str]]:
    """
    Get changelog entries for specific versions.
    
    Args:
        versions: List of version strings
        
    Returns:
        Dict of version -> changes for the requested versions
    """
    return {v: CHANGELOG[v] for v in versions if v in CHANGELOG}
