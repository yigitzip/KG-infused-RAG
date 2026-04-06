#!/usr/bin/env bash
# Neo4j 5+ örnek: instance STOP iken neo4j-admin
# JAVA_HOME: Java 21 (Neo4j 2026.x)
set -euo pipefail
echo "Örnek (yolları kendinize göre düzenleyin):"
echo './bin/neo4j-admin database import full neo4j \'
echo '  --overwrite-destination=true --multiline-fields=true \'
echo '  --nodes=Entity="$HOME/Desktop/neo4j_import_turkey_project/entities.csv" \'
echo '  --relationships="$HOME/Desktop/neo4j_import_turkey_project/relationships.csv"'
