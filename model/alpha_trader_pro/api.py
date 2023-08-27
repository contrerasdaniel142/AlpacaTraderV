import urllib.request  # Para realizar solicitudes HTTP
import json  # Para trabajar con datos JSON
import re  # Para expresiones regulares
# Importaciones para la clase AlphaTraderPro
from .enums import BaseUrl, Exchange, Type, Side, Status
# Importación de la clase 'Order' desde el módulo 'models'
from .models import Order
# Importaciones de tipos de Python
from typing import Dict, List

class AlphaTraderPro:
    """Clase para interactuar con AlphaTraderPro.

        Esta clase proporciona una interfaz para interactuar con la API de AlphaTraderPro.
        Permite realizar operaciones en el exchange y obtener información sobre las órdenes y posiciones.

        Attributes:
            base_url (str): La URL base de la API.
            connection (bool): Un indicador que muestra si la conexión con la API se ha establecido correctamente.
        """
           
    def __init__(self, par_base_url: BaseUrl = BaseUrl.LOCALHOST) -> None:
        """Clase para interactuar con AlphaTraderPro.

        Esta clase proporciona una interfaz para interactuar con la API de AlphaTraderPro.
        Permite realizar operaciones en el exchange y obtener información sobre las órdenes y posiciones.

        Args:
            par_base_url (BaseUrl, opcional): La URL base de la API. Por defecto, se utiliza BaseUrl.LOCALHOST.

        Attributes:
            base_url (str): La URL base de la API.
            connection (bool): Un indicador que muestra si la conexión con la API se ha establecido correctamente.
        """
        self.base_url = par_base_url
        try:
            urllib.request.urlopen(f'{self.base_url}/connection').read()
            self.connection = True
        except:
            self.connection = False
    
    #region Utilities   
    def _convert_data_orders(self, par_data_byte_string: bytes) -> Dict[str, Dict[str, str]]:
        """
        Convierte la tabla de ordenes recibida de AlphaTraderPro en un diccionario anidado. Se aplican ciertas transformaciones
        para ajustar el formato antes de convertirlo a un diccionario en Python.

        Args:
            par_data_byte_string (bytes): El byte-string que contiene la información a convertir.

        Returns:
            dict: Un diccionario anidado con las claves y valores extraídos como cadenas de texto.
        """
        # Convertir el byte-string a un string y eliminar las comillas dobles exteriores
        data_string = par_data_byte_string.decode('utf-8').replace('=', ':').replace('[', '{').replace(']', '}').replace(' ', '')
        # Eliminar las comillas dobles del inicio y final del string (si están presentes)
        data_string = data_string.strip('"')
        # Reemplazar comas por puntos en los valores numéricos de la parte de "Price"
        data_string = re.sub(r'Price:(\d+),(\d+)', r'Price:\1.\2', data_string)
        # Agregar y quitar comillas para construir el diccionario
        if data_string != '{}':
            data_string = data_string.replace('{', '{"').replace('}', '"}').replace(',', '","').replace(':', '":"').replace('"{', '{').replace('}"', '}')
        # Convertir la data a diccionario en python
        data_dict = json.loads(data_string)
        return data_dict
    
    def _convert_data_positions(self, par_data_byte_string: bytes) -> List[Dict[str, str]]:
        """
        Convierte una lista de posiciones de AlphaTraderPro en una lista de diccionarios anidados. Se aplican
        ciertas transformaciones para ajustar el formato antes de convertirlo a un diccionario en Python.

        Args:
            par_data_byte_string (bytes): La lista de byte-strings que contiene la información de las posiciones a convertir.

        Returns:
            list: Una lista de diccionarios anidados con las claves y valores extraídos de los byte-strings.
        """
        data_list = par_data_byte_string.decode('utf-8')
        data_list = json.loads(data_list)
        positions_list = []
        for data in data_list:
            # Convertir el string y eliminar las comillas dobles exteriores
            position = data.strip('"')
            position = position.replace('=', ':').replace('[', '{').replace(']', '}').replace(' ', '')
            # Reemplazar comas por puntos en los valores numéricos de la parte de "PosAvgPrice"
            position = re.sub(r'PosAvgPrice:(-?\d+),(\d+)', r'PosAvgPrice:\1.\2', position)
            # Reemplazar comas por puntos en los valores numéricos de la parte de "LastPrice"
            position = re.sub(r'LastPrice:(-?\d+),(\d+)', r'LastPrice:\1.\2', position)
            # Reemplazar comas por puntos en los valores numéricos de la parte de "Unrealized"
            position = re.sub(r'Unrealized:(-?\d+),(\d+)', r'Unrealized:\1.\2', position)
            # Reemplazar comas por puntos en los valores numéricos de la parte de "NetPnl"
            position = re.sub(r'NetPnl:(-?\d+),(\d+)', r'NetPnl:\1.\2', position)
            # Reemplazar comas por puntos en los valores numéricos de la parte de "GrossPnl"
            position = re.sub(r'GrossPnl:(-?\d+),(\d+)', r'GrossPnl:\1.\2', position)
            # Agregar y quitar comillas para construir el diccionario
            position = position.replace('{', '{"').replace('}', '"}').replace(',', '","').replace(':', '":"')
            # Convertir la data a diccionario en python
            position = json.loads(position)
            positions_list.append(position)      
        
        return positions_list
      
    def _convert_price_to_format(self, par_price: float) -> str:
        """
        Convierte un precio dado en formato de punto flotante (con punto decimal) a un formato de cadena
        con coma decimal.

        Parámetros:
            par_price (float): El precio en formato de punto flotante a convertir.

        Retorna:
            str: El precio convertido en formato de cadena con coma decimal.

        Ejemplo:
            >>> _convert_price(200.56)
            '200,56'
        """
        converted = str(par_price).replace('.', ',')
        return converted
    
    #endregion
    
    #region Getters
    def get_all_orders(self)->Dict[str, Dict[str,str]]:
        """Obtiene todas las ordenes de AlphaTraderPro y los devuelve como un diccionario anidado.

        Retorna:
            Dict[str, Dict[str,str]]: Un diccionario anidado con la información de todas las ordenes realizadas.
        """
        url = f'{self.base_url}/orders'
        request_table = urllib.request.urlopen(url).read()
        data = self._convert_data_orders(request_table)
        return data
    
    def get_all_positions(self)-> List[Dict[str,str]]:
        """Obtiene todas las posiciones de AlphaTraderPro y los devuelve como una lista de diccionarios.

        Retorna:
            List[Dict[str,str]]: Una lista de diccionarios con la información de todas las posiciones realizadas.
        """
        url = f'{self.base_url}/positions'
        request = urllib.request.urlopen(url).read()
        positions_list = self._convert_data_positions(request)
        open_positions_list = []
        for position in positions_list:
            if int(position['Qty']) != 0:
                open_positions_list.append(position)
        return open_positions_list
        
      
    def get_status_order(self, par_id: str)-> str: 
        """Obtener el estado de una orden.

        Esta función busca en todas las órdenes para determinar el estado de una orden con el ID proporcionado.

        Args:
            par_id (str): El ID de la orden para la cual se desea obtener el estado.

        Returns:
            str: El estado de la orden con el ID dado. Puede ser "Open", "Filled", "Canceled" o "None" si no se encuentra la orden.
        """   
        orders_table = self.get_all_orders()
        for _, order in orders_table.items():
            if order["OrderID"] == par_id:
                return order["Status"]
        return None
      
    #endregion
    
    def send_order(self, par_order: Order) -> str:
        """Enviar una orden al exchange.

        Esta función envía una solicitud para realizar una orden con la información proporcionada en el objeto 'par_order'.

        Args:
            par_order (Order): El objeto que contiene la información de la orden a realizar.

        Returns:
            str: El estado actual de la orden enviada.
                
        Si la orden está abierta, se devuelve el ID de la orden.
        Si la orden se completó, se devuelve el status 'filled'
        Si la orden fue rechazada por AlphaTraderPro, se devuelve el status 'rejected'."""# Convierte el precio en el formato válido
        converted_price = self._convert_price_to_format(par_order.price)# Crea la solicitud con los parámetros necesarios
        url = f'{self.base_url}/sendOrder?symbol={par_order.symbol}&qty={str(par_order.quantity)}&exchange={par_order.exchange}&type={par_order.type}&side={par_order.side}&price={converted_price}'# Envia la solicitud al exchange
        result = urllib.request.urlopen(url).read()# Verifica si la orden fue rechazada por AlphaTrader
        result = result.decode('utf-8')
        if "rejected" in result:
            return "rejected"# Obtiene todas las posiciones abiertas de AlphaTrader
        positions_list = self.get_all_positions()# Busca la orden enviada en la tabla de posiciones para obtener su estado actual
        for position in positions_list:
            if (position["Symbol"] == par_order.symbol):
                return "filled"# Si no se encontró la posicion, se considera que la orden fue rechazada
        return "rejected"

    #region Requests
    def send_order(self, par_order: Order) -> str:
        """Enviar una orden al exchange.

        Esta función envía una solicitud para realizar una orden con la información proporcionada en el objeto 'par_order'.

        Args:
            par_order (Order): El objeto que contiene la información de la orden a realizar.

        Returns:
            str: El estado actual de la orden enviada.
                - Si la orden está abierta, se devuelve el ID de la orden.
                - Si la orden se completó, se devuelve el status 'filled'
                - Si la orden fue rechazada por AlphaTraderPro, se devuelve el status 'rejected'.
        """
        # Convierte el precio en el formato válido
        converted_price = self._convert_price_to_format(par_order.price)
        # Crea la solicitud con los parámetros necesarios
        url = f'{self.base_url}/sendOrder?symbol={par_order.symbol}&qty={str(par_order.quantity)}&exchange={par_order.exchange}&type={par_order.type}&side={par_order.side}&price={converted_price}'
        # Envia la solicitud al exchange
        result = urllib.request.urlopen(url).read()
        # Verifica si la orden fue rechazada por el exchange
        result = result.decode('utf-8')
        if "rejected" in result:
            return "rejected"
        # Obtiene todas las órdenes del exchange (suponemos que existe una función 'get_all_orders')
        orders_table = self.get_all_orders()
        # Busca la orden enviada en la tabla de órdenes para obtener su estado actual
        for _, order in orders_table.items():
            if (
                order["Symbol"] == par_order.symbol
                and order["Qty"] == par_order.quantity
                and order["OrderType"] == par_order.type
            ):
                if order["Status"] == Status.OPEN:
                    return order["OrderID"]
        # Si no se encontró la orden en la tabla o su estado no es 'OPEN', se considera que la orden fue completada
        return "filled"
          
    def cancel_order(self, par_id: str):
        """Cancelar una orden.

        Esta función envía una solicitud para cancelar la orden identificada por el ID proporcionado.

        Args:
            par_id (str): El ID de la orden a cancelar.
        """
        url = f'{self.base_url}/cancelOrder?id={par_id}'
        urllib.request.urlopen(url).read()
    
    def cancel_all_orders_open(self):
        """Cancelar todas las órdenes abiertas.

        Esta función obtiene todas las órdenes y cancela aquellas que estén abiertas (Status.OPEN).
        """
        orders_table = self.get_all_orders()
        for _, order in orders_table.items():
            if (
                order["Status"] == Status.OPEN
            ):
                self.cancel_order(order["OrderID"])
        
    def close_positions_of_a_symbol(self, par_symbol:str):
        """Cerrar todas las posiciones abiertas de un símbolo específico enviando órdenes de mercado.

        Esta función cierra todas las posiciones abiertas para un símbolo específico en el exchange enviando órdenes de mercado.
        Obtiene la lista de posiciones abiertas, crea una orden de mercado para cada posición del símbolo proporcionado y la envía para cerrarla.

        Args:
            par_symbol (str): El símbolo del activo para el cual se desean cerrar las posiciones abiertas.
        """
        list_positions = self.get_all_positions()
        for data_order in list_positions:
            if par_symbol == data_order['Symbol']:
                order = Order(
                    symbol= data_order['Symbol'],
                    price= float(data_order['LastPrice']),
                    quantity= int(data_order['Qty']),
                    exchange= Exchange.BATS,
                    type= Type.LIMIT,
                    side= data_order['Side']
                    )
                order.convert_to_close_position()
                self.send_order(order)
    
    def close_position_of_a_order(self, par_order: Order):
        """Cierra la posición asociada a una orden específica.
        
        Args:
            par_order (Order): La orden que se desea cerrar. Debe ser una orden que representa una posición abierta.
        """
        par_order.convert_to_close_position()
        self.send_order(par_order)
        
    def close_all_positions(self):
        """Cerrar todas las posiciones abiertas enviando órdenes de mercado.

        Esta función cierra todas las posiciones abiertas en el exchange enviando órdenes de mercado.
        Obtiene la lista de posiciones abiertas, crea una orden de mercado para cada posición y la envía para cerrarla.
        """
        list_positions = self.get_all_positions()
        for data_order in list_positions:
            order = Order(
                symbol= data_order['Symbol'],
                price= float(data_order['LastPrice']),
                quantity= int(data_order['Qty']),
                exchange= Exchange.BATS,
                type= Type.LIMIT,
                side= data_order['Side']
                )
            self.close_position_of_a_order(order)
                
    #endregion
