#!/usr/bin/env python3
"""
Memory Backup Script for Narusya
Backs up Hermes, Honcho, and Qdrant data
"""

import os
import tarfile
from datetime import datetime
from pathlib import Path

# Configuration - adjust these paths if needed
HERMES_PATH = Path.home() / '.hermes'
HONCHO_PATH = Path.home() / 'honcho'
QDRANT_PATH = Path.home() / 'qdrant_storage'
BACKUP_DIR = Path.home() / 'backups'

def create_backup(source_path, backup_name, exclude_patterns=None):
    """Create a compressed tar.gz backup of the source path"""
    if not source_path.exists():
        print(f"⚠️  Warning: {source_path} does not exist, skipping...")
        return False
    
    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = BACKUP_DIR / f"{backup_name}-{timestamp}.tar.gz"
    
    print(f"📦 Creating backup: {backup_file}")
    
    try:
        with tarfile.open(backup_file, "w:gz") as tar:
            # Add each file, excluding patterns if needed
            for root, dirs, files in os.walk(source_path):
                # Modify dirs in-place to skip excluded directories
                if exclude_patterns:
                    # We need to check if any exclude pattern matches the current root
                    # For simplicity, we'll skip if any excluded pattern is in the root path
                    # This is a basic implementation; for production, use more robust matching
                    skip = False
                    for pattern in exclude_patterns:
                        if pattern in root:
                            skip = True
                            break
                    if skip:
                        # Don't descend into this directory
                        dirs[:] = []
                        continue
                for file in files:
                    file_path = Path(root) / file
                    # Check if file should be excluded
                    if exclude_patterns:
                        excluded = False
                        for pattern in exclude_patterns:
                            if pattern in str(file_path):
                                excluded = True
                                break
                        if excluded:
                            continue
                    # Add file to archive with relative path
                    rel_path = file_path.relative_to(source_path.parent)
                    tar.add(file_path, arcname=rel_path)
        print(f"✅ Backup completed: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def main():
    print("🔄 Starting memory backup process...")
    print("=" * 50)
    
    # Define exclude patterns for large directories we don't need to backup
    hermes_excludes = [
        "hermes-agent/venv",  # Large virtual environment
        "hermes-agent/node_modules",  # Large node modules
        "hermes-agent/.git",  # Git history (can be re-cloned)
    ]
    
    honcho_excludes = [
        "honcho/venv",  # Virtual environment if exists
    ]
    
    # Backup each system
    hermes_success = create_backup(HERMES_PATH, "hermes", hermes_excludes)
    honcho_success = create_backup(HONCHO_PATH, "honcho", honcho_excludes)
    qdrant_success = create_backup(QDRANT_PATH, "qdrant")  # No excludes for Qdrant
    
    print("=" * 50)
    print("📊 Backup Summary:")
    print(f"   Hermes: {'✅ Success' if hermes_success else '❌ Failed'}")
    print(f"   Honcho: {'✅ Success' if honcho_success else '❌ Failed'}")
    print(f"   Qdrant: {'✅ Success' if qdrant_success else '❌ Failed (not found)'}")
    
    if hermes_success or honcho_success or qdrant_success:
        print("\n🎉 Backup process completed!")
        print(f"📁 Backups stored in: {BACKUP_DIR}")
    else:
        print("\n💥 All backups failed!")

if __name__ == "__main__":
    main()