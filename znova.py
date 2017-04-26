#!/usr/bin/python
# -*- coding: utf-8 -*-

# Chce dva sloupce potencionalnich jednoslovnych parafrazi, oddelene \t
# Z nich potom udela lemmata tech, ktere se shoduji na POS[0]

from string import punctuation
from find_idioms import new_MWE
from collections import defaultdict
from itertools import combinations
import gzip
import re
import pickle
import sys



class Sentence(object):
    def __init__(self,line, phrases):
        self.words = [Word(unit,idx) for idx,unit in enumerate(line.strip().split())]
        self.verbs = filter(lambda x: x.is_verb(), self.words)
        if not self.verbs:
            print(self)
            return
        self.pairing = self.adjoin_lvcs(phrases)
        if self.pairing:
            self._filter()
            for x in self.pairing:
                self.connect_words((x,self.pairing[x][0]))
        #print(" ".join([x.split("|")[0] for x in line.strip().split()]))
        print(self)

    def lemma(self,idx):
        return self.words[idx].shortlemma

    def __str__(self):
        return " ".join([word.shortlemma for word in self.words])

    def _covered_words(self,idx):
        return set([x for y in self.pairing[idx] for x in y])

    def pairing_distance(self,idx,idx_arr):
        return min(abs(idx-min(idx_arr)),abs(idx-max(idx_arr)))
    
    def _filter(self):
        #nejprve se zkusim zbavit kolizi
        for key in self.pairing:
            if not self.pairing[key]:
                continue
            collisions = [key2 for key2 in self.pairing if key2!=key if self.pairing[key2] \
                          if self._covered_words(key).intersection(self._covered_words(key2))]
            for key2 in collisions:
                if len(self.pairing[key]) == 1 and len(self.pairing[key2]) == 1:
                    diff1 = self.pairing_distance(key,self.pairing[key][0])
                    diff2 = self.pairing_distance(key2,self.pairing[key2][0])
                    if diff1 < diff2:
                        self.pairing[key2]=[]
                    else:
                        self.pairing[key]=[]
                elif len(self.pairing[key2]) > 1 and len(self.pairing[key]) > 1:
                    collided = list(self._covered_words(key).intersection(self._covered_words(key2)))
                    for v in collided:
                        if self.pairing_distance(key,[v]) < self.pairing_distance(key2,[v]):
                            to_remove = [x for x in self.pairing[key2] if v in x]
                            for x in to_remove:
                                self.pairing[key2].remove(x)
                        else:
                            to_remove = [x for x in self.pairing[key] if v in x]
                            for x in to_remove:
                                self.pairing[key].remove(x)
                if len(self.pairing[key]) > 1:
                   self.pairing[key] = [x for x in self.pairing[key] if x not in self.pairing[key2]]
                if len(self.pairing[key2]) > 1:
                   self.pairing[key2] = [x for x in self.pairing[key2] if x not in self.pairing[key]] 
        idx_to_remove = []
        for x in self.pairing.keys():
            if not self.pairing[x]: 
                idx_to_remove.append(x)
        for x in idx_to_remove:
            del self.pairing[x]
        #potom zjistim jestli neco ma vice hodnot
        more_options_idx = [x for x in self.pairing if len(self.pairing[x]) > 1]
        for x in more_options_idx:
            self.pairing[x] = sorted(self.pairing[x],\
                                  key = lambda y: min(abs(x-min(y)),abs(x-max(y))))

    def sentence_range(self,bottom,top):
        bottom = max(0,bottom)
        top = min(top,len(self.words))
        return range(bottom,top)

    def get_all_phrases(self,idx1,idx2):
        result = []
        for start, end in combinations(self.sentence_range(idx1,idx2),2):
            result.append([x.position for x in self.words[start:end+1]])
            #result.append(" ".join([x.word for x in self.words[start:end+1]]))
        return result

    def connect_words(self,pairing):
        idx = [x for x in range(len(self.words)) if self.words[x].position == pairing[0]][0]
        new_lemma = "%s_%s" % (self.lemma(idx),
                              "_".join([x.word.lower() for x in self.words if x.position in pairing[1]]))
        self.words[idx].lemma = new_lemma
        self.words[idx].shortlemma = new_lemma
        self.words = [x for x in self.words if x.position not in pairing[1]]
   
    def adjoin_lvcs(self,phrases):
        results = defaultdict(list)
        possible_phr_verbs_idxs = [x.position for x in self.verbs if x.shortlemma in phrases]
        for idx in possible_phr_verbs_idxs:
            lemma = self.words[idx].shortlemma
            possible_lvcs = phrases[lemma].dphrs
            for phrase in self.get_all_phrases(idx-4,idx):
                string_phrase = " ".join([self.words[x].word for x in phrase]).lower()
                if string_phrase in possible_lvcs:
                    results[idx].append(phrase)
            for phrase in self.get_all_phrases(idx + 1, idx + 5):
                string_phrase = " ".join([self.words[x].word for x in phrase]).lower()
                if string_phrase in possible_lvcs:
                    results[idx].append(phrase)

            pronouns = [self.words[x] for x in range(max(0, idx - 5), min(idx + 5, len(self.words))) \
                        if self.words[x].word in phrases[lemma].reflexive]
            for pronoun in pronouns:
                possible_lvcs = phrases[lemma].reflexive[pronoun.word]
                for phrase in self.get_all_phrases(idx - 4, idx):
                    string_phrase = " ".join([self.words[x].word for x in phrase]).lower()
                    if string_phrase in possible_lvcs:
                        results[idx].append([pronoun.position]+phrase)
                for phrase in self.get_all_phrases(idx + 1, idx + 5):
                    string_phrase = " ".join([self.words[x].word for x in phrase]).lower()
                    if string_phrase in possible_lvcs:
                        results[idx].append([pronoun.position]+phrase)
        return results

class Word(object):
    def __init__(self, unit, position):
        parts = unit.split("|")
        if unit.startswith("|"):
            parts=["|","|",unit.split("|")[-1]]
        self.word = parts[0]
        self.lemma = parts[1]
        self.tag = parts[2]
        self.position = position
        self.shortlemma = self._shortlemma()

    def __str__(self):
        return self.word

    def case(self):
        return self.tag[4]

    def get_lemma(self):
        return self.shortlemma

    def is_pronoun(self):
        return self.tag.startswith("P7")

    def has_tag(self,tag):
        return re.match(tag,self.tag)

    def is_accusative(self):
        return self.case() == "4"

    def is_object(self,case="4",number="S"):
        return self.is_noun() and self.new_lemmacase() == case and self.number() == number

    def is_noun(self, case=None, number=None):
        return_value = self.tag.startswith("N")
        if case is not None:
            return_value &= self.case() == case
        if number is not None:
            return_value &= self.number() == number
        return return_value

    def is_verb(self):
        return self.tag.startswith("V")

    def _shortlemma(self):
        if len(self.lemma) < 2 or self.lemma[0] in ["^","_",";","`","-"]:
            return self.lemma
        return re.match("[^_;`-]+",self.lemma).group(0)


def load_tab(filename):
    phrases = defaultdict(list)
    for line in open(filename,"r"):
        tabs = line.strip().split("\t")
        phrases[tabs[0]].append(tabs[1])
    return phrases

def load_lvc():
    return load_tab("lvc_golden_data"), load_tab("lvc_vendula")



#line = sys.stdin.readline()
if __name__ == "__main__":
    verbs = pickle.load(open("filtered_new_mwe.pickle","rb"))
    for line in gzip.open(sys.argv[1],"rt"):
   # for line in open(sys.argv[1],"r"):
        sentence = Sentence(line,verbs)


        #myslenka - v podstate se opakouje ty phrases, ne?
   # nejprve bych ingnorovala reflexiva




