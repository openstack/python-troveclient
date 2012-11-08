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

# the funmaker
function start_server() {
    pushd $reddwarf_path
    bin/start_server.sh --pid_file=$reddwarf_pid_file
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
tox
stop_server


trap - EXIT
echo "Ran tests successfully. :)"
exit 0
