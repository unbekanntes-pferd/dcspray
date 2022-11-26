import sys

from urllib.parse import urlparse

import typer
from httpx import ConnectError, HTTPStatusError
from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.errors import HTTPUnauthorizedError, DRACOONHttpError, HTTPNotFoundError


def add_https_protocol(url: str) -> str:

    if url[:7] == 'http://':
        url = f"https://{url[7:]}"
        return url

    if url[:8] != 'https://':
        url = f"https://{url}"
        return url

    return url

async def verify_dracoon_url(url: str):

    dracoon = DRACOON(base_url=url)

    test_url = f"{url}/api/v4/public/software/version"

    try:
        response = await dracoon.client.downloader.get(url=test_url)
        response.raise_for_status()
    except ConnectError:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication error: {url} is not a valid DRACOON url.')
        await dracoon.client.disconnect()
        sys.exit(1)
    except HTTPStatusError as err:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication error: {url} is not a valid DRACOON url.')
        await dracoon.client.disconnect()
        sys.exit(1)


    
async def password_flow(target_url: str, client_id: str, client_secret: str = None) -> DRACOON:

    username = typer.prompt('Please enter username')
    password = typer.prompt('Please enter password', hide_input=True)

    if client_secret:
        dracoon = DRACOON(base_url=target_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
    
    dracoon = DRACOON(base_url=target_url, raise_on_err=True)

    try:
        await dracoon.connect(connection_type=OAuth2ConnectionType.password_flow, username=username, password=password)
    except HTTPUnauthorizedError as err:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Unauthorized (wrong credentials / client?): {err.error.response.status_code}')
        await dracoon.client.disconnect()
        sys.exit(1)
    except HTTPNotFoundError as err:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication error: {target_url} is not a valid DRACOON url.')
        await dracoon.client.disconnect()
        sys.exit(1)
    except DRACOONHttpError as err:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication errror: {err.error.response.status_code}')
        await dracoon.client.disconnect()
        sys.exit(1)

    return dracoon
    
async def auth_code_flow(client_id: str,  client_secret: str, target_url: str) -> DRACOON:
    """ authenticate via authorization code """
    dracoon = DRACOON(base_url=target_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)

    typer.launch(dracoon.get_code_url())
    auth_code = typer.prompt('Paste authorization code')
    
    try:
        await dracoon.connect(auth_code=auth_code)
    except HTTPUnauthorizedError as err:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Unauthorized (wrong code / client?): {err.error.response.status_code}')
        await dracoon.client.disconnect()
        sys.exit(1)
    except HTTPNotFoundError as err:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication error: {target_url} is not a valid DRACOON url.')
        await dracoon.client.disconnect()
        sys.exit(1)
    except DRACOONHttpError as err:
        error_txt = typer.style('Error:', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication errror: {err.error.response.status_code}')
        await dracoon.client.disconnect()
        sys.exit(1)

    return dracoon
