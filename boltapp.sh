#/bin/bash


# On BOLT V2 device: /data/data/com.wahoofitness.bolt/databases/BoltApp.sqlite
# Table: CloudPoiDao


sqlite3 -column -header BoltApp.sqlite "PRAGMA table_info(CloudPoiDao);"

echo
echo

sqlite3 -column -header BoltApp.sqlite "SELECT sql FROM sqlite_master WHERE type='table' AND name='CloudPoiDao';"

echo
echo

sqlite3 -column -header BoltApp.sqlite "SELECT *, HEX(custom) FROM CloudPoiDao;"



