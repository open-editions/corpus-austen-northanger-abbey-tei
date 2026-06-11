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
    "Sir Charles Grandison": "Q3521260"
}

def get_wikidata_label(qid):
    uri = f"http://www.wikidata.org/entity/{qid}"
    sparql = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label WHERE {{ <{uri}> rdfs:label ?label . FILTER(LANG(?label) = 'en') }}
    """
    results = store.query(sparql)
    for row in results:
        return row["label"].value
    return None

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
            if p not in metadata:
                metadata[p] = []
            metadata[p].append(o)
    return metadata

def mark_intertextuality(parent, text):
    last_end = 0
    # Sort keys by length descending
    sorted_titles = sorted(NOVELS.keys(), key=len, reverse=True)
    pattern_str = r'\b(' + '|'.join(re.escape(t) for t in sorted_titles) + r')\b'
    pattern = re.compile(pattern_str, re.IGNORECASE)
    
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
        # Find the original title key to get QID
        original_title = next(t for t in sorted_titles if re.fullmatch(re.escape(t), matched_text, re.IGNORECASE))
        qid = NOVELS[original_title]
        
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

    # Get Metadata for Northanger Abbey (Q477508)
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
    author.text = "Austen, Jane, 1775-1817"
    respStmt = ET.SubElement(titleStmt, "respStmt")
    resp = ET.SubElement(respStmt, "resp")
    resp.text = "creation of machine-readable version"
    respName = ET.SubElement(respStmt, "name")
    respName.text = "Gemini CLI using Libroj"
    
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
    ET.SubElement(bibl, "date").text = "2010"
    
    # profileDesc
    profileDesc = ET.SubElement(header, "profileDesc")
    textClass = ET.SubElement(profileDesc, "textClass")
    keywords = ET.SubElement(textClass, "keywords", scheme="http://www.wikidata.org/entity/")
    term = ET.SubElement(keywords, "term", xmlid="Q477508")
    term.text = "Northanger Abbey"
    
    # revisionDesc
    revisionDesc = ET.SubElement(header, "revisionDesc")
    change = ET.SubElement(revisionDesc, "change", when="2026-06-10")
    ET.SubElement(change, "label").text = "Editor"
    ET.SubElement(change, "name").text = "Gemini CLI"
    change.text = "Began creation of Open Editions TEI XML for Northanger Abbey using Libroj."

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
        line_num = 1
        while curr:
            if curr.name == 'h2':
                break
            if curr.name == 'p':
                text = curr.get_text().strip()
                if text:
                    tei_p = ET.SubElement(div, "p")
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    for line in lines:
                        lb = ET.SubElement(tei_p, "lb", n=f"{i}{line_num:04d}")
                        mark_intertextuality(tei_p, line)
                        line_num += 1
            elif curr.name == 'pre':
                lg = ET.SubElement(div, "lg", type="verse")
                for line in curr.get_text().split('\n'):
                    if line.strip():
                        l_tag = ET.SubElement(lg, "l")
                        lb = ET.SubElement(l_tag, "lb", n=f"{i}{line_num:04d}")
                        mark_intertextuality(l_tag, line.strip())
                        line_num += 1
            curr = curr.find_next_sibling()

    xmlstr = ET.tostring(tei_root, encoding='utf-8')
    reparsed = minidom.parseString(xmlstr)
    return reparsed.toprettyxml(indent="  ")

if __name__ == "__main__":
    html_file = sys.argv[1]
    print(generate_tei(html_file))
