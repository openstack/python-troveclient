#!/usr/bin/env bash
# Specify the path to the RDL repo as argument one.
# Argument 2 cna be a log file for the RDL output.
# This script will create a .pid file and report in the current directory.

set -e

me=${0##*/}

function print_usage() {
  cat >&2 <<EOS
Run tests against a local instance of reddwarf

Usage: $me reddwarf_path [logfile]
EOS
}

# parse options
while getopts ":h" opt; do
    case "$opt" in
        h|\?) print_usage; exit 5 ;;
    esac
done
shift $((OPTIND-1))

if [ $# -lt 1 ]; then
    print_usage
    exit 5
fi

reddwarf_path=$1
reddwarf_pid_file="`pwd`.pid"

function start_server() {
    server_log=`pwd`/rdserver.txt
    set +e
    rm $server_log
    set -e
    pushd $reddwarf_path
    bin/start_server.sh --pid-file=$reddwarf_pid_file \
                        --override-logfile=$server_log
    popd
}

function stop_server() {
    if [ -f $reddwarf_pid_file ];
    then
        pushd $reddwarf_path
        bin/stop_server.sh $reddwarf_pid_file
        popd
    else
        echo "The pid file did not exist, so not stopping server."
    fi
}

function on_error() {
    echo "Something went wrong!"
    stop_server
}

trap on_error EXIT  # Proceed to trap - END in event of failure.

start_server
tox -edocs
mkdir -p .tox/docs/html
.tox/docs/bin/sphinx-build -b doctest docs/source .tox/docs/html
.tox/docs/bin/sphinx-build -b html docs/source .tox/docs/html
stop_server


trap - EXIT
echo "Ran tests successfully. :)"
exit 0
