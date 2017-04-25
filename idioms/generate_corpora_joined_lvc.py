# Chce dva sloupce potencionalnich jednoslovnych parafrazi, oddelene \t
# Z nich potom udela lemmata tech, ktere se shoduji na POS[0]

from string import punctuation
#from ufal.morphodita import *

from collections import defaultdict
from itertools import combinations
import gzip
import re
import sys
from find_idioms import new_MWE
import pickle

#TODO: davat tam ty spojene, ne jednotlive (resp. mozna vyzkouset oboje)

class Sentence(object):
    def __init__(self,line, mwe):
        self.words = [Word(unit,idx) for idx,unit in enumerate(str(line).strip().split())]
        self.verbs = [x for x in self.words if x.is_verb() and x.shortlemma in mwe]
        if not self.verbs:
           # print(self)
            return

        pairings={}
        for verb in self.verbs:
            found = self.find_mwe(verb.position,mwe[verb.shortlemma].dphrs,mwe[verb.shortlemma].reflexive)
            if found:
                pairings[verb] = found
        if len(found) == 1:
            import pdb;
            pdb.set_trace()
            self.connect_words((found[0]))
            print(self)
        if len(found) > 1:
            import pdb; pdb.set_trace()
     #   sentence = " ".join([word.word for word in self.words])
     #   candidates = {}
     #   for phrase in mwe.phrases:
     #       if phrase in sentence:
     #           import pdb; pdb.set_trace()

     #   self.verbs = filter(lambda x: x.is_verb(), self.words)
    #    self.pairing = self.adjoin_lvcs(phrases,accusatives)
    #    if self.pairing:
#            import pdb; pdb.set_trace()
    #        self._filter()
    #        for x,y in self.pairing.iteritems():
    #            self.connect_words((x,y[0]))
        #print(self)

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
                              "_".join([x.word for x in self.words if x.position in pairing[1]]))
        self.words[idx].lemma = new_lemma
        self.words[idx].shortlemma = new_lemma
        self.words = [x for x in self.words if x.position not in pairing[1]]

    def check_phrases_around(self,idx,phrases):
        results = []
        for phrase in self.get_all_phrases(idx - 4, idx):
            string_phrase = " ".join([self.words[x].word for x in phrase])
            if string_phrase in phrases:
               results.append(phrase)
        for phrase in self.get_all_phrases(idx + 1, idx + 5):
            string_phrase = " ".join([self.words[x].word for x in phrase])
            if string_phrase in phrases:
               results.append(phrase)
        return results


    def find_mwe(self,idx,phrases,reflexive):
        results = []
        phrases = self.check_phrases_around(idx,phrases)
        if phrases:
            results = [(idx,phrases)]
        found_reflexives = [self.words[x].position for x in range(max(0,idx-5),min(idx+5,len(self.words))) \
                            if self.words[x].word in reflexive]
        for x in found_reflexives:
            phrases = self.check_phrases_around(idx,reflexive[x])
            if phrases:
                results.append(([idx,x],phrases))
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

       

if __name__ == "__main__":
    verbs = pickle.load(open("new_mwe.pickle","rb"))
    for line in gzip.open(sys.argv[1],"rt"):
   # for line in open(sys.argv[1],"r"):
        sentence = Sentence(line,verbs)

#def load_lvc():
#    return load_tab("lvc_golden_data"), load_tab("lvc_vendula")

#phrases,accusatives = load_lvc()

#line = sys.stdin.readline()

#for line in gzip.open(sys.argv[1],"r"):
#    sentence = Sentence(line,phrases,accusatives)



