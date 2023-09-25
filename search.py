import json
from urllib.parse import quote
from flask import Flask, render_template, request
from elasticsearch import Elasticsearch

app = Flask(__name__)
es = Elasticsearch(
    [{'host': 'es-dev-data01.sgdctroy.net', 'port': 9200, 'scheme': 'http'}])


@app.route('/')
def index():
    # Retrieve list of indices from Elasticsearch using the _cat API
    indices = es.cat.indices(format="json")

    # Extract the index names from the response
    index_names = [index_info['index'] for index_info in indices]

    return render_template('index.html', indices=index_names)


@app.route('/search', methods=['POST'])
def search():
    index_name = request.form.get('index_name') or request.form.get('index_dropdown')
    query = request.form.get('query')

    if not index_name:
        return 'Index is required!', 400

    # Constructing the appropriate query based on whether the input query is blank or not.
    if query:
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"]
                }
            },
            "size": 100  # This will fetch 100 results. Adjust as needed.
        }

    else:
        body = {
            'query': {
                'match_all': {}
            }
        }

    response = es.search(index=index_name, body=body)
    results = [hit['_source'] for hit in response['hits']['hits']]

    # Generate the Elasticsearch query URL
    es_host = es.transport.hosts[0]['host']
    es_port = es.transport.hosts[0]['port']
    es_url = f"http://{es_host}:{es_port}/{index_name}/_search?source={json.dumps(body)}&source_content_type=application/json"

    return render_template('results.html', results=results, index_name=index_name, query=query or 'All Results', es_url=es_url)


if __name__ == "__main__":
    app.run(debug=True)
