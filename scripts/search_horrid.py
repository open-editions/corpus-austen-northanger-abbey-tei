import sys
from pathlib import Path

# Add libroj to sys.path
sys.path.append("/home/jon/Programaroj/libroj/src")
from libroj.store import LibrojStore

store = LibrojStore(Path("/home/jon/Programaroj/libroj/data/store"))

horrid_novels = [
    "The Necromancer; or, The Tale of the Black Forest",
    "The Midnight Bell",
    "The Orphan of the Rhine",
    "Horrid Mysteries",
    "The Castle of Wolfenbach",
    "Clermont",
    "Mysterious Warnings"
]

for title in horrid_novels:
    print(f"--- Searching for {title} ---")
    sparql = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    SELECT DISTINCT ?s ?label ?wd WHERE {{
      ?s rdfs:label ?label .
      FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{title}")))
      OPTIONAL {{ ?s wdt:P629 ?wd . }}
      OPTIONAL {{ ?s wdt:P31 ?wd . }}
    }} LIMIT 5
    """
    try:
        results = store.query(sparql)
        for row in results:
            print(f"  {row['s'].value} | {row['label'].value} | {row['wd'].value if 'wd' in row else 'No WD'}")
    except Exception as e:
        print(f"  Error: {e}")
