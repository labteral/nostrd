import requests
import bech32
from digsig.hashing import hash_message, HashFunctions
from enum import Enum
from . import env


class BitcoinInspectorInterface:

    def balance(self, address):
        raise NotImplementedError


class BlockstreamInspector(BitcoinInspectorInterface):

    def __init__(self):
        self._base_url = "https://blockstream.info/api"

    def balance(self, address):
        url = f"{self._base_url}/address/{address}"
        data = requests.get(url).json()['chain_stats']
        return data['funded_txo_sum'] - data['spent_txo_sum']


class BitcoinInspector:
    # Using the Blockstream API for demonstration purposes only
    def __init__(self, inspector_class=None):
        if inspector_class is None:
            inspector_class = BlockstreamInspector

        if issubclass(inspector_class, BitcoinInspectorInterface):
            self._inspector = inspector_class()

    def balance(self, address):
        return self._inspector.balance(address)


class WitnessProgram(Enum):
    P2WSH = 0
    P2TR = 1


class HumanReadablePart(Enum):
    MAINNET = 'bc'
    TESTNET = 'tb'


def get_address_from_public_key(
    prefix: bytes,
    public_key: bytes,
    human_readable_part: str = None,
    witness_program: int = None
):
    if human_readable_part is None:
        human_readable_part = HumanReadablePart.MAINNET.value

    if witness_program is None:
        witness_program = WitnessProgram.P2WSH.value

    address = hash_message(prefix + public_key, HashFunctions.SHA256)
    address = hash_message(address, HashFunctions.RIPEMD160)

    address = bech32.encode(
        human_readable_part,
        witness_program,
        address,
    )

    return address


inspector = BitcoinInspector()


def check_public_key_funds(public_key: str):
    funded_address = False
    for prefix in [b'\02', b'\03']:
        address = get_address_from_public_key(
            prefix,
            bytes.fromhex(public_key),
        )
        balance = inspector.balance(address)
        if balance >= env.MIN_PUBLIC_KEY_SATS:
            print(
                f"Public key {public_key} is funded at {address} "
                f"with {balance} sats."
            )
            funded_address = True
    return funded_address
