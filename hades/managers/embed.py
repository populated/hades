from urllib.parse import quote, urlencode
import typing
import json

from curl_cffi.requests import Session
from discord import Embed

session: Session = Session(
    impersonate="chrome119"
)

def rgb_to_hex(rgb: typing.Tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def parse_response(response: str) -> typing.List[typing.Dict[str, typing.Any]]:
    return [json.loads(part) for part in response.split('\n') if part.strip()]

def get_embed(
    embed: Embed,
    provider: typing.Optional[str] = None,
    provider_url: typing.Optional[str] = None,
    video: typing.Optional[str] = None
) -> str:
    if embed.fields:
        return  # Fields currently unsupported.

    params: typing.Dict[str, str] = {
        "provider": provider if provider else "",
        "author": embed.author.name if embed.author and embed.author.name else "",
        "title": embed.title if embed.title else "",
        "color": rgb_to_hex(embed.colour.to_rgb()) if embed.colour else "",
        "media_type": "video" if video else ("thumbnail" if embed.thumbnail else "none"),
        "desc": embed.description if embed.description else ""
    }

    if video:
        params["media_type"] = "video"

    
    data: typing.Dict[str, typing.Any] = {
        "0": {
            "json": {
                key: value
                for key, value in {
                    "provider": provider if provider else None,
                    "providerLink": provider_url if provider_url else None,
                    "author": embed.author.name if embed.author and embed.author.name else None,
                    "authorLink": embed.url if embed.url else None,
                    "title": embed.title if embed.title else None,
                    "color": "#000000",
                    "description": embed.description if embed.description else None,
                    "mediaType": params.get("media_type"),
                    "mediaSource": embed.thumbnail.url if embed.thumbnail and embed.thumbnail.url else None
                }.items()
                if value is not None
            }
        }
    }

    serialized: str = json.dumps(data)

    res = session.get(
        "https://beta.embedl.ink/api/trpc/create.embed",
        headers={
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "priority": "u=1, i",
            "referer": "https://beta.embedl.ink/",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "trpc-accept": "application/jsonl",
            "x-trpc-source": "nextjs-react",
        },
        params={
            "batch": 1,
            "input": data
        }
    ) 

    _json: typing.List[typing.Dict[str, typing.Any]] = parse_response(res.text)

    if not _json:
        raise ValueError("Failed to parse JSON response")

    code: int = _json[3]["json"][2][0][0].get("id")

    return f"https://beta.embedl.ink/e/{code}"

def hidden(value: str) -> str:
    return (
        "||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||"
        f" _ _ _ _ _ _ {value}"
    )
