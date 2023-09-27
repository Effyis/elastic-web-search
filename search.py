from copy import deepcopy
import json
import re
import urllib.parse
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

    processed_results = []

    for hit in results["hits"]["hits"]:
        # Make a deep copy to preserve the original
        original_hit = deepcopy(hit)
        processed_hit = hyperlink_urls_in_dict(
            hit)  # This modifies the hit in-place
        processed_results.append({
            "original": original_hit,
            "display": processed_hit
        })

    body_json = json.dumps(body)
    encoded_body = urllib.parse.quote(body_json)
    original_url = f"http://es-dev-data01.sgdctroy.net:9200/{index_pattern}/_search?source_content_type=application/json&source={encoded_body}"

    return render_template('results.html', results=processed_results, original_url=original_url, query=query)


def hyperlink_urls_in_dict(d):
    # Pattern to match URLs (with or without http/https) and file paths
    url_pattern = re.compile(
        r'(?:(?:http[s]?://)?(?:(?:[a-zA-Z0-9-]+)\.)+[a-zA-Z]{2,6}[\w/._-]*(?:\?[^\s]*)?)|(/[\w/._-]+)'
    )

    for key, value in d.items():
        if isinstance(value, dict):
            hyperlink_urls_in_dict(value)
        elif isinstance(value, str):
            # Create the hyperlink for matched patterns
            def repl(match):
                url = match.group(0)
                # If it doesn't start with 'http', consider it as a relative URL (add http)
                if not url.startswith(('http://', 'https://', '/')):
                    url = 'http://' + url
                return f'<a href="{url}" target="_blank">{match.group(0)}</a>'
            
            d[key] = url_pattern.sub(repl, value)

    return d


if __name__ == "__main__":
    app.run(debug=True)
