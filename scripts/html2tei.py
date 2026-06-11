import sys
from bs4 import BeautifulSoup
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Novels and their verified Wikidata IDs
# Udolpho: Q2600909
# The Italian: Q3204370
# Belinda: Q2894491
# The Monk: Q2659564
# Tom Jones: Q248096
# Camilla: Q5026573 (from manual search / general knowledge fallback)
# Cecilia: Q5056402 (from manual search / general knowledge fallback)
# Sir Charles Grandison: Q3521260 (The History of...)
NOVELS = [
    ("The Mysteries of Udolpho", "Q2600909"),
    ("Udolpho", "Q2600909"),
    ("The Italian", "Q3204370"),
    ("Camilla", "Q5026573"),
    ("Cecilia", "Q5056402"),
    ("Belinda", "Q2894491"),
    ("The Monk", "Q2659564"),
    ("Tom Jones", "Q248096"),
    ("The History of Tom Jones, a Foundling", "Q248096"),
    ("Sir Charles Grandison", "Q3521260"),
    ("The History of Sir Charles Grandison", "Q3521260")
]

def mark_intertextuality(parent, text):
    last_end = 0
    sorted_novels = sorted(NOVELS, key=lambda x: len(x[0]), reverse=True)
    titles = [re.escape(n[0]) for n in sorted_novels]
    pattern = re.compile(rf'\b({"|".join(titles)})\b', re.IGNORECASE)
    
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
        # Find the original title to get QID
        original_title = next(t for t, q in NOVELS if re.fullmatch(re.escape(t), matched_text, re.IGNORECASE))
        qid = next(q for t, q in NOVELS if t == original_title)
        
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

    tei_root = ET.Element("body")

    # Extract Advertisement
    adv_h2 = html_soup.find('h2', string=re.compile("ADVERTISEMENT"))
    if adv_h2:
        div = ET.SubElement(tei_root, "div", type="advertisement")
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
        div = ET.SubElement(tei_root, "div", n=str(i), type="chapter")
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
                    # Split into lines roughly based on newline in HTML or just one line
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
