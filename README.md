#### **HTTP WEB SERVER**
This is the simple web server coded in Python 3.8.

#### **How to use**
You can import this project as a library. 
This toolkit allows you to carry out simple work with a web server.
You can view directory listings, images, multimedia files, send HTTP requests 
to the server, create your own templates, and so on.

#### **Simple start**
The following is an example of using this project as a library.

_import os_  
_from web import Webserver_

_app = Webserver(host='localhost', port=8080)_

_@app.route('/')_  
_def my_func():_  
_return app.handle_dir(os.getcwd())_

_app.run()_

This example illustrates the listing of the current directory.

#### **Webserver**
_Webserver(host, port, hostname, workers)_  

Before you begin, you can set the following settings:  
`host` - host (default: 127.0.0.1)  
`port` - port, use port 80 for HTTP protocol (default: 8080)  
`hostname` - special name for the host (default: _hostname_)  
`workers` - number of worker threads during work (default: number of cores - 1)  

This class includes basic methods for working:  
`run` - start work  
`route` - decorator that configures routing.  
`get` - method for get request  
`post` - method for post request  
`handle_file` - method for returning a file from the server  
`handle_dir` - method for listing directory

##### **Route**
_app = Webserver()_
  
_@app.route(path)_  
_def func(...):_  
_....return app.method(...)_  

_app.run()_
  

Use `route` to create routes for your sever

##### **Handle_file**
_app = Webserver()_  
_@app.route(path)_  
_def func():_  
_....return app.handle_file(file, root, content-type)_  

_app.run()_

Use `handle_file` to receive files from the server

##### **Handle_dir**
_app = Webserver()_  
_@app.route(path)_  
_def func():_  
_....return app.handle_dir(dirname)_  

_app.run()_

Use `handle_dir` to create listing of choosen directory

##### **HTTP methods**
_app = Webserver()_  
_@app.route(path)_  
_def func():_  
_....return app.get(body, headers, params)_  

_app.run()_  

Use `get` or `post` to create requests to the web server

##### **Simple template**
_app = Webserver()_  
_@app.route(/hello/(?P\<name>.*))_  
_def func(name):_  
_....return app.get(f'Hello, {name}')_  

_app.run()_  

After going to address http://127.0.0.1:8080/hello/World   
You will see a well-known message: "Hello, world"

#### **Addition**
1. You can also start the server in the main project.  
To do this, write the code after the if \_\_name__ == "\_\_main__" construct

2. There is a folder of files. There you can test the library