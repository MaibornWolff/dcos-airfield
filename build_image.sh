#!/bin/bash

DOCKER_REGISTRY=${DOCKER_REGISTRY:-maibornwolff}
DOCKER_TAG=${DOCKER_TAG:-dev}
DOCKER_IMAGE=$DOCKER_REGISTRY/airfield:$DOCKER_TAG

cd airfield-frontend
npm install
npm run build
cd ..
docker build . -t $DOCKER_IMAGE

