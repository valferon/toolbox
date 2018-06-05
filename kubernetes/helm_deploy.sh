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
KUBERNETES_PASSWORD="................."
CONTEXT="gocd-context"

# Set to '1' if you want to deploy to additional cluster and uncomment above kubernetes cluster config
UPGRADE_DEV=0
UPGRADE_PROD=0
# When migration is complete, turn off UPGRADE and replace "PROD_CLUSTER_NAME" with the migrated one ( PROD_1_x_CLUSTER_NAME )


CHART_NAME=$1
RELEASE_NAME=$2     # Name of HELM release  (ie. gateway)
NAMESPACE=$3        # Kubernetes Namespace  (ie. staging)
PARENT_PIPELINE=$4  # Parent Pipelin, comes from gocd script params
PARTNER=$5
CHART_OVERRIDE=$6   # Path of Dir used to gather all files for docker build



# Figuring out what's the label of the docker-build pipeline
PARENT_CLEAN=$(echo $PARENT_PIPELINE | sed -r 's/-/_/g;s/.*/\U&/g')
FULL_PARENT=$(echo GO_DEPENDENCY_LABEL_${PARENT_CLEAN}  | sed -r 's/-/_/g;s/.*/\U&/g')
IMAGE_TAG="${!FULL_PARENT}"


function var_dump {
    echo  "--------------------------------------------"
    echo  "CHART_NAME       >>>     ${CHART_NAME}"
    echo  "RELEASE_NAME     >>>     ${RELEASE_NAME}"
    echo  "NAMESPACE        >>>     ${NAMESPACE}"
    echo  "CHART_OVERRIDE   >>>     ${CHART_OVERRIDE}"
    echo  "--------------------------------------------"
    echo  "PARENT_CLEAN   >>>     ${PARENT_CLEAN}"
    echo  "FULL_PARENT   >>>     ${FULL_PARENT}"
    echo  ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
    echo  "IMAGE_TO_DEPLOY   >>>     ${IMAGE_TAG}"
    echo  "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    echo  "--------------------------------------------"
}

function set_context {
    if [[ "$NAMESPACE" != "prod" ]]
    then
        kubectl config set-cluster ${DEV_CLUSTER_NAME} --server=${DEV_KUBERNETES_HOST} --insecure-skip-tls-verify=true
        kubectl config set-credentials ${USER} --token=$(cat ~/.kube_dev_gocd_token)
        kubectl config set-context ${NAMESPACE} --cluster=${DEV_CLUSTER_NAME} --user=${USER} --namespace=kube-system #${NAMESPACE}
        kubectl config use-context ${NAMESPACE}
    else
        kubectl config set-cluster ${PROD_CLUSTER_NAME} --server=${PROD_KUBERNETES_HOST} --insecure-skip-tls-verify=true
        kubectl config set-credentials ${USER} --token=$(cat ${PROD_GOCD_TOKEN_PATH})
        kubectl config set-context ${NAMESPACE} --cluster=${PROD_CLUSTER_NAME} --user=${USER} --namespace=kube-system #${NAMESPACE}
        kubectl config use-context ${NAMESPACE}
    fi
}



function dev_migrate {
    if [[ "$NAMESPACE" != "prod" ]]
    then
        kubectl config set-cluster ${DEV_CLUSTER_NAME} --server=${DEV_KUBERNETES_HOST} --insecure-skip-tls-verify=true
        kubectl config set-credentials ${USER} --token=$(cat ~/.kube_dev_gocd_token)
        kubectl config set-context ${CONTEXT} --cluster=${DEV_CLUSTER_NAME} --user=${USER} --namespace=kube-system #${NAMESPACE}
        kubectl config use-context ${CONTEXT}


        echo "helm ls | grep ${RELEASE_NAME} | wc -l"
        DEPLOYS=$(helm ls --all ${RELEASE_NAME} | grep ${RELEASE_NAME} | grep -v "\-${RELEASE_NAME}" | wc -l)

        if [ ${DEPLOYS}  -eq 0 ]; then
            echo "No existing version of the deployment returned"
            echo "Var dump"
            var_dump
            echo "Attempting deployment with a 15 minutes timeout"
            echo "helm install --wait  --timeout 900 --name=${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG}"
            helm install --wait --timeout 900 --name=${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG} || { echo "helm install failed" ; exit 1; }
        else
            echo "Upgrading version of the deployment"
            echo "Var dump"
            var_dump
            echo "Attempting deployment with a 15 minutes timeout"
            echo "helm upgrade --wait  --timeout 900 ${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG}"
            helm upgrade --wait  --timeout 900 ${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG} || { echo "helm upgrade failed" ; exit 1; }
fi
    fi
}

### START ###
echo "##################################"
echo "###### STARTING HELM DEPLOY ######"
echo "##################################"


#gocd
if [ -z "${AGENT_WORK_DIR}" ]; then
    echo  "--------------------------------------------"
    echo "Failed to get environment variable AGENT_WORK_DIR"
    echo  "--------------------------------------------"
fi

if [ -z "${GO_PIPELINE_NAME}" ]; then
    echo  "--------------------------------------------"
    echo "Failed to get environment variable GO_PIPELINE_LABEL"
    echo  "--------------------------------------------"
fi

if [ -z "${GO_PIPELINE_LABEL}" ]; then
    echo  "--------------------------------------------"
    echo "Failed to get environment variable GO_PIPELINE_LABEL"
    echo  "--------------------------------------------"
fi

# script args
if [ -z "${RELEASE_NAME}" ]; then
    echo  "--------------------------------------------"
    echo "Failed to get environment variable RELEASE_NAME - Please configure it in gocd command arguments"
    echo  "--------------------------------------------"
fi

if [ -z "${NAMESPACE}" ]; then
    echo  "--------------------------------------------"
    echo "Failed to get environment variable NAMESPACE - Please configure it in gocd command arguments"
    echo  "--------------------------------------------"
fi

if [ -z "${CHART_OVERRIDE}" ]; then
    echo  "--------------------------------------------"
    echo "No CHART_OVERRIDE - - Please configure it in gocd command arguments if needed"
    echo  "--------------------------------------------"
fi

# config
set_context

# deploy
cd charts/${NAMESPACE}

echo "helm ls | grep ${RELEASE_NAME} | wc -l"
DEPLOYS=$(helm ls --all ${RELEASE_NAME} | grep ${RELEASE_NAME} | grep -v "\-${RELEASE_NAME}" | wc -l)

STATUS_FAILED=$(helm ls --all ${RELEASE_NAME} | grep ${RELEASE_NAME} | grep -v "\-${RELEASE_NAME}" | grep "FAILED" | wc -l)

if [[ $(echo $STATUS_FAILED | awk '{ print $2 }') == "1" ]];then
    echo "First run failed, resetting helm deployment"
    helm delete  --purge ${RELEASE_NAME}
    DEPLOYS=0
fi


if [ ${DEPLOYS}  -eq 0 ]; then
    echo "No existing version of the deployment returned"
    echo "Var dump"
    var_dump
    echo "Attempting deployment with a 15 minutes timeout"
    echo "helm install --wait  --timeout 900 --name=${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG}"
    helm install --wait --timeout 900 --name=${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG} || { echo "helm install failed" ; exit 1; }
else
    echo "Upgrading version of the deployment"
    echo "Var dump"
    var_dump
    echo "Attempting deployment with a 15 minutes timeout"
    echo "helm upgrade --wait  --timeout 900 ${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG}"
    helm upgrade --wait  --timeout 900 ${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG}

    if [ $? -eq 0 ];then
        echo "Deploy succesful"
    else
        echo "Deploy failed"
        if [[ "$NAMESPACE" != "prod" ]]
        then
            echo "Deploy failed, trying to solve the issue with deployment"
            error_msg=$(helm upgrade --wait  --timeout 900 ${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG}  2>&1)

            if [[ $(echo "$error_msg" | grep "no deployed releases") ]]; then
                echo "No deployed release - purging ${RELEASE_NAME}"
                helm delete --purge ${RELEASE_NAME}
                echo "helm install ${RELEASE_NAME}"
                helm install --wait --timeout 900 --name=${RELEASE_NAME} ${CHART_NAME} --namespace=${NAMESPACE} --set image.tag=${IMAGE_TAG}
                if [ $? -eq 0 ];then
                    echo "Deploy succesful"
                    exit 0
                fi
            else
                echo "Deploy failed, there is most likely an error with the microservice on startup."
                exit 1
            fi
        else
            exit 1
        fi
    fi
fi


# extra deploy for the new kubernetes prod cluster
if [ $UPGRADE_DEV == 1 ]; then
    dev_migrate
fi
# extra deploy for the new kubernetes prod cluster
if [ $UPGRADE_PROD == 1 ]; then
    prod_migrate
fi

echo "##################################"
echo "###### END OF HELM DEPLOY ########"
echo "##################################"
