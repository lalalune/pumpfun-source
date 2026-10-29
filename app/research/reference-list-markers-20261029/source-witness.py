from pathlib import Path
from urllib.parse import urlsplit
import hashlib, importlib.util, json, sys

root = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('reference_extractor', root / 'app/scripts/extract-reference-pages.py')
extractor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = extractor
spec.loader.exec_module(extractor)
manifest = json.loads((root / 'app/evidence/web/manifest.json').read_text())
css_path = 'evidence/web/objects/4a341ff6a9551721.css'
css_sha = '8bda96ca39398a46befb900a2d43a4e695ff9975ce6c4bb83c1f45bb47eced93'
css = (root / 'app' / css_path).read_bytes()
assert hashlib.sha256(css).hexdigest() == css_sha
records = [item for item in manifest['records'] if item.get('path') == css_path]
assert len(records) == 1
record = records[0]
assert record['sha256'] == css_sha and record['bytes'] == len(css) and record['status'] == 200
assert record['final_url'] == record['url']
rule = b'.list-disc{list-style-type:disc}'
offset = css.index(rule)
documents = []
for key, source in extractor.SOURCES.items():
    extractor.verify_manifest(manifest, source)
    data = (root / 'app' / source['path']).read_bytes()
    document = extractor.parse_document_bytes(key, source, data)
    parser = extractor.TreeParser()
    parser.feed(data.decode('utf8'))
    main = extractor.find_document_main(parser.root, source['title'])
    lists = [node for node in extractor.walk(main) if node.tag in {'ul', 'ol'}]
    assert all(node.tag == 'ul' and 'list-disc' in node.attrs.get('class', '').split() for node in lists)
    stylesheet_path = urlsplit(record['url']).path
    link = ('<link rel="stylesheet" href="' + stylesheet_path + '"').encode()
    link_offset = data.index(link)
    opening_tags = []
    for class_name in sorted({node.attrs['class'] for node in lists}):
        tag = ('<ul class="' + class_name + '">').encode()
        start = 0
        while True:
            position = data.find(tag, start)
            if position < 0:
                break
            opening_tags.append({'range': [position, position + len(tag)], 'text': tag.decode(), 'sha256': hashlib.sha256(tag).hexdigest()})
            start = position + len(tag)
    assert len(opening_tags) == len(lists)
    documents.append({'key': key, 'source': document['source'], 'stylesheetLink': {'range': [link_offset, link_offset + len(link)], 'text': link.decode()}, 'lists': len(lists), 'items': sum(len([child for child in node.children if isinstance(child, extractor.Node) and child.tag == 'li']) for node in lists), 'openingTags': opening_tags})
print(json.dumps({'css': {'url': record['url'], 'path': css_path, 'bytes': len(css), 'sha256': css_sha, 'rule': {'range': [offset, offset + len(rule)], 'text': rule.decode(), 'sha256': hashlib.sha256(rule).hexdigest()}}, 'documents': documents}, indent=2))
