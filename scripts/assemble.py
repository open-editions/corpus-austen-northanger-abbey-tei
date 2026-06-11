import sys
import re

header = """<?xml version="1.0" encoding="UTF-8" ?>
<?xml-stylesheet type="text/xsl" href="https://jonathanreeve.github.io/corpus-joyce-portrait-TEI/portrait.xsl"/ ?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc>
            <titleStmt>
                <title type="main">Northanger Abbey</title>
                <author>Austen, Jane, 1775-1817</author>
                <respStmt>
                    <resp>creation of machine-readable version</resp>
                    <name>Gemini CLI</name>
                </respStmt>
            </titleStmt>
            <publicationStmt>
                <publisher>Open Editions</publisher>
                <date>2026</date>
                <availability status="free">
                    <licence target="http://creativecommons.org/licenses/by-sa/4.0/">
                        Distributed under a Creative Commons Attribution-ShareAlike 4.0 International License.
                    </licence>
                </availability>
            </publicationStmt>
            <sourceDesc>
                <bibl>
                    <title>Northanger Abbey</title>
                    <author>Jane Austen</author>
                    <publisher>Project Gutenberg</publisher>
                    <idno type="Gutenberg">121</idno>
                    <date>2010</date>
                </bibl>
            </sourceDesc>
        </fileDesc>
        <profileDesc>
            <textClass>
                <keywords scheme="http://www.wikidata.org/entity/">
                    <term xml:id="Q477508">Northanger Abbey</term>
                </keywords>
            </textClass>
        </profileDesc>
        <revisionDesc>
            <change when="2026-06-10">
                <label>Editor</label>
                <name>Gemini CLI</name>
                Began creation of Open Editions TEI XML for Northanger Abbey.
            </change>
        </revisionDesc>
    </teiHeader>
    <text>
        <front>
            <titlePage>
                <docTitle>
                    <titlePart type="main">NORTHANGER ABBEY</titlePart>
                </docTitle>
                <docAuthor>By Jane Austen</docAuthor>
            </titlePage>
"""

footer = """
        </body>
    </text>
</TEI>
"""

with open('body.xml', 'r') as f:
    body_content = f.read()

# Strip XML declaration and the root <body> tag
body_content = body_content.replace('<?xml version="1.0" ?>', '')
body_content = body_content.strip()
if body_content.startswith('<body>'):
    body_content = body_content[len('<body>'):]
if body_content.endswith('</body>'):
    body_content = body_content[:-len('</body>')]

# Find advertisement and move it to front
adv_match = re.search(r'(<div type="advertisement">.*?</div>)', body_content, re.DOTALL)
adv_xml = ""
if adv_match:
    adv_xml = adv_match.group(1)
    body_content = body_content.replace(adv_xml, '')

print(header)
if adv_xml:
    print(adv_xml)
print("        </front>")
print("        <body>")
print(body_content)
print(footer)
