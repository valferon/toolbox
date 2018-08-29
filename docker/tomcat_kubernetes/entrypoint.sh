#!/bin/bash

DEFAULT_MEM_JAVA_PERCENT=75

if [ -z "$MEM_JAVA_PERCENT" ]; then
    MEM_JAVA_PERCENT=$DEFAULT_MEM_JAVA_PERCENT
fi

# If MEM_TOTAL_MB is set, the heap is set to a percent of that
# value equal to MEM_JAVA_PERCENT; otherwise it uses the default
# memory settings.
if [ ! -z "$MEM_TOTAL_MB" ]; then
    MEM_JAVA_MB=$(($MEM_TOTAL_MB * $MEM_JAVA_PERCENT / 100))
    MEM_JAVA_ARGS="-Xmx${MEM_JAVA_MB}m"
else
    MEM_JAVA_ARGS="-XX:+UnlockExperimentalVMOptions -XX:+UseCGroupMemoryLimitForHeap"
fi

# Whatever options you need for you service
# > prometheus jmx exporter agent to scrape JVM info
# > HeapDumpOnOutOfMemoryError to get a dump in case of crashes
# > others are personal requirements examples
CATALINA_OPTS="-javaagent:/opt/config/jmx_prometheus_javaagent-0.3.1.jar=9404:/opt/config/config.yaml \
 $MEM_JAVA_ARGS \
 -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/heapdump/ \
 -Dexternal.config=/opt/config/application.properties \
 -Dlogback.configurationFile=file:/opt/config/logback.xml \
 -Dsentry.properties.file=/opt/config/sentry.properties"

echo "CATALINA_OPTS=\"$CATALINA_OPTS\"" > $CATALINA_HOME/bin/setenv.sh
chmod 777 $CATALINA_HOME/bin/setenv.sh

# Once the options are added to catalina setenv.sh
# Run catalina ("/usr/local/tomcat/bin/catalina.sh", "run")
exec "$@"