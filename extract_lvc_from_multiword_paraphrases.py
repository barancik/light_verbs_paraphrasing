#!/usr/bin/python
# -*- coding: utf-8 -*-

# Chce dva sloupce potencionalnich jednoslovnych parafrazi, oddelene \t
# Z nich potom udela lemmata tech, ktere se shoduji na POS[0]

from string import punctuation
from ufal.morphodita import *
from collections import defaultdict

import re
import sys

def short_lemma(lemma):
    predek = re.match("([^\-_]+)[\-_\'']",lemma)
    if predek:
	return predek.group(1)
    return lemma

def encode_entities(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def is_verb_and_noun(lemmas):
    if len(lemmas) != 2:
	return ""
    noun = [lemma for lemma in lemmas if lemma.tag.encode("utf-8").startswith("N")]
    verb = [lemma for lemma in lemmas if lemma.tag.encode("utf-8").startswith("V")]
    if noun and verb:
        return "%s %s" % (short_lemma(verb[0].lemma.encode("utf-8")), 
			  short_lemma(noun[0].lemma.encode("utf-8")))
    return ""

def is_verb(lemmas):
   verb = [lemma for lemma in lemmas if lemma.tag.encode("utf-8").startswith("V")]
   if not verb:
       return ""
   typ = verb[0].tag.encode("utf-8")[11]
   verb = short_lemma(verb[0].lemma.encode("utf-8"))
   if len(lemmas) == 1:
	return "%s\t%s" % (verb,typ)
   pronoun = [lemma for lemmma in lemmas if lemma.lemma.encode("utf-8").startswith("se_^(zvr.")]
   if len(lemmas) == 2 and pronoun:
	return "%s %s\t%s" % (verb, short_lemma(pronoun[0].lemma.encode("utf-8")),typ)
   return ""

def load_tab(filename):
    phrases = defaultdict(list)
    for line in open(filename,"r"):
        tabs = line.strip().split("\t")
        phrases[tabs[0]].append(tabs[1])
    return phrases

def load_lvc():
    return load_tab("lvc_golden_data"), load_tab("lvc_vendula")

def tag(tagger,text):
    forms = Forms()
    lemmas = TaggedLemmas()
    tokens = TokenRanges()
    tokenizer = tagger.newTokenizer()
    tokenizer.setText(text)
    while tokenizer.nextSentence(forms, tokens):
        tagger.tag(forms, lemmas)
    return lemmas



def is_lvc(line,phrases,accusatives,tagger):
    lemmas = tag(tagger,line)
    verbs =  [lemma.lemma.encode("utf-8") for lemma in lemmas \
             if lemma.tag.encode("utf-8").startswith("V")]
    for verb in verbs:
        if verb in phrases:
            for phrase in phrases[verb]:
                if phrase in line:
                    return True
        if verb in accusatives:
            accs =  [lemma for lemma in lemmas if lemma.tag.encode("utf-8").startswith("N") \
                     if lemma.tag.encode("utf-8")[4] == "4" ]
            for x in accs:
                if x in accusatives[verb]:
                    return True
    return False

sys.stderr.write('Loading dictionary: ')
#morpho=Morpho.load("/net/projects/morphodita/models/czech-morfflex-pdt-131112/czech-morfflex-131112-pos_only-raw_lemmas.dict")
tagger = Tagger.load("/net/projects/morphodita/models/czech-morfflex-pdt-131112/czech-morfflex-pdt-131112.tagger-best_accuracy")

if not tagger:
    sys.stderr.write("Cannot load dictionary.")
    sys.exit(1)


#line = sys.stdin.readline()
phrases,accusatives = load_lvc() 
#while line:
for line in open(sys.argv[1]):
    tabs = line.strip().split("\t")
    if is_lvc(tabs[0],phrases,accusatives,tagger):
        print "%s\t%s" % (tabs[0],tabs[1])
    if is_lvc(tabs[1],phrases,accusatives,tagger):
        print "%s\t%s" % (tabs[1],tabs[0])
#    import pdb; pdb.set_trace()

