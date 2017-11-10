#!/bin/bash -l

checkDB () {
  # Check if the DB is live
  psql -d "$CKAN_SQLALCHEMY_URL"
}

checkDB

while [ $? -gt 0 ]; do
  echo 'DB not ready waiting 10 seconds'
	sleep 10
	checkDB
done