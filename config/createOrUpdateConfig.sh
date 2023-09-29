#!/bin/bash
ENV=$1

if [[ "${ENV}" != "dev" && "${ENV}" != "prod" ]]; then
    echo "Invalid \$ENV '${ENV}'. Only supports 'dev' or 'prod'."
    exit 1
fi

namespace="sg-boards-${ENV}-crawlers"
kubectl -n ${namespace} delete configmap search-vortex-logs-config
kubectl -n ${namespace} create configmap search-vortex-logs-config \
    --from-file=${PWD}/configurations/${ENV} | kubectl -n ${namespace} apply -f -

echo "Done with createOrUpdateConfig.sh"