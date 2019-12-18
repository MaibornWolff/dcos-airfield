#!/bin/bash

DOCKER_REGISTRY=${DOCKER_REGISTRY:-maibornwolff}
DOCKER_TAG=${DOCKER_TAG:-dev}
DOCKER_IMAGE=$DOCKER_REGISTRY/airfield:$DOCKER_TAG

if [ -z $NO_BUILD_FRONTEND ]; then
	cd frontend
	npm install
	npm run build
	cd ..
fi
docker build . -t $DOCKER_IMAGE

