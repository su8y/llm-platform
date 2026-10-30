"""IMAP 수신 소스. imaplib 은 동기이므로 asyncio.to_thread 로 감싼다."""
import asyncio
import imaplib
import logging
import re
import socket
from dataclasses import dataclass

from utils.error import DataError, MailSourceError


@dataclass
class ImapConfig:
    host: str
    port: int
    use_ssl: bool
    username: str
    password: str
    folder: str = "INBOX"


@dataclass
class ImapFetchResult:
    uidvalidity: int
    messages: list[tuple[int, bytes]]        # (uid, raw)
    last_uid: int


def _connect(config: ImapConfig) -> imaplib.IMAP4:
    socket.setdefaulttimeout(20)
    client = imaplib.IMAP4_SSL(config.host, config.port) if config.use_ssl else imaplib.IMAP4(config.host, config.port)
    client.login(config.username, config.password)
    return client


def _select(client: imaplib.IMAP4, folder: str) -> int:
    folder = folder.replace('"', "").replace("\r", "").replace("\n", "") or "INBOX"
    status, data = client.select(f'"{folder}"', readonly=True)
    if status != "OK":
        raise MailSourceError(f"IMAP select failed for folder {folder}")
    status, data = client.status(f'"{folder}"', "(UIDVALIDITY)")
    match = re.search(rb"UIDVALIDITY (\d+)", data[0] if data and data[0] else b"")
    return int(match.group(1)) if match else 0


def _fetch_sync(config: ImapConfig, last_uid: int, limit: int) -> ImapFetchResult:
    client = _connect(config)
    try:
        uidvalidity = _select(client, config.folder)
        status, data = client.uid("search", None, f"UID {last_uid + 1}:*")
        if status != "OK":
            raise MailSourceError("IMAP UID search failed")
        uids = [int(u) for u in (data[0].split() if data and data[0] else []) if int(u) > last_uid]
        uids = sorted(uids)[:limit]
        messages: list[tuple[int, bytes]] = []
        for uid in uids:
            status, parts = client.uid("fetch", str(uid), "(RFC822)")
            if status != "OK" or not parts or not isinstance(parts[0], tuple):
                logging.warning(f"[module.MailReceiver.imap_source._fetch_sync] 🔁 skip uid {uid}: fetch returned {status}")
                continue
            messages.append((uid, parts[0][1]))
        return ImapFetchResult(uidvalidity=uidvalidity, messages=messages, last_uid=max(uids) if uids else last_uid)
    finally:
        try:
            client.logout()
        except Exception:
            pass


def _test_sync(config: ImapConfig) -> dict:
    client = _connect(config)
    try:
        uidvalidity = _select(client, config.folder)
        status, data = client.uid("search", None, "ALL")
        count = len(data[0].split()) if status == "OK" and data and data[0] else 0
        return {"ok": True, "folder": config.folder, "uidvalidity": uidvalidity, "messageCount": count}
    finally:
        try:
            client.logout()
        except Exception:
            pass


class ImapSource:
    @staticmethod
    async def fetch_new(config: ImapConfig, last_uid: int, limit: int = 50) -> ImapFetchResult:
        try:
            return await asyncio.to_thread(_fetch_sync, config, last_uid, limit)
        except MailSourceError:
            raise
        except imaplib.IMAP4.error as e:
            raise MailSourceError(f"IMAP error: {e}") from e
        except (OSError, socket.timeout) as e:
            raise MailSourceError(f"IMAP connection failed: {e}") from e

    @staticmethod
    async def test_connection(config: ImapConfig) -> dict:
        try:
            return await asyncio.to_thread(_test_sync, config)
        except MailSourceError:
            raise
        except imaplib.IMAP4.error as e:
            raise MailSourceError(f"IMAP error: {e}") from e
        except (OSError, socket.timeout) as e:
            raise MailSourceError(f"IMAP connection failed: {e}") from e
