import pathlib
import xml.etree.ElementTree as ET
from pyknp import Juman
import json
import re
import pathlib


class Counter(dict):
    def __missing__(self, key):
        return 0

    def sum(self):
        s = 0
        for k, v in self.items():
            s += v
        return s


jumanpp = Juman()
data_dir = 'livedoor-news-data'
data_path = pathlib.Path(data_dir)
word_count = Counter()
for p in data_path.iterdir():
    tree = ET.parse(p)
    root = tree.getroot()

    for doc in root.findall('doc'):
        for field in doc:
            if field.attrib['name'] == 'body':
                text = field.text
                if text != None:
                    for sentence in re.split('？。.‥…', text):
                        try:
                            if sentence != "":
                                analysis = jumanpp.analysis(sentence)
                                for mrph in analysis.mrph_list():
                                    if mrph.hinsi == "名詞":
                                        word_count[mrph.midasi] += 1
                        except:
                            continue

with open('count.json', 'w') as file:
    file.write(json.dumps(word_count))
