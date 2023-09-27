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
    # Regular expression pattern for URLs
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F])|[#])+')

    # Regular expression pattern for file paths
    filepath_pattern = re.compile(r'\/mnt\/[a-zA-Z0-9\/\.\-_]+')

    for key, value in d.items():
        if isinstance(value, dict):
            hyperlink_urls_in_dict(value)
        elif isinstance(value, str):
            # Replace URLs with hyperlinks
            d[key] = url_pattern.sub(
                r'<a href="\g<0>" target="_blank">\g<0></a>', value)

            # Replace file paths with hyperlinks (with a placeholder href for now)
            d[key] = filepath_pattern.sub(
                r'<a href="#" target="_blank">\g<0></a>', d[key])

    return d


if __name__ == "__main__":
    app.run(debug=True)
