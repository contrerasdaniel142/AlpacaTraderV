
class Exchange:
    """Clase que define constantes para representar diferentes casas de bolsa o mercados financieros.

    Atributos:
        ARCA (str): Representa la casa de bolsa ARCA.
        ARCAMPLA (str): Representa la casa de bolsa ARCA Amplify.
        BATS (str): Representa la casa de bolsa BATS.
        EDGA (str): Representa la casa de bolsa EDGA.
        EDGX (str): Representa la casa de bolsa EDGX.
        NSDQ (str): Representa la casa de bolsa NASDAQ.
        NSDQTFTY (str): Representa la casa de bolsa NASDAQ TotalView-ITCH.
        NSDQSAVE (str): Representa la casa de bolsa NASDAQ Save.
        NSDQMOO (str): Representa la casa de bolsa NASDAQ Market-on-Open.
        NSDQLOO (str): Representa la casa de bolsa NASDAQ Limit-on-Open.
        NSDQMOC (str): Representa la casa de bolsa NASDAQ Market-on-Close.
        NYSE (str): Representa la casa de bolsa New York Stock Exchange (NYSE).
        NYSEMOO (str): Representa la casa de bolsa NYSE Market-on-Open.
        NYSELOO (str): Representa la casa de bolsa NYSE Limit-on-Open.
        NYSEMOC (str): Representa la casa de bolsa NYSE Market-on-Close.
        COVMID (str): Representa la casa de bolsa COV Midpoint Peg.
        SMARTMID (str): Representa la casa de bolsa Smart Midpoint Peg.
        XFINDERMID (str): Representa la casa de bolsa XFinder Midpoint Peg.
        AMEXMOO (str): Representa la casa de bolsa NYSE American (AMEX) Market-on-Open.
        AMEXMOC (str): Representa la casa de bolsa NYSE American (AMEX) Market-on-Close.
        AMEXLOO (str): Representa la casa de bolsa NYSE American (AMEX) Limit-on-Open.
        AMEXLOC (str): Representa la casa de bolsa NYSE American (AMEX) Limit-on-Close.
        MEMX (str): Representa la casa de bolsa MEMX (Members Exchange).

    """
    ARCA = "arca"
    ARCAMPLA = "arcampla"
    BATS = "bats"
    EDGA = "edga"
    EDGX = "edgx"
    NSDQ = "nsdq"
    NSDQTFTY = "nsdqtfty"
    NSDQSAVE = "nsdqsave"
    NSDQMOO = "nsdqmoo"
    NSDQLOO = "nsdqloo"
    NSDQMOC = "nsdqmoc"
    NYSE = "nyse"
    NYSEMOO = "nysemoo"
    NYSELOO = "nyseloo"
    NYSEMOC = "nysemoc"
    COVMID = "covmid"
    SMARTMID = "smartmid"
    XFINDERMID = "xfindermid"
    AMEXMOO = "amexmoo"
    AMEXMOC = "amexmoc"
    AMEXLOO = "amexloo"
    AMEXLOC = "amexloc"
    MEMX = "memx"

class Type:
    """Clase que define constantes para los tipos de órdenes en un mercado financiero.

    Atributos:
        MARKET (str): Representa el tipo de orden 'market', que es una orden de mercado.
        LIMIT (str): Representa el tipo de orden 'limit', que es una orden limitada.
        STOP (str): Representa el tipo de orden 'stop', que es una orden de stop-market.
                    (Nota: las órdenes de stop-limit aún no son compatibles).

    """   
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    
class Side:
    """Clase que define constantes para representar los lados o direcciones de una operación en un mercado financiero.

    Atributos:
        BUY (str): Representa el lado 'compra' de una operación.
        SELL (str): Representa el lado 'venta' de una operación.
        SSHRT (str): Representa el lado 'venta en corto' de una operación.
    """
    BUY = "buy"
    SELL = "sell"
    SSHRT = "sshrt"

class BaseUrl:
    """Clase que define constantes para las URLs base en diferentes entornos.

    Atributos:
        LOCALHOST (str): Representa la URL base para el entorno local con el puerto 5005.
    """
    LOCALHOST = "http://localhost:5005"
    
class Status:
    """Clase que define constantes para representar los estados de una orden en un mercado financiero.

    Atributos:
        FILLED (str): Representa el estado 'Filled', que indica que la orden ha sido completada.
        CANCELED (str): Representa el estado 'Canceled', que indica que la orden ha sido cancelada.
        OPEN (str): Representa el estado 'PendingNew', que indica que la orden es nueva o activa y aún no se ha completado.
    """
    FILLED = "Filled"
    CANCELED = "Canceled"
    OPEN = "PendingNew"