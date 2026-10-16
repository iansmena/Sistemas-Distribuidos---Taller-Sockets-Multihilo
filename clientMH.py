import socket
import logging

# Configuración básica del sistema de logs para imprimir mensajes formateados en la consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SocketClient:
    """
    Cliente TCP limpio y reutilizable. 
    Su única responsabilidad es establecer la conexión de red con el servidor,
    enviar un mensaje y recibir la respuesta correspondiente.
    """
    def __init__(self, host: str, port: int):
        self._host = host           # Dirección IP del servidor al que nos queremos conectar (ej. '127.0.0.1')
        self._port = port           # Puerto del servidor (ej. 8080)
        self._buffer_size = 1024    # Tamaño máximo en bytes que el cliente aceptará leer de golpe en cada respuesta

    def send_message(self, message: str) -> str:
        """
        Conecta con el servidor, envía un mensaje de texto, espera la respuesta 
        y asegura el cierre de la conexión de forma limpia.
        """
        try:
            # Creamos un socket TCP (AF_INET = IPv4, SOCK_STREAM = TCP)
            # El uso de 'with' (Context Manager) es una buena práctica de Clean Code:
            # garantiza que el socket se cierre automáticamente al salir del bloque,
            # incluso si ocurre un error inesperado (evita fugas de descriptores de red).
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                
                # 1. Conexión: El cliente toca la puerta del servidor en la IP y puerto indicados
                sock.connect((self._host, self._port))
                
                # 2. Envío: Convertimos el string de texto a bytes usando UTF-8 y lo enviamos completo
                sock.sendall(message.encode('utf-8'))
                
                # 3. Recepción: Esperamos la respuesta del servidor (operación bloqueante).
                # Leemos hasta un máximo de bytes definido por _buffer_size
                response = sock.recv(self._buffer_size)
                
                # 4. Procesamiento de salida: Convertimos los bytes recibidos de vuelta a un string legible
                return response.decode('utf-8')
                
        except socket.error as e:
            # Capturamos cualquier fallo de red (ej. el servidor está apagado o no hay conexión)
            logging.error(f"Error de comunicación con el servidor: {e}")
            raise


# --- EJECUCIÓN PRINCIPAL DEL CLIENTE ---
if __name__ == "__main__":
    # Definimos a qué servidor nos vamos a conectar
    HOST = '127.0.0.1'  # Localhost (la misma máquina)
    PORT = 8080         # El mismo puerto en el que está escuchando el servidor

    # Instanciamos nuestro objeto cliente pasándole las coordenadas del servidor
    client = SocketClient(HOST, PORT)
    
    # Lista de mensajes de prueba que queremos enviar al servidor uno por uno
    messages = ["Hola Servidor", "Sistemas Distribuidos", "Sockets Multihilo en Python"]
    
    # Iteramos sobre cada mensaje para realizar una prueba de comunicación
    for msg in messages:
        logging.info(f"Enviando: '{msg}'")
        
        # Llamamos al método del cliente. Cada llamada abre una conexión nueva,
        # envía el mensaje, recibe el eco y cierra la conexión automáticamente.
        reply = client.send_message(msg)
        
        # Imprimimos la respuesta obtenida desde el servidor
        logging.info(f"Respuesta recibida -> {reply}")