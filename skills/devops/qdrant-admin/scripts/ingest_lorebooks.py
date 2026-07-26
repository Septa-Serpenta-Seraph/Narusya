# Lorebook Ingestion Script
#
# IMPORTANT: This script contains credential-loading code.
# Due to Hermes security.redact_secrets, DO NOT copy-paste this into
# write_file from a new session. Instead, copy from the known-good version:
#   cp ~/.hermes/scripts/ingest_lorebooks.py <skill_scripts_path>/ingest_lorebooks.py
#
# Or re-create it using terminal:
#   cat <<'PYEOF' > target.py
#   ... (paste script content)
#   PYEOF
#
# The working script at ~/.hermes/scripts/ingest_lorebooks.py already:
# - Loads OPENROUTER_API_KEY from env or ~/.hermes/.env
# - Extracts title, keywords, priority tier from each lorebook .md
# - Embeds via OpenRouter (openai/text-embedding-3-large, 3072 dims)
# - Upserts to Qdrant with UUID point IDs
# - Stores metadata (not full content) in payloads
#
# Usage:
#   python3 ~/.hermes/scripts/ingest_lorebooks.py
#
# Re-run after editing any lorebook .md files.
#
# Config is embedded in the script:
#   LOREBOOKS_DIR = ~/.hermes/lorebooks/
#   COLLECTION_NAME = narusya_lorebooks
#   PRIORITY_TIER_1 = ["BYPASS", "HEART", "EMOTION", "AGENCY", "ALIGNMENT", "SASS", "STATUS"]
#   PRIORITY_TIER_2 = ["COMPENDIUM", "CORE_VALUES", ...]
#   SKIP_FILES = tier 99 (never auto-inject)
