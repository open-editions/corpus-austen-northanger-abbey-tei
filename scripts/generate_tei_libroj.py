import sys
from pathlib import Path
from bs4 import BeautifulSoup
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Add libroj to sys.path
sys.path.append("/home/jon/Programaroj/libroj/src")
from libroj.store import LibrojStore

# Initialize libroj store
STORE_PATH = Path("/home/jon/Programaroj/libroj/data/store")
store = LibrojStore(STORE_PATH)

# Novel QIDs to search for in the text
NOVELS = {
    "The Mysteries of Udolpho": "Q2600909",
    "Udolpho": "Q2600909",
    "The Italian": "Q3204370",
    "Camilla": "Q5026573",
    "Cecilia": "Q5056402",
    "Belinda": "Q2894491",
    "The Monk": "Q2659564",
    "Tom Jones": "Q248096",
    "The History of Tom Jones, a Foundling": "Q248096",
    "Sir Charles Grandison": "Q3521260",
    "The History of Sir Charles Grandison": "Q3521260",
    "The Castle of Wolfenbach": "Q7721588",
    "Castle of Wolfenbach": "Q7721588",
    "Clermont": "Q5131885",
    "Mysterious Warnings": "Q6948135",
    "The Mysterious Warning": "Q6948135",
    "The Necromancer; or, The Tale of the Black Forest": "Q7753331",
    "The Necromancer": "Q7753331",
    "Necromancer of the Black Forest": "Q7753331",
    "The Midnight Bell": "Q7751307",
    "Midnight Bell": "Q7751307",
    "The Orphan of the Rhine": "Q7755439",
    "Orphan of the Rhine": "Q7755439",
    "Horrid Mysteries": "Q5905030"
}

def get_work_metadata(qid):
    uri = f"http://www.wikidata.org/entity/{qid}"
    sparql = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?pLabel ?oLabel ?o WHERE {{
      <{uri}> ?p ?o .
      ?p rdfs:label ?pLabel .
      OPTIONAL {{ ?o rdfs:label ?oLabel . FILTER(LANG(?oLabel) = 'en') }}
      FILTER(LANG(?pLabel) = 'en')
    }}
    """
    results = store.query(sparql)
    metadata = {}
    for row in results:
        p = row["pLabel"].value
        o = row["oLabel"].value if row["oLabel"] else row["o"].value
        if p not in metadata:
            metadata[p] = []
        metadata[p].append(o)
    return metadata

def mark_intertextuality(parent, text):
    last_end = 0
    # Sort keys by length descending
    sorted_titles = sorted(NOVELS.keys(), key=len, reverse=True)
    
    # Create a regex that allows any whitespace (including newlines) between words
    patterns = []
    for t in sorted_titles:
        p = re.escape(t).replace(r'\ ', r'\s+')
        patterns.append(f"(?P<title_{hash(t) & 0xFFFFFFFF}>{p})")
    
    pattern_str = r'\b(' + '|'.join(patterns) + r')\b'
    pattern = re.compile(pattern_str, re.IGNORECASE)
    
    # To map back from group name to QID, we need a map
    group_to_qid = {}
    for t, qid in NOVELS.items():
        group_to_qid[f"title_{hash(t) & 0xFFFFFFFF}"] = qid

    for match in pattern.finditer(text):
        if match.start() > last_end:
            if len(parent) > 0:
                if parent[-1].tail is None:
                    parent[-1].tail = text[last_end:match.start()]
                else:
                    parent[-1].tail += text[last_end:match.start()]
            else:
                parent.text = (parent.text or "") + text[last_end:match.start()]
        
        matched_text = match.group(0)
        # Find which group matched
        qid = None
        for g_name, q in group_to_qid.items():
            if match.group(g_name):
                qid = q
                break
        
        ref = ET.SubElement(parent, "ref", target=f"https://www.wikidata.org/wiki/{qid}")
        ref.text = matched_text
        last_end = match.end()
    
    if last_end < len(text):
        if len(parent) > 0:
            if parent[-1].tail is None:
                parent[-1].tail = text[last_end:]
            else:
                parent[-1].tail += text[last_end:]
        else:
            parent.text = (parent.text or "") + text[last_end:]

def generate_tei(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html_soup = BeautifulSoup(f, 'html.parser')

    # Get Metadata for Northanger Abbey (Q477508) and Jane Austen (Q36322)
    work_meta = get_work_metadata("Q477508")
    author_meta = get_work_metadata("Q36322")
    
    tei_root = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    header = ET.SubElement(tei_root, "teiHeader")
    
    # fileDesc
    fileDesc = ET.SubElement(header, "fileDesc")
    titleStmt = ET.SubElement(fileDesc, "titleStmt")
    mainTitle = ET.SubElement(titleStmt, "title", type="main")
    mainTitle.text = "Northanger Abbey"
    author = ET.SubElement(titleStmt, "author")
    
    # Get author dates from author_meta
    birth = author_meta.get("date of birth", ["1775"])[0][:4]
    death = author_meta.get("date of death", ["1817"])[0][:4]
    author.text = f"Austen, Jane, {birth}-{death}"
    
    respStmt = ET.SubElement(titleStmt, "respStmt")
    resp = ET.SubElement(respStmt, "resp")
    resp.text = "creation of machine-readable version"
    respName = ET.SubElement(respStmt, "name")
    respName.text = "Gemini CLI with Libroj integration"
    
    pubStmt = ET.SubElement(fileDesc, "publicationStmt")
    publisher = ET.SubElement(pubStmt, "publisher")
    publisher.text = "Open Editions"
    date = ET.SubElement(pubStmt, "date")
    date.text = "2026"
    availability = ET.SubElement(pubStmt, "availability", status="free")
    licence = ET.SubElement(availability, "licence", target="http://creativecommons.org/licenses/by-sa/4.0/")
    licence.text = "Distributed under a Creative Commons Attribution-ShareAlike 4.0 International License."
    
    sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
    bibl = ET.SubElement(sourceDesc, "bibl")
    ET.SubElement(bibl, "title").text = "Northanger Abbey"
    ET.SubElement(bibl, "author").text = "Jane Austen"
    ET.SubElement(bibl, "publisher").text = "Project Gutenberg"
    ET.SubElement(bibl, "idno", type="Gutenberg").text = "121"
    
    # Get publication year from work_meta
    pub_date_raw = work_meta.get("publication date", ["1818"])
    pub_year = pub_date_raw[0][:4] if pub_date_raw else "1818"
    ET.SubElement(bibl, "date").text = pub_year
    
    # profileDesc
    profileDesc = ET.SubElement(header, "profileDesc")
    textClass = ET.SubElement(profileDesc, "textClass")
    keywords = ET.SubElement(textClass, "keywords", scheme="http://www.wikidata.org/entity/")
    term = ET.SubElement(keywords, "term", xmlid="Q477508")
    term.text = "Northanger Abbey"
    
    # Add genre keywords from work_meta
    if "genre" in work_meta:
        for genre in work_meta["genre"]:
            g_term = ET.SubElement(keywords, "term")
            g_term.text = genre

    # revisionDesc
    revisionDesc = ET.SubElement(header, "revisionDesc")
    change = ET.SubElement(revisionDesc, "change", when="2026-06-10")
    ET.SubElement(change, "label").text = "Editor"
    ET.SubElement(change, "name").text = "Gemini CLI"
    change.text = "Began creation of Open Editions TEI XML for Northanger Abbey using Libroj pipeline."

    text_tag = ET.SubElement(tei_root, "text")
    front = ET.SubElement(text_tag, "front")
    titlePage = ET.SubElement(front, "titlePage")
    docTitle = ET.SubElement(titlePage, "docTitle")
    ET.SubElement(docTitle, "titlePart", type="main").text = "NORTHANGER ABBEY"
    ET.SubElement(titlePage, "docAuthor").text = "By Jane Austen"
    
    body = ET.SubElement(text_tag, "body")

    # Extract Advertisement
    adv_h2 = html_soup.find('h2', string=re.compile("ADVERTISEMENT"))
    if adv_h2:
        div = ET.SubElement(front, "div", type="advertisement")
        head = ET.SubElement(div, "head")
        head.text = adv_h2.get_text().strip()
        
        p = adv_h2.find_next('p')
        while p:
            if p.name == 'p' and p.get_text().strip():
                tei_p = ET.SubElement(div, "p")
                mark_intertextuality(tei_p, p.get_text().strip())
            elif p.name == 'h2' or p.name == 'hr':
                break
            p = p.find_next_sibling()

    # Extract Chapters
    chapters = html_soup.find_all('h2', string=re.compile("CHAPTER"))
    for i, chap_h2 in enumerate(chapters, 1):
        div = ET.SubElement(body, "div", n=str(i), type="chapter")
        head = ET.SubElement(div, "head")
        head.text = chap_h2.get_text().strip()
        
        curr = chap_h2.find_next_sibling()
        while curr:
            if curr.name == 'h2':
                break
            if curr.name == 'p':
                text = curr.get_text().strip()
                if text:
                    tei_p = ET.SubElement(div, "p")
                    mark_intertextuality(tei_p, text)
            elif curr.name == 'pre':
                lg = ET.SubElement(div, "lg", type="verse")
                for line in curr.get_text().split('\n'):
                    if line.strip():
                        l_tag = ET.SubElement(lg, "l")
                        mark_intertextuality(l_tag, line.strip())
            curr = curr.find_next_sibling()

    xmlstr = ET.tostring(tei_root, encoding='utf-8')
    reparsed = minidom.parseString(xmlstr)
    return reparsed.toprettyxml(indent="  ")

if __name__ == "__main__":
    html_file = sys.argv[1]
    print(generate_tei(html_file))
