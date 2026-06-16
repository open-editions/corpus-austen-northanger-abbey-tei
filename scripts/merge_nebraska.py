import sys
from pathlib import Path
from lxml import etree
import re

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
    "the Italian": "Q3204370",
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

# Namespaces
TEI_NS = "http://www.tei-c.org/ns/1.0"
NS_MAP = {None: TEI_NS}

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
        p = str(row["pLabel"].value)
        o = str(row["oLabel"].value) if row["oLabel"] else str(row["o"].value)
        if p not in metadata:
            metadata[p] = []
        metadata[p].append(o)
    return metadata

def mark_text(element, text_attr, text):
    """
    Applies intertextuality matching to a text segment and replaces it with elements if matches are found.
    This is complex with lxml because we might need to insert multiple elements.
    """
    if not text:
        return
    
    sorted_titles = sorted(NOVELS.keys(), key=len, reverse=True)
    # Regex with named groups for each title to track QIDs
    patterns = []
    group_to_qid = {}
    for i, t in enumerate(sorted_titles):
        p = re.escape(t).replace(r'\ ', r'\s+')
        g_name = f"t_{i}"
        patterns.append(f"(?P<{g_name}>{p})")
        group_to_qid[g_name] = NOVELS[t]
    
    pattern_str = r'\b(' + '|'.join(patterns) + r')\b'
    pattern = re.compile(pattern_str, re.IGNORECASE)
    
    matches = list(pattern.finditer(text))
    if not matches:
        return
    
    # We found matches. We need to reconstruct this part of the tree.
    # If text_attr is 'text', we are replacing the start of the element.
    # If text_attr is 'tail', we are replacing the tail of an element.
    
    # Actually, it's easier to use a temporary container or just handle it surgically.
    # Let's use a simpler approach: process matches and insert <ref> tags.
    
    last_end = 0
    new_elements = []
    
    for match in matches:
        pre_text = text[last_end:match.start()]
        matched_text = match.group(0)
        qid = None
        for g_name in group_to_qid:
            if match.group(g_name):
                qid = group_to_qid[g_name]
                break
        
        ref = etree.Element(f"{{{TEI_NS}}}ref", target=f"https://www.wikidata.org/wiki/{qid}")
        ref.text = matched_text
        
        new_elements.append((pre_text, ref))
        last_end = match.end()
    
    post_text = text[last_end:]
    
    # Now we have a list of (text, element) pairs and a final tail.
    # We need to insert them into the tree.
    
    if text_attr == 'text':
        # Start of the element
        element.text = new_elements[0][0]
        curr = new_elements[0][1]
        element.insert(0, curr)
        for i in range(1, len(new_elements)):
            t, e = new_elements[i]
            curr.tail = t
            element.insert(i, e)
            curr = e
        curr.tail = (curr.tail or "") + post_text
    else:
        # Tail of an element (which is the text following it within the parent)
        parent = element.getparent()
        index = parent.index(element)
        
        element.tail = new_elements[0][0]
        curr = new_elements[0][1]
        parent.insert(index + 1, curr)
        
        for i in range(1, len(new_elements)):
            t, e = new_elements[i]
            curr.tail = t
            parent.insert(index + 1 + i, e)
            curr = e
        curr.tail = (curr.tail or "") + post_text

def process_intertextuality(root):
    # Iterate over all elements that might contain text
    # We'll check both .text and .tail
    for el in root.xpath("//*"):
        if el.text and not list(el): # Leaf node or text start
             # But wait, if it has children, we only want the text *before* the first child
             # and then tails of children.
             pass
        
    # Better approach: walk the tree and check text/tail
    # We need to avoid re-processing nodes we just added.
    # So we'll gather nodes first.
    
    # Actually, lxml's itertext() is good for viewing, but not for modifying.
    # Let's use a standard recursive walker.
    
    to_process = []
    for el in root.xpath("//tei:body//text()", namespaces={'tei': TEI_NS}):
        parent = el.getparent()
        is_tail = (el == parent.tail)
        to_process.append((parent, 'tail' if is_tail else 'text', str(el)))
    
    # Process from bottom up or carefully to avoid index issues
    # Reversing helps when dealing with indexes? Not necessarily here.
    # Let's just be careful.
    
    for parent, attr, text in reversed(to_process):
        mark_text(parent, attr, text)

def merge_nebraska(nebraska_path):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(nebraska_path, parser)
    root = tree.getroot()
    
    # 1. Update Intertextuality
    process_intertextuality(root)
    
    # 2. Enrich Header
    work_meta = get_work_metadata("Q477508")
    author_meta = get_work_metadata("Q36322")
    
    header = root.find(f".//{{{TEI_NS}}}teiHeader")
    # Replace respStmt
    titleStmt = header.find(f".//{{{TEI_NS}}}titleStmt")
    respStmt = titleStmt.find(f".//{{{TEI_NS}}}respStmt")
    if respStmt is not None:
        titleStmt.remove(respStmt)
    
    new_resp = etree.SubElement(titleStmt, f"{{{TEI_NS}}}respStmt")
    etree.SubElement(new_resp, f"{{{TEI_NS}}}resp").text = "creation of machine-readable version"
    etree.SubElement(new_resp, f"{{{TEI_NS}}}name").text = "Gemini CLI with Libroj integration, based on University of Nebraska edition"
    
    # Add genre to profileDesc
    profileDesc = header.find(f".//{{{TEI_NS}}}profileDesc")
    textClass = profileDesc.find(f".//{{{TEI_NS}}}textClass")
    keywords = textClass.find(f".//{{{TEI_NS}}}keywords")
    if keywords is None:
        keywords = etree.SubElement(textClass, f"{{{TEI_NS}}}keywords", scheme="http://www.wikidata.org/entity/")
    
    # Add Northanger Abbey term if not present
    na_term = keywords.xpath(".//tei:term[@xmlid='Q477508']", namespaces={'tei': TEI_NS})
    if not na_term:
        term = etree.SubElement(keywords, f"{{{TEI_NS}}}term", xmlid="Q477508")
        term.text = "Northanger Abbey"
        
    if "genre" in work_meta:
        for genre in work_meta["genre"]:
            g_term = etree.SubElement(keywords, f"{{{TEI_NS}}}term")
            g_term.text = genre

    # Add change to revisionDesc
    revisionDesc = header.find(f".//{{{TEI_NS}}}revisionDesc")
    change = etree.Element(f"{{{TEI_NS}}}change", when="2026-06-10")
    change.text = "Enriched with intertextual references and Libroj metadata based on the University of Nebraska edition."
    etree.SubElement(change, f"{{{TEI_NS}}}label").text = "Editor"
    etree.SubElement(change, f"{{{TEI_NS}}}name").text = "Gemini CLI"
    revisionDesc.insert(0, change)

    # Update publisher
    pubStmt = header.find(f".//{{{TEI_NS}}}publicationStmt")
    publisher = pubStmt.find(f"{{{TEI_NS}}}publisher")
    if publisher is not None:
        publisher.text = "Open Editions"

    # Add Stylesheet PI
    pi = etree.ProcessingInstruction("xml-stylesheet", 'type="text/xsl" href="https://jonathanreeve.github.io/corpus-joyce-portrait-TEI/portrait.xsl"')
    root.addprevious(pi)

    return etree.tostring(tree, encoding='utf-8', pretty_print=True, xml_declaration=True).decode('utf-8')

if __name__ == "__main__":
    neb_file = sys.argv[1]
    print(merge_nebraska(neb_file))
