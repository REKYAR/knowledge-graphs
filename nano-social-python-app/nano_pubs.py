from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON

from constans import TEXT_NOT_FOUND, AUTHOR_NOT_FOUNT, DATE_NOT_FOUND


class NanoPubs:
    def __init__(self, endpoint: str | None = None) -> None:
        if endpoint is None:
            self.endpoint = "https://virtuoso.nps.knowledgepixels.com/sparql"
        else:
            self.endpoint = endpoint

        self.sparql = SPARQLWrapper(self.endpoint)

    def get_random_npubs(
            self,
            n: int = 10,
            simple: bool = False
            ) -> list[dict[str]]:

        assert type(n) is int
        assert n > 0

        print("get_random_npubs")

        query = """
        SELECT distinct ?publication ?p ?o WHERE {
            ?publication <https://w3id.org/np/o/ntemplate/wasCreatedFromTemplate> <https://w3id.org/np/RA66vcP_zCtPYIqFaQkv-WhjYZnUiToHRG5EmbMAovZSw> .
            ?publication ?p ?o .
        }
        ORDER BY RAND()
        LIMIT """ + str(n)

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()
        if not simple:
            return results
        else:
            results = results["results"]["bindings"]
            return [e["publication"]["value"] for e in results]

    def get_user_npubs(
            self,
            user_id: str,
            simple: bool = False
            ) -> list[dict[str]]:

        query = (
            """
            SELECT distinct ?a  WHERE {
            ?a ?b ?c .
            """
            +
            f"""FILTER(?c = <https://orcid.org/{user_id}> &&"""
            +
            """
                    ?b = <http://purl.org/dc/terms/creator>)
            }
            """
        )

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()

        if not simple:
            return results
        else:
            results = results["results"]["bindings"]
            return [e["a"]["value"] for e in results]

    def get_author(
            self,
            npub_id: str | None = None,
            npub_uri: str | None = None
            ) -> str:

        if npub_uri is None:
            npub_uri = f"https://w3id.org/np/{npub_id}"

        query = f"""
        SELECT?o WHERE {{
            <{npub_uri}> <http://purl.org/dc/terms/creator> ?o .
        }}
        """

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()
        results = results["results"]["bindings"]

        if len(results) == 0:
            return AUTHOR_NOT_FOUNT

        return results[0]["o"]["value"]

    def get_date(
            self,
            npub_id: str | None = None,
            npub_uri: str | None = None
            ) -> str:

        if npub_uri is None:
            npub_uri = f"https://w3id.org/np/{npub_id}"

        query = f"""
        SELECT?o WHERE {{
            <{npub_uri}> <http://purl.org/dc/terms/created> ?o .
        }}
        """

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()
        results = results["results"]["bindings"]

        if len(results) == 0:
            return DATE_NOT_FOUND

        return results[0]["o"]["value"]

    def get_npub_comments(
            self,
            npub_id: str | None = None,
            npub_uri: str | None = None,
            simple: bool = False
            ) -> list[dict[str]]:

        if npub_uri is None:
            npub_uri = f"https://w3id.org/np/{npub_id}"

        query = f"""
        SELECT DISTINCT ?referring ?target WHERE {{
            VALUES ?target {{ <{npub_uri}> }}
            ?referring <http://purl.org/nanopub/admin/refersToNanopub> ?target .
        }}
        """

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()

        if simple:
            results = results["results"]["bindings"]
            return [e["a"]["value"] for e in results]
        else:
            return results

    def get_npub_comments_tree(
            self,
            npub_id: str | None = None,
            npub_uri: str | None = None
            ) -> list[dict[str]]:

        if npub_uri is None:
            npub_uri = f"https://w3id.org/np/{npub_id}"

        tree = []
        comments = self.get_npub_comments(npub_uri=npub_uri)
        for comment in comments["results"]["bindings"]:
            uri = comment["referring"]["value"]
            the_comment = {
                "uri": uri,
                "text": self.get_npub_text(npub_uri=uri),
                "author": self.get_author(npub_uri=uri),
                "date": self.get_date(npub_uri=uri),
                "comments": self.get_npub_comments_tree(npub_uri=uri)
            }
            tree.append(the_comment)

        return tree

    def get_npub_text(
            self,
            npub_id: str | None = None,
            npub_uri: str | None = None,
            simple: bool = True
            ) -> str:

        if npub_uri is None:
            npub_uri = f"https://w3id.org/np/{npub_id}"

        query = f"""
        SELECT?o WHERE {{
            <{npub_uri}#assertion> <http://www.w3.org/2000/01/rdf-schema#label> ?o .
        }}
        """

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()
        if not simple:
            return results
        else:
            results = results["results"]["bindings"]
            if len(results) == 0:
                return TEXT_NOT_FOUND

            return results[0]["o"]["value"]


if __name__ == "__main__":
    nano_pubs = NanoPubs()

    for i in nano_pubs.get_random_npubs(10, True):
        print(i)

    # for i in nano_pubs.get_user_npubs("0009-0009-6638-993X", True):
    #     print(i)

    # for i in nano_pubs.get_npub_comments("RAG7srcMhYZqsqWoNVs_dh8XwM359JGjLwaiGZ8yxctuU")["results"]["bindings"]:
    #     print(i)

    # print(nano_pubs.get_npub_comments_tree("RAG7srcMhYZqsqWoNVs_dh8XwM359JGjLwaiGZ8yxctuU"))
