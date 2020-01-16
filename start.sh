#!/usr/bin/bash

screen -S serverFree python3 ./serverFree.py
screen -S serverBasic python3 ./serverBasic.py
screen -S serverPro python3 ./serverPro.py
