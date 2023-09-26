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
    index_pattern = request.form.get(
        'index_name') or request.form.get('index_dropdown')
    query = request.form.get('query')

    # Construct the search body based on the query
    if query:
        body = {
            "size": 100,
            "query": {
                "multi_match": {
                    "query": query,
                    "type": "phrase",
                    "fields": ["*"]
                }
            },
            "sort": [
                {
                    "@timestamp": {
                        "order": "desc"
                    }
                }
            ]
        }
    else:
        body = {
            "query": {
                "match_all": {}
            }
        }

    results = es.search(index=index_pattern, body=body)
    
    # Extract hits
    hits = results["hits"]["hits"]
    
    original_url = f"http://es-dev-data01.sgdctroy.net:9200/{index_pattern}/_search?source_content_type=application/json&source={body}"

    return render_template('results.html', results=hits, original_url=original_url)


if __name__ == "__main__":
    app.run(debug=True)
