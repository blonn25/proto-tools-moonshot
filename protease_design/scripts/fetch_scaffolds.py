"""Fetch experimental scaffold records and preserve source checksums."""

import argparse
import hashlib
import json
import logging
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LOGGER = logging.getLogger(__name__)
PDB_IDS = ("4Y7P", "3PSG", "4PEP", "1EI5", "1LYA", "1LYW")
UNIPROT_IDS = ("P94288", "P07339")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/references"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    sources = {}
    for pdb_id in PDB_IDS:
        sources.update({
            f"{pdb_id}.cif": f"https://files.rcsb.org/download/{pdb_id}.cif",
            f"{pdb_id}_entity.json": f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/1",
            f"{pdb_id}_entry.json": f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}",
        })
        if pdb_id in ("1LYA", "1LYW"):
            sources[f"{pdb_id}_entity2.json"] = f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/2"
    for accession in UNIPROT_IDS:
        sources[f"{accession}.json"] = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
    for filename, url in sources.items():
            target = args.output / filename
            if not target.exists():
                request = urllib.request.Request(url, headers={"User-Agent": "protease-design-research/1.0"})
                for attempt in range(3):
                    try:
                        with urllib.request.urlopen(request, timeout=60) as response:
                            data = response.read()
                        break
                    except OSError:
                        if attempt == 2:
                            raise
                        time.sleep(2 * (attempt + 1))
                temporary = target.with_suffix(target.suffix + ".part")
                temporary.write_bytes(data)
                temporary.replace(target)
            data = target.read_bytes()
            records.append({
                "file": filename, "url": url, "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
            LOGGER.info("Verified %s (%d bytes)", filename, len(data))
    (args.output / "sources.json").write_text(json.dumps({
        "checked_utc": datetime.now(timezone.utc).isoformat(), "records": records,
    }, indent=2) + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    main()
