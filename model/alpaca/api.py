#region Imports
# Importaciones para la interacción con la API de Alpaca
from alpaca.common.rest import RESTClient  # Para hacer solicitudes HTTP a la API de Alpaca
from alpaca.trading.client import TradingClient  # Para enviar órdenes y obtener información de cuenta
from alpaca.data.historical.stock import StockHistoricalDataClient  # Para obtener datos históricos de mercado
from alpaca.data.live.stock import StockDataStream  # Para obtener flujos de datos de mercado en tiempo real
from alpaca.trading.requests import GetAssetsRequest  # Para obtener información sobre los activos disponibles en Alpaca
from alpaca.data.requests import StockBarsRequest  # Para obtener barras de precios de un símbolo durante un período de tiempo
from alpaca.data.requests import StockLatestBarRequest # Para obtener la ultima barra de precios de un símbolo
from alpaca.data.requests import StockLatestTradeRequest # Para obtener el ultimo trade de un símbolo
from alpaca.common.enums import BaseURL  # La URL base para las solicitudes a la API de Alpaca

# Importaciones relacionadas con el manejo de fechas y tiempos
from datetime import datetime, timedelta  # Para manejar fechas y tiempos
import pytz  # Para manejar zonas horarias
import holidays # Para saber si es dia festivo

# Importaciones para definir tipos de datos
from typing import Union, Dict, Any, List

# Importaciones relacionadas con los modelos de datos de Alpaca
from alpaca.trading.models import UUID  # Modelo de UUID de Alpaca
from alpaca.trading.models import Position  # Modelo de posición de Alpaca
from alpaca.trading.models import ClosePositionResponse  # Modelo de respuesta al cerrar posición de Alpaca
from alpaca.data.models import Bar  # Modelo de conjunto de barras de precios
from alpaca.trading.models import Order  # Modelo de orden de Alpaca
from alpaca.data.models import Trade # Modelo de trade de Alpaca
from alpaca.trading.models import Asset  # Modelo de activo de Alpaca

# Importaciones relacionadas con las solicitudes y filtrado de datos
from alpaca.trading.requests import ClosePositionRequest  # Para solicitar el cierre de una posición en Alpaca
from alpaca.trading.requests import OrderRequest  # Para enviar una orden en Alpaca
from alpaca.data.enums import Adjustment  # Para especificar ajustes de stock split o dividendos
from alpaca.data.enums import DataFeed  # Para especificar el feed de datos que se quiere utilizar (IEX, SIP)
from alpaca.trading.enums import AssetStatus  # Para filtrar los activos disponibles en Alpaca por su estado
from alpaca.trading.enums import AssetClass  # Para filtrar los activos disponibles en Alpaca por su clase
from alpaca.data.timeframe import TimeFrame  # Para definir el marco de tiempo de los datos solicitados

#endregion

class ApiAlpaca:
    # region initial
    def __init__(self, api_key_id:str, api_secret_key:str, data_feed:DataFeed):
        """
        Inicializa la clase ApiAlpaca con las claves de la API de Alpaca y la alimentación de datos.

        Args:
            api_key_id (str): La clave de la API de Alpaca.
            api_secret_key (str): La clave secreta de la API de Alpaca.
            data_feed (DataFeed):La alimentación de datos de Alpaca a utilizar.
        """
        # Inicializa el numero de intentos maximos para hacer solicitudes al servidor de alpaca
        self.maximum_request = 5
        
        #Inicializa la variable que tendra el tipo de Feed
        self.data_feed: DataFeed = data_feed
        
        # Crea un cliente de trading utilizando la API de Alpaca
        self._trading_client = TradingClient(
            api_key = api_key_id,
            secret_key = api_secret_key,
            oauth_token = None,
            paper = True,
            raw_data = False,
            url_override = None
        )
        
        # Crea un cliente para recuperar datos históricos de stock utilizando la API de Alpaca
        self._stock_historical_data_client = StockHistoricalDataClient(
            api_key = api_key_id,
            secret_key = api_secret_key,
            oauth_token = None,
            use_basic_auth = False,
            raw_data = False,
            url_override = None
        )
        
        # Crea un cliente REST para interactuar con la API de Alpaca
        self._rest_v1beta1_client = RESTClient(
            api_version = 'v1beta1',                # La version de la API de Alpaca a la cual se le hara la solicitud
            base_url = BaseURL.DATA,                # Define la URL de datos de Alpaca para conectar a la API de Alpaca
            api_key = api_key_id,
            secret_key = api_secret_key
        )
       
        
    #endregion
        
    # region Getters

    def get_symbols_assets_with(self, par_status:AssetStatus = None, par_asset_class:AssetClass = None, par_exchange: str = None)-> List[str]:
        """
        Esta función devuelve una lista de símbolos de activos que cumplen ciertos criterios.
        Los criterios se basan en el estado y la clase de activos proporcionados como parámetros.
        
        Args:
            par_status (AssetStatus): El estado de los activos a recuperar. Ejemplo: AssetStatus.ACTIVE.
            par_asset_class (AssetClass): La clase de activos a recuperar. Ejemplo: AssetClass.US_EQUITY.
            par_exchange (str): El exchange al que estan asociados los activos. Ejemplo: "NASDAQ"

        Returns:
            List[str]: Una lista de símbolos de activos que cumplen con los criterios especificados.

        Ejemplo de uso:
        >> obj = ApiAlpaca()
        >> symbols = obj.get_symbols_assets_with(AssetStatus.ACTIVE, AssetClass.US_EQUITY)
        >> print(symbols)
        ['AAPL', 'GOOG', 'MSFT', ...]
        """
        # Crea una solicitud de activos con el estado y la clase de activos proporcionados
        asset_resquest = GetAssetsRequest(
            status= par_status,           # Estado de los activos a recuperar
            asset_class= par_asset_class, # Clase de los activos a recuperar
            exchange= par_exchange               # No especifica ninguna bolsa en particular
        )
        
        # Usa el cliente de trading para obtener todos los activos que cumplen con el filtro de la solicitud de activos
        for i in range(0, self.maximum_request):
            try:
                assets = self._trading_client.get_all_assets(filter= asset_resquest)
                break
            except:
                print("Error al hacer la solicitud.")
                if i == 4:
                    return None
        
        # Filtra la lista de activos para incluir sólo aquellos que son cortos, fácilmente prestables y negociables
        filtered_assets = filter(lambda asset: asset.shortable and asset.easy_to_borrow and asset.tradable, assets)
        
        # Crea una lista de los símbolos de los activos que cumplen con los criterios
        list_symbols_assets = [asset.symbol for asset in filtered_assets]
        
        # Devuelve la lista de símbolos
        return list_symbols_assets
        
    def get_historical_assets_bars_with(self, par_time_frame:TimeFrame, par_days:int, par_symbols_assets:List[str]) -> Dict[str, List[Bar]]:
        """
        Este método recupera los datos históricos de uno o mas símbolos en específico durante un cierto número de días.

        Args:
            par_time_frame (TimeFrame): La temporalidad de las barras. Ejemplo: TimeFrame.Day, TimeFrame.Minute
            par_days (int): El número de días a contar desde la fecha actual hacia atrás para recuperar datos.
            par_symbols_assets (str): El/los símbolos del activo para el cual recuperar los datos. Ejemplo: ["NVDA", "AMD"], "NVDA"
            
        Returns:
            StockBars: Un objeto BarSet que contiene los datos históricos del símbolo dado.
            
        Nota 1:
            Los datos se ajustan para splits.

        Ejemplo de uso:
        >> obj = ApiAlpaca()
        >> historical_bars = obj.get_historical_assets_bars_with(TimeFrame.Day, 10, "AAPL")
        >> print(historical_bars)
        [(BarSet | RawData)(...), (BarSet | RawData)(...), ...]
        """
        current_date = datetime.now().astimezone(pytz.utc)
        
        if par_days == 1:
            start =  current_date - timedelta(days=2)
            us_holidays = holidays.country_holidays('US')  
            while start.weekday() >= 4 or start in us_holidays:
                start -= timedelta(days=1)
        else:
            start = current_date - timedelta(days=par_days)
        
        stock_bars= StockBarsRequest(
            symbol_or_symbols=par_symbols_assets,
            start= start,                                       # Fecha con parDays antes de la fecha actual y conversión a utc
            end= current_date,                                  # Fecha actual y conversión a utc
            limit=None,                                                                # Sin límite para el número de barras
            timeframe= par_time_frame,                                                   # Temporalidad de las barras
            adjustment=Adjustment.SPLIT,                                               # Data ajustada por splits
            feed= self.data_feed                                                        # Alimentación de datos definida en la instanciación de la clase
        )

        # Solicita las barras de stock a la API de Alpaca utilizando el cliente de datos históricos
        bars_day = self._stock_historical_data_client.get_stock_bars(stock_bars)

        # Devolver las barras de stock recuperadas
        return bars_day

    def get_last_10_minute_bars(self, par_symbols_assets: List[str]) -> Dict[str, List[Bar]]:             
        current_date = datetime.now().astimezone(pytz.utc) + timedelta(minutes=1)
        market_open = current_date.replace(hour=14, minute=40, second=0, microsecond=0)
        start = current_date.replace(hour=19, minute=50, second=0, microsecond=0)
        us_holidays = holidays.country_holidays('US')
        
        if current_date.hour < 20  and current_date >= market_open :
            start = current_date - timedelta(minutes=10)
        elif current_date < market_open:
            start -= timedelta(days=1)
            
            
        while start.weekday() >= 5 or start in us_holidays:
            start -= timedelta(days=1)

        stock_bars = StockBarsRequest(
            symbol_or_symbols=par_symbols_assets,
            start= start,  # Fecha con parDays antes de la fecha actual y conversión a UTC
            end= current_date,  # Fecha actual y conversión a UTC
            limit= None,  # Sin límite para el número de barras
            timeframe=TimeFrame.Minute,  # Temporalidad de las barras
            adjustment=Adjustment.SPLIT,  # Datos ajustados por splits
            feed=self.data_feed  # Alimentación de datos definida en la instanciación de la clase
        )

        bars_day = self._stock_historical_data_client.get_stock_bars(stock_bars)
        return bars_day

    def get_opening_bar(self, par_symbols_assets: List[str]) -> Dict[str, List[Bar]]:
        """
        Obtener las barras ultimas barras creadas hasta la apertura para los activos especificados.

        Args:
            par_symbols_assets (List[str]): Lista de símbolos de activos.

        Returns:
            Dict[str, List[Bar]] or None: Un diccionario que mapea los símbolos de activos a las listas de barras de apertura, o None si es fin de semana o día festivo.
        """
        current_date = datetime.now().astimezone(pytz.utc)
        end = current_date.replace(hour=14, minute=0, second=0, microsecond=0)
        start = current_date.replace(hour=19, minute=59, second=0, microsecond=0) - timedelta(days=1)
        us_holidays = holidays.country_holidays('US')           
            
        while start.weekday() >= 5 or start in us_holidays:
            start -= timedelta(days=1)

        stock_bars = StockBarsRequest(
            symbol_or_symbols=par_symbols_assets,
            start=start,  # Fecha con parDays antes de la fecha actual y conversión a UTC
            end=end,  # Fecha actual y conversión a UTC
            limit=None,  # Sin límite para el número de barras
            timeframe=TimeFrame.Minute,  # Temporalidad de las barras
            adjustment=Adjustment.SPLIT,  # Datos ajustados por splits
            feed=self.data_feed  # Alimentación de datos definida en la instanciación de la clase
        )

        bars_day = self._stock_historical_data_client.get_stock_bars(stock_bars)
        return bars_day

    def get_news_with(self, par_days:int, par_symbols_assets:str) -> Dict[Any, Any]:
        """
        Obtiene las noticias relacionadas con los símbolos dados en el intervalo de tiempo especificado.

        Args:
            par_days (int): Número de días en el pasado desde la fecha actual para iniciar la recopilación de noticias.
            par_symbols_assets (str): Símbolos de las acciones separados por comas para los que se recopilarán noticias. Ejemplo: ["NVDA", "AMD"], "NVDA".

        Returns:
            HTTPResult: Resultado de la solicitud HTTP al endpoint de noticias. Contiene las noticias recopiladas para los símbolos y el intervalo de tiempo especificado.
        
            
        Usage:
            >>> api = ApiAlpaca()
            >>> news = api.get_news_with(7, ["NVDA", "AMD"])
        """
        # Define la ruta de las noticias
        path_news = '/news'
        
        #Convierte la lista de simbolos en string para que sea aceptada en los parametros
        symbols_str = ','.join(par_symbols_assets)
        
        # Define los parámetros de la solicitud
        parameters = {
            'start': (datetime.now() - timedelta(days=par_days)).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),  # Inicio del período de tiempo para recopilar noticias
            'end': datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),                                # Fin del período de tiempo para recopilar noticias
            'symbols': symbols_str                                                                          # Símbolos de las acciones para las cuales se recogerán noticias
        }
        
        # Hace una solicitud GET al punto final de las noticias con los parámetros definidos
        return_news = self._rest_v1beta1_client.get(path_news, parameters,)
        
        # Devuelve el resultado de la solicitud
        return return_news

    def get_all_positions(self) -> Union[List[Position], Dict[str, Any]]:
        """
        Método para obtener todas las posiciones.

        Este método utiliza la instancia de TradingClient para recuperar todas las posiciones de un portafolio de inversión.
        Las posiciones representan los diferentes activos y su cantidad que el portafolio posee.

        Returns:
            Union[List[Position], Dict[str, Any]]: Retorna una lista de objetos de tipo 'Position', cada uno representando
            una posición en un activo específico. En caso de error, retorna un diccionario con información adicional del error.
        """
        # Solicita las posiciones abiertas a la API de Alpaca
        allPositions = self._trading_client.get_all_positions()
        return allPositions
    
    def get_positions_with(self, par_symbol_or_asset_id: Union[UUID, str]) -> Union[Position, Dict[str, Any]]:
        """
        Método para obtener las posiciones abiertas para un símbolo o ID de activo específico.

        Este método utiliza la instancia de TradingClient para recuperar las posiciones abiertas para el símbolo o ID de activo dado.
        Una posición abierta representa un activo que actualmente está en posesión y puede resultar en ganancia o pérdida.

        Args:
            par_symbol_or_asset_id (Union[UUID, str]): El símbolo o ID del activo para el cual se deben recuperar las posiciones.
            Esto podría ser, por ejemplo, el símbolo de una acción ('AAPL' para Apple Inc.) o un ID único de activo.

        Returns:
            Union[Position, Dict[str, Any]]: Retorna un objeto de tipo 'Position' representando la posición en el activo especificado.
            En caso de error, retorna un diccionario con información adicional del error.
        """
        # Solicita las posicios abiertas con el símbolo o ID de activo dado a la API de Alpaca
        selectPositions = self._trading_client.get_open_position(par_symbol_or_asset_id)
        return selectPositions
    
    def get_lastet_bar_with(self, par_symbols_assets: str)-> Dict[str, List[Bar]]:
        stock_latest_bar = StockLatestBarRequest(
            symbol_or_symbols = par_symbols_assets, 
            feed = self.data_feed, 
            currency = None)
        last_bar_minute = self._stock_historical_data_client.get_stock_latest_bar(stock_latest_bar)
        return last_bar_minute
    
    def get_lastet_trade_with(self, par_symbols_assets: str)-> Dict[str, Trade]:
        stock_latest_trade = StockLatestTradeRequest(
            symbol_or_symbols = par_symbols_assets, 
            feed = self.data_feed, 
            currency = None
            )
        last_trade = self._stock_historical_data_client.get_stock_latest_trade(stock_latest_trade)
        return last_trade
    
    # endregion
    
    # region close Positions
    def closeAllPositions(self, cancel_orders: bool) -> Union[List[ClosePositionResponse], Dict[str, Any]]:
        """
        Método para cerrar todas las posiciones.

        Este método utiliza la instancia de TradingClient para cerrar todas las posiciones de un portafolio de inversión.
        Las posiciones representan los diferentes activos y su cantidad que el portafolio posee.

        Args:
            cancel_orders (bool): Indica si se deben cancelar las órdenes asociadas a las posiciones.

        Returns:
            Union[List[ClosePositionResponse], Dict[str, Any]]: Retorna una lista de objetos de tipo 'ClosePositionResponse',
            cada uno representando el resultado del cierre de una posición específica.
            En caso de error, retorna un diccionario con información adicional del error.
        """
        # Solicita el cierre de todas las posiciones a la API de Alpaca
        closePositions = self._trading_client.close_all_positions(cancel_orders)
        return closePositions
    def closePositionsWith(self, symbol_or_asset_id: Union[UUID, str], close_options: Union[ClosePositionRequest, None]) -> Union[Order, Dict[str, Any]]:
        """
        Método para cerrar las posiciones abiertas para un símbolo o ID de activo específico.

        Este método utiliza la instancia de TradingClient para cerrar las posiciones abiertas para el símbolo o ID de activo dado.
        Una posición abierta representa un activo que actualmente está en posesión y puede resultar en ganancia o pérdida.

        Args:
            symbol_or_asset_id (Union[UUID, str]): El símbolo o ID del activo para el cual se deben cerrar las posiciones.
            Esto podría ser, por ejemplo, el símbolo de una acción ('AAPL' para Apple Inc.) o un ID único de activo.
            close_options (Union[ClosePositionRequest, None]): Opciones adicionales para el cierre de posiciones.

        Returns:
            Union[Order, Dict[str, Any]]: Retorna un objeto de tipo 'Order' representando la orden de cierre de la posición en el activo especificado.
            En caso de error, retorna un diccionario con información adicional del error.
        """
        # Solicita el cierre de las posiciones con el símbolo o ID de activo dado a la API de Alpaca
        closePositions = self._trading_client.close_position(symbol_or_asset_id, close_options)
        return closePositions
    # endregion


