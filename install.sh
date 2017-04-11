#!/usr/bin/env bash

env git clone --depth=1 git@github.com:dacapo1142/PTTfeeds.git || {
    printf "\e[31mError: git clone of PTTfeeds repo failed\n\e[0m"
    exit 1
}

env pip install -U -r PTTfeeds/requirements.txt  ||
{
    printf "\e[31mError: pip install requirements.txt repo failed\n\e[0m"
    exit 1
}