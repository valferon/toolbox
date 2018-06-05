#!/bin/bash

#### DOC
#
##
##  gocd parameters
##
##  namespace       - refers to charts/[env]
##  chart name      - refers to charts/env/[microservice].yaml
##  chart override  - refers to extra parameters for helm to override existing values
##  release name    - refers to the name that kubernetes is going to display for the deployment, service and ingress
##
#



DEV_CLUSTER_NAME="kube-dev-xxxxxx.com"
DEV_KUBERNETES_HOST="https://api.kube-dev-xxxxxx.com"

PROD_CLUSTER_NAME="kube-prod-yyyyyy.com"
PROD_KUBERNETES_HOST="https://api.kube-prod-yyyyyy.com"
PROD_GOCD_TOKEN_PATH="/var/go/.kube_prod_gocd_token"




USER="gocd"
KUBERNETES_GOCD_SVC_ACCNT="gocd"
KUBERNETES_PASSWORD=""
CONTEXT="gocd-context"




NAMESPACE=$1        # Kubernetes Namespace  (ie. staging)
DEPLOYMENT=$2
SCALING=$3


function var_dump {
    echo  "--------------------------------------------"
    echo  "NAMESPACE        >>>     ${NAMESPACE}"
    echo  "--------------------------------------------"
}

function set_context {
    if [[ "$NAMESPACE" != "prod" ]]
    then
        kubectl config set-cluster ${DEV_CLUSTER_NAME} --server=${DEV_KUBERNETES_HOST} --insecure-skip-tls-verify=true
        kubectl config set-credentials ${USER} --token=$(cat ~/.kube_dev_gocd_token)
        kubectl config set-context ${CONTEXT} --cluster=${DEV_CLUSTER_NAME} --user=${USER} --namespace=kube-system #${NAMESPACE}
        kubectl config use-context ${CONTEXT}
#    else
#        kubectl config set-cluster ${PROD_CLUSTER_NAME} --server=${PROD_KUBERNETES_HOST} --insecure-skip-tls-verify=true
#        kubectl config set-credentials ${USER} --token=$(cat ~/.kube_prod_gocd_token)
#        kubectl config set-context ${CONTEXT} --cluster=${PROD_CLUSTER_NAME} --user=${USER} --namespace=kube-system #${NAMESPACE}
#        kubectl config use-context ${CONTEXT}
    fi
}

### START ###
echo "##################################"
echo "###### STARTING SCALING ######"
echo "##################################"


if [ -z "${NAMESPACE}" ]; then
    echo  "--------------------------------------------"
    echo "Failed to get environment variable NAMESPACE - Please configure it in gocd command arguments"
    echo  "--------------------------------------------"
fi

if [ -z "${DEPLOYMENT}" ]; then
    echo  "--------------------------------------------"
    echo "No DEPLOYMENT configured [number of desired pods]- - Please configure it in gocd command arguments if needed"
    echo  "--------------------------------------------"
fi

if [ -z "${SCALING}" ]; then
    echo  "--------------------------------------------"
    echo "No SCALING configured [number of desired pods]- - Please configure it in gocd command arguments if needed"
    echo  "--------------------------------------------"
fi

# config
set_context

#####

kubectl config set-context $(kubectl config current-context) --namespace ${NAMESPACE}
var_dump

if [[ "$NAMESPACE" != "prod" ]]
then
    if [[ "$DEPLOYMENT" != "all" ]]
    then
        echo "##################################"
        echo "Current deployment status"
        kubectl get deploy/${DEPLOYMENT}
        echo "##################################"
        echo "Updating deployment"
        kubectl scale --replicas=${SCALING} deployment/${DEPLOYMENT}
    else
        echo "##################################"
        echo "Current deployment status"
        kubectl get deploy
        echo "##################################"
        echo "Scaling all deployments to ${SCALING}"
        cd ..
        for dep in $( kubectl get deploy | awk '{ print $1 }' | grep -v NAME)
        do
            echo "kubectl scale --replicas=${SCALING}  deployment/$dep"
            ./kubectl_dev scale --replicas=${SCALING}  deploy/${dep}
            sleep 5
        done
    fi
else
    echo "Updating prod deployment scaling not yet available"
fi

echo "##################################"
echo "######         END        ########"
echo "##################################"
