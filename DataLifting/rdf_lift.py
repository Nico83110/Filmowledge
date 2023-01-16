import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

g = Graph()

# On charge les schémas
g.parse("../ontology/schema/MergedSchemas.ttl", format="turtle")
g.parse("../DataEnriching/topics.ttl", format="turtle")

# On défini les namespaces utilisés dans le schéma
movie = Namespace("http://example.com/movie#")
myvocab = Namespace("http://myvocab.org/")

# On lit le fichier JSON
with open("../DataEnriching/movies_enriched.json") as json_file:
    data = json.load(json_file)
    for item in data:
        film = URIRef("http://example.com/movie/" + str(item["id"]))
        g.add((film, RDF.type, movie.Movie))
        g.add((film, movie.Title, Literal(item["title"])))
        g.add((film, movie.Adult, Literal(item["adult"])))
        g.add((film, movie.Overview, Literal(item["overview"])))
        g.add((film, movie.Popularity, Literal(item["popularity"])))
        g.add((film, movie.PosterPath, Literal(item["poster_path"])))
        g.add((film, movie.Video, Literal(item["video"])))
        g.add((film, movie.VoteAverage, Literal(item["vote_average"])))
        g.add((film, movie.VoteCount, Literal(item["vote_count"])))
        g.add((film, movie.OriginalLanguage, Literal(item["original_language"])))
        g.add((film, movie.OriginalTitle, Literal(item["original_title"])))

        if 'topics' in item:
            # Ajouter des triples pour les sujets
            for topic in item['topics']:
                topic_uri = myvocab[topic.replace(" ", "")]
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