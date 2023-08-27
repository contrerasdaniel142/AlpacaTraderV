import numpy as np
from alpaca.data.models import Bar  # Importación de los modelos de barras de precios desde el módulo "models" en el paquete "data" de la API de Alpaca
from typing import Dict, List, Tuple  # Importación de módulos para definir tipos de datos

class PivotsAlpaca:
    def __init__(self, par_asset_name: str, par_number_pivots: int)-> None:
        """
        Crea una instancia de la clase para encontrar y almacenar los pivots.

        Args:
            par_asset_name (str): El nombre del activo.
            par_number_pivots (int): El número de pivots a buscar.
        """
        # Variables de instancia
        self.asset_name: str= par_asset_name
        self.number_pivots: int= par_number_pivots
        self.atr: float= None
        self.list_array_strong_peaks: List[np.ndarray]= []
        self.list_array_strong_valleys: List[np.ndarray]= []
        self.list_array_weak_peaks: List[np.ndarray]= []
        self.list_array_weak_valleys: List[np.ndarray]= []
        self.current_price = 0
        
    def _found_atr(self, par_array_bars: np.ndarray) -> None:
        """
        Calcula el Average True Range (ATR) para los últimos 14 días.

        Args:
            par_array_bars (np.ndarray): Array que almacena los valores de high, low y close de los últimos 15 días.
        """   
        # Obtener los valores de high, low y close de los datos y convertirlos en arrays NumPy
        high = par_array_bars[:,0]
        low = par_array_bars[:,1]
        close = par_array_bars[:,2]
        
        len_array = len(par_array_bars) - 1
        
        # Calcular el rango verdadero (true range)
        true_range = np.maximum(high[-len_array:] - low[-len_array:], np.abs(high[-len_array:] - close[1:]), np.abs(low[-len_array:] - close[1:]))

        # Calcular el ATR
        self.atr = np.average(true_range)
                
    def get_pivots(self, par_bars: List[Bar], par_current_price: float, par_find_weak_pivots: bool= True) -> None:
        """
        Busca los pivots en una lista de barras y los almacena. Encuentra los pivots con las condiciones predefinidas.

        Args:
            par_bars (List[Bar]): Lista de barras.
            par_current_price (float): Precio actual que se utilizará para encontrar los picos y valles.
            par_find_weak_pivots (bool, optional): Indica si se deben buscar pivots débiles en la lista.
        """      
        # Se almacena el precio con el que se buscaron pivots
        self.current_price = par_current_price
        # Se crea un array de barras con los datos que nos sirven, columna 0 = timestamp, columna 1 = high, columna 2 = low
        array_bars = np.array([(bar.timestamp, bar.high, bar.low) for bar in par_bars])
        if np.any(array_bars):
            # Escala de busqueda de pivotes, se multiplica por el atr
            scaling = 3
            # El porcentaje de diferencia que habra entre pivots
            slip_percentage = 0.1
            # Se busca el atr en caso de ser la primera vez que se llama el metodo
            if self.atr is None:
                array_bars_atr = np.array([(bar.high, bar.low, bar.close) for bar in par_bars[-15:]])
                # Busca el atr con un periodo de 14 dias
                self._found_atr(array_bars_atr)
                array_bars_atr = None
            
            # Se calcula el precio de rango de la busqueda y el slip que habra entre pivotes
            price_range = np.float16(scaling * self.atr)
            slip_ratio = (slip_percentage * self.atr)
            
            # Se calculan los pivotes fuertes que se encuentren en el rango de precio
            array_peaks, array_valleys= self._found_pivots_in_range(array_bars, par_current_price, price_range)
            
            # Hallamos los indices que cumplen las condiciones de pivots fuertes
            strong_peaks_indexes = np.where(array_peaks[:,1] > par_current_price)
            strong_valleys_indexes = np.where(array_valleys[:,2] < par_current_price)

            # Obtenemos los picos y valles filtrados usando los indices
            strong_peaks = array_peaks[strong_peaks_indexes]
            strong_valleys = array_valleys[strong_valleys_indexes]
            
            # Filtrar los pivots fuertes cercanos
            self.list_array_strong_peaks = np.array(self._filtered_strong_pivots(strong_peaks, 1, slip_ratio)[:self.number_pivots])
            self.list_array_strong_valleys = np.array(self._filtered_strong_pivots(strong_valleys, 2, slip_ratio)[:self.number_pivots])
                    
            # Si par_find_weak_pivots es verdadero entonces se procede a buscar pivots debiles
            if par_find_weak_pivots:
                # Encontramos la cantidad de pivots que faltan
                length_diference_peaks = self.number_pivots - len(self.list_array_strong_peaks)
                length_diference_valleys = self.number_pivots - len(self.list_array_strong_valleys)
                
                if length_diference_peaks > 0:
                    # Hallamos los indices que cumplen las condiciones de pivots debiles
                    weak_peaks_indexes = np.where(array_valleys[:,2] > par_current_price)
                    # Obtenemos los picos filtrados usando los indices
                    weak_peaks = array_valleys[weak_peaks_indexes]
                    # Encontrar y filtrar los pivots debiles cercanos                
                    self.list_array_weak_peaks = np.array(self._filtered_weak_pivots(weak_peaks, self.list_array_strong_peaks, 2, slip_ratio)[:length_diference_peaks])                   
                    
                if length_diference_valleys > 0:
                    # Hallamos los indices que cumplen las condiciones de pivots debiles
                    weak_valleys_indexes = np.where(array_peaks[:,1] < par_current_price)
                    # Obtenemos los picos y valles filtrados usando los indices
                    weak_valleys = array_peaks[weak_valleys_indexes]
                    # Encontrar y filtrar los pivots debiles cercanos   
                    self.list_array_weak_valleys = np.array(self._filtered_weak_pivots(weak_valleys, self.list_array_strong_valleys, 1, slip_ratio)[:length_diference_valleys])
             
    def _found_pivots_in_range(self, par_array_bars: np.ndarray, par_current_price: np.float16, par_price_range: np.float16) -> Tuple[np.ndarray, np.ndarray]:
        last_bar = par_array_bars[-1]
        first_bar = par_array_bars[0]
        par_array_bars = np.insert(par_array_bars, 0, first_bar, axis=0)
        par_array_bars = np.append(par_array_bars, [last_bar], axis=0)
                
        two_previous = par_array_bars[:-4]        # Array con dos elementos atras de los actuales
        one_previous = par_array_bars[1:-3]       # Array con un elemento atras de los actuales
        current = par_array_bars[2:-2]            # Array con los elementos actuales a comparar
        one_next = par_array_bars[3:-1]           # Array con un elemento adelante de los actuales 
        two_next = par_array_bars[4:]             # Array con dos elemento adelante de los actuales 

        peak_property_column = np.uint8(1) 
        valley_property_column = np.uint8(2)
        
        peak_filter_array = (
            (
                np.abs(current[:, peak_property_column] - par_current_price) < par_price_range
            ) &
            (
                (
                    (np.abs(current[:, peak_property_column] - par_current_price) > par_price_range) &
                    (current[:, peak_property_column] > two_previous[:, peak_property_column]) &
                    (current[:, peak_property_column] > one_previous[:, peak_property_column]) &
                    (current[:, peak_property_column] > one_next[:, peak_property_column])
                ) |
                (
                    (current[:, peak_property_column] > one_previous[:, peak_property_column]) &
                    (current[:, peak_property_column] > one_next[:, peak_property_column]) &
                    (current[:, peak_property_column] > two_next[:, peak_property_column])
                )
            )
        )  # Máscara (Matriz o array booleano) de elementos que cumplen el criterio
            
        valley_filter_array = (
            (
                np.abs(current[:, valley_property_column] - par_current_price) < par_price_range
            ) &
            (
                (
                    (current[:, valley_property_column] < two_previous[:, valley_property_column]) &
                    (current[:, valley_property_column] < one_previous[:, valley_property_column]) &
                    (current[:, valley_property_column] < one_next[:, valley_property_column])
                ) |
                (
                    (current[:, valley_property_column] < one_previous[:, valley_property_column]) &
                    (current[:, valley_property_column] < one_next[:, valley_property_column]) &
                    (current[:, valley_property_column] < two_next[:, valley_property_column])
                )
            )
        )  # Máscara (Matriz o array booleano) de elementos que cumplen el criterio
            
        peaks_in_range = current[peak_filter_array]    # Elementos que cumplen el criterio
        valleys_in_range = current[valley_filter_array]
            
        return peaks_in_range, valleys_in_range
        
    def _filtered_strong_pivots(self, par_list_array_pivots: np.ndarray, par_property_column: int, par_slip_ratio: float) -> List[np.ndarray]:
        """
        Filtra y retorna los pivots fuertes encontrados.

        Args:
            par_list_array_pivots (np.ndarray): Array de pivots.
            par_property_column (int): Columna que contiene el precio. 1 para picos (high), 2 para valles (low).
            par_slip_ratio (float): Rango mínimo de precio que debe haber entre pivots.

        Returns:
            List[np.ndarray]: Lista de pivots fuertes encontrados.
        """  

        # Ordenar el array  basado en par_property_column (índice 1 = high, indice 2 = low) 
        if par_property_column == 1:
            # Ordena de menor a mayor
            par_list_array_pivots = par_list_array_pivots[np.argsort(par_list_array_pivots[:, par_property_column])]
        else:
            # Ordena de mayor a menor
            par_list_array_pivots = par_list_array_pivots[np.argsort(-par_list_array_pivots[:, par_property_column])]

        filtered_pivots: List[np.ndarray] = []
        last_remove_pivot: np.ndarray = None

        for current_pivot in par_list_array_pivots:
            if filtered_pivots:
                last_pivot = filtered_pivots[-1]
                price_last_pivot = last_pivot[1]
                price_current_pivot = current_pivot[par_property_column]
                price_difference = abs(price_last_pivot - price_current_pivot)
                if price_difference < par_slip_ratio:
                    date_current_pivot = current_pivot[0]
                    date_last_pivot = last_pivot[0]
                    date_difference_in_days = (date_current_pivot - date_last_pivot).days
                    if -365 < date_difference_in_days :
                        if last_remove_pivot is not None:
                            filtered_pivots.pop()
                            price_last_remove_pivot = last_remove_pivot[1]
                            price_difference = abs(price_last_remove_pivot - price_current_pivot)
                            if price_difference > par_slip_ratio:
                                filtered_pivots.append(last_remove_pivot)
                                last_remove_pivot = None
                        else:
                            last_remove_pivot = filtered_pivots.pop()
                            
                        filtered_pivots.append(current_pivot[[0, par_property_column]])                                
                else:
                    last_remove_pivot = None
                    filtered_pivots.append(current_pivot[[0, par_property_column]])
            else:
                filtered_pivots.append(current_pivot[[0, par_property_column]]) 

        # Se ordenan los encontrados del mas reciente al mas antiguo
        filtered_pivots = sorted(filtered_pivots, key=lambda array_pivot: array_pivot[0], reverse=True)

        return filtered_pivots    
    
    def _filtered_weak_pivots(self, par_list_array_pivots: np.ndarray, par_array_strongs: np.ndarray, par_property_column: int, par_slip_ratio: float) -> List[np.ndarray]:
        """
        Filtra y retorna los pivots débiles encontrados.

        Args:
            par_list_array_pivots (np.ndarray): Array de pivots.
            par_list_array_strongs (np.ndarray): Array de los pivots fuertes encontrados.
            par_property_column (int): Columna que contiene el precio. 1 para picos (high), 2 para valles (low).
            par_slip_ratio (float): Rango mínimo de precio que debe haber entre pivots.

        Returns:
            List[np.ndarray]: Lista de pivots débiles encontrados.
        """
        # Ordenar el array  basado en par_property_column (índice 1 = high, indice 2 = low) 
        if par_property_column == 1:
            # Ordena de menor a mayor
            par_list_array_pivots = par_list_array_pivots[np.argsort(-par_list_array_pivots[:, par_property_column])]
        else:
            # Ordena de mayor a menor
            par_list_array_pivots = par_list_array_pivots[np.argsort(par_list_array_pivots[:, par_property_column])]

        # Lista para almacenar los picos o valles débiles filtrados
        filtered_auxiliary: List[np.ndarray] = []
        filtered_pivots: List[np.ndarray] = []
        repeat = 0

        for i, current_pivot in enumerate(par_list_array_pivots):
            if filtered_auxiliary:
                last_pivot = filtered_auxiliary[-1]
                price_last_pivot = last_pivot[1]
                price_current_pivot = current_pivot[par_property_column]
                price_difference = abs(price_last_pivot - price_current_pivot)

                # Comprobar si el pico o valle actual está dentro del rango de deslizamiento
                if price_difference < par_slip_ratio:
                    repeat += 1
                    date_current_pivot = current_pivot[0]
                    date_last_pivot = last_pivot[0]
                    date_difference_in_days = (date_current_pivot - date_last_pivot).days

                    # Comprobar si la diferencia de días entre los pivotes es menor a 7
                    if -365 < date_difference_in_days and filtered_auxiliary:
                        filtered_auxiliary.remove(last_pivot)
                        filtered_auxiliary.append(current_pivot[[0, par_property_column]])
                else:
                    if repeat > 2:
                        # Comprobar si el pico o valle débil está cerca del pico o valle fuerte
                        if len(par_array_strongs) > 0:
                            weak_in_strongs_indexes = np.where(abs(price_last_pivot - par_array_strongs[:, 1]) < par_slip_ratio)
                        else:
                            weak_in_strongs_indexes = np.empty(1)
                            
                        if weak_in_strongs_indexes[0].size>0:
                            # Eliminar el pico o valle de la lista de picos o valles débiles
                            filtered_auxiliary.remove(last_pivot)
                            break
                        else:
                            filtered_pivots.append(last_pivot)                              
                    else:
                        filtered_auxiliary.remove(last_pivot)
            else:
                repeat = 0
                filtered_auxiliary.append(current_pivot[[0, par_property_column]])

        if filtered_pivots:
            print('Pivots debiles encontrados')
            
        # Se ordenan los encontrados del mas reciente al mas antiguo
        filtered_pivots.sort(key=lambda array_pivot: array_pivot[0], reverse=True) 

        return filtered_pivots
    