import socket, sys
import time
from thread import *

maxConnection = 5
bufferSize = 8192
listeningPort = 8080
userAgent = "CN Proxy Server (v1.0.0)"
clients = {}
volum = int("80000000")
blockedTargets = ["sib.ir"]
slowedTargets = {"acm.ut.ac.ir": 1000}
logName = "proxy.log"

def makeDict(message):

	currentChar = ""
	resultDict = {}
	phrase = ""
	definition = ""

	while (message) and (message[0] != "\r" ):
		phrase = ""
		definition = ""
		while currentChar != " ":
			currentChar = message[0]
			message = message[1:]
			phrase += currentChar
		while  currentChar != "\n":
			if not message:
				break
			currentChar = message[0]
			message = message[1:]
			definition += currentChar
		resultDict[phrase[:len(phrase) - 1]] = definition[:-2]
	return resultDict

def addPrivacy(content, mHeaders):
	editedContent = ""
	editedContent += ("GET " + mHeaders['GET'][:-1] + "0\r\n")
	editedContent += ("Host: " + mHeaders['Host:'] + "\r\n")
	editedContent += ("User-Agent: " + userAgent + "\r\n")
	editedContent += ("Connection: Close\r\n")
	for x in mHeaders.keys():
		if(x != "GET" and x != "Host:" and x != "User-Agent:" and x != "Connection:"):
			editedContent += (x + ' ' + mHeaders[x] + "\r\n")
	endHeader = content.find("\r\n\r\n")
	editedContent += (content[(endHeader+2):])
	return editedContent

def start():
	i = 1
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(('', listeningPort))
		s.listen(maxConnection)
	except KeyboardInterrupt:
		s.close()
		print("server closed")
		sys.exit(1)
	except Exception, e:
		s.close()
		print "[*] Unable to initialize socket"
		sys.exit(2)

	while 1:
		try:
			connection, address = s.accept()
			content = connection.recv(bufferSize)
			start_new_thread(handleConnection, (i, connection, content, address))
			i = i + 1
		except KeyboardInterrupt:
			s.close()
			print("[*] Proxy server shutting down")
			sys.exit(1)
	s.close()

def handleConnection(i, connection, content, address):
	try:
		splitedContent = content.split('\n')
		firstLine = splitedContent[0]
		url = firstLine.split(' ')[1]
		httpPosition = url.find("://")

		if (httpPosition == -1):
			temp = url
		else:
			temp = url[(httpPosition+3):]

		portPosition = temp.find(":")

		webServerPosition = temp.find("/")
		if webServerPosition == -1:
			webServerPosition = len(temp)
		webServer = ""
		port = -1
		if (portPosition == -1 or webServerPosition < portPosition):
			port = 80
			webServer = temp[:webServerPosition]
		else:
			port = int((temp[portPosition + 1:])[:webServerPosition - portPosition -1])
			webServer = temp[:portPosition]

		#restrictions
		if webServer in blockedTargets:
			print("blocked")
			raise ConnectionAbortedError
		if webServer in slowedTargets.keys():
			print("slow start")
			time.sleep(slowedTargets[webServer] / 1000)
		else:
			print("no restrictions")
		#

		#caching
		f = open("cache/creq" + str(i) + ".txt","w+")
		f.write(content)
		f.close()
		#

		#accounting
		if port in clients:
			if clients[port] - len(content) > 0:
				proxyServer(i, webServer, port, connection, content, address)
				clients[port] -= len(content)
				print("trafic of " + str(port) + " is " + str(clients[port]))
			else:
				print("your trafic is accumulated")
				raise ConnectionAbortedError
		else:
			clients[port] = volum
			print("trafic of " + str(port) + " is " + str(clients[port]))
			proxyServer(i, webServer, port, connection, content, address)
		#

	except Exception, e:
		pass

def proxyServer(i, webServer, port, connection, content, address):
	print("Enter ProxyServer")
	try:
		mHeaders = makeDict(content)
		editedContent = addPrivacy(content, mHeaders)

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((webServer, port))
		s.send(editedContent)

		while 1:
			response = s.recv(bufferSize)

			#caching
			f = open("cache/cres" + str(i) + ".txt","w+")
			f.write(response)
			f.close()
			#

			if (len(response) > 0):
				print("entered if")
				connection.send(response)
				temp = float(len(response))
				temp = float(temp / 1024)
				temp = "%.3s" % (str(temp))
				temp = "%s KB" % (temp)
				print("Request done: %s => %s <=" % (str(address[0]), str(temp)))
			else:
				break

		print("exiting thread")
		s.close()
		connection.close()
	except socket.error, (value, message):
		print("error message:")
		print(message)
		s.close()
		connection.close()
		print("[*] Socket error")
		sys.exit(1)
	except KeyboardInterrupt:
		s.close()
		connection.close()
		print("[*] Proxy server shutting down")
		sys.exit(1)

start()
