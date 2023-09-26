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
    index_pattern = request.form.get('index_name') or request.form.get('index_dropdown')
    query = request.form.get('query')

    # Construct the search body based on the query
    if query:
        body = {
            "size": 100,
            "query": {
                "query_string": {
                    "query": query,
                    "default_field": "*"
                }
            }
        }
    else:
        body = {
            "query": {
                "match_all": {}
            }
        }

    results = es.search(index=index_pattern, body=body)
    all_keys = set()
    for hit in results["hits"]["hits"]:
        all_keys.update(hit.keys())  # Add this to include top-level keys like _id, _index, etc.
        all_keys.update(hit['_source'].keys())
    all_keys = sorted(list(all_keys))
    
    original_url = f"http://es-dev-data01.sgdctroy.net:9200/{index_pattern}/_search?source_content_type=application/json&source={body}"

    return render_template('results.html', results=results["hits"]["hits"], all_keys=all_keys, original_url=original_url)

if __name__ == "__main__":
    app.run(debug=True)
