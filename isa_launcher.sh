#!/bin/bash

dirname=$(dirname "$0")

source $dirname/.venv/bin/activate
streamlit run $dirname/app.py

$SHELL