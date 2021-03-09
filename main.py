import json
import re
import spacy
from pyknp import Juman
from ginza import bunsetu, bunsetu_spans
from collections import defaultdict
from typing import List

jumanpp = Juman()
nlp = spacy.load('ja_ginza')
summary_count = 8


class Counter(dict):
    def __missing__(self, key):
        return 0

    def sum(self):
        s = 0
        for k, v in self.items():
            s += v
        return s


def preprocess(text) -> str:
    text = re.sub('[「」『』【】\r\n]', '', text)
    text = re.sub('[！？‥…]', '。', text)
    text = text.strip()
    return text


# most match sentence with title word
def title_similar_sentence(title, sentences) -> str:
    title_word = []
    title = preprocess(title)
    for mrph in jumanpp.analysis(title).mrph_list():
        if mrph.hinsi == "名詞":
            title_word.append(mrph.midasi)

    cand_sents = []
    for s in sentences:
        point = 0
        for mrph in jumanpp.analysis(s).mrph_list():
            if mrph.midasi in title_word:
                point += 1
        cand_sents.append([s, point])

    return max(cand_sents, key=lambda x: x[1])[0]


def get_test_data(path) -> dict:
    with open(path) as file:
        test_data = json.load(file)
        test_data["body"] = preprocess(test_data["body"]).split("。")
        return test_data


def is_meisi(mrph) -> bool:
    return mrph.hinsi == "名詞" or mrph.imis.find("品詞推定:名詞") != -1


test_data = get_test_data('testdata/mizuho_19805517.json')
candidates = []
test_count = Counter()
corpus_count = {}
with open('count.json') as file:
    corpus_count = json.load(file)

analysis_cache = []
for s in test_data["body"]:
    an = jumanpp.analysis(s)
    analysis_cache.append(an)
    for mrph in an.mrph_list():
        if is_meisi(mrph):
            test_count[mrph.midasi] += 1

for i, s in enumerate(test_data["body"]):
    if s == "":
        continue
    tfidf = 0
    an = analysis_cache[i]
    for mrph in an.mrph_list():
        if is_meisi(mrph):
            tf = (test_count[mrph.midasi]) / max(test_count.sum(), 1)
            idf = 1 / corpus_count.get(mrph.midasi, 10)
            tfidf += (tf*idf)
    candidates.append([s, tfidf])

candidates = sorted(candidates, key=lambda x: x[1])
cand_sentences = list(map(lambda x: x[0], candidates))
cand_sentences = cand_sentences[-summary_count:]
cand_sentences.append(title_similar_sentence(
    test_data["title"], test_data["body"]))

summary_list = []

for s in cand_sentences[-summary_count:]:
    doc = nlp(s)
    summary = ""
    for sent in doc.sents:
        for t in bunsetu_spans(sent):
            for b in bunsetu(t.root, join_func=lambda tokens: tokens):
                if b.dep_ in ["nsubj", "obj", "ROOT", "acl", "nmod", "compound", "nummod"]:
                    summary += b.lemma_
    summary_list.append(summary)

for i, s in enumerate(summary_list):
    if i < summary_count - 1:
        print(str(i) + ". " + s)
    else:
        print("タイトルに最も一致する一文 : " + s)
