import socket
import os
import time
import threading
import sys

class FS_Node:
    def __init__(self, server_ip, server_port, udp_port, directory_path):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket tcp
        self.directory_path = directory_path
        self.udp_port = udp_port
        self.udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # socket udp
        self.nodes_response_time = {}
        self.node_ip = ip_address
        self.udp_server_socket.bind((self.node_ip, 9090)) ## bind do socket
        self.files_content = {} ## dicionário utilizado para atribuir a cada file_name um tuplo (nr_fragment,content_of_fragment)

    # faz a conexão entre o node e o tracker
    def connect_to_tracker(self, tracker_ip, tracker_port):
        self.client_socket.connect((tracker_ip, tracker_port))
        self.send_node_info()

    # envia a informação do node
    def send_node_info(self):
        available_files = self.get_available_documents()
        files_str = ""
        for file in available_files:
            files_str += file + ";"
        message = "Connection_from " + self.node_ip + " with_files " + files_str[:-1] + "|"
        self.client_socket.send(message.encode('utf-8'))

    # envia uma mensagem via tcp para o tracker
    def send_message(self, message):
        self.client_socket.send(message.encode('utf-8'))

    # fecha a conexão entre o node e o tracker       
    def close_connection(self):
        self.client_socket.close()

    # retorna os files que um node possui
    def get_available_documents(self):
        try:
            if os.path.exists(self.directory_path) and os.path.isdir(self.directory_path):
                documents = [file for file in os.listdir(self.directory_path) if os.path.isfile(os.path.join(self.directory_path, file))]
                return documents
            else:
                return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    # handle dos comandos efetuados no terminal do node
    def handle_command(self, command):
        if command.lower() == "exit":
            print("Stopping the node as per the received command.")
            self.close_connection()
        
        elif command.lower().startswith("get "):
            file_name = command[4:] 
            print(f"Requested file: {file_name}")
            self.send_message("get_response " + file_name + " " + ip_address + "|")

    # retorna o content de um file 
    def file_content(self,file):
        try:
            with open(file, 'r') as file:
                content = file.read()
                return content
        except FileNotFoundError:
            print(f"Ficheiro não encontrado: {file}")
        except Exception as e:
            print(f"Ocorreu um erro ao ler o ficheiro: {e}")

    # cria um ficheiro file com o conteúdo content
    def create_file(self, file, content):
        try:
            # abre o ficheiro em modo de escrita
            with open(file, 'w') as ficheiro:
                # escreve o conteúdo no ficheiro
                ficheiro.write(content)
            print(f"Ficheiro '{file}' criado com sucesso.")
        except Exception as e:
            print(f"Ocorreu um erro ao criar o ficheiro: {e}")

    # dá handle as mensagens tcp recebidas do tracker
    def handle_tcp_message(self):
        print("Conexão FS Track Protocol com servidor 10.4.4.1 porta 9090.")
        buffer = ""
        while True:
            chunk = self.client_socket.recv(1024).decode('utf-8')
            buffer += chunk

            if '|' in buffer:
                messages = buffer.split("|")
                for message in messages:
                    if message.startswith("matching_nodes "):
                        _, file_name, nodes_aux = message.split(" ", 2)
                        nodes = nodes_aux.split(";")
                        ## ver se o node ja tem o file
                        e = 0
                        for node in nodes:
                            if str(node) == str(ip_address):
                                e = 1
                                print("This Node already have the requested File")
                        if e == 0:
                            print("Nodes with the File: " + nodes_aux)
                            # se a lista só tiver um elemento então esse é o fastest node
                            if len(nodes) == 1: 
                                fastest_node = nodes[0]
                            else:
                            # usar metodo para ver qual o node mais rapido
                                fastest_node = self.fastest_node(nodes)
                            print("The Fastest Node to Receive the File is: " + fastest_node)
                            # usar metodo para receber o file do node mais rapido 
                            message = "file_request " + file_name + " " + ip_address + "|"
                            self.udp_server_socket.sendto(message.encode('utf-8'), (fastest_node, 9090))

                    # response = "atual_file " + self.nodes[ip] + "|" 
                    if message.lower().startswith("atual_file "):
                        tokens = message.split(" ")
                        files = tokens[1]
                        print("My Available Files Rigth Now Are: " + files)
                buffer = ""

    # dá handle as mensagens udp recebidas provenientes de outros nodes
    def handle_udp_message(self): 
        print("FS Transfer Protocol: à escuta na porta UDP 9090.")
        buffer = ""
        while True:
            try:
                chunk = self.udp_server_socket.recv(1024).decode('utf-8')
            except OSError as e:
                print(f"Erro no socket: {e}")
                break

            if not chunk:
                print("Conexão fechada pelo cliente.")
                break

            buffer += chunk
            
            if '|' in buffer:
                messages = buffer.split("|")
                for message in messages:
                    # quando recebe um ping deve mandar um ping_response com o tempo que recebeu no ping
                    if message.lower().startswith("ping "):
                        self.send_message("ping_response " + message[4:] + " " + self.node_ip + "|")
                    # quando recebe um ping_response deve calcular o tempo de resposta com base no tempo inicial
                    elif message.lower().startswith("ping_response "):
                        tokens = message.split(" ")
                        time_now = time.time()
                        start_time = float(tokens[1])
                        node_ip = tokens[2]
                        response_time = time_now - start_time
                        self.nodes_response_time[node_ip] = response_time
                    # quando recebe um file_request deve calcular quantos fragmentos são necessários para a tranferência desse ficheiro
                    # e enviar um fille_chunk_sent e no final um file_complete_check
                    elif message.lower().startswith("file_request "):
                        tokens = message.split(" ")
                        file_name = tokens[1]
                        ip_address_dest = tokens[2]
                        print(file_name + " requested from " + ip_address_dest)
                        content = self.file_content("node_files/" + file_name) 
                        #message = "file_sent " + file_name + " " + ip_address + " " + content + "|"
                        content_size = len(content) - 1
                        # TAMANHO DE CADA FRAGMENTO => 5 CHAR
                        if content_size % 5 == 0:
                            nr_fragments = content_size // 5
                        else: 
                            nr_fragments = (content_size // 5) + 1
                        for i in range (1, nr_fragments):
                            chunk_content = content[(i-1)*5:i*5]
                            message = "file_chunk_sent " + file_name + " " + ip_address + " " + chunk_content +  " " + str(i) + " " + str(nr_fragments) + "|"   
                            self.udp_server_socket.sendto(message.encode('utf-8'), (ip_address_dest, 9090))
                        chunk_content = content[(nr_fragments-1)*5:]
                        message = "file_chunk_sent " + file_name + " " + ip_address + " " + chunk_content +  " " + str(nr_fragments) + " " + str(nr_fragments) + "|"   
                        self.udp_server_socket.sendto(message.encode('utf-8'), (ip_address_dest, 9090))
                        message = "file_complete_check " + file_name + " " + str(nr_fragments) + "|"   
                        self.udp_server_socket.sendto(message.encode('utf-8'), (ip_address_dest, 9090))
                        print(file_name + " sent to " + ip_address_dest )  
                    # quando recebe um file_chunk_sent deve guardar a informação que recebeu certo fragmento de certo ficheiro no dicionário 
                    elif message.lower().startswith("file_chunk_sent "): 
                        tokens = message.split(" ")
                        file_name = tokens[1]
                        ip = tokens[2]
                        chunk_content = tokens[3]
                        i = tokens[4]
                        nr_fragments = tokens[5]                        
                        print(file_name + " chunk " + i + " of " + nr_fragments + " received from " + ip + " with content: " + chunk_content)
                        if file_name not in self.files_content:
                            self.files_content[file_name] = [(int(i), chunk_content)]
                        else:
                            if int(i) not in [tupla[0] for tupla in self.files_content[file_name]]:
                                self.files_content[file_name].append((int(i), chunk_content)) 
                    # quando recebe um file_complete_check deve ver se todos os fragmentos já foram recebidos e se já foram deve criar o ficheiro e os fragmentos
                    elif message.lower().startswith("file_complete_check "): 
                        tokens = message.split(" ")
                        file_name = tokens[1]
                        nr_fragments = int(tokens[2])
                        content = ""
                        if len(self.files_content[file_name]) == nr_fragments:
                            # lista ordenada de forma a que o i menor apareça primeiro
                            lista_ordenada = sorted(self.files_content[file_name],
                                                     key=lambda tuple: tuple[0])
                            for i, c in lista_ordenada:
                                self.create_file("node_fragments/" + file_name + "." + str(i), c)
                                content += c
                            self.create_file("node_files/" + file_name, content)
                            # comunicar ao servidor que recebeu o ficheiro
                            message = "file_received " + self.node_ip + " " + file_name +  "|"
                            self.client_socket.send(message.encode('utf-8'))
                buffer = ""
    
    # envia um ping a um node 
    def ping_node(self, ip):
        start_time = time.time()
        message = "ping " + str(start_time) + "|"
        self.udp_server_socket.sendto(message.encode('utf-8'), (ip, 9090))

    # calcula o node mais rápido para recever ficheiro
    def fastest_node(self, matching_nodes_ip):
        fastest_node = matching_nodes_ip[0]
        fastest_time = float('inf')  # inicializa com infinito
        for ip in matching_nodes_ip:
            self.ping_node(ip)
        time.sleep(1)
        for node_ip, response_time in self.nodes_response_time.items(): 
            if response_time < fastest_time:
                    fastest_time = response_time
                    fastest_node = node_ip
            del self.nodes_response_time[node_ip]
        return fastest_node   
   
if __name__ == "__main__":
    tracker_ip = '10.4.4.1'
    tracker_port = 9090

    ## obtém os argumentos da linha de comando
    folder = sys.argv[1]
    ip_address = sys.argv[2]
    port = sys.argv[3]
    print(f"Ficheiros em: {folder}")
    print(f"Endereço IP: {ip_address}")
    print(f"Porta: {port}")

    directory_path = folder
    udp_port = int(port)
    node = FS_Node(tracker_ip, tracker_port, udp_port, directory_path)
    node.connect_to_tracker(tracker_ip,tracker_port)
    ## criação de thread para dar handle a mensagens tcp
    tcp_thread = threading.Thread(target=node.handle_tcp_message, args=()) 
    tcp_thread.start()
    ## criação de thread para dar handle a mensagens udp
    udp_thread = threading.Thread(target=node.handle_udp_message, args=()) 
    udp_thread.start()
    ## obter os ficheiros que o node possui
    available_files = node.get_available_documents()
    print("My Available Files Right Now Are: " + str(available_files))
    c = True
    while c == True:
        user_input = input("Enter a command: ")
        node.handle_command(user_input)
        ## time sleep para não aparecer o "enter a comand" enquanto o comand anterior não tiver acabado
        time.sleep(3)
    node.close_connection()