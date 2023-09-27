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
            hit, query)  # This modifies the hit in-place
        processed_results.append({
            "original": original_hit,
            "display": processed_hit
        })

    body_json = json.dumps(body)
    encoded_body = urllib.parse.quote(body_json)
    original_url = f"http://es-dev-data01.sgdctroy.net:9200/{index_pattern}/_search?source_content_type=application/json&source={encoded_body}"

    return render_template('results.html', results=processed_results, original_url=original_url, query=query, index=index_pattern)

def hyperlink_urls_in_dict(d, query):
    # Pattern to match URLs and file paths
    url_pattern = re.compile(
        r'(?:(?:http[s]?://)?(?:(?:[a-zA-Z0-9-]+)\.)+[a-zA-Z]{2,6}[\w/._-]*(?:\?[^\s]*)?)|(/[\w/._-]+)'
    )
    
    for key, value in d.items():
        if isinstance(value, dict):
            hyperlink_urls_in_dict(value, query)
        elif isinstance(value, str):
            # Create the hyperlink for matched patterns
            def repl(match):
                url = match.group(0)
                # If it's a file path, replace text with "view file"
                if url.startswith('/'):
                    return f'<a href="{url}" target="_blank">view file</a>'
                return f'<a href="{url}" target="_blank">{url}</a>'
            
            value = url_pattern.sub(repl, value)
            
            # Split the string using '<a' and '</a>' as delimiters
            # Only apply highlighting outside of these delimiters to avoid corrupting anchor tags
            parts = re.split(r'(<a|</a>)', value)
            for i, part in enumerate(parts):
                # If the part is not inside an anchor tag, apply highlighting
                if i % 3 == 0:
                    parts[i] = re.sub(re.escape(query), r'<span style="background-color: #ADD8E6">\g<0></span>', part, flags=re.IGNORECASE)
            
            d[key] = ''.join(parts)

    return d

if __name__ == "__main__":
    app.run(debug=True)
