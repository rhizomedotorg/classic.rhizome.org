#!/bin/sh
cd ~/src/apache-solr-1.4.1/example/

# Run the example Solr+Jetty implementation
nohup java -jar start.jar >logfile 2>&1 &

# Write the process ID into the file "pid"
echo $! > pid

echo "Done; running under process ID $!";
exit