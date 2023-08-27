from .enums import Exchange, Type, Side, Status

class Order:
    """
    Representa una orden de compra o venta de un activo en un exchange específico.
    
    Attributes:
        id (Optional[str]): El identificador único de la orden. Inicialmente es None.
        status (Status): El estado de la orden (por ejemplo, Filled, Open, Canceled, etc.). Inicialmente es None.
        symbol (str): El símbolo del activo asociado a la orden.
        price (float): El precio de la orden.
        quantity (int): La cantidad de activos en la orden.
        exchange (Exchange): El exchange donde se realizará la orden.
        type (Type): El tipo de orden.
        side (Side): El lado de la orden.
    """

    def __init__(self, symbol: str, price: float, quantity: int, exchange: Exchange, type: Type, side: Side) -> None:
        """
        Inicializa una nueva instancia de la clase Order.

        Args:
            symbol (str): El símbolo del activo asociado a la orden.
            price (float): El precio de la orden.
            quantity (int): La cantidad de activos en la orden.
            exchange (Exchange): El exchange donde se realizará la orden.
            type (Type): El tipo de orden.
            side (Side): El lado de la orden
        """
        self.id = None
        self.status = None
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.exchange = exchange
        self.type = type
        self.side = side

    def set_id(self, order_id: str) -> None:
        """
        Establece el identificador único de la orden.

        Args:
            order_id (str): El identificador único de la orden.
        """
        self.id = order_id

    def set_status(self, status: Status) -> None:
        """
        Establece el estado de la orden.

        Args:
            status (Status): El estado de la orden (por ejemplo, Filled, Open, Canceled, etc.).
        """
        self.status = status
        
    def convert_to_close_position(self):
        """Convertir la orden a una operación de cierre de posición.
        Esta función modifica la orden existente para convertirla en una operación de cierre de posición.
        Cambia el tipo de orden a 'MARKET' y el lado de la operación a 'BUY' si la orden era originalmente de venta ('SELL'),
        o cambia el lado a 'SELL' si la orden era originalmente de compra ('BUY').
        
        Nota:
            Antes de llamar a esta función, asegúrate de que la orden sea válida y esté abierta.

        """
        self.type = Type.MARKET
        self.side = Side.BUY if self.side == Side.SELL else Side.SELL
        self.status = None
        self.id = None




        