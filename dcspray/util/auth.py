import typer
from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.errors import HTTPUnauthorizedError, DRACOONHttpError

async def password_flow(target_url: str, client_id: str, client_secret: str = None):

    username = typer.prompt('Please enter username')
    password = typer.prompt('Please enter password', hide_input=True)

    if client_secret:
        dracoon = DRACOON(base_url=target_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
    
    dracoon = DRACOON(base_url=target_url, raise_on_err=True)

    try:
        await dracoon.connect(connection_type=OAuth2ConnectionType.password_flow, username=username, password=password)
    except HTTPUnauthorizedError as err:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Unauthorized (wrong credentials / client?): {err.error.response.status_code}')
        await dracoon.client.disconnect()
        typer.Abort()
    except DRACOONHttpError as err:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication errror: {err.error.response.status_code}')
        await dracoon.client.disconnect()
        typer.Abort()

    return dracoon
    
async def auth_code_flow(client_id: str,  client_secret: str, target_url: str):
    
    dracoon = DRACOON(base_url=target_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)

    typer.launch(dracoon.get_code_url())
    auth_code = typer.prompt('Paste authorization code')
    
    try:
        await dracoon.connect(auth_code=auth_code)
    except HTTPUnauthorizedError as err:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Unauthorized (wrong code / client?): {err.error.response.status_code}')
        await dracoon.client.disconnect()
        typer.Abort()
    except DRACOONHttpError as err:
        error_txt = typer.style('Error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} Authentication errror: {err.error.response.status_code}')
        await dracoon.client.disconnect()
        typer.Abort()

    return dracoon
