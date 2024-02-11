import socket
import threading

class FS_Tracker:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nodes = {}

    # adiciona node à base de dados
    def add_node(self, node, files):
        self.nodes[node] = files

    # remove um node da base de dados
    def remove_node(self, node):
        del self.nodes[node]

    # dá handle as mensagens trocadas com os clientes
    def handle_message_tcp(self, client_socket, client_adress):

        if not isinstance(client_socket, socket.socket):
            print("Erro: O objeto não é um socket.")
            return
        
        buffer = ""
        while True:
            try:
                chunk = client_socket.recv(1024).decode('utf-8')
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
                    # se recebe um get_response deve ver que nodes possuem tal ficheiro
                    if message.startswith("get_response "):
                        _, file_name, ip_destination = message.split(" ", 2)
                        print(ip_destination + " requisitou " + file_name)
                        matching_nodes = self.get_nodes_with_file(file_name)
                        print(file_name + " está presente em: " + matching_nodes )
                        response = "matching_nodes " + file_name + " " + matching_nodes + "|"
                        client_socket.send(response.encode('utf-8'))
                    # se recebe um connection from deve dar add de node à base de dados
                    elif message.startswith("Connection_from "):
                        tokens = message.split(" ")
                        ip = tokens[1]
                        files = tokens[3].split(";")
                        self.add_node(ip,files)
                        print(f"Connection from {ip} with files: {files}")
                    # se recebe um file_received deve atualizar a base de dados relativa a esse node e deve enviar um atual_file para o node saber que essa informação foi recebida 
                    elif message.startswith("file_received "):
                        tokens = message.split(" ")
                        ip = tokens[1]
                        file_name = tokens[2]
                        self.nodes[ip].append(file_name)
                        # mandar mensagem ao node para ele dar print aos seus novos files
                        files_str = ""
                        for file in self.nodes[ip]:
                            files_str += file + ";"
                        response = "atual_file " + files_str[:-1] + "|"
                        client_socket.send(response.encode('utf-8'))
                buffer = ""
          
    def start(self):
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        print(f"Servidor ativo em {self.ip} porta {self.port}.")
        
        while True:
            client_socket, client_address = self.server_socket.accept()
            # cria uma thread para cada cliente
            client_handler_thread = threading.Thread(target=self.handle_message_tcp, args=(client_socket, client_address))
            client_handler_thread.start()

    ## retorna os ip's dos nodes que possuem certo ficheiro
    def get_nodes_with_file(self, file_name):
        matching_nodes = ""
        for ip, files in self.nodes.items():
            for file in files:
                if file == file_name:
                    matching_nodes += ip + ";"
                    break
        return matching_nodes[:-1]

if __name__ == "__main__":
    server = FS_Tracker('10.4.4.1', 9090)
    server.start()

    ########### COMANDS ###########
    ##
    ## TRACKER: python3 ../../../home/core/Desktop/CC_TP/FS_Tracker.py
    ##
    ## NODE(mudar dependente do ip e dos files que queremos fazer):
    ## mkdir node_files && mkdir node_fragments && echo "ajjauhhdidi" > node_files/file1 && python3 ../../../home/core/Desktop/CC_TP/FS_Node.py node_files 10.1.1.1 9090 