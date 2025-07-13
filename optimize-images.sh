#!/usr/bin/env sh

for file in $(find ./ -type f -name '*.png')
do
    oxipng -o 6 -i 1 --strip safe "$file" --fix
done

