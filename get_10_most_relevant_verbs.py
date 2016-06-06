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

def load_model(name,path=FILE):
    return gensim.models.Word2Vec.load(name)

def return_most_similar(model,phrase):
    similar = model.most_similar(positive=[phrase])
    print "%s %s" % (phrase," ".join([g[0] for g in similar]))

def get_paraphrases(name,lvc_list="found_LVC_over_100"):
    model = load_model(name)
    for line in open(lvc_list,"r"):
        line = line.strip()
        return_most_similar(model,line)

def short_lemma(lemma):
    predek = re.match("([^\-_]+)[\-_\'']",lemma)
    if predek:
	return predek.group(1)
    return lemma

def tag(tagger,text):
    forms = Forms()
    lemmas = TaggedLemmas()
    tokens = TokenRanges()
    tokenizer = tagger.newTokenizer()
    tokenizer.setText(text)
    while tokenizer.nextSentence(forms, tokens):
        tagger.tag(forms, lemmas)
    return lemmas


sys.stderr.write('Loading dictionary: ')
tagger = Tagger.load("/net/projects/morphodita/models/czech-morfflex-pdt-131112/czech-morfflex-pdt-131112.tagger-best_accuracy")
name = "w2vmodel_vector_500"

if not tagger:
    sys.stderr.write("Cannot load dictionary.")
    sys.exit(1)

if __name__ == '__main__':
    model = load_model(name)
    
    
    
