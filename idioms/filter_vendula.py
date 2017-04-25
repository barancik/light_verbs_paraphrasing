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
        self.dphrs = set([])
        self.reflexive = defaultdict(set)
        self.joint_verbs = "_".join(verbs)

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
	
def extract(vallex_file=VALLEX_FILE):
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


def from_vendula():
    found = pickle.load(open("new_mwe.pickle", "rb"))
    FILE="vendula_remove.txt"
    for line in open(FILE,"r"):
        print(line.strip())
        tabs = [x.strip() for x in line.split("-")]
        verbs = [Verb(x.strip()) for x in tabs[0].split(",")]
        phrase = tabs[1]
        for verb in verbs:
            if verb.reflexive:
                found[verb.lemma].reflexive.discard(phrase)
                if not found[verb.lemma].reflexive:
                    found[verb.lemma].pop(verb.reflexive)
            else:
                found[verb.lemma].dphrs.discard(phrase)
        import pdb; pdb.set_trace()
        if not found[verb.lemma].reflexive and not found[verb.lemma].dphrs:
            found.pop(verb.lemma)
            print("Removing %s" % verb.lemma)
    return found





if __name__ == "__main__":
    x=from_vendula()
    import pdb; pdb.set_trace()
