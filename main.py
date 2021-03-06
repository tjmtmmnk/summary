import xml.etree.ElementTree as ET
from pyknp import Juman
import json
import re
import spacy
from ginza import *
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


def title_sim(title, sentences) -> str:
    title_word = []
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

    return max(cand_sents, key=lambda x: x[1])


def get_test_data(path) -> List[str]:
    with open(path) as test_file:
        test_data = test_file.read()
        test_data = preprocess(test_data)
        return test_data.split("。")


def is_meisi(mrph) -> bool:
    return mrph.hinsi == "名詞" or mrph.imis.find("品詞推定:名詞") != -1


# increase word by length of bunsetu
def get_important_words(evaled_word, bunsetu_spans):
    num = len(bunsetu_spans) // 5
    if num == 0:
        num = 1
    return evaled_word[-num:]


test_data = get_test_data('testdata/19629300.txt')
cand = []
cnt = Counter()
corpus_count = {}
with open('count.json') as file:
    corpus_count = json.load(file)

test_data_analysis = []
for s in test_data:
    an = jumanpp.analysis(s)
    test_data_analysis.append(an)
    for mrph in an.mrph_list():
        if is_meisi(mrph):
            cnt[mrph.midasi] += 1

word = defaultdict(lambda: 0)
cnt_sum = cnt.sum()
for i, s in enumerate(test_data):
    if s == "":
        continue
    tfidf = 0
    an = test_data_analysis[i]
    for mrph in an.mrph_list():
        if is_meisi(mrph):
            if cnt_sum == 0:
                cnt_sum = 1
            tf = (cnt[mrph.midasi]) / cnt_sum
            idf = 1 / corpus_count.get(mrph.midasi, 10)
            tfidf += (tf*idf)
            word[mrph.midasi] += tfidf
    cand.append([s, tfidf])

cand = sorted(cand, key=lambda x: x[1])
cand_sentences = list(map(lambda x: x[0], cand))

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
    print(str(i) + ". " + s)
