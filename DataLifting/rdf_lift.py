import json
from tqdm import tqdm
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
from pyshacl import validate


def to_camel_case(string):
    string = string.replace('-', ' ')
    words = string.split(" ")
    camel_case = ""
    for word in words[:]:
        camel_case += word.capitalize()
    return camel_case


'''
Does a SPARQL request to retrieve the movies from the given topics.
Topics has to be a list : names = ["Action", "Romantic", "Thriller", ...]
'''
def sparql_request_from_topics(topics):
    topics = [':'+topic for topic in topics] # Add ':' to match the format of topics in the graph
    sparql_query = """
    PREFIX movie: <http://example.com/movie#>
    SELECT *
    WHERE {
        ?movie movie:hasTopic ?topic.
        ?movie movie:Title ?title.
        ?movie movie:Popularity ?popularity.
        FILTER (?topic IN ( """ + ' '.join(topics) + """))
    }
    ORDER BY DESC(?popularity)
    """
    qres = g.query(sparql_query)
    for row in qres:
        print(f"{row.title} is about {row.topic} and has a popularity of {row.popularity}")


g = Graph()

# On charge les schémas
g.parse("../ontology/schema/MergedSchemas.ttl", format="turtle")
g.parse("../DataEnriching/topics.ttl", format="turtle")

# On défini les namespaces utilisés dans le schéma
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SH = Namespace("http://www.w3.org/ns/shacl#")
movie = Namespace("http://example.com/movie#")
myvocab = Namespace("http://myvocab.org/")

# On charge les contraintes SHACL
constraints = Graph()
constraints.parse("../SHACL/BasicConstraints2.ttl", format="turtle")

# On effectue la validation
print("Validation SHACL des données en cours...")
conforms, results_graph, results_text = validate(g, shacl_graph=constraints)

if conforms:
    print("La validation SHACL a réussi !")
else:
    # On affiche les résultats de la validation
    for result in results_graph.subjects(predicate=RDF.type, object=SH.ValidationResult):
        print(results_graph.value(result, SH.resultMessage))

# On lit le fichier JSON
with open("../DataEnriching/movies_enriched.json") as json_file:
    data = json.load(json_file)
    for item in tqdm(data):
        film = URIRef("http://example.com/movie/" + str(item["id"]))
        g.add((film, RDF.type, movie.Movie))
        g.add((film, movie.Title, Literal(item["title"])))
        g.add((film, movie.Adult, Literal(item["adult"])))
        g.add((film, movie.Overview, Literal(item["overview"])))
        g.add((film, movie.Popularity, Literal(item["popularity"], datatype=XSD.integer)))
        g.add((film, movie.PosterPath, Literal(item["poster_path"])))
        g.add((film, movie.Video, Literal(item["video"])))
        g.add((film, movie.VoteAverage, Literal(item["vote_average"], datatype=XSD.integer)))
        g.add((film, movie.VoteCount, Literal(item["vote_count"])))
        g.add((film, movie.OriginalLanguage, Literal(item["original_language"])))
        g.add((film, movie.OriginalTitle, Literal(item["original_title"])))

        if 'topics' in item:
            # Ajouter des triples pour les sujets
            for topic in item['topics']:
                topic_uri = myvocab[to_camel_case(topic)]
                g.add((film, movie.hasTopic, topic_uri))
                
        if 'genre_ids' in item:
            for genre_id in item['genre_ids']:
                genre = URIRef("http://myvocab.org/genre/" + str(genre_id))
                g.add((film, movie.hasGenre, genre))
        #if 'release_date' in item:
            #g.add((film, movie.ReleaseDate, Literal(item["release_date"], datatype=XSD.date)))

# On peut ensuite sauvegarder le résultat en utilisant la méthode serialize()
with open("output.ttl", "w") as f:
    f.write(g.serialize(format="turtle"))


#Appel d'exemple, pour récupérer les films parlant de Criminals
sparql_request_from_topics(["Criminals"])