#!/usr/bin/env bash

TARGET_NUM_REVISIONS=10
TARGET_NUM_REVISIONS=$(($TARGET_NUM_REVISIONS+0))

RELEASES=$(kubectl --namespace=kube-system get cm -l OWNER=TILLER -o go-template --template='{{range .items}}{{ .metadata.labels.NAME }}{{"\n"}}{{ end }}' | sort -u)

# create the directory to store backups
mkdir configmaps

for RELEASE in $RELEASES
do
  # get the revisions of this release
  REVISIONS=$(kubectl --namespace=kube-system get cm -l OWNER=TILLER -l NAME=$RELEASE | awk '{if(NR>1)print $1}' | sed 's/.*\.v//' | sort -n)
  NUM_REVISIONS=$(echo $REVISIONS | tr " " "\n" | wc -l)
  NUM_REVISIONS=$(($NUM_REVISIONS+0))

  echo "Release $RELEASE has $NUM_REVISIONS revisions. Target is $TARGET_NUM_REVISIONS."
  if [[ $NUM_REVISIONS -gt $TARGET_NUM_REVISIONS ]]; then
    NUM_TO_DELETE=$(($NUM_REVISIONS-$TARGET_NUM_REVISIONS))
    echo "Will delete $NUM_TO_DELETE revisions"

    TO_DELETE=$(echo $REVISIONS | tr " " "\n" | head -n $NUM_TO_DELETE)

    for DELETE_REVISION in $TO_DELETE
    do
      CMNAME=$RELEASE.v$DELETE_REVISION
      echo "Deleting $CMNAME"
      # Take a backup
      kubectl --namespace=kube-system get cm $CMNAME -o yaml > configmaps/$CMNAME.yaml
      # Do the delete
      kubectl --namespace=kube-system delete cm $CMNAME
    done
  fi
done