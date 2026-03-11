"""
Module for managing authenticated HTTP sessions with CargaMaquina.
"""

import logging
import aiohttp
from bs4 import BeautifulSoup
from src.core.config import ConfigManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class SessionManager:
    """
    Manages HTTP sessions, CSRF tokens, and authentication state.
    Keeps a persistent aiohttp.ClientSession() to be used across the app.
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.session = None
        self.base_url = ""
        self.login_code_url = ""

    async def _ensure_session(self) -> None:
        """Ensures the aiohttp session is created within an active event loop."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

    async def login(self) -> bool:
        """
        Attempts to authenticate using credentials from ConfigManager.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        session_config = self.config_manager.get_session_config()
        username = session_config.get("username")
        password = session_config.get("password")

        if not username or not password:
            logging.warning("Missing credentials. Cannot attempt login.")
            return False
        await self._ensure_session()

        try:
            logging.info("Fetching CSRF token from CargaMaquina...")
            async with self.session.get(
                "https://lanx.cargamaquina.com.br/", allow_redirects=True
            ) as response:
                response.raise_for_status()
                response_text = await response.text()

                # Extract dynamic URL parts
                final_url = str(response.url)
                self.base_url = final_url.split("/site")[0]
                self.login_code_url = final_url.split("/c/")[-1]

                # Parse HTML to find the CSRF token
                soup = BeautifulSoup(response_text, "html.parser")
                csrf_input = soup.find("input", {"name": "YII_CSRF_TOKEN"})

                if not csrf_input or not csrf_input.get("value"):
                    logging.error("CSRF token not found in the HTML response.")
                    return False

                csrf_token = csrf_input["value"]
                logging.info("CSRF token extracted successfully.")

                login_payload = {
                    "YII_CSRF_TOKEN": csrf_token,
                    "LoginForm[username]": username,
                    "LoginForm[password]": password,
                    "LoginForm[codigoConexao]": self.login_code_url,
                    "yt0": "Entrar",
                }

                login_url = f"{self.base_url}/site/login/c/{self.login_code_url}"
                logging.info("Sending POST request to authenticate...")

                async with self.session.post(
                    login_url, data=login_payload
                ) as post_response:
                    post_response.raise_for_status()
                    post_text = await post_response.text()
                    post_url = str(post_response.url)

                    # Verify if login was successful by checking if we are still on the login page
                    if "LoginForm" in post_text or "login" in post_url:
                        logging.error("Login failed. Invalid credentials.")
                        return False

                    logging.info("Login successful! Session is now authenticated.")
                    return True

        except aiohttp.ClientError as e:
            logging.error("Network or HTTP error during login: %s", e)
            return False
        except Exception as e:
            logging.exception("Unexpected error during login: %s", e)
            return False

    async def close(self):
        """Closes the underlying aiohttp session safely."""
        if self.session and not self.session.closed:
            await self.session.close()
