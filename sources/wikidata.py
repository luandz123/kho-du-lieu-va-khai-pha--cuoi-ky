"""Nguồn 3: Wikidata SPARQL (https://query.wikidata.org).

Tra từng IMDb ID (thuộc tính P345) ra:
  - mã Wikidata của phim (Q...)
  - tên bài Wikipedia tiếng Anh và tiếng Việt  -> cần cho Pageviews và EventStreams
  - quốc gia sản xuất, số giải Oscar đã thắng

Chạy: python -m sources.wikidata
"""
from datetime import datetime, timezone
import time

from pipeline import lake
from sources.catalog import ml1m_imdb_ids
from sources.web import get

ENDPOINT = "https://query.wikidata.org/sparql"
BATCH = 200

QUERY = """
SELECT ?imdb ?film ?enwiki ?viwiki
       (GROUP_CONCAT(DISTINCT ?countryLabel; separator="|") AS ?countries)
       (COUNT(DISTINCT ?oscar) AS ?oscar_wins)
WHERE {
  VALUES ?imdb { %s }
  ?film wdt:P345 ?imdb .
  OPTIONAL { ?en schema:about ?film ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?enwiki . }
  OPTIONAL { ?vi schema:about ?film ; schema:isPartOf <https://vi.wikipedia.org/> ; schema:name ?viwiki . }
  OPTIONAL { ?film wdt:P495 ?country . ?country rdfs:label ?countryLabel . FILTER(LANG(?countryLabel) = "en") }
  OPTIONAL { ?film p:P166 ?aw . ?aw ps:P166 ?oscar . ?oscar wdt:P31 wd:Q19020 . }
}
GROUP BY ?imdb ?film ?enwiki ?viwiki
"""


def fetch(ids: list[str]) -> list[dict]:
    values = " ".join(f'"{i}"' for i in ids)
    r = get(ENDPOINT, params={"query": QUERY % values, "format": "json"}, timeout=120)
    r.raise_for_status()
    out = []
    for b in r.json()["results"]["bindings"]:
        out.append({k: v["value"] for k, v in b.items()})
    return out


def main():
    ids = sorted(set(ml1m_imdb_ids().values()))
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for i in range(0, len(ids), BATCH):
        batch = ids[i:i + BATCH]
        for r in fetch(batch):
            r["fetched_at"] = fetched_at
            rows.append(r)
        print(f"  wikidata: {min(i + BATCH, len(ids))}/{len(ids)} IMDb ID")
        time.sleep(1)  # lịch sự với dịch vụ công cộng
    target = lake.bronze_path("wikidata", "film_links", "film_links.jsonl")
    n = lake.put_json_lines(rows, target)
    found = len({r["imdb"] for r in rows if r.get("enwiki")})
    print("bronze <-", target, f"({n} dòng, {found}/{len(ids)} phim có bài Wikipedia tiếng Anh)")


if __name__ == "__main__":
    main()
