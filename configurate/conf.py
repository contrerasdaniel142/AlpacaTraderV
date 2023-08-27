import os
from dotenv import load_dotenv
from alpaca.data.enums import DataFeed
from alpaca.trading.enums import AssetStatus
from alpaca.trading.enums import AssetClass
from alpaca.common.enums import BaseURL 

load_dotenv()

alpaca_api_key_id= os.getenv("ALPACA_API_KEY_ID")
alpaca_api_secret_key= os.getenv("ALPACA_API_SECRET_KEY")
openai_api_key= os.getenv("OPENAI_API_KEY")

#Variables globales
#Conexion
alpaca_data_feed = DataFeed.IEX     #replace to 'SIP' if you have PRO subscription or IEX if is not
#Consultar simbolos
alpaca_symbol_status = AssetStatus.ACTIVE
alpaca_asset_class = AssetClass.US_EQUITY   

