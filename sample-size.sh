#!/bin/bash

python main.py clean
python main.py outage 100 > out100.csv

for i in 1 5 10 50 100 500 1000 5000 10000 50000 100000
do
    echo "Process $i"
    python main.py failure $i < out100.csv > fail$i.csv
    python main.py simulate < fail$i.csv > sim$i.csv
    python main.py analyse < sim$i.csv > analysis$i.csv
done

echo "All Finished"
exit 0
