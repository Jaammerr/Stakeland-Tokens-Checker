import asyncio
import random
import pyuseragents

from typing import Literal
from loguru import logger
from web3 import Web3, Account

from curl_cffi.requests import AsyncSession
from models import Account as MemeAccount, ExportAccountData

from loader import config
from .wallet import Wallet
from .exceptions.base import MemeError

Account.enable_unaudited_hdwallet_features()


class MemeChecker:
    API_URL = "https://memestaking-api.stakeland.com"

    def __init__(self, account: MemeAccount):
        super().__init__()
        self.account = account
        self.session = self.setup_session()
        self.web3 = Web3(Web3.HTTPProvider(config.eth_rpc))

        self.wallet = Wallet(account.pk_or_mnemonic)

    @property
    def address(self) -> str:
        return self.wallet.address

    @property
    def get_proxy(self) -> str:
        values = self.account.proxy.replace("http://", "").replace("@", ":").split(":")
        proxy_str = f"{values[2]}:{values[3]}:{values[0]}:{values[1]}"
        return proxy_str

    def setup_session(self):
        session = AsyncSession()
        session.headers = {
            "authority": "memestaking-api.stakeland.com",
            "accept": "application/json",
            "accept-language": "fr-FR,fr;q=0.9",
            "origin": "https://www.stakeland.com",
            "user-agent": pyuseragents.random(),
        }
        session.proxies = {
            "http": self.account.proxy,
            "https": self.account.proxy,
        }
        session.verify = False

        return session

    async def send_request(
        self,
        request_type: Literal["POST", "GET"] = "POST",
        method: str = None,
        json_data: dict = None,
        params: dict = None,
        url: str = None,
        verify: bool = True,
    ):
        def _verify_response(_response: dict) -> dict:
            if "success" in _response:
                if not _response["success"]:
                    raise MemeError({"error_message": _response.get("error")})

            return _response

        if request_type == "POST":
            if not url:
                response = await self.session.post(
                    f"{self.API_URL}{method}", json=json_data, params=params
                )

            else:
                response = await self.session.post(url, json=json_data, params=params)

        else:
            if not url:
                response = await self.session.get(
                    f"{self.API_URL}{method}", params=params
                )

            else:
                response = await self.session.get(url, params=params)

        response.raise_for_status()
        if verify:
            return _verify_response(response.json())
        return response.json()

    async def wallet_info(self) -> dict:
        response = await self.send_request(
            request_type="GET", method=f"/wallet/info/{self.address}"
        )
        return response

    async def auth(self) -> bool:
        for _ in range(3):
            try:
                signature_data = self.wallet.get_signature_data()

                json_data = {
                    "address": self.address,
                    "message": signature_data.message,
                    "signature": signature_data.signature,
                }

                response = await self.send_request(
                    request_type="POST", method="/wallet/auth", json_data=json_data
                )
                if not response.get("accessToken"):
                    raise Exception("Auth failed")

                self.session.headers["authorization"] = (
                    f"Bearer {response['accessToken']}"
                )
                logger.success(f"Account: {self.address} | Authenticated successfully")
                return True

            except Exception as error:
                logger.error(
                    f"Account: {self.address} | Failed to authenticate | Error: {error} | Retrying.."
                )
                await self.process_sleep()

        logger.error(
            f"Account: {self.address} | Failed to authenticate | Max retries exceeded"
        )


    async def process_sleep(self):
        delay = random.randint(1, 5)
        logger.debug(
            f"Account: {self.address} | Waiting for {delay} sec..."
        )
        await asyncio.sleep(delay)

    async def get_tokens_amount(self) -> int:
        wallet_info = await self.wallet_info()
        if wallet_info.get("steaks").get("conversions"):
            return wallet_info["steaks"]["conversions"][0].get("tokenDecimals", 0)

        return 0

    async def export_account(self, success: bool, tokens: int = None) -> ExportAccountData:
        if success:
            return ExportAccountData(
                address=self.address,
                proxy=self.get_proxy,
                tokens=tokens,
                pk_or_mnemonic=self.account.pk_or_mnemonic,
                success=True,
            )

        return ExportAccountData(
            address=self.address,
            proxy=self.get_proxy,
            pk_or_mnemonic=self.account.pk_or_mnemonic,
            success=False,
        )

    async def start(self) -> ExportAccountData | None:
        try:
            if not await self.auth():
                return await self.export_account(success=False)

            tokens = await self.get_tokens_amount()
            logger.info(f"Account: {self.address} | Tokens: {tokens}")
            return await self.export_account(success=True, tokens=tokens)


        except Exception as error:
            logger.error(f"Account: {self.address} | Unknown error | Error: {error}")
