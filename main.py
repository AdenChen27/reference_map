import requests
import joblib
import json
import networkx as nx
from pyvis.network import Network

class Work:
    def get_intext_authors(self):
        # return authors in intext citation format (e.g. "A & B, (yyyy)", "A et al., (yyyy)")
        # return False if failed
        if not hasattr(self, "crossref_response"):
            return False
        authors = self.crossref_response["author"]
        # print(authors)
        # names = [au["family"] for au in authors]
        names = []
        for author in authors:
            if "family" in author:
                names.append(author["family"])
            elif "name" in author:
                names.append(author["name"])
        author_n = len(authors)
        if author_n == 1:
            return f"{names[0]}, ({self.publish_year})"
        elif author_n == 2:
            return f"{names[0]} & {names[1]}, ({self.publish_year})"
        else:
            return f"{names[0]} et al., ({self.publish_year})"

    def init_from_doi(self, doi=None):
        # init from self.doi if not provided in argument
        if doi:
            self.doi = doi
        # get info from crossref
        page = requests.get(rf"http://api.crossref.org/works/{self.doi}")

        if page.status_code != 200:
            print(f"[{page.status_code}]", end="", flush=True)
            return False
        
        response = json.loads(page.content)["message"]

        self.crossref_response = response
        self.title = response["title"]
        self.publish_year = response["published"]["date-parts"][0][0]
        self.doi_ref = set() # reference list in doi
        
        if "reference" in response:
            for reference in response["reference"]:
                if "DOI" in reference:
                    self.doi_ref.add(reference["DOI"])

    def init_from_dict(self, attr):
        for key, value in attr.items():
            setattr(self, key, value)

    def __init__(self, *args):
        # no args: empty
        # 1 args: init from doi/dict of attributes
        if len(args) == 0:
            return
        if len(args) == 1:
            arg = args[0]
            if type(arg) == str:
                self.init_from_doi(arg)
            elif type(arg) == dict:
                init_from_dict(arg)
            else:
                raise Exception("Work.__init__(arg): make sure arg is str/dict")
        else:
            raise Exception("Work.__init__() don't know how to handle two arguments or more")

def log(filename):
    joblib.dump({
        "works_n": works_n, 
        "all_doi": all_doi, 
        "works": works, 
        "doi_to_id": doi_to_id, 
        "works_ref": works_ref, 
        "expended_works_i": expended_works_i, 
    }, filename)

def load_log(filename):
    global works, works_n, all_doi, doi_to_id, works_ref
    log = joblib.load(filename)
    works = log["works"]
    works_n = log["works_n"]
    all_doi = log["all_doi"]
    doi_to_id = log["doi_to_id"]
    works_ref = log["works_ref"]
    expended_works_i = log["expended_works_i"]

# plotting
def generate_graph(filename="graph.html"):
    nx_graph = nx.DiGraph()
    for work_i, work in works.items():
        if not hasattr(work, "doi_ref"):
            continue
        for doi in work.doi_ref:
            # if not(doi in all_doi):
            # if not(doi in all_doi and \
            #     hasattr(works[doi_to_id[doi]], "crossref_response") and \
            #     hasattr(works[doi_to_id[work.doi]], "crossref_response")):
            #     continue
            # nx_graph.add_edge(
            #     works[doi_to_id[work.doi]].get_intext_authors(), 
            #     works[doi_to_id[doi]].get_intext_authors(), 
            # )
            if not(doi in all_doi and \
                hasattr(works[doi_to_id[doi]], "title") and \
                hasattr(works[doi_to_id[work.doi]], "title") # and \
                # "gender" in works[doi_to_id[work.doi]].title[0].lower() and \
                # "gender" in works[doi_to_id[doi]].title[0].lower()
            ):
                continue
            title1 = works[doi_to_id[work.doi]].title[0]
            title2 = works[doi_to_id[doi]].title[0]
            nx_graph.add_edge(
                title1, 
                title2, 
            )
            # if "gender" in title1.lower():
            #     nx_graph.nodes[title1]["color"] = "red"
            # if "gender" in title2.lower():
            #     nx_graph.nodes[title2]["color"] = "red"

            # nx_graph.add_edge(
            #     str(doi_to_id[work.doi]), 
            #     str(doi_to_id[doi])
            # )
            # nx_graph.add_edge(
            #     str(works[doi_to_id[work.doi]].publish_year), 
            #     str(works[doi_to_id[doi]].publish_year), 
            # )
    # import matplotlib.pyplot as plt
    # nx.draw(nx_graph, with_labels=True)
    # plt.show()
    # plt.savefig("test.png")
    
    network = Network("1500px", "2000px", directed=True)
    # network.show_buttons(filter_=['physics'])
    network.set_options("""
const options = {
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -2250,
      "centralGravity": 0.55,
      "springLength": 165,
      "springConstant": 0.015,
      "damping": 0.56
    },
    "minVelocity": 0.75
  }
}""")
    network.from_nx(nx_graph)
    network.show(filename)

def expand(work_i):
    # work_i: Work object's key in `works`
    # load Work objects from `work.doi_ref` (reference list in doi)
    print("[+]start expending...")
    global works, works_n, all_doi, doi_to_id, works_ref, expended_works_i

    for doi in works[work_i].doi_ref:
        if doi in all_doi:
            # loaded
            i_ref.append(doi_to_id[doi])
            print(".", end="", flush=True)
        else:
            print(f"on doi:{doi}", end="... ", flush=True)
            works_n += 1
            works[works_n] = Work(doi)
            doi_to_id[doi] = works_n
            all_doi.add(doi)
            if not hasattr(works[works_n], "title"):
                print("[failed]")
            else:
                print("done.")
                log(f"log01_{works_n}.joblib")

    expended_works_i.add(work_i)
    print("[+]done")

# print("Init seed...", end=" ", flush=True)
# seed_doi = "10.1002/ijop.12265"

# works_n = 1
# works = {1: Work(seed_doi)}
# doi_to_id = {seed_doi: 1}
# all_doi = set([seed_doi])
# expended_works_i = set()
# works_ref = {}
# print("done")
# reference list using index (starts from 1)
# ={index: [ref_list_in_indexs], }

# load_log("log01.joblib")
# log("log02.joblib")


load_log("log011.joblib")
# expand(1)
# log("log011.joblib")
generate_graph("6.html")
# [works[k].publish_year for k in works if hasattr(works[k], "publish_year")]
# [list(works[k].doi_ref)[0] for k in works if hasattr(works[k], "doi_ref")]

