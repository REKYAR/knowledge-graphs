from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON


class NanoPubs:
    def __init__(self, endpoint: str | None = None) -> None:
        if endpoint is None:
            self.endpoint = "https://virtuoso.nps.knowledgepixels.com/sparql"
        else:
            self.endpoint = endpoint

        self.sparql = SPARQLWrapper(self.endpoint)

    def get_random_npubs(self, n: int = 10) -> list[dict[str]]:
        assert type(n) is int
        assert n > 0

        query = """
        SELECT ?publication ?p ?o WHERE {
            ?publication ?p ?o .
        }
        ORDER BY RAND()
        LIMIT """ + str(n)
        print(query)

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        return self.sparql.queryAndConvert()["results"]["bindings"]

    def get_user_npubs(self, user_id: str) -> list[dict[str]]:
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
        print(query)

        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        return self.sparql.queryAndConvert()["results"]["bindings"]


if __name__ == "__main__":
    nano_pubs = NanoPubs()

    # for i in nano_pubs.get_random_npubs():
    #     print(i)

    for i in nano_pubs.get_user_npubs("0009-0009-6638-993X"):
        print(i)
