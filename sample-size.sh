#! /bin/bash

python2 main.py outage 100 > out100.csv

python2 main.py failure 10 < out100.csv | python2 main.py simulate > fail10.csv
python2 main.py analyse < fail10.csv > analysis10.csv

python2 main.py failure 100 < out100.csv | python2 main.py simulate > fail100.csv
python2 main.py analyse < fail100.csv > analysis100.csv

python2 main.py failure 1000 < out100.csv | python2 main.py simulate > fail1000.csv
python2 main.py analyse < fail1000.csv > analysis1000.csv

python2 main.py failure 10000 < out100.csv | python2 main.py simulate > fail10000.csv
python2 main.py analyse < fail10000.csv > analysis10000.csv

python2 main.py failure 100000 < out100.csv | python2 main.py simulate > fail100000.csv
python2 main.py analyse < fail100000.csv > analysis100000.csv
