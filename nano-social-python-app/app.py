from flask import Flask, request, jsonify, render_template
import pandas as pd
from nanopub import NanopubClient
import requests

app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')
client = NanopubClient()

@app.route('/')
def home():
    # Strona główna aplikacji
    return render_template('index.html')


@app.route('/search_nanopubs', methods=['GET'])
def search_nanopubs():
    keyword = request.args.get('keyword', default='', type=str)
    author = request.args.get('author', default='', type=str)
    limit = request.args.get('limit', default=10, type=int)

    try:
        # Wykonanie zaawansowanego zapytania SPARQL w celu wyszukiwania nanopublikacji
        query = f"""
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX np: <http://www.nanopub.org/nschema#>
        SELECT DISTINCT ?nanopub ?author ?title WHERE {{
            ?nanopub a np:Nanopublication .
            ?nanopub dcterms:title ?title .
            ?nanopub dcterms:creator ?author .
            FILTER(CONTAINS(LCASE(?title), LCASE("{keyword}")))
        
            {f'FILTER(CONTAINS(LCASE(?author), LCASE("{author}")))' if author else ''}
        }}
        LIMIT {limit}
        """

        nanopub_uris = list(client.find_nanopubs_with_text(query))

        # Jeśli serwer zwróci HTML zamiast JSON, to może być błąd serwera.
        if not nanopub_uris:
            return jsonify({'error': 'No results found or query failed.'})

        nanopub_data = []

        for uri in nanopub_uris[:limit]:
            try:
                # Pobieranie szczegółów nanopublikacji
                nanopub = client.fetch(uri)
                assertion = nanopub.rdf.assertion.serialize(format='n3')
                nanopub_data.append({
                    'URI': uri,
                    'Creator': nanopub.creator,
                    'Assertion': assertion
                })
            except Exception as fetch_error:
                # Obsługa błędów podczas pobierania szczegółów nanopublikacji
                print(f"Error fetching nanopub {uri}: {fetch_error}")

        # Tworzymy tabelę pandas z wynikami, a następnie konwertujemy do słownika
        if nanopub_data:
            df = pd.DataFrame(nanopub_data)
            result = df.to_dict(orient='records')
            print(result)  # Debug: logowanie zwracanych danych
            return jsonify(result)
        else:
            return jsonify({'error': 'No valid nanopublications found.'})

    except Exception as e:
        return jsonify({'error': f'SPARQL query failed: {str(e)}'})



@app.route('/fetch_doi_details', methods=['GET'])
def fetch_doi_details():
    doi_url = request.args.get('doi_url', type=str)
    try:
        # Używamy content negotiation, aby uzyskać dane RDF z DOI
        response = requests.get(doi_url, headers={"Accept": "application/rdf+xml"})
        if response.status_code == 200:
            return response.text
        else:
            return jsonify({'error': f'Failed to fetch DOI details, status code: {response.status_code}'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/publish_nanopub', methods=['POST'])
def publish_nanopub():
    try:
        # Pobierz dane z formularza
        assertion = request.form['assertion']
        creator = request.form['creator']
        # Utwórz nanopublikację
        response_info = client.publish(assertion_rdf=assertion, introduces_concept=None)
        return jsonify({'message': 'Nanopublication published successfully!', 'uri': response_info.get('nanopub_uri')})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)