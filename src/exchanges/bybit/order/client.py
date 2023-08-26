import asyncio
import hashlib
import hmac
import json
import time

import aiohttp

from src.exchanges.bybit.order.endpoints import BaseEndpoints


class Client:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self.base_endpoint = BaseEndpoints.MAINNET1
        self.api_key = api_key
        self.api_secret = api_secret
        self.recvWindow = "5000"
        self.timestamp = str(int(time.time() * 1000))

    def _sign(self, payload: str) -> dict:
        param_str = "".join([self.timestamp, self.api_key, self.recvWindow, payload])
        header = {
            "X-BAPI-TIMESTAMP": self.timestamp,
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-RECV-WINDOW": self.recvWindow,
        }
        hash_signature = hmac.new(bytes(self.api_secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
        header["X-BAPI-SIGN"] = hash_signature.hexdigest()
        return header

    async def submit(self, session: aiohttp.ClientSession, endpoint: str, payload: dict):
        payload_str = json.dumps(payload)
        signed_header = self._sign(payload_str)
        endpoint = self.base_endpoint + endpoint

        max_retries = 3

        for attempt in range(max_retries):
            try:
                req = await session.request("POST", endpoint, headers=signed_header, data=payload_str)
                response_data = await req.text()
                response = json.loads(response_data)

                ret_msg = response.get("retMsg", "")
                if ret_msg in ["OK", "success"]:
                    return {"return": response["result"], "latency": int(response["time"]) - int(self.timestamp)}
                elif ret_msg == "too many visit":
                    print("Rate limits hit, cooling off...")
                    break
                elif response.get("retCode") == "110001":
                    print(f"Msg: {ret_msg}, Payload: {payload_str}")
                    break
                else:
                    print(f"Msg: {ret_msg}, Payload: {payload_str}")
                    break

            except Exception as e:
                print(f"Error at {endpoint}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(attempt + 1)
                    self.timestamp = str(int(time.time() * 1000))
                    signed_header = self._sign(payload_str)
                else:
                    raise


# Usage
# async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=10)) as session:
#     client = Client(api_key="your_api_key", api_secret="your_api_secret")
#     await client.submit(session, "/some_endpoint", {"key": "value"})
