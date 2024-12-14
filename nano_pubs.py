from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper import JSON
from bs4 import BeautifulSoup
import requests

from constans import TEXT_NOT_FOUND, AUTHOR_NOT_FOUNT, DATE_NOT_FOUND


def download_npub_comment(npub_uri: str) -> str | None:
    page_url = f"https://nanodash.knowledgepixels.com/explore?2&id={npub_uri}"
    try:
        response = requests.get(page_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        jsonld_link = soup.find('a', string="JSON-LD")

        if jsonld_link:
            jsonld_url = jsonld_link['href']

            if not jsonld_url.startswith("http"):
                jsonld_url = requests.compat.urljoin(page_url, jsonld_url)

            response = requests.get(jsonld_url)
            response.raise_for_status()
            json_data = response.json()

            comment_uri = "http://www.w3.org/2000/01/rdf-schema#comment"
            for element in json_data:
                for dict_ in element["@graph"]:
                    if comment_uri in dict_:
                        return dict_[comment_uri][0]["@value"]
            return None
        else:
            print("Nie znaleziono linku do `JSON-LD`.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Błąd przy próbie pobrania strony: {e}")
        return None


class NanoPubs:
    def __init__(self, endpoint: str | None = None) -> None:
        if endpoint is None:
            self.endpoint = "https://virtuoso.nps.knowledgepixels.com/sparql"
        else:
            self.endpoint = endpoint

        self.sparql = SPARQLWrapper(self.endpoint)

    def prepare_comment_query(
            self,
            commented_uri: str,
            comment_uri: str
            ) -> str:

        return f"""
            SELECT ?comment WHERE {{
            GRAPH ?commenter {{
                <{commented_uri}> <http://www.w3.org/2000/01/rdf-schema#comment> ?comment .
            }}
            <{comment_uri}> <http://www.nanopub.org/nschema#hasAssertion> ?commenter .
            }}
        """

    def get_random_npubs(
            self,
            n: int = 10,
            simple: bool = False
            ) -> list[dict[str]]:

        assert type(n) is int
        assert n > 0

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

    def get_npub_comments_uris(
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
            return [e["referring"]["value"] for e in results]
        else:
            return results

    def get_npub_comments_tree(
            self,
            npub_id: str | None = None,
            npub_uri: str | None = None
            ) -> list[dict[str]]:

        if npub_uri is None:
            npub_uri = f"https://w3id.org/np/{npub_id}"

        comments_uris = self.get_npub_comments_uris(
            npub_uri=npub_uri, simple=True
            )

        tree = []
        for comment_uri in comments_uris:
            text = self.get_npub_comment_text(npub_uri, comment_uri)
            the_comment = {
                "uri": comment_uri,
                "text": text,
                "author": self.get_author(npub_uri=comment_uri),
                "date": self.get_date(npub_uri=comment_uri),
                "comments": self.get_npub_comments_tree(npub_uri=comment_uri)
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

    def get_npub_comment_text(self, npub_uri: str, comment_uri: str) -> str:
        query = self.prepare_comment_query(npub_uri, comment_uri)
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.queryAndConvert()

        comment_content = results["results"]["bindings"]
        if len(comment_content) == 0:
            return []

        return comment_content[0]["comment"]["value"]
