#!/bin/bash

curl -X POST -H "Content-Type: application/json" -d '{"v": [["all", 1.02], ["os", 1], ["sleep", 1.01], ["bat", 1], ["signal", 1], ["temp", 1], ["latch", 1], ["humid", 1]]}' http://localhost:8081/
curl -X POST -H "Content-Type: application/json" -d '{"b": 3.9, "s": 2, "t": [["s1", 24.125], ["s2", 23.5]], "l": [0, 1], "h": [["h1", 50], ["h2", 55]]}' http://localhost:8081/
