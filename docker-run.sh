set -e

#flask will run interactively
oecho () {
  O='\e[38;5;208m'
  NC='\033[0m'
  echo -e "${O}$1${NC}"
}


python /usr/share/pureswagger/server.py &
sleep 1
oecho "Open your browser to http://127.0.0.1, use Ctrl+C to end close PureSwagger" 

while true; do sleep 1000; done

