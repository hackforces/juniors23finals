#!/bin/sh
gcc -fno-stack-protector -fno-pie -no-pie -z execstack -o /companion_app main.c -lz -static
