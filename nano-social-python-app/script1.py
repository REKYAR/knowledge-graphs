from rdflib import Graph, URIRef
from SPARQLWrapper import SPARQLWrapper, JSON

def get_nanopub_references(endpoint_url, start_nanopub):
    sparql = SPARQLWrapper(endpoint_url)
    references = []
    
    def query_references(nanopub):
        query = f"""
        SELECT DISTINCT ?referring ?target WHERE {{
            VALUES ?target {{ <{nanopub}> }}
            ?referring <http://purl.org/nanopub/admin/refersToNanopub> ?target .
        }}
        """
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.queryAndConvert()
        
        for result in results["results"]["bindings"]:
            referring = result["referring"]["value"]
            target = result["target"]["value"]
            references.append((referring, target))
            # Recursively query for references to this nanopub
            query_references(referring)
    
    # Start recursive query from the initial nanopub
    query_references(start_nanopub)
    return references

def print_reference_tree(references, root_nanopub, level=0):
    # Find all nanopubs that refer to this one
    referrers = [ref[0] for ref in references if ref[1] == root_nanopub]
    
    for referrer in referrers:
        print("  " * level + f"{referrer} http://purl.org/nanopub/admin/refersToNanopub {root_nanopub}")
        # Recursively print references to this nanopub
        print_reference_tree(references, referrer, level + 1)

# Example usage
endpoint_url = "https://virtuoso.nps.knowledgepixels.com/sparql"
start_nanopub = "https://w3id.org/np/RAG7srcMhYZqsqWoNVs_dh8XwM359JGjLwaiGZ8yxctuU"

references = get_nanopub_references(endpoint_url, start_nanopub)
print_reference_tree(references, start_nanopub)