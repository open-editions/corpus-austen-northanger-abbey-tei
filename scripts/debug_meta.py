import sys
from pathlib import Path

# Add libroj to sys.path
sys.path.append("/home/jon/Programaroj/libroj/src")
from libroj.store import LibrojStore

store = LibrojStore(Path("/home/jon/Programaroj/libroj/data/store"))

def get_work_metadata(qid):
    uri = f"http://www.wikidata.org/entity/{qid}"
    sparql = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    SELECT ?pLabel ?oLabel WHERE {{
      <{uri}> ?p ?o .
      OPTIONAL {{ ?p rdfs:label ?pLabel . FILTER(LANG(?pLabel) = "en") }}
      OPTIONAL {{ ?o rdfs:label ?oLabel . FILTER(LANG(?oLabel) = "en") }}
    }}
    """
    results = store.query(sparql)
    metadata = {}
    for row in results:
        p = row["pLabel"].value if "pLabel" in row else None
        o = row["oLabel"].value if "oLabel" in row else None
        if p and o:
            print(f"DEBUG: p={p}, o={o}")
            if p not in metadata:
                metadata[p] = []
            metadata[p].append(o)
    return metadata

print("--- Northanger Abbey Metadata ---")
get_work_metadata("Q477508")
