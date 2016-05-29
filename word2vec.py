#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os.path
import sys
import multiprocessing
 
import gzip 
import gensim
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

STOPWORDS = ["a","aby","ale","ani","se","v","na","ten","on","že","s","z","který", \
             "do","já","o","k","i","jeho","ale","svůj","jako","za","pro","tak","po",\
             "tento","co","když","všechen","už","jak","od","nebo","jen","můj","jenž",\
             "ty","u","až","než","ještě","při","pak","před","však","ani","také",\
             "podle","mezi","tam","kde"]
FILE="new_corpora"

class MySentences(object):
    def __init__(self, dirname):
        self.dirname = dirname
         
    def __iter__(self):
        for fname in os.listdir(self.dirname):
            for line in gzip.open(os.path.join(self.dirname, fname)):
                yield [x for x in line.lower().split() if x not in STOPWORDS]

def train_model(name,path=FILE):
    sentences = MySentences(path)
    model = gensim.models.Word2Vec(sentences, min_count=100, \
                                   size=500,workers=multiprocessing.cpu_count())
    model.save(name)

def load_model(name,path=FILE):
    return gensim.models.Word2Vec.load(name)

def return_most_similar(model,phrase):
    similar = model.most_similar(positive=[phrase])
    print "%s: %s" % (phrase," ".join([g[0] for g in similar]))

def get_paraphrases(name,lvc_list="found_LVC_over_100"):
    model = load_model(name)
    for line in open(lvc_list,"r"):
        line = line.strip()
        return_most_similar(model,line)

name = "w2vmodel_vector_500"

if __name__ == '__main__':
#    train_model(name)
    get_paraphrases(name)
