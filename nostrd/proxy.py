import websocket
from .message_types import MessageTypes
from .utils import serialize_json
from .env import RELAY_URL


class Connection:

    def __init__(self, url: str = None):
        self._url = url or RELAY_URL
        self._websocket = None
        self._subscription_id = None
        self._filters = None
        self._closed = None

    def connect(self):
        if self._websocket is None:
            self._websocket = websocket.create_connection(self._url)

    def send(self, event):
        self.connect()
        self._websocket.send(serialize_json(event.to_json_object()))

    def subscribe(self, subscription_id, filters):
        self._subscription_id = subscription_id
        self._filters = filters

    async def close(self):
        if self._subscription_id is None:
            raise ValueError

        self._closed = True
        request = [MessageTypes.CLOSE.value, self._subscription_id]
        self._websocket.send(serialize_json(request))
        self._websocket.close()

    async def listen(self):
        if self._subscription_id is None:
            raise ValueError

        self.connect()

        request = [
            MessageTypes.REQUEST.value,
            self._subscription_id,
        ] + self._filters.to_json_array()

        if len(request) == 2:
            request.append({})  # Make request compatible with existing relays
        serialized_request = serialize_json(request)
        self._websocket.send(serialized_request)

        self._closed = False
        while not self._closed:
            response = self._websocket.recv()
            yield response
