import asyncio
import struct
import base64

class ClientError(Exception):
    pass

class InvalidPassword(Exception):
    pass

class TimeoutError(Exception):
    pass

class BaseRCON:
    def __init__(self, host: str, port: int, password: str, timeout: int = 15):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self._auth = False
        self._reader = None
        self._writer = None

    async def __aenter__(self):
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout
            )
            await self._authenticate()
        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout while connecting to {self.host}:{self.port}")
        except Exception as e:
            raise ClientError(f"Error connecting to {self.host}:{self.port} - {e}")
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
                self._auth = True
            except Exception as e:
                raise InvalidPassword(f"Authentication failed - {e}")

    async def _read_data(self, leng: int) -> bytes:
        try:
            return await asyncio.wait_for(self._reader.read(leng), timeout=self.timeout)
        except asyncio.TimeoutError:
            raise TimeoutError("Timeout while reading data from server")

    async def _send(self, typen: int, message: str) -> str:
        if not self._writer:
            raise ClientError('Not connected.')

        encoded_message = message.encode('utf-8')
        out = struct.pack('<li', 0, typen) + encoded_message + b'\x00\x00'
        out_len = struct.pack('<i', len(out))
        self._writer.write(out_len + out)
        await self._writer.drain()

        in_len = struct.unpack('<i', await self._read_data(4))[0]
        in_payload = await self._read_data(in_len)

        in_id, _ = struct.unpack('<ii', in_payload[:8])
        in_data, in_padd = in_payload[8:-2], in_payload[-2:]

        if in_padd != b'\x00\x00':
            raise ClientError('Incorrect padding.')
        if in_id == -1:
            raise InvalidPassword('Incorrect password.')

        return in_data.decode('utf-8', errors='replace')

class GameRCON(BaseRCON):
    async def send(self, cmd: str) -> str:
        if not self._auth:
            raise ClientError("Client not authenticated.")
        return await self._send(2, cmd)

class GameRCONBase64(BaseRCON):
    async def send(self, cmd: str) -> str:
        if not self._auth:
            raise ClientError("Client not authenticated.")
        encoded_cmd = base64.b64encode(cmd.encode('utf-8')).decode('utf-8')
        result = await self._send(2, encoded_cmd)
        try:
            return base64.b64decode(result.encode('utf-8')).decode('utf-8')
        except Exception:
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
        
async def main():
    async with GameRCON("127.0.0.1", 25575, "pass") as rcon:
        response = await rcon.send("ListPlayers")
        print(response)

if __name__ == "__main__":
    asyncio.run(main())