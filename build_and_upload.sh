#!/bin/bash

set -e

zip -r build.zip drink_tracker.py venv/lib/python3.9/site-packages

aws lambda update-function-code --function-name drink-tracker --zip-file fileb://./build.zip

rm -f build.zip