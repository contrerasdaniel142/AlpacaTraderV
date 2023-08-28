#region Librerias
import os                 # Para interactuar con el sistema operativo
import sys                # Para manipular la configuración del intérprete de Python
import requests           # Para enviar solicitudes HTTP
from typing import Dict, List, Tuple  # Para definir tipos de datos
from bs4 import BeautifulSoup  # Para analizar y extraer datos HTML
from datetime import datetime, timedelta  # Para manejar fechas y tiempos
import pytz               # Para manejar zonas horarias
import json               # Para trabajar con datos en formato JSON
from jinja2 import Template  # Para trabajar con plantillas HTML
import webbrowser         # Para abrir enlaces y archivos en el navegador web
import statistics as st   # Para realizar cálculos estadísticos
import numpy as np        # Para realizar operaciones numéricas eficientes


import multiprocessing    # Para trabajo en paralelo
from multiprocessing import Queue


# Obtiene la ruta absoluta del directorio actual
current_file = os.path.abspath(os.getcwd())
current_file = sys.path.append("D:\Daniel\Documents\SimonsTraderV")
# Agrega el directorio actual al sys.path
sys.path.append(sys.path.append("D:\Daniel\Documents\SimonsTraderV"))

# Importaciones específicas del proyecto
from configurate import conf  # Importa el módulo conf desde el paquete configurate
from model.alpha_trader_pro.api import AlphaTraderPro # Importa la clase AlphaTraderPro 
from model.alpha_trader_pro.models import Order # Importa la clase Order con la cual se haran ordenes a AlphaTraderPro
from model.alpha_trader_pro.enums import Exchange, Type, Side, Status # Importa los Enums que se usaran en AlphaTraderPro
from model.alpaca.find_pivots import PivotsAlpaca  # Importa la clase PivotsAlpaca desde el módulo pivots del paquete model.alpaca
from model.alpaca.api import ApiAlpaca  # Importa la clase ApiAlpaca desde el módulo api del paquete model.alpaca
from alpaca.data.timeframe import TimeFrame  # Importa la clase TimeFrame desde el módulo timeframe del paquete alpaca.data
from alpaca.data.models import Bar  # Importa la clase Bar desde el módulo models del paquete alpaca.data
from alpaca.trading.client import TradingClient # Importa la clase TradingClient de alpaca
from alpaca.trading.models import Clock # Clase que contiene la informacion de tiempo del mercado
import time

from alpaca.data.live.stock import StockDataStream # Para obtener datos en tiempo real del mercado
from alpaca.data.enums import DataFeed  # Para especificar el feed de datos que se quiere utilizar (IEX, SIP)

#endregion


#region Filtros

class PivotFilter:
    """
    Clase que se encargara de controlar los filtros para la estrategia de pivotes
    """
    def __init__(self) -> None:
        """
        Inicializador de la clase PivotFilter. Se encarga de filtrar las listas de activos.
        """
        # Creamos una instancia de la clase clsApiAlpaca utilizando las claves de API de la configuración.
        self._api_alpaca = ApiAlpaca(conf.alpaca_api_key_id, conf.alpaca_api_secret_key, conf.alpaca_data_feed)
        # Creamos un diccionario que contendrá los pivotes de cada activo.
        self.dict_asset_pivots: Dict[str, PivotsAlpaca]= {}
        # Creamos una lista de strings que contendrá los activos que pasen por el filtro 1.
        self.list_filter_1: List[str] = []
        # Variable que almacenara el volumen de los ultimos 19 dias de los activos del filto 1
        self._volume_19_days = {}
        # Variable que almacenara el volumen de los ultimos 10 minutoes de los activos del filto 2
        self._volume_10_minutes = {}
        print("filtro 1")
        self._filter_1()
    
    def _filter_1(self) -> None:
        """
        Realiza el primer filtro a los activos. Filtra los activos utilizando reglas establecidas y realiza consultas a la API de Alpaca para obtener datos históricos.

        Returns:
            None
        """
        # Creamos un objeto para filtrar los activos según las reglas establecidas.
        finviz_filtered = FinvizFiltered()

        # Obtenemos los símbolos que maneja Alpaca para evitar errores al intentar manejar activos no admitidos por Alpaca.
        alpaca_assets = self._api_alpaca.get_symbols_assets_with(conf.alpaca_symbol_status, conf.alpaca_asset_class, None)

        # Filtrar activos según las reglas y la lista de activos admitidos por Alpaca
        filtered_list_assets = [item for item in finviz_filtered.list_filtered_assets  if item in alpaca_assets]
        
        # Obtiene las barras de apertura de las 9 am
        opening_bars = self._api_alpaca.get_opening_bar(filtered_list_assets)

        if opening_bars is None:
            print("Hoy no hay actividad en el mercado financiero.")
        else:
            array_opening_bars = np.array([[symbol, bar_list[-1].close] for symbol, bar_list in opening_bars.data.items()], dtype=object)
                        
            list_unfound_assets = filtered_list_assets

            for year in range(1, 5):
                if not list_unfound_assets:
                    break

                print('')
                print('Símbolos a buscar:')
                print(list_unfound_assets)
                print(str(len(list_unfound_assets)))
                print('')
                print('Consultando los símbolos (', year, ' años)')

                # Obtener datos históricos de los activos no encontrados
                dict_asset_bars_day = self._api_alpaca.get_historical_assets_bars_with(TimeFrame.Day, 365*year, list_unfound_assets)              

                # Realizar el bucle de pivotes
                list_unfound_assets = self._find_pivots(dict_asset_bars_day, array_opening_bars, year, 5)

    def _find_pivots(self, par_dict_asset_bars_days, par_opening_bars: np.ndarray, par_year, par_number_pivots) -> List[str]:
        """
        Realiza un bucle de pivotes para cada activo en el diccionario de barras de activos.

        Args:
            par_dict_asset_bars_days (Dict[str, List[Bar]]): Diccionario que contiene las barras de activos por símbolo.
            par_opening_bars (Dict[str, List[Bar]]): Diccionario que contiene las barras de apertura por símbolo.
            par_year (int): El año actual en el bucle de pivotes.
            par_number_pivots (int): El número de pivotes a buscar.

        Returns:
            List[str]: Una lista de activos no encontrados.

        """
        list_unfound_assets: List[str] = []
        for asset, bars in par_dict_asset_bars_days.data.items():
            print(asset)
            # Buscar las filas donde la primera columna (asset) coincide con el valor deseado
            matching_rows = np.where(par_opening_bars[:, 0] == asset)[0]
            # En caso de encontrar obtiene el precio de apertura de esta, en caso contrario continua con el siguiente activo
            if matching_rows.size > 0:
                last_opening_bar_close = par_opening_bars[matching_rows[-1], 1]
            else:
                continue
                    
            if par_year == 1:
                asset_pivot = PivotsAlpaca(asset, par_number_pivots)
            else:
                asset_pivot = self.dict_asset_pivots[asset]

            asset_pivot.get_pivots(
                par_bars= bars,
                par_current_price= last_opening_bar_close,
                par_find_weak_pivots= (par_year == 4)
            )

            self.dict_asset_pivots[asset] = asset_pivot
            
            pivot_peaks_strong = asset_pivot.list_array_strong_peaks
            pivot_valleys_strong = asset_pivot.list_array_strong_valleys

            if len(pivot_peaks_strong) < par_number_pivots or len(pivot_valleys_strong) < par_number_pivots:
                list_unfound_assets.append(asset)
                
            if asset not in self.list_filter_1:
                self.list_filter_1.append(asset)
                
        return list_unfound_assets
    
    def _find_volume_19_days(self):
        # Obtener los datos históricos de barras para los activos filtrados en un marco de tiempo diario 
        bars_day = self._api_alpaca.get_historical_assets_bars_with(TimeFrame.Day, 30, self.list_filter_1)
        # Variable que almacenara el volumen de los ultimos 19 dias
        volume_days = {}
        current_day = (datetime.now().astimezone(pytz.utc)).day
  
        volume_days = {
            asset: (
                volumes_bar[:-1] if (bars[-1].timestamp).day == current_day else volumes_bar[1:]
            )
            for asset, bars in bars_day.data.items()
            for volumes_bar in [np.array([(bar.timestamp, bar.volume) for bar in bars[-20:]])]
        }
            
        self._volume_19_days = volume_days
    
    def filter_2(self) -> np.ndarray:
        """
        Filtra y selecciona activos basados en criterios específicos.

        Realiza una serie de pasos de filtrado y selección de activos basados en volumen, precio y condiciones de pivot.

        Returns:
            np.ndarray: Un arreglo estructurado que contiene los activos que cumplen con los criterios.
        """        
        # Encuentra el volumen de los días anteriores si self._volume_days está vacío
        if not self._volume_19_days:
            print("filtro 2")
            self._find_volume_19_days()
               
        # Obtén la última barra de día para los activos en list_filter_1
        last_bar_day = self._api_alpaca.get_historical_assets_bars_with(TimeFrame.Day, 1, self.list_filter_1)
        array_volume_day = np.array([(bars[-1].symbol, bars[-1].timestamp, bars[-1].volume) for _, bars in last_bar_day.data.items()])
        # Filtra las barras con volumen mayor a 50,000
        filtered_bar_day = array_volume_day[array_volume_day[:, 2] > 50000]
        
        # Obtén el precio más reciente para los activos en list_filter_1
        last_trades = self._api_alpaca.get_lastet_trade_with(self.list_filter_1)
        trade_arrays = np.array([(trade.symbol, trade.price) for _, trade in last_trades.items()], dtype=[('symbol', '<U32'), ('price', float)])
        # Filtra los trades con precio entre 20 y 500
        filtered_trades = trade_arrays[(trade_arrays['price'] >= 20) & (trade_arrays['price'] <= 500)]

        # Encuentra los símbolos que pasaron los filtros anteriores
        common_symbols = np.intersect1d(filtered_bar_day[:, 0], filtered_trades['symbol'])
        
        # Filtra los símbolos con volumen promedio de 20 días superior a 30,000
        list_20_days_volume_filter = [
            symbol
            for symbol in common_symbols
            if self._volume_19_days[symbol][-1, 0] != filtered_bar_day[filtered_bar_day[:, 0] == symbol][-1, 1]
            and np.mean(np.append(self._volume_19_days[symbol][:, 1], filtered_bar_day[filtered_bar_day[:, 0] == symbol][-1, 2])) > 30000
        ]
        
        list_near_pivot = []

        for symbol in list_20_days_volume_filter:
            # Verifica si el precio está cerca de un punto de pivote
            pivot_peak = self._check_price_near_pivot(self.dict_asset_pivots[symbol].list_array_strong_peaks, trade_arrays[(trade_arrays['symbol'] == symbol)]['price'][0], self.dict_asset_pivots[symbol].atr * 0.30)
            pivot_valley = self._check_price_near_pivot(self.dict_asset_pivots[symbol].list_array_strong_valleys, trade_arrays[(trade_arrays['symbol'] == symbol)]['price'][0], self.dict_asset_pivots[symbol].atr * 0.30)
            
            # Agrega símbolos que cumplen las condiciones a la lista
            if pivot_peak is not None and pivot_peak > trade_arrays[(trade_arrays['symbol'] == symbol)]['price'][0]:
                list_near_pivot.append((symbol, pivot_peak, "buy"))
            if pivot_valley is not None and pivot_valley < trade_arrays[(trade_arrays['symbol'] == symbol)]['price'][0]:
                list_near_pivot.append((symbol, pivot_valley, "sell"))
        
        # Extrae los símbolos de la lista cerca de puntos de pivote
        symbol_list = [symbol for symbol, _, _ in list_near_pivot]
        
        # Obtiene los últimos datos de barras de 10 minutos para los símbolos
        bars_10_minutes = self._api_alpaca.get_last_10_minute_bars(symbol_list)
        
        # Calcula el close promedio de 5 minutos anteriores y filtra resultados mayores a 0
        window_size = 5  # Tamaño de la ventana para el promedio de cierres
        avg_close_last_5 = np.array([
            (symbol, np.mean([bar.close for bar in bars[-window_size:]]))
            for symbol, bars in bars_10_minutes.data.items()
            if len(bars) >= window_size
        ], dtype=[('symbol', 'U10'), ('avg_close', float)])
        # Crea una nueva lista para almacenar los elementos válidos
        new_list_near_pivot = []
        
        new_list_near_pivot = [
            (symbol, pivot, action)
            for symbol, pivot, action in list_near_pivot
            if (
                (action == "buy" and trade_arrays[trade_arrays['symbol'] == symbol]['price'][0] >
                avg_close_last_5[avg_close_last_5['symbol'] == symbol]['avg_close'])
                or
                (action == "sell" and trade_arrays[trade_arrays['symbol'] == symbol]['price'][0] <
                avg_close_last_5[avg_close_last_5['symbol'] == symbol]['avg_close'])
            )
        ]
        # Actualiza la lista original con los elementos válidos
        list_near_pivot = new_list_near_pivot
                
        # Calcula el volumen promedio de 10 minutos y filtra aquellos mayores a 1000
        avg_volume_minutes = [
            (symbol, avg)
            for symbol, bars in bars_10_minutes.data.items()
            if (avg := np.mean([bar.volume for bar in bars])) > 1000
        ]
        
        # Crea un array con los símbolos cerca de pivotes y su información
        array_near_pivot = np.array([
            (symbol, action, pivot, avg)
            for symbol, pivot, action in list_near_pivot
            for symbol_avg, avg in avg_volume_minutes
            if symbol_avg == symbol
        ], dtype=[('symbol', '<U32'), ('action', '<U32'), ('pivot', float), ('avg', float)])
                                        
        print(str(len(array_near_pivot['symbol'])))
        print(array_near_pivot['symbol'])
        
        return array_near_pivot

    def _save_to_file(self, text_list: list[str]):
        """
        Guarda una lista de texto en un archivo llamado 'approved_filter_2.txt'.
        
        Si el archivo no existe, se creará automáticamente.
        Si el archivo existe, los textos de la lista se añadirán debajo del contenido existente.

        Args:
            text_list (list): La lista de textos que se van a guardar en el archivo.
        """
        # Convertir la lista de textos en una cadena de texto unida por saltos de línea
        text_to_write = '\n'.join(text_list)

        # Agregar un salto de línea antes de la cadena text_to_write
        text_to_write_with_newline = '\n' + text_to_write

        # Abrir el archivo en modo escritura (append)
        with open('approved_filter_2.txt', 'a') as archivo_salida:
            # Añadir el nuevo texto al final del archivo
            archivo_salida.write(text_to_write_with_newline)

    def _check_price_near_pivot(self, list_pivots: np.ndarray, current_price: float, par_slip: float) -> float:
        """
        Revisa si hay un pivote cercano al precio actual del activo dentro de un rango dado.

        Args:
            list_pivots (np.ndarray): Lista de arrays que contiene los pivotes.
            current_price (float): El precio actual del activo.
            par_slip (float): El rango mínimo de precio entre el precio actual y los pivotes.

        Returns:
            float-None: float si encuentra un pivote cercano al precio actual dentro del rango de par_slip dólares, en caso contrario None.
        """
        # Se revisa si la lista esta vacia
        if np.any(list_pivots):
            # Busca los pivots que se encuentren cerca al precio
            check_near_strong_pivot = np.where(np.abs(list_pivots[:,1] - current_price) < par_slip | np.abs(list_pivots[:,1] - current_price) > par_slip*0.5)
            check_near_strong_pivot = list_pivots[check_near_strong_pivot]
            # En caso de encontrar retorna True
            if np.any(check_near_strong_pivot) :
                return check_near_strong_pivot[-1][1]
            else:
                return None
        else:
            return None

    def plot_pivots(self, year: int = 1) -> None:
        """
        Genera un gráfico de los pivotes de los activos y los muestra en un navegador.

        Args:
            year (int): Número de años de datos históricos a considerar. Por defecto, es 1.
        """
        
        # Obtener la lista de símbolos
        symbol_list = self.list_filter_1
        
        # Obtener datos históricos de los activos
        assets_bars = self._api_alpaca.get_historical_assets_bars_with(TimeFrame.Day, 365*year, symbol_list)

        # Estructuras de datos para almacenar los pivotes
        data = {}
        pivot_strong_data = {}
        pivot_weak_data = {}

        # Generar los datos para cada activo
        for asset, bars in assets_bars.data.items():
            new_list_bars = [{
                'time': {
                    'year': bar.timestamp.year,
                    'month': bar.timestamp.month,
                    'day': bar.timestamp.day
                },
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume
            } for bar in bars]
            data[asset] = new_list_bars
                        
            pivots = self.dict_asset_pivots[asset]

            list_strong_peaks = [peak[1] for peak in pivots.list_array_strong_peaks]
            list_strong_valleys = [valley[1] for valley in pivots.list_array_strong_valleys]
            list_weak_peaks = [peak[1] for peak in pivots.list_array_weak_peaks]
            list_weak_valleys = [valley[1] for valley in pivots.list_array_weak_valleys]

            pivot_strong_data[asset] = [list_strong_peaks, list_strong_valleys]
            pivot_weak_data[asset] = [list_weak_peaks, list_weak_valleys]

        # Convertir pivot_strong_data a JSON
        pivot_strong_data_json = json.dumps(pivot_strong_data)

        # Convertir pivot_weak_data a JSON
        pivot_weak_data_json = json.dumps(pivot_weak_data)

        # Convertir data a JSON
        data_json = json.dumps(data)

        # Leer el archivo HTML original
        with open('D:\Daniel\Documents\SimonsTraderV/controller/templates/index.html', 'r') as file:
            html_template = file.read()

        # Crear un objeto Template de Jinja
        template = Template(html_template)

        # Renderizar la plantilla con los datos necesarios
        rendered_html = template.render(symbol_list=symbol_list, data=data_json, pivot_strong_data=pivot_strong_data_json, pivot_weak_data=pivot_weak_data_json)

        # Guardar el código HTML actualizado en un nuevo archivo
        with open('D:\Daniel\Documents\SimonsTraderV/controller/templates/index_updated.html', 'w') as file:
            file.write(rendered_html)

        # Obtener la ruta absoluta del archivo
        abs_file_path = os.path.abspath('D:\Daniel\Documents\SimonsTraderV/controller/templates/index_updated.html')

        # Abrir el archivo HTML en un navegador
        webbrowser.open('file://' + abs_file_path)
    
class FinvizFiltered:
    """
    Clase que se encarga de conectarse a finviz.com para obtener y filtrar activos.
    """  
    def __init__(self) -> None:
        """
        Método inicializador de la clase FinvizFilteredAssets. Se encarga de buscar y filtrar los activos en Finviz
        según ciertos criterios y guardarlos en la variable pública list_filtered_assets.

        Args:
            No recibe argumentos.

        Returns:
            No devuelve ningún valor.
        """        
        # URL que dirige al screener de Finviz. El screener ayuda a capturar activos con filtros establecidos. En la URL proporcionada se encuentran los siguientes filtros:
        # - Exchange: Any
        # - Market Cap: Large ($10B to $200B)
        # - Float: Over 50M
        # De esta manera, es más rápido y fácil aplicar los filtros necesarios.

        self._url = "https://finviz.com/screener.ashx?v=121&f=cap_largeover,sh_float_o1,ta_pattern_tlresistance&ft=4"
        # Crear el diccionario que almacenará los resultados del screener
        self.list_filtered_assets: List[str]= []
        # Capturamos todos los activos en el screener de Finviz y los guardamos en list_filtered_assets
        self._find_screener_assets()
        
    def _find_screener_assets(self) -> None:
        """
        Método privado de la clase FinvizFilteredAssets que realiza el scraping del screener de Finviz,
        filtrando y reduciendo los activos a revisar según los siguientes filtros:
        - Exchange: NASDAQ
        - Market Cap: Large ($10B to $200B)
        - Float: Over 50M

        Esta función permite reducir el rango de busqueda para aplicar los filtros necesarios de manera más rápida y sencilla.
        """   
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        A=requests.get(self._url, headers=headers, timeout=1) 
        A=A.content
        # Realizar la solicitud GET a la página y parsear el contenido HTML utilizando BeautifulSoup
        soup = BeautifulSoup(A, 'html.parser')
        # Encontrar el número de activos filtrados en Finviz
        number_assets = int(soup.find("div", id="screener-total", class_ = "count-text whitespace-nowrap").text.split()[2])
        # Crear el diccionario para almacenar los resultados
        for i in range(1, number_assets, 20):
            if i != 1:
                # Actualizar la solicitud GET a la página y parsear el contenido HTML utilizando BeautifulSoup
                soup = BeautifulSoup(requests.get(self._url+"&r="+str(i), headers=headers,timeout=1).content, 'html.parser')
            # Encontrar todas las filas de la tabla
            table_rows = soup.select('.table-light.is-new tr')[1:]
            # Iterar sobre cada fila y capturar el Market Cap y el volumen para filtrarlos
            for row in table_rows:
                asset_name = row.select_one('td:nth-child(2)').text
                #market_cap = self._convert_str_to_float(row.select_one('td:nth-child(3)').text)
                
                # if 25e9 < market_cap < 200e9:
                #     # Almacenar los resultados en el diccionario
                #     continue
                self.list_filtered_assets.append(asset_name)     
    
    def _convert_str_to_float(self, value: str) -> float:
        """
        Método privado de la clase FinvizFilteredAssets que se encarga de convertir las cadenas de texto
        que contienen información de los activos en valores de tipo float utilizables.

        Args:
            value (str): Cadena de texto que se va a convertir en un valor float.

        Returns:
            float: Valor convertido a tipo float.
        """
        # Definir los multiplicadores para las abreviaturas de unidades (K, M, B, T)
        multipliers = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
        # Eliminar las comas de la cadena de texto
        value = value.replace(",", "")
        # Comprobar si el valor es un guion ('-'), en cuyo caso se retorna 0.0
        if value == '-':
            return 0.0
        # Comprobar si el valor tiene una longitud de 1, en cuyo caso se agrega '.0' al final
        if len(value) == 1:
            value += '.0'
        # Obtener la parte numérica del valor y la letra que indica el multiplicador
        number_part = float(value[:-1])
        letter = value[-1]
        # Comprobar si la letra está en los multiplicadores predefinidos
        if letter in multipliers:
            # Calcular el resultado multiplicando la parte numérica por el multiplicador correspondiente
            result = number_part * multipliers[letter]
        else:
            # Si la letra no está en los multiplicadores, convertir directamente el valor a tipo float
            result = float(value)
        return result

#endregion

#region Controladores
class RealTimeController:
    def __init__(self, queue: Queue, list_symbols: List[str]) -> None:
        self._queue = queue
        self.list_symbols = list_symbols
        self._stream = StockDataStream(
            api_key=conf.alpaca_api_key_id,
            secret_key=conf.alpaca_api_secret_key,
            raw_data=False,
            feed=conf.alpaca_data_feed,
            websocket_params=None,
            url_override=None)
        
    async def _trade_callback(self, trade):
        trade_data = trade_data = {
            'symbol': trade.symbol,
            'price': trade.price,
            'size': trade.size,
            'timestamp': trade.timestamp
        }
        self._queue.put(trade_data)
        
    def start(self):
        self._stream.subscribe_trades(self._trade_callback, *self.list_symbols)
        self._stream.run()
    

class AlphaController:
    def __init__(self) -> None:
        """
        Inicializa la clase AlphaController.

        Crea una instancia de AlphaTraderPro para interactuar con la plataforma de trading.
        Inicializa una lista para rastrear los activos que han sido objeto de operaciones.

        Attributes:
            client (AlphaTraderPro): Instancia de AlphaTraderPro para interactuar con la plataforma de trading.
            traded_assets (List[str]): Lista de activos que han sido objeto de operaciones.
        """
        self._client = AlphaTraderPro()
        self.subscribed_symbols = np.empty((0, 4), dtype=[('symbol', '<U32'), ('action', '<U32'), ('pivot', float), ('avg', float)])
        self.traded_assets: List[str] = []

    def _buy(self, symbol):
        """
        Realiza una operación de compra.

        Realiza un intento de compra del activo utilizando AlphaTraderPro.
        Si la orden se completa exitosamente, agrega el activo a la lista de activos negociados.

        Args:
            symbol (str): Símbolo del activo a comprar.

        Returns:
            bool: True si la operación se completó, False si no.
        """
        if symbol not in self.traded_assets:
            print("Compra: ", symbol)
            for i in range(1, 3):
                print("Intento numero: ", i)
                order = self._client.send_order(Order(symbol, 0, 100, Exchange.BATS, Type.MARKET, Side.BUY))
                time.sleep(1)
                if order == 'filled':
                    self.traded_assets.append(symbol)
                    print("Orden completada")
                    return True
            print("Orden no completada")
            return False

    def _sell(self, symbol) -> bool:
        """
        Realiza una operación de venta.

        Realiza un intento de venta del activo utilizando AlphaTraderPro.
        Si la orden se completa exitosamente, agrega el activo a la lista de activos negociados.

        Args:
            symbol (str): Símbolo del activo a vender.

        Returns:
            bool: True si la operación se completó, False si no.
        """
        if symbol not in self.traded_assets:
            print("Venta: ", symbol)
            for i in range(1, 3):
                print("Intento numero: ", i)
                order = self._client.send_order(Order(symbol, 0, 100, Exchange.BATS, Type.MARKET, Side.SELL))
                time.sleep(1)
                if order == 'filled':
                    self.traded_assets.append(symbol)
                    print("Orden completada")
                    return True
            print("Orden no completada")
            return False

    def check_trade(self, queue: Queue):
        while True:
            trade = queue.get()
            matching_symbol = self.subscribed_symbols['symbol'] == trade['symbol']
            index = np.where(matching_symbol)[0]  # Obtiene los índices donde se cumple la condición
            if index.size > 0:
                find_symbol = self.subscribed_symbols[index[0]]
                
                symbol = trade['symbol']
                price = trade['price']
                volume = trade['volume']
                pivot = find_symbol['pivot']
                avg = find_symbol['avg']
                action = find_symbol['action']
                
                if action == "buy" and pivot < price and volume > avg * 5:
                    self._buy(symbol)
                if action == "sell" and pivot > price and volume > avg * 5:
                    self._sell(symbol)    
    
    def check_positions(self):
        """
        Verifica y gestiona las posiciones de trading.

        Obtiene todas las posiciones de trading y verifica si alguna posición
        tiene pérdidas considerables o ganancias considerables.
        Realiza operaciones de compra o venta según las condiciones.
        """
        while True:
            time.sleep(1)
            positions_list = self._client.get_all_positions()
            for position in positions_list:
                if float(position['Unrealized']) <= -3 or float(position['Unrealized']) >= 5:
                    if int(position['Qty']) > 0:
                        self._client.send_order(Order(position['Symbol'], 0, 100, Exchange.BATS, Type.MARKET, Side.SELL))
                    else:
                        self._client.send_order(Order(position['Symbol'], 0, 100, Exchange.BATS, Type.MARKET, Side.BUY))
          
class PivotController:
    def __init__(self) -> None:
        """
        Inicializa la clase RealTimeController.

        Crea una instancia de la clase StockDataStream para manejar el flujo de datos de acciones en tiempo real.
        Inicializa otras variables necesarias.

        Attributes:
            _stream (StockDataStream): Instancia de StockDataStream para obtener los datos en tiempo real.
            _alpha_controller (AlphaController): Instancia de AlphaController para realizar decisiones de trading.
            _subscribed_symbols (np.ndarray): Array de símbolos suscritos con acciones, pivotes y promedios.
            _current_minute (int): Minuto actual para el seguimiento de volumen.
            trades (dict): Diccionario para rastrear el volumen de operaciones por símbolo.
        """
        self.next_close = TradingClient(conf.alpaca_api_key_id, conf.alpaca_api_secret_key).get_clock().next_close
        self.pivot_filter = PivotFilter()
        self._last_minute = None
        self.trades = {}
    
    def _start_real_time(self, list_symbols: List[str], queue: Queue):
        controller = RealTimeController(queue, list_symbols)
        controller.start()
        
    def _receive_trade(self, queue: Queue):
        while True:
            trade = queue.get()
            current_time = datetime.now().astimezone(pytz.utc)
            # Si cambió el minuto, reiniciamos los datos de operaciones
            if self._last_minute != current_time.minute:
                self._reset_trades(current_time.minute)
            # Actualizamos los datos de operaciones y verificamos condiciones
            self._update_trade_data(trade)
            self._check_trade_condition(trade, queue)

    def _reset_trades(self, new_minute):
        """
        Reinicia los datos de operaciones cuando cambia el minuto.

        Args:
            new_minute: Nuevo minuto actual.
        """
        self._last_minute = new_minute
        self.trades = {}

    def _update_trade_data(self, trade):
        """
        Actualiza los datos de operaciones por símbolo.

        Args:
            trade: Objeto de operación recibido en tiempo real.
        """
        if trade['symbol'] not in self.trades:
            self.trades[trade['symbol']] = 0

        # Acumula el tamaño de la operación si el minuto actual coincide
        if self._last_minute == trade['timestamp'].minute:
            self.trades[trade['symbol']] += trade['size']
            
    def _check_trade_condition(self, trade, queue: Queue):
        # Verifica si el tamaño de operación supera el umbral y toma acción si es así
        current_volume = self.trades.get(trade['symbol'], 0)
        if current_volume > 5000:
            # Se guarda el volumen actual del activo
            trade['volume'] = current_volume
            # Enviar trade a alphatrader para comprobar si es comprable
            queue.put(trade)

    def start(self):
        """
        Inicia el proceso de gestión de trading.

        Este método coordina los procesos de recepción de trades, verificación y ejecución de trades,
        y administración de posiciones. Se encarga de gestionar las suscripciones a activos en tiempo real
        basándose en ciertos filtros y condiciones.

        El proceso de trading continuará hasta que se acerque la hora de cierre del mercado, momento en el cual
        se terminarán los procesos en curso y se cerrarán todas las posiciones abiertas.

        Nota:
            Este método utiliza varios métodos auxiliares privados para lograr su funcionalidad.

        """
        real_time_process = None
        list_symbols_to_subscribed: List[str] = []
        real_time_queue = multiprocessing.Queue()
        
        # Proceso que estara encargado de recibir los trades que lleguen de real_time_process y procesarlos
        receive_trades_process = multiprocessing.Process(target=self._receive_trade, args=(real_time_queue,))
        receive_trades_process.start()
        
        # Proceso que estara encargado de procesar los trades cuyo volumen supere el umbral y tradearlos
        alpha_trader = AlphaController()
        alpha_trader_queue = multiprocessing.Queue()
        check_trades_process = multiprocessing.Process(target=alpha_trader.check_trade, args=(alpha_trader_queue,))
        check_trades_process.start()
        
        # Proceso que estara encargado de consultar las posiciones para administrar ganancias o perdidas
        check_positions_process = multiprocessing.Process(target=alpha_trader.check_positions)
        check_positions_process.start()
        
        # Tiempo de cierre establecido  5  minutos antes del mercado
        time_to_close = self.next_close - timedelta(minutes=5)
        
        while True:
            # Obtén la fecha y hora actuales
            current_time = datetime.now().astimezone(pytz.utc)
            print("")
            print(current_time)
            assets_filter_2 = self.pivot_filter.filter_2()
            
            if current_time > time_to_close:
                receive_trades_process.terminate()
                check_trades_process.terminate()
                check_positions_process.terminate()
                if real_time_process is not None:
                        real_time_process.terminate()
                alpha_trader._client.close_all_positions()
                break
                
            if assets_filter_2.size != 0:
                # Crear una máscara booleana que indica si los simbolos del filtro 2 ya fueron tradeados en alpha_trader
                mask = np.isin(assets_filter_2['symbol'], alpha_trader.traded_assets)
                # Filtrar el array original para mantener solo los símbolos que no están en la lista
                filtered_assets = assets_filter_2[~mask]
                list_symbols_to_subscribed = filtered_assets['symbol'].tolist()
                # Obtiene las listas y las convierte en set para comparar si son iguales
                set_suscribed_symbols = set(alpha_trader.subscribed_symbols['symbol'].tolist())
                set_symbols_to_subscribed = set(list_symbols_to_subscribed)
                
                if set_suscribed_symbols != set_symbols_to_subscribed:
                    if real_time_process is not None:
                        real_time_process = real_time_process.terminate()
                        
                    alpha_trader.subscribed_symbols = filtered_assets
                    real_time_process = multiprocessing.Process(target=self._start_real_time, args=(list_symbols_to_subscribed, real_time_queue,))
                    real_time_process.start()
            else:
                if real_time_process is not None:
                    real_time_process = real_time_process.terminate()
     

#endregion
