#from util import *

import rdflib
from rdflib import Namespace, Literal
from rdflib import OWL, RDF, RDFS, XSD, TIME
from rdflib import Graph,URIRef
import re


##### Initialize graph prefixes
NAME_SPACE = "http://stko-kwg.geog.ucsb.edu/"

_PREFIX = {
    "kwgr": Namespace(f"{NAME_SPACE}lod/resource/"),
    "kwg-ont": Namespace(f"{NAME_SPACE}lod/ontology/"),
    "geo": Namespace("http://www.opengis.net/ont/geosparql#"),
    "geof": Namespace("http://www.opengis.net/def/function/geosparql/"),
    "sf": Namespace("http://www.opengis.net/ont/sf#"),
    "wd": Namespace("http://www.wikidata.org/entity/"),
    "wdt": Namespace("http://www.wikidata.org/prop/direct/"),
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD,
    "owl": OWL,
    "time": TIME,
    "dbo": Namespace("http://dbpedia.org/ontology/"),
    "time": Namespace("http://www.w3.org/2006/time#"),
    "ssn": Namespace("http://www.w3.org/ns/ssn/"),
    "sosa": Namespace("http://www.w3.org/ns/sosa/"),
    "skos": Namespace("http://www.w3.org/2004/02/skos/core#"),
    "doid": Namespace("http://purl.obolibrary.org/obo/doid#"),
    "prov": Namespace("http://www.w3.org/ns/prov#")
}



print("Begin loading graph")
g = rdflib.Graph()
g.parse ('https://raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/main/src/ontology/doid.owl', format='application/rdf+xml')
print(len(g))

preds = set() #predicate list

def _main():
    output_file_h = "do_topic_hierarchy.ttl"
    print("Start triplification")
    graph_do = construct_topic_hierarchy()
    with open(output_file_h, "w") as out_h:
        temp = graph_do.serialize(format="turtle", encoding="utf-8", destination=None)
        out_h.write(temp.decode("utf-8"))
    print("Completed triplification and file saved")        



        
## a general function to generate iri
def MakeIRI(type, id, pref=_PREFIX['kwgr']):
    id = re.sub(r"_[0-9a-zA-Z]", lambda m: m.group().upper(), id) # use camelback instead of underscore
    id = id.replace('_', '')
    if type != '':
        return pref[f'{type}.{id}']
    else:
        return pref[f'{id}']

## a general function to generate iri
def MakeConnectIRI(type, subject, object, pref=_PREFIX['kwgr']):
    subject = re.sub(r"_[0-9a-zA-Z]", lambda m: m.group().upper(), subject) # use camelback instead of underscore
    subject = subject.replace('_', '')
    object = re.sub(r"_[0-9a-zA-Z]", lambda m: m.group().upper(), object) # use camelback instead of underscore
    object = object.replace('_', '')
    return pref[f'{type}.{subject}.{object}']


# KG Construction Function
def init_kg_with_prefix(_PREFIX):
    kg = Graph()
    for prefix in _PREFIX:
        kg.bind(prefix, _PREFIX[prefix])   
    return kg

def get_predicate_list():
  count= 0
  subClasses = []

  obo = URIRef("http://www.w3.org/2002/07/owl#equivalentClass")
  
  for p in g.predicates():
    if p not in preds:
        preds.add(p)
  #print(preds)
  for subj, obj in g.subject_objects(predicate=obo):
    print(type(subj), type(obj))
    print("done")

#####################parsing through Disease_ontology to get rdfs:subClassOf#############################
import pandas as pd
def Initial_KG(_PREFIX):
    kg = init_kg_with_prefix(_PREFIX)
#     Add_Ontology_Triple_To_KG(kg, _PREFIX)
    return kg
def construct_topic_hierarchy():

  #kwgrGraph = rdflib.Graph()
  kwgrGraph = Initial_KG(_PREFIX)

  for subj_iri, obj_iri in g.subject_objects(predicate=RDFS.subClassOf):
    ###############include function for general set of predicates#####

    ######check whether subject and object nodes are specifically from Disease Ontology (DO)########################
    do_prefix = "http://purl.obolibrary.org/obo/DOID"
    print(do_prefix)
    
    if (do_prefix in subj_iri) and (do_prefix in obj_iri):
        ###############get subject and object names#####
        subj = subj_iri.rsplit('/', 1)[-1]
        obj = obj_iri.rsplit('/', 1)[-1]

        print(subj)
        ##################get labels for subject and object##########
        subj_label = g.value(subj_iri, RDFS.label)
        obj_label = g.value(obj_iri, RDFS.label)
    

        ######make IRIs for topic hierarchy (of the format topic.disease)########################
        subj_disease_topic_iri = MakeIRI('topic',subj)
        obj_disease_topic_iri = MakeIRI('topic',obj)
    
        if subj_disease_topic_iri is not None:
            #####################adding to the graph##################
            kwgrGraph.add( (subj_disease_topic_iri, RDF.type, _PREFIX["kwg-ont"]["Topic"]) )
            kwgrGraph.add( (subj_disease_topic_iri, RDFS.label, Literal(str(subj_label) + " topic")) )

            kwgrGraph.add( (obj_disease_topic_iri, RDF.type, _PREFIX["kwg-ont"]["Topic"]) )
            kwgrGraph.add( (obj_disease_topic_iri, RDFS.label, Literal(str(obj_label)+ " topic")) )

            kwgrGraph.add( (subj_disease_topic_iri, _PREFIX["kwg-ont"]["isSubTopicOf"], obj_disease_topic_iri) )
            #kwgrGraph.add( (obj_disease_topic_iri, _PREFIX["kwg-ont"]["hasRelatedTopic"], uberon_topic_iri) )

            #####################create topic-connectedness relation##################
            topic_connectedness_iri = MakeConnectIRI('topicConnect', subj, obj)
            connect_description = str(obj_label)+ " is a sub-topic of "+str(subj_label) ## this will be updated if relations other than subclass are materialized
            kwgrGraph.add( (topic_connectedness_iri, RDF.type, _PREFIX["kwg-ont"]["TopicConnectednessRelation"]) )
            kwgrGraph.add( (topic_connectedness_iri, RDFS.label, Literal("Entity describing the relation between "+str(subj_disease_topic_iri)+" and "+ str(obj_disease_topic_iri))) )
            kwgrGraph.add( (topic_connectedness_iri, _PREFIX["skos"]["description"], Literal(connect_description)) )
            kwgrGraph.add( (topic_connectedness_iri, _PREFIX["prov"]["hadPrimarySource"], _PREFIX["doid"][obj_iri]) )
            kwgrGraph.add( (subj_disease_topic_iri, _PREFIX["kwg-ont"]["hasConnectDescription"], topic_connectedness_iri) )
            kwgrGraph.add( (obj_disease_topic_iri, _PREFIX["kwg-ont"]["hasConnectDescription"], topic_connectedness_iri) )
  return kwgrGraph

_main()

