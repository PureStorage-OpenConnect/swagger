# Pure Swagger

This is a tool that provides the Pure Storage FlashArray and FlashBlade API documentation into the popular interactive Swagger UI.  This lets you browse the API documentation in a convenient format and even execute API calls interactively directly to a FlashArray or FlashBlade!


## Try It: 
Requires [docker](https://docs.docker.com/install/) to be installed

> docker run -it --rm -p 80:5000 sile16/pureswagger 

Then open your browser to http://127.0.0.1
Then select an API spec and enter your FlashArray or FlashBlade IP
That's it!

## To stop run:
just ctrl^c on the console docker container 

## Update to the latest version

> docker pull sile16/pureswagger


## Screenshots

### Documentation in collapsable easy to read format
![docs](https://raw.githubusercontent.com/PureStorage-OpenConnect/swagger/master/images/docs.png)

### See detailed paramater information
![array_details](https://raw.githubusercontent.com/PureStorage-OpenConnect/swagger/master/images/array_details.png)

### See body param documentation
![array_details](https://raw.githubusercontent.com/PureStorage-OpenConnect/swagger/master/images/body_params.png)

### Every Endpoint is documented !
![array_details](https://raw.githubusercontent.com/PureStorage-OpenConnect/swagger/master/images/list_of_endpoints.png)

### Actually send API commands to an Array:
![array_details](https://raw.githubusercontent.com/PureStorage-OpenConnect/swagger/master/images/list_api.png)

### Start a session:
![array_details](https://raw.githubusercontent.com/PureStorage-OpenConnect/swagger/master/images/start_session.png)

### Get Controller Info:
![array_details](https://raw.githubusercontent.com/PureStorage-OpenConnect/swagger/master/images/get_controllers.png)

## Notes:

In order to send API calls to an array you must 
1.  Have a FlashArray or FlashBlade

