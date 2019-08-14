#!/bin/bash
date=$(date +%s)
tmpfile=$(mktemp /tmp/test-manpage-$date.1)
manpage=$PWD/qpc.1
cd ../; make manpage MANPAGE_OUTPUT=$tmpfile

DIFF=$(diff $tmpfile $manpage)
CMP=$(cmp $tmpfile $manpage)

if [ "$DIFF" != "" ]
then
  echo "Make manpage was not run."
  echo "$DIFF"
  exit 1
fi

if [ "$CMP" != "" ]
then
  echo "`make manpage` was not run."
  echo "$CMP"
  exit 1
fi
echo "Successful Test"