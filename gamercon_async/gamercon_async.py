import asyncio
import struct
import logging
from socket import socket, AF_INET, SOCK_STREAM
from enum import Enum
from random import randint
from typing import NamedTuple

class ClientError(Exception):
    pass

class InvalidPassword(Exception):
    pass

class ConnectionError(Exception):
    pass

class CommandExecutionError(Exception):
    pass

class EmptyResponse(Exception):
    pass

class LittleEndianSignedInt32(int):
    MIN = -2_147_483_648
    MAX = 2_147_483_647

    def __init__(self, value):
        if not self.MIN <= value <= self.MAX:
            raise ValueError("Signed int32 out of bounds:", value)
        super().__init__()

    def __bytes__(self):
        return self.to_bytes(4, "little", signed=True)

    @classmethod
    def from_bytes(cls, b):
        return cls(int.from_bytes(b, "little", signed=True))

class Type(Enum):
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0

    def __bytes__(self):
        return LittleEndianSignedInt32(self.value).__bytes__()

class Packet(NamedTuple):
    id: LittleEndianSignedInt32
    type: Type
    payload: bytes
    terminator: bytes = b"\x00\x00"

    def __bytes__(self):
        payload = bytes(self.id) + bytes(self.type) + self.payload + self.terminator
        size = LittleEndianSignedInt32(len(payload))
        return bytes(size) + payload

    @classmethod
    def make_command(cls, command, encoding='utf-8'):
        return cls(LittleEndianSignedInt32(randint(0, LittleEndianSignedInt32.MAX)), Type.SERVERDATA_EXECCOMMAND, command.encode(encoding))

    @classmethod
    def make_login(cls, password, encoding='utf-8'):
        return cls(LittleEndianSignedInt32(randint(0, LittleEndianSignedInt32.MAX)), Type.SERVERDATA_AUTH, password.encode(encoding))

class GameRCON:
    def __init__(self, host, port, password, timeout=15):
        self.host = host
        self.port = int(port)
        self.password = password
        self.timeout = timeout
        self._auth = False
        self._reader = None
        self._writer = None

    async def __aenter__(self):
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), self.timeout)
            await self._authenticate()
            return self
        except asyncio.TimeoutError as e:
            logging.error(f"Timeout error: {e}")
            raise ConnectionError(f"Connection to {self.host}:{self.port} timed out.")
        except Exception as e:
            logging.error(f"Error connecting: {e}")
            raise ConnectionError(f"Error connecting to {self.host}:{self.port} - {e}")

    async def __aexit__(self, exc_type, exc, tb):
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

    async def _authenticate(self):
        login_packet = Packet.make_login(self.password)
        await self._send_packet(login_packet)
        response_packet = await self._read_packet()
        if response_packet.id == -1:
            raise InvalidPassword()
        self._auth = True

    async def _send_packet(self, packet):
        if not self._auth and packet.type != Type.SERVERDATA_AUTH:
            raise ClientError('Client not authenticated.')
        if not self._writer:
            raise ClientError('Not connected.')

        self._writer.write(bytes(packet))
        await self._writer.drain()

    async def _read_packet(self):
        size_data = await asyncio.wait_for(self._reader.read(4), self.timeout)
        if not size_data:
            raise EmptyResponse()

        size = LittleEndianSignedInt32.from_bytes(size_data)
        packet_data = await asyncio.wait_for(self._reader.read(size), self.timeout)
        if not packet_data:
            raise EmptyResponse()

        id = LittleEndianSignedInt32.from_bytes(packet_data[:4])
        type = Type(LittleEndianSignedInt32.from_bytes(packet_data[4:8]))
        payload = packet_data[8:-2]
        return Packet(id, type, payload)

    async def send(self, cmd):
        if not self._auth:
            raise ClientError("Not authenticated with RCON server.")

        command_packet = Packet.make_command(cmd)
        await self._send_packet(command_packet)
        response_packet = await self._read_packet()

        if response_packet.id == -1:
            raise InvalidPassword()
        if response_packet.type != Type.SERVERDATA_RESPONSE_VALUE:
            raise CommandExecutionError("Unexpected response type.")

        return response_packet.payload.decode('utf-8')

class EvrimaRCON:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = 30

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.wait_for(asyncio.open_connection(self.host, self.port), timeout=self.timeout)

            payload = bytes('\x01', 'utf-8') + self.password.encode() + bytes('\x00', 'utf-8')
            self.writer.write(payload)
            await self.writer.drain()

            response = await asyncio.wait_for(self.reader.read(1024), timeout=self.timeout)
            if "Accepted" not in str(response):
                self.writer.close()
                await self.writer.wait_closed()
                return "Login failed"

            return "Connected"
        except asyncio.TimeoutError:
            return "Connection timed out"
        except asyncio.CancelledError:
            return "Connection cancelled"
        except Exception as e:
            return f"Socket error: {e}"

    async def send_command(self, command_bytes):
        try:
            self.writer.write(command_bytes)
            await asyncio.ensure_future(self.writer.drain())

            response = await asyncio.wait_for(self.reader.read(1024), timeout=self.timeout)
            return response.decode()

        except Exception as e:
            return f"Error sending command: {e}"
        
async def main():
    async with GameRCON("127.0.0.1", 25575, "pass") as rcon:
        response = await rcon.send("ListPlayers")
        print(response)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()