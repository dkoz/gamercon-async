import asyncio
import struct

class ClientError(Exception):
    pass

class InvalidPassword(Exception):
    pass

class GameRCON:
    def __init__(self, host, port, password):
        self.host = host
        self.port = int(port)
        self.password = password
        self._auth = None
        self._reader = None
        self._writer = None

    async def __aenter__(self):
        if not self._writer:
            try:
                self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
            except Exception as e:
                raise ClientError(f"Error connecting to {self.host}:{self.port} - {e}")
            await self._authenticate()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def _authenticate(self):
        if not self._auth:
            try:
                await self._send(3, self.password)
            except Exception as e:
                raise InvalidPassword(f"Authentication failed - {e}")
            self._auth = True

    async def _read_data(self, leng):
        data = b''
        while len(data) < leng:
            data += await self._reader.read(leng - len(data))
        return data

    async def _send(self, typen, message):
        if not self._writer:
            raise ClientError('Not connected.')

        out = struct.pack('<li', 0, typen) + message.encode('utf8') + b'\x00\x00'
        out_len = struct.pack('<i', len(out))
        self._writer.write(out_len + out)

        in_len = struct.unpack('<i', await self._read_data(4))
        in_payload = await self._read_data(in_len[0])

        in_id, in_type = struct.unpack('<ii', in_payload[:8])
        in_data, in_padd = in_payload[8:-2], in_payload[-2:]

        if in_padd != b'\x00\x00':
            raise ClientError('Incorrect padding.')
        if in_id == -1:
            raise InvalidPassword('Incorrect password.')

        data = in_data.decode('utf8')
        return data

    async def send(self, cmd):
        if not self._auth:
            raise ClientError("Client not authenticated.")

        result = await self._send(2, cmd)
        return result

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