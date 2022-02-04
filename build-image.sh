#!/bin/bash

set -e

docker build --tag iit-thesis --label iit-thesis-build .

docker image prune -f --filter="label=iit-thesis-build"
