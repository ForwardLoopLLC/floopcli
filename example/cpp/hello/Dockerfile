FROM library/debian:jessie
RUN apt-get update && apt-get install -y g++
# by default, target source code will be at /floop/ 
# on the target device test environment
CMD ["bash", "-c", "/floop/run.sh"]
