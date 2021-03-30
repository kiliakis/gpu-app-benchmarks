#!/bin/bash

string="$1"
shift
grep $string --color -riInH "$@"
