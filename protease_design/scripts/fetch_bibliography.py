"""Retrieve bibliographic metadata from Crossref; preserve responses and hashes."""

import concurrent.futures
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

REFERENCES = {
    "asano1996": "10.1074/jbc.271.47.30256",
    "nakano2015": "10.1038/srep13836",
    "lee1998": "10.1038/2306",
    "goldfarb2005": "10.1021/bi0511686",
    "beyer1996": "10.1074/jbc.271.26.15590",
    "baldwin1993": "10.1073/pnas.90.14.6796",
    "keilova1968": "10.1111/j.1432-1033.1968.tb00232.x",
    "popp2009": "10.1002/0471140864.ps1503s56",
    "kobashigawa2009": "10.1007/s10858-008-9296-5",
    "arai2001": "10.1093/protein/14.8.529",
    "lin2023": "10.1126/science.ade2574",
    "abramson2024": "10.1038/s41586-024-07487-w",
    "watson2023": "10.1038/s41586-023-06415-8",
    "dauparas2022": "10.1126/science.add2187",
    "dauparas2025": "10.1038/s41592-025-02626-1",
    "lauko2025": "10.1126/science.adu2454",
    "rfdiffusion2": "10.1038/s41592-025-02975-x",
    "passaro2025": "10.1101/2025.06.14.659707",
    "olsson2011": "10.1021/ct100578z",
    "sondergaard2011": "10.1021/ct200133y",
    "boyken2019": "10.1126/science.aav7897",
    "dagliyan2018": "10.1038/s41467-018-06531-4",
    "konno2000": "10.1021/bi991923d",
    "bompard2000": "10.1016/S0969-2126(00)00188-X",
    "fanuel1999": "10.1042/0264-6021:3410147",
    "haim2026": "10.1002/anie.202521611",
    "merchant2026": "10.64898/2026.06.22.733870",
    "eastman2024": "10.1021/acs.jpcb.3c06662",
    "maier2015": "10.1021/acs.jctc.5b00255",
    "onufriev2004": "10.1002/prot.20033",
}


def retrieve(pair):
    key, doi = pair
    url = "https://api.crossref.org/v1/works/" + urllib.parse.quote(doi, safe="") + "/transform"
    request = urllib.request.Request(url, headers={"User-Agent": "ProteaseDesignLiteratureReview/1.0",
                                                  "Accept": "application/x-bibtex"})
    cache = Path("data/corehpc/protease_design/bibliography")
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{key}.bib"
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(request, timeout=90).read())
    raw = path.read_bytes()
    entry = re.sub(r"(@\w+\{)[^,]+,", lambda m: m[1] + key + ",", raw.decode(), count=1)
    if not entry.lstrip().startswith("@"):
        raise ValueError(f"Not BibTeX: {doi}")
    return key, entry, {"doi": doi, "url": url, "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    directory = Path("protease_design/manuscript")
    directory.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(retrieve, pair): pair[0] for pair in REFERENCES.items()}
        results, errors = [], {}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except (urllib.error.HTTPError, urllib.error.URLError) as error:
                errors[futures[future]] = str(error)
        results.sort(key=lambda row: list(REFERENCES).index(row[0]))
    (directory / "references.bib").write_text("\n\n".join(entry.strip() for _, entry, _ in results) + "\n")
    (directory / "bibliography_provenance.json").write_text(json.dumps({key: meta for key, _, meta in results}, indent=2) + "\n")
    if errors:
        raise SystemExit(f"Bibliography incomplete; cached successful entries. Missing: {errors}")


if __name__ == "__main__":
    main()
