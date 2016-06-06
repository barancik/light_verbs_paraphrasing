#!/usr/bin/python
# -*- coding: utf-8 -*-

# Chce dva sloupce potencionalnich jednoslovnych parafrazi, oddelene \t
# Z nich potom udela lemmata tech, ktere se shoduji na POS[0]

from string import punctuation
from ufal.morphodita import *
from collections import defaultdict

import re
import sys

import os.path
import sys
 
import gensim

FILE="new_corpora"
TAGGER = Tagger.load("/net/projects/morphodita/models/czech-morfflex-pdt-131112/czech-morfflex-pdt-131112.tagger-best_accuracy")

def load_model(name,path=FILE):
    return gensim.models.Word2Vec.load(name)

def return_most_similar(model,phrase):
    similar = model.most_similar(positive=[phrase],topn=30)
    lvcs = [x[0] for x in similar if "_" in x[0]][:10]
    verbs = [x[0] for x in similar if "_" not in x[0] \
            if tag(tagger,x[0])[0].tag.encode("utf-8").startswith("V")][:10]
    return lvcs,verbs

def get_paraphrases(name,lvc_list="found_LVC_over_100"):
    model = load_model(name)
    i=1
    for line in open(lvc_list,"r"):
        phrase = line.strip()
        lvcs,verbs = return_most_similar(model,phrase)
        print i,phrase
        print ", ".join(verbs)
        print ", ".join(lvcs)

def tag(text,tagger=TAGGER):
    forms = Forms()
    lemmas = TaggedLemmas()
    tokens = TokenRanges()
    tokenizer = tagger.newTokenizer()
    tokenizer.setText(text)
    while tokenizer.nextSentence(forms, tokens):
        tagger.tag(forms, lemmas)
    return lemmas


sys.stderr.write('Loading dictionary: ')
name = "w2vmodel_vector_500"

if not tagger:
    sys.stderr.write("Cannot load dictionary.")
    sys.exit(1)

if __name__ == '__main__':
    model = load_model(name)
    get_paraphrases(model)
    
    
    
