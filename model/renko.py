import pandas as pd
from pandas_datareader import data as pdr
import mplfinance as fplt


class vRenko:
    def __init__(self, brick_size, rates):
        self.brick_size = brick_size
        self.bricks=[]
        self.dfRates = self._convert_data_to_df(rates)
        self.dfBricks = None
        self._dfBricks_to_draw = None
        self._Find_first_ideal_brick()
        
    def _convert_data_to_df(self, data):
        # Convertir los datos de Renko a un DataFrame de pandas
        df = pd.DataFrame(data)
        # Convertir la columna "time" a formato de fecha y hora
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
        
    def _Find_first_ideal_brick(self):
        # Buscar el primer valor que cumpla las condiciones de low y high
        for index, row in self.dfRates.iterrows():
            if (row['high'] - row['low']) >= self.brick_size * 3:
                primer_valor = row
                break
        # Obtener el índice del primer valor que cumple las condiciones
        indice = self.dfRates.index[self.dfRates['time'] == primer_valor['time']][0]
        # Recortar el DataFrame df a partir del primer valor
        self.dfRates = self.dfRates.iloc[indice:]
        # Ajustar el 'open' del valor que cumple las condiciones para que empiece en en el brick size
        self.dfRates = self.dfRates.reset_index(drop=True)
    
    def price_adjustment_to_up(self, price):
        if price - int(price) < self.brick_size:
            price = int(price) + self.brick_size
        elif price - int(price) > self.brick_size:
            price = int(price) + self.brick_size * 2
        return price
    
    def price_adjustment_to_down(self, price):
        if price - int(price) < self.brick_size:
            price = int(price)
        elif price - int(price) > self.brick_size:
            price = int(price) + self.brick_size
        return price
            
    def create_renko(self):
        index = 0
        fcount = 0
        while index < len(self.dfRates):
            last_brick = self.bricks[-1] if  len(self.bricks) > 0 else last_brick if index >= 1 else {}
            if fcount == 0:
                current_bar = self.dfRates.iloc[index].copy()
                if current_bar["open"] < current_bar["close"]:
                    if self.price_adjustment_to_down(current_bar["open"]) >= current_bar["low"]:
                        current_bar["open"] = self.price_adjustment_to_down(current_bar["open"])
                    elif self.price_adjustment_to_up(current_bar["open"]) <= current_bar["high"]:
                        current_bar["open"] = self.price_adjustment_to_up(current_bar["open"])
                    delta = current_bar["high"] - current_bar["open"]  
                elif current_bar["open"] > current_bar["close"]:
                    if self.price_adjustment_to_up(current_bar["open"]) <= current_bar["high"]:
                        current_bar["open"] = self.price_adjustment_to_up(current_bar["open"])
                    elif self.price_adjustment_to_down(current_bar["open"]) >= current_bar["low"]:
                        current_bar["open"] = self.price_adjustment_to_down(current_bar["open"])
                    delta = current_bar["open"] - current_bar["low"]      
                if not last_brick:
                    last_brick["open"] = current_bar["open"] 
                delta = delta + abs(current_bar["open"] - last_brick["open"])  
                fcount = int(delta / self.brick_size)
                index = index + 1
            else:
                special_brick_up = False
                special_brick_down = False                    
                if len(self.bricks) == 0:
                    if current_bar["open"] + self.brick_size <= current_bar["high"]:
                        type="up"
                    elif current_bar["open"] - self.brick_size >= current_bar["low"]:
                        type = "down"
                    first_open_price = current_bar["open"]
                    special_brick_down = first_open_price - self.brick_size >= current_bar["low"] and first_open_price + self.brick_size < current_bar["high"]
                    special_brick_up = first_open_price + self.brick_size <= current_bar["high"] and first_open_price - self.brick_size > current_bar["low"]
                    
                elif last_brick["type"] == "up":
                    if last_brick["open"] - self.brick_size >= current_bar["low"] and last_brick["close"] < current_bar["high"]:
                        special_brick_down = True
                    elif  last_brick["close"] + self.brick_size <= current_bar["high"] and last_brick["open"] > current_bar["low"]:
                        special_brick_up = True
                    elif last_brick["close"] + self.brick_size  <= current_bar["close"]:
                        type = "up"
                    elif last_brick["open"] - self.brick_size >= current_bar["close"]:
                        type = "down"
                    
                elif last_brick["type"] == "down":
                    if last_brick["close"] - self.brick_size >= current_bar["low"] and last_brick["open"] < current_bar["high"]:
                        special_brick_down = True
                    elif last_brick["open"] + self.brick_size <= current_bar["high"] and last_brick["close"] > current_bar["low"]:
                        special_brick_up = True
                    if last_brick["open"] + self.brick_size <= current_bar["close"]:
                        type = "up"
                    elif last_brick["close"] - self.brick_size >= current_bar["close"]:
                        type = "down"
                    
                if special_brick_up:
                    self._add_brick("up", current_bar["time"], first_open_price, current_bar["low"])
                elif special_brick_down:
                    self._add_brick("down", current_bar["time"], first_open_price, current_bar["high"])
                elif fcount>1:
                    self._add_brick(type, current_bar["time"], first_open_price)
                elif type == "up":
                    self._add_brick(type, current_bar["time"], first_open_price, current_bar["low"])
                elif type == "down":
                    self._add_brick(type, current_bar["time"], first_open_price, current_bar["high"])  
                
                fcount -= 1
                
                last_brick = self.bricks[-1]
                if len(self.bricks) > 1:
                    if last_brick["time"] != self.bricks[-2]["time"]:
                        if self.bricks[-2]["type"] == "down" and last_brick["type"] == "down":
                            if last_brick["high"]>self.bricks[-2]["high"]:
                                self.bricks[-2]["high"] = last_brick["high"]
                                last_brick["high"] = last_brick["open"]
                        elif self.bricks[-2]["type"] == "up" and last_brick["type"] == "up":
                            if last_brick["low"]<self.bricks[-2]["low"]:
                                self.bricks[-2]["low"] = last_brick["low"]
                                last_brick["low"] = last_brick["open"]
                            
        self.dfBricks = self._convert_data_to_df(self.bricks)
        self._dfBricks_to_draw = self.dfBricks.copy()
        self._dfBricks_to_draw.index = pd.to_datetime(self._dfBricks_to_draw.index)
                      
    def _add_brick(self, type: str, time, first_open_price: float= None, wick: float = None):
        if len(self.bricks) == 0:
            if type == "up":
                open_price = first_open_price
                close_price = first_open_price + self.brick_size
                high_price = first_open_price + self.brick_size
                low_price = first_open_price if wick == None else wick
            elif type == "down":
                open_price = first_open_price
                close_price = first_open_price - self.brick_size
                high_price = first_open_price if wick == None else wick
                low_price = first_open_price - self.brick_size
        else:
            last_brick = self.bricks[-1]
            if type == "up":
                if last_brick["type"] in ["up"]:
                    open_price = last_brick["close"]
                    close_price = last_brick["close"] + self.brick_size 
                    high_price = last_brick["close"] + self.brick_size
                    low_price = last_brick["close"] if wick == None  else wick
                elif last_brick["type"] == "down":
                    open_price = last_brick["open"]
                    close_price = last_brick["open"] + self.brick_size
                    high_price = last_brick["open"] + self.brick_size 
                    low_price = last_brick["open"] if wick == None  else wick
            elif type == "down":
                if last_brick["type"] == "up":
                    open_price = last_brick["open"]
                    close_price = last_brick["open"] - self.brick_size
                    high_price = last_brick["open"] if wick == None  else wick
                    low_price = last_brick["open"] - self.brick_size 
                elif last_brick["type"] in ["down"]:
                    open_price = last_brick["close"]
                    close_price = last_brick["close"] - self.brick_size
                    high_price = last_brick["close"] if wick == None  else wick
                    low_price = last_brick["close"] - self.brick_size 
        
        new_brick = {"time": time, "type": type, "open": open_price, "close": close_price, "high": high_price, "low": low_price}
        self.bricks.append(new_brick)


    def draw_chart(self):
        # Call the fplt.plot function and execute
        fplt.plot(self._dfBricks_to_draw, type='renko', renko_params=dict(brick_size=self.brick_size), style='yahoo', figsize=(18, 7), title="RENKO")
