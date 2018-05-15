# Pure FA Swagger Generator

This is a tool that converts the Pure FlashArray API pdf documentation into an interactive Swagger UI.  This lets you browse the API documentation in a convienent format and even execute API calls interactively directly to a FlashArray!


## Try It: 
Requires [docker](https://docs.docker.com/install/) to be installed

> docker run -it --rm -p 80:5000 sile16/pureswagger 

Then open your browser to http://127.0.0.1 (use firefox to enable real time API calls!)
Then load a [FlashArray REST pdf from Pure Support](https://support.purestorage.com/FlashArray/PurityFA/Purity_FA_REST_API/Reference/REST_API_PDF_Reference_Guides)

That's it!

## To stop run:
just ctrl^c on the console docker container 


## Screenshots

### Documentation in collapsable easy to read format
![docs](https://raw.githubusercontent.com/sile16/pureswagger/master/images/docs.png)

### See detailed paramater information
![array_details](https://raw.githubusercontent.com/sile16/pureswagger/master/images/array_details.png)

### See body param documentation
![array_details](https://raw.githubusercontent.com/sile16/pureswagger/master/images/body_params.png)

### Every Endpoint is documented !
![array_details](https://raw.githubusercontent.com/sile16/pureswagger/master/images/list_of_endpoints.png)

### Actually send API commands to an Array:
![array_details](https://raw.githubusercontent.com/sile16/pureswagger/master/images/list_api.png)

### Start a session:
![array_details](https://raw.githubusercontent.com/sile16/pureswagger/master/images/start_session.png)

### Get Controller Info:
![array_details](https://raw.githubusercontent.com/sile16/pureswagger/master/images/get_controllers.png)

## Notes:

In order to send API calls to an array you must 
1.  Have a FlashArray





