import rdflib
from rdflib import Namespace

g = rdflib.Graph(bind_namespaces="rdflib")

filepath = '../DataEnriching/topics.ttl'
#g.parse("http://danbri.org/foaf.rdf#")
g.parse(filepath)

sparql_query = """
PREFIX : <http://myvocab.org/>

SELECT *
WHERE {
    ?x :similarTo ?z
}
"""

qres = g.query(sparql_query)
for row in qres:
    print(f"{row.x} is similar to {row.z}")