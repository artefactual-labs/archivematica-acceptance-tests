"""Embryonic script for getting directory structure from AIP.

Note: this could be re-usable functionality: a correct API (with tests) for
encoding a directory structure in a METS file and getting the same directory
structure back again. Is this already in mets-reader-writer?
"""

from lxml import etree
import os
import pprint

path = ('/Users/joeldunham/Downloads/zn-92bd2579-326d-44c1-9a72-271ad53e4266/'
        'data/METS.92bd2579-326d-44c1-9a72-271ad53e4266.xml')

# Namespace map for parsing METS XML.
ns = {
    'mets': 'http://www.loc.gov/METS/',
    'premis': 'info:lc/xmlns/premis-v2',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'xlink': 'http://www.w3.org/1999/xlink'
}

def _get_subpaths_from_struct_map(elem, ns, base_path='', paths=None):
    if not paths:
        paths = set()
    for div_el in elem.findall('mets:div', ns):
        path = os.path.join(base_path, div_el.get('LABEL'))
        paths.add(path)
        for subpath in _get_subpaths_from_struct_map(
                div_el, ns, base_path=path, paths=paths):
            paths.add(subpath)
    return paths

with open(path) as filei:
    mets = etree.parse(filei)
    struct_map_el = mets.find('.//mets:structMap[@TYPE="physical"]', ns)
    subpaths = _get_subpaths_from_struct_map(struct_map_el, ns)
    print('got subpaths of structmap')
    pprint.pprint(subpaths)
