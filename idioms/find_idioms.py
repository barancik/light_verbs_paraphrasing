# Takes vallex and generates possible adress on the webpage for every
# verb, then clusterize verbs.
# Returns frozenset of verbs -> [Frame] dict

from collections import defaultdict
#from unidecode import unidecode
from string import digits
import re
import pickle

VALLEX_FILE = "/home/pida/vallex/trunk/aktualni_data/data-txt/vallex.txt"

class MWE(object):
    def __init__(self,verbs):
        self.verbs = verbs
        self.joint_verbs = "_".join(verbs)
        self.dphrs = set([])

    def add_dphrs(self,dphrs):
        self.dphrs.update(dphrs)

class new_MWE(object):
    def __init__(self,verbs):
        self.joint_verbs = "_".join(verbs)
        self.dphrs = set([])
        self.reflexive = defaultdict(set)

    def add_dphrs(self,dphrs,reflexive=False):
        if reflexive:
            self.reflexive[reflexive].update(dphrs)
        else:
            self.dphrs.update(dphrs)

class Verb(object):
    def __init__(self,verb):
        tabs = verb.split(" ")
        self.reflexive = False
        if len(tabs) == 2:
            self.reflexive = tabs[1]
        self.lemma = tabs[0]

def normalize_verb(line):
     return line.strip()[2:].decode('utf-8').lower()
	
def printverb(verb):
    verb = "".join([c for c in verb.lower() if not c.isdigit()])
    return set([x.strip() for x in re.split('[,/]',verb)])
	
def get_DPHRS(verb):
    return re.search("DPHR\(([^)]*)",verb).group(1).split(";")[0].split(",")

def new_extract(vallex_file=VALLEX_FILE):
    found = {}
    for line in open(vallex_file):
        if line.startswith('#'):
            continue
        if line.startswith("*"):
            all_verbs = printverb(line.strip()[2:])
        if "DPHR" in line and line.startswith(' +i '):
            verbs = [Verb(x) for x in all_verbs]
            for verb in verbs:
                if verb.lemma not in found:
                    found[verb.lemma] = new_MWE(all_verbs)
            dphrs = get_DPHRS(line.strip())
            for verb in verbs:
                found[verb.lemma].add_dphrs(dphrs,verb.reflexive)
    return found

def extract(vallex_file=VALLEX_FILE):
    found = {}
    for line in open(vallex_file):
        if line.startswith('#'):
            continue
        if line.startswith("*"):
            verb = line.strip()[2:]
            all_verbs = printverb(verb)
        if "DPHR" in line and line.startswith(' +i '):
            verbs = [Verb(x) for x in all_verbs]
            for verb in verbs:
                if verb.lemma not in found:
                     found[verb] = MWE(all_verbs)
            dphrs = get_DPHRS(line.strip())
            found[verb].add_dphrs(dphrs)
    return found

if __name__ == "__main__":
    found = new_extract()
    pickle.dump(found,open("new_mwe.pickle","wb"))
