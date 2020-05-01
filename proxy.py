from socket import *;
from _thread import *;
import sys;
buffer_size=4096;
serverPort = 12000;
block_list=["ust.hk","porn","sexy","activity.windows","beacons"];
def http_proxy(clientSocket,client_address,data):
    while True:
        temp="";
        first_line=data.split("\n")[0];
        url=first_line.split(" ")[1];
        http_pos=url.find("://");
        if (http_pos==-1):
            temp=url;
        else:
            temp=url[http_pos+3:];
        webserver_pos=temp.find("/");
        if (webserver_pos==-1):
            webserver_pos=len(temp);
        webserver=temp[:webserver_pos];
        relative=temp[webserver_pos:];
        port=80;
        data=data.replace(url,relative);
        filename=temp;
        filename=filename.replace("/","_");
        fileExist=False;
        try:
            f = open(filename, "rb")
            outputdata = f.readlines()
            fileExist = True;
            for reply in outputdata:
                clientSocket.send(reply);
            print ("Read from cache");
            f.close();
            data = clientSocket.recv(buffer_size);
            if (len(data)<=0):
                clientSocket.close();
                break;
            data=data.decode("utf-8");
            data=data.replace("Proxy-Connection","Connection");
        except IOError: 
            print("Cache miss",filename);
            if (fileExist == False):
                s = socket(AF_INET, SOCK_STREAM) 
                s.connect((webserver,port));
                s.send(data.encode());
                while True:
                    reply=s.recv(buffer_size);
                    if (len(reply)>0):
                        tmpFile = open(filename,"ab");
                        tmpFile.write(reply);
                        clientSocket.send(reply);
                        tmpFile.close();
                    else:
                        break;
                data= clientSocket.recv(buffer_size);
                if (len(data)<=0):
                    clientSocket.close();
                    s.close();
                    s.close();
                    break;
                data=data.decode("utf-8");
                data=data.replace("Proxy-Connection","Connection");   
def forward_request(clientSocket,s,request,webserver,connectionreset_count_server):
    try:
        s.settimeout(20.0);
        s.send(request);
    except OSError:
        return;
    while True:
        try:
            reply = s.recv(buffer_size);
            if (len(reply) == buffer_size):
                clientSocket.send(reply);
            elif ((len(reply) < buffer_size)and(len(reply)>0)):  
                clientSocket.send(reply);
                break;
            else:
                break;
        except timeout:
            break;
        except ConnectionResetError:
            connectionreset_count_server+=1;
            if (connectionreset_count_server<5):
                continue;
            else:
                break;
        except ConnectionAbortedError:
            break;
        except OSError:
            break;
def https_proxy(clientSocket,client_address,data):
    first_line=data.split("\n")[0];
    url=first_line.split(" ")[1];
    port_pos=url.find(":");
    webserver=url[:port_pos];
    port=url[port_pos+1:];
    s=socket(AF_INET,SOCK_STREAM);
    s.connect((webserver,int(port))); 
    connect_req = 'HTTP/1.1 200 Connection established\r\n\r\n';
    clientSocket.send(connect_req.encode());
    request="";
    connectionreset_count_client=0;
    connectionreset_count_server=0;
    while True:
        try:
            clientSocket.settimeout(20.0);
            request = clientSocket.recv(buffer_size);     
            if (len(request)<=0):
                break;
            else:
                start_new_thread(forward_request,(clientSocket, s,request,webserver,connectionreset_count_server));
        except timeout:
            break;
        except ConnectionResetError:
            connectionreset_count_client+=1;
            if (connectionreset_count_client<5):
                continue;
            else:
                break;
        except ConnectionAbortedError:
            break;
        except OSError:
            break;
    s.close();
    clientSocket.close();
       
def conn_string(clientSocket,client_address):
    data = clientSocket.recv(buffer_size);
    if (len(data)<=0):
        clientSocket.close();
        return;
    data=data.decode("utf-8");
    
    data=data.replace("Proxy-Connection","Connection");
    first_line=data.split("\n")[0];
    url=first_line.split(" ")[1];
    method=first_line.split(" ")[0];
    blocked=False;
    for i in range(0, len(block_list)):
        if block_list[i] in url:
            error_message=""
            error_message+="HTTP/1.1 404 Not Found\r\n";
            error_message+="Content-Type: text/html\r\n\r\n";
            error_message+="<html><head></head><body><h1>404 Not Found</h1></body></html>";
            clientSocket.send(error_message.encode());
            blocked=True;
            break;
    if (blocked==False):      
        if (method=="GET"):
            http_proxy(clientSocket,client_address,data);
        elif (method=="CONNECT"):
            https_proxy(clientSocket,client_address,data);
    else:
        clientSocket.close();
        
try:
    serverSocket = socket(AF_INET,SOCK_STREAM);
    serverSocket.bind(("",serverPort));
    serverSocket.listen(5);
except Exception:
    print("Unable to initialize socket");
    sys.exit(2);
print ("The server is ready to receive");
while True:
    try:
        (clientSocket, client_address) = serverSocket.accept();
        start_new_thread(conn_string,(clientSocket, client_address));
    except KeyboardInterrupt:
        serverSocket.close();
        print("Socket is shutting down");
        sys.exit(1);
serverSocket.close();

