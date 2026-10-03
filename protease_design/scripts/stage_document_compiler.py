"""Download the pinned portable Tectonic release into ignored project data."""

import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path

URL = ("https://github.com/tectonic-typesetting/tectonic/releases/download/"
       "tectonic%400.17.0/tectonic-0.17.0-x86_64-unknown-linux-musl.tar.gz")
SHA256 = "8533d07f9ccbd7a65824b9e0459041bca34af1eb33daba48f59215593753a3b7"


def main():
    raw = urllib.request.urlopen(URL, timeout=120).read()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise RuntimeError("Compiler archive hash differs from the recorded release.")
    output = Path("data/corehpc/protease_design/tex")
    output.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(output, filter="data")
    (output / "compiler_provenance.json").write_text(json.dumps({"url": URL, "sha256": SHA256}, indent=2) + "\n")


if __name__ == "__main__":
    main()
