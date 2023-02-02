#!/bin/bash

echo "sudo ./main $1"
sudo dmesg -C
pushd ../../KeyFinder
make clean && make && sudo ./main $1
popd
dmesg > sample.txt
python3 example.py
