#! /bin/bash

python main.py outage 100 > out100.csv

python main.py failure 1 < out100.csv > fail1.csv


python main.py failure 5 < out100.csv > fail5.csv


python main.py failure 10 < out100.csv > fail10.csv


python main.py failure 50 < out100.csv > fail50.csv


python main.py failure 100 < out100.csv > fail100.csv


python main.py failure 500 < out100.csv > fail500.csv


python main.py failure 1000 < out100.csv > fail1000.csv


python main.py failure 5000 < out100.csv > fail5000.csv


python main.py failure 10000 < out100.csv > fail10000.csv


python main.py failure 50000 < out100.csv > fail50000.csv


python main.py failure 100000 < out100.csv > fail100000.csv

