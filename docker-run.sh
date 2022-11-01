set -e

#flask will run interactively
#this makes the text output Orange :)
oecho () {
  O='\e[38;5;208m'
  NC='\033[0m'
  echo -e "${O}$1${NC}"
}

#this suppresses a warning about running in developer mode
#export FLASK_ENV=development
export FLASK_DEBUG=1
python /usr/share/pureswagger/server.py &

#delay for a second to make sure it's loaded.
sleep 1
oecho "Open your browser to http://127.0.0.1, use Ctrl+C to end close PureSwagger" 

#sleep forever to make sure Docker container doesn't shutdown
while true; do sleep 1000; done

