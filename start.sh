#!bin/bash

git pull

if [ ! -f ./aternos/tmp/test-user-data-dir ]; then
    rm -r aternos/tmp/test-user-data-dir
fi

pipenv run python3 main.py 2>&1 | tee log.txt
