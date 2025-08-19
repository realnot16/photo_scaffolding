import json
from pathlib import Path

def check_cache(media_type: str):
    cache_file = Path(f"cache/{media_type}/cache.json")
    output_dir = Path(f"output/{media_type}")

    if not cache_file.exists():
        print(f"[{media_type}] ❌ Cache file not found: {cache_file}")
        return

    if not output_dir.exists():
        print(f"[{media_type}] ❌ Output directory not found: {output_dir}")
        return

    # Load cache
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[{media_type}] ❌ Failed to read cache: {e}")
        return

    cached_mtime = cache.get("__meta__", {}).get("folder_mtime", None)
    actual_mtime = output_dir.stat().st_mtime

    print(f"[{media_type}] Cached mtime: {cached_mtime}")
    print(f"[{media_type}] Actual  mtime: {actual_mtime}")

    if cached_mtime == actual_mtime:
        print(f"[{media_type}] ✅ Cache is up-to-date")
    else:
        print(f"[{media_type}] ⚠️ Cache outdated → run cache_builder.py")

if __name__ == "__main__":
    check_cache("foto")
    print()
    check_cache("video")
