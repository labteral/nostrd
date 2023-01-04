from os import environ

MIN_PUBLIC_KEY_SATS = environ.get('NOSTRD_MIN_PUBLIC_KEY_SATS', 25000)
RELAY_URL = environ.get('NOSTRD_RELAY_URL', 'wss://relay.damus.io')
