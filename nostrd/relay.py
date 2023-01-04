import asyncio
from nostr.event import Event
from nostr.filter import Filter, Filters
from nostr.subscription import Subscription
from .proxy import Connection
from .message_types import MessageTypes
from .utils import (
    serialize_json,
    deserialize_json,
)
from .errors import InvalidMessage
from .bitcoin import check_public_key_funds


def parse_message(message):
    message = deserialize_json(message)

    if not isinstance(message, list):
        raise InvalidMessage

    if len(message) < 2:
        raise InvalidMessage

    if not isinstance(message[0], str):
        raise InvalidMessage

    message_type = message[0]
    if message_type not in MessageTypes.values:
        raise InvalidMessage

    if message_type == MessageTypes.EVENT.value:
        if len(message) != 2:
            raise InvalidMessage

        event_dict = message[1]
        event_dict['public_key'] = event_dict.pop('pubkey')
        event_dict['signature'] = event_dict.pop('sig')
        event = Event(**event_dict)

        funded_address = check_public_key_funds(event.public_key)
        if not funded_address:
            raise InvalidMessage('Public key not funded.')

        return {
            'type': MessageTypes.EVENT,
            'event': event,
        }

    if message_type == MessageTypes.REQUEST.value:
        if len(message) < 2:
            raise InvalidMessage

        subscription_id = message[1]
        if not isinstance(subscription_id, str):
            raise InvalidMessage('Invalid subscription id.')

        filter_dicts = message[2:]
        filters = Filters([Filter(**filter) for filter in filter_dicts])

        return {
            'type': MessageTypes.REQUEST,
            'subscription': Subscription(subscription_id, filters)
        }

    if message_type == MessageTypes.CLOSE.value:
        if len(message) != 2:
            raise InvalidMessage

        subscription_id = message[1]
        if not isinstance(subscription_id, str):
            raise InvalidMessage('Invalid subscription id.')

        return {
            'type': MessageTypes.CLOSE,
            'subscription': Subscription(subscription_id),
        }

    raise InvalidMessage


async def handler(websocket):
    subscriptions = {}
    base_connection = Connection()

    async def subscription_handler(subscription):
        async for raw_event in subscription.listen():
            await websocket.send(raw_event)

    async for message in websocket:
        try:
            result = parse_message(message)

            if result['type'] == MessageTypes.EVENT:
                base_connection.send(result['event'])

            if result['type'] == MessageTypes.CLOSE:
                subscription_id = result['subscription'].id
                if subscription_id not in subscriptions:
                    await websocket.send(
                        serialize_json(['NOTICE', 'Unknown subscription.'])
                    )
                    websocket.close()
                await subscriptions[subscription_id].close()

            if result['type'] == MessageTypes.REQUEST:
                subscription_id = result['subscription'].id
                filters = result['subscription'].filters

                if subscription_id not in subscriptions:
                    subscription = Connection()
                    subscription.subscribe(subscription_id, filters)
                    subscriptions[subscription_id] = subscription
                    asyncio.create_task(subscription_handler(subscription))

        except (KeyError, InvalidMessage) as error:
            message = ['NOTICE', f'Invalid message: {str(error)}']
            await websocket.send(serialize_json(message))
