FROM tomcat:latest
MAINTAINER Val Feron

# War file replacement
RUN rm -rf /usr/local/tomcat/webapps/*
COPY app.war /usr/local/tomcat/webapps/ROOT.war
# Unzipping for faster startup time
RUN \
    mkdir /usr/local/tomcat/webapps/ROOT \
    && unzip /usr/local/tomcat/webapps/ROOT.war -d /usr/local/tomcat/webapps/ROOT \
    && rm /usr/local/tomcat/webapps/ROOT.war

# Config files required by the service
VOLUME /opt/config
COPY docker_items/ /opt/config/

# Entrypoint script
COPY entrypoint.sh entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["entrypoint.sh", "/usr/local/tomcat/bin/catalina.sh", "run"]