#!/bin/bash

curl -X POST -H "Content-Type: application/json" -d '{"f": ["bat", "sleep", "temp"], "b": 3.9, "t": [["s1", 24.125], ["s2", 23.5]]}' http://localhost:8081/
curl -X POST -H "Content-Type: application/json" -d '{"c": [["s1", 0], ["s2", 0]], "p": 11}' http://localhost:8081/


curl -X POST -H "Content-Type: application/json" -d '{"b": 3.6797, "t": [["s1", 24.125], ["s2", 23.5]], "y": ["c"]}' http://localhost:8081/
