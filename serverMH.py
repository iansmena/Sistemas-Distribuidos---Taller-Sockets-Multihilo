import socket
import threading
import logging
from abc import ABC, abstractmethod

# Configuración básica del sistema de logs para imprimir mensajes formateados en consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- ABSTRACCIÓN (Principio Abierto/Cerrado & Inversión de Dependencias) ---

class MessageHandler(ABC):
    """
    Interfaz abstracta (contrato). Define qué debe hacer cualquier manejador 
    de mensajes de negocio, desacoplando la lógica de la red.
    """
    @abstractmethod
    def handle(self, message: str) -> str:
        """Método abstracto que procesa un mensaje de texto y retorna una respuesta."""
        pass


class EchoMessageHandler(MessageHandler):
    """
    Implementación concreta de MessageHandler. Realiza la lógica de negocio 
    más simple: devolver el mismo mensaje transformado en eco.
    """
    def handle(self, message: str) -> str:
        # Registra en los logs el mensaje de negocio recibido
        logging.info(f"Procesando mensaje de negocio: {message}")
        # Retorna el texto modificado como respuesta al cliente
        return f"ECO: {message}"


# --- GESTOR DE CONEXIÓN POR CLIENTE (Responsabilidad Única) ---

class ClientHandler:
    """
    Encargado exclusivamente de gestionar el ciclo de vida de la conexión 
    individual con un cliente específico.
    """
    def __init__(self, client_socket: socket.socket, address: tuple, message_handler: MessageHandler):
        self._client_socket = client_socket       # Socket exclusivo para hablar con este cliente
        self._address = address                   # Tupla (IP, puerto) del cliente conectado
        self._message_handler = message_handler   # Inyección de dependencia para procesar el mensaje
        self._buffer_size = 1024                  # Tamaño máximo en bytes a leer por vez

    def process(self) -> None:
        """Gestiona la recepción, procesamiento y envío de respuestas dentro del hilo."""
        try:
            # Context manager ('with') asegura que el socket del cliente se cierre al terminar
            with self._client_socket:
                logging.info(f"Conexión establecida con {self._address}")
                while True:
                    # Lee datos enviados por el cliente (operación bloqueante)
                    data = self._client_socket.recv(self._buffer_size)
                    
                    # Si 'data' está vacío, significa que el cliente cerró la conexión
                    if not data:
                        break
                    
                    # Decodifica los bytes a string UTF-8 y elimina espacios sobrantes
                    message = data.decode('utf-8').strip()
                    
                    # Delega la lógica de negocio al manejador inyectado
                    response = self._message_handler.handle(message)
                    
                    # Envía la respuesta codificada de vuelta al cliente
                    self._client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            # Captura cualquier error imprevisto durante la comunicación con este cliente
            logging.error(f"Error en la conexión con {self._address}: {e}")
        finally:
            # Mensaje informativo cuando el hilo está por terminar su ciclo
            logging.info(f"Conexión finalizada con {self._address}")


# --- SERVIDOR MULTIHILO (Responsabilidad Única: Red y Concurrencia) ---

class ThreadedSocketServer:
    """
    Servidor TCP multihilo. Su única responsabilidad es abrir el puerto,
    escuchar nuevas conexiones y lanzar un hilo independiente por cada cliente.
    """
    def __init__(self, host: str, port: int, message_handler: MessageHandler):
        self._host = host
        self._port = port
        self._message_handler = message_handler
        
        # Crea el socket principal del servidor (Familia IPv, Protocolo TCP)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Permite reutilizar el puerto inmediatamente después de cerrar el servidor (evita el error 'Address already in use')
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self) -> None:
        """Inicia el ciclo principal del servidor para aceptar conexiones entrantes."""
        # Asocia el socket a la IP y puerto indicados
        self._server_socket.bind((self._host, self._port))
        
        # Pone al servidor en modo escucha (acepta cola de conexiones pendientes)
        self._server_socket.listen()
        logging.info(f"Servidor iniciado y escuchando en {self._host}:{self._port}")

        try:
            while True:
                # Bloquea la ejecución hasta que un nuevo cliente se conecte.
                # Retorna un nuevo socket para la comunicación y la dirección del cliente.
                client_socket, address = self._server_socket.accept()
                
                # Instancia el manejador para este cliente específico, pasándole sus dependencias
                handler = ClientHandler(client_socket, address, self._message_handler)
                
                # Crea un hilo independiente para atender a este cliente sin bloquear a los demás.
                # 'daemon=True' hace que el hilo muera automáticamente si el programa principal se apaga.
                thread = threading.Thread(target=handler.process, daemon=True)
                
                # Inicia la ejecución del hilo (llama internamente a handler.process())
                thread.start()
        except KeyboardInterrupt:
            # Permite apagar limpiamente el servidor presionando Ctrl+C en la terminal
            logging.info("Servidor detenido por el usuario.")
        finally:
            # Asegura el cierre del socket principal del servidor al salir
            self._server_socket.close()


if __name__ == "__main__":
    # Configuración de red local para pruebas
    HOST = '127.0.0.1'
    PORT = 8080
    
    # Se instancia la regla de negocio (Eco)
    handler = EchoMessageHandler()
    
    # Se instancia el servidor inyectándole la lógica de negocio
    server = ThreadedSocketServer(HOST, PORT, handler)
    
    # Se pone en marcha el servidor
    server.start()