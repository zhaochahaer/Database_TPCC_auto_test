#!/bin/bash

# 1.remove foreign key,the performance will increase 20%
sed -i "s/AFTER_LOAD=\"indexCreates foreignKeys extraHistID buildFinish\"/AFTER_LOAD=\"indexCreates extraHistID buildFinish\"/g" ./run/runDatabaseBuild.sh
