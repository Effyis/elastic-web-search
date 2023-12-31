import os
import re
import yaml
from copy import deepcopy
from flask import Flask, render_template, request
from elasticsearch import Elasticsearch

# Load configurations from config.yaml
with open("config/config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# Retrieve Elasticsearch configurations
elasticsearch_hosts = config["elasticsearch_hosts"]
elasticsearch_index = config["index"]

es_hosts = [{"scheme": host["scheme"], "host": host["host"], "port": host["port"]} for host in elasticsearch_hosts]

app = Flask(__name__)
es = Elasticsearch(es_hosts)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')

    # Construct the search body based on the query
    if query:
        body = {
            "size": 10000,
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

    results = es.search(index=elasticsearch_index, body=body)

    processed_results = []

    for hit in results["hits"]["hits"]:
        # Make a deep copy to preserve the original
        original_hit = deepcopy(hit)

        # Add the file size info to the hit
        log_file_path = os.path.join("static", "logs", hit["_source"]["logFileName"].replace("/mnt/data/ftp/qsend/", "").split("/")[-2], hit["_source"]["logFileName"].split("/")[-1])
        #print(log_file_path)
        if os.path.exists(log_file_path):
            # Get the size in bytes
            size_in_bytes = os.path.getsize(log_file_path)
            # Convert to KB and add it to the hit
            hit["_source"]["logFileSize"] = f"{size_in_bytes / 1024:.2f} KB"
        else:
            hit["_source"]["logFileSize"] = "File not found"

        processed_hit = hyperlink_urls_in_dict(hit, query)  # This modifies the hit in-place

        processed_results.append({
            "original": original_hit,
            "display": processed_hit
        })

    return render_template('results.html', results=processed_results, query=query)


def hyperlink_urls_in_dict(d, query):
    for key, value in d.items():
        if isinstance(value, dict):
            hyperlink_urls_in_dict(value, query)
        elif isinstance(value, str):
            # Handle special cases for certain keys
            if key == 'siteUrl' and not value.startswith(('http://', 'https://')):
                value = 'http://' + value
            elif key == 'logFileName':
                value = value.replace('/mnt/data/ftp/qsend/', '/static/')
                value = f'<a href="{value}" target="_blank">Download Log File</a>'

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
