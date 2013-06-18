#!/usr/bin/env bash
# Specify the path to the RDL repo as argument one.
# Argument 2 cna be a log file for the RDL output.
# This script will create a .pid file and report in the current directory.

set -e

me=${0##*/}

function print_usage() {
  cat >&2 <<EOS
Run tests against a local instance of trove

Usage: $me trove_path [logfile]
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

trove_path=$1
trove_pid_file="`pwd`.pid"

function start_server() {
    server_log=`pwd`/rdserver.txt
    set +e
    rm $server_log
    set -e
    pushd $trove_path
    bin/start_server.sh --pid-file=$trove_pid_file \
                        --override-logfile=$server_log
    popd
}

function stop_server() {
    if [ -f $trove_pid_file ];
    then
        pushd $trove_path
        bin/stop_server.sh $trove_pid_file
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
