from dracoon import core
import typer

def password_flow(client_id: str,  target_url: str, 
                  username: str, password: str, client_secret: str = None):

    if client_secret:
        my_dracoon = core.Dracoon(clientID=client_id, clientSecret=client_secret)
    else:
          my_dracoon = core.Dracoon(clientID=client_id)

    my_dracoon.set_URLs(target_url)
    # try to authenticate - exit if request fails (timeout, connection error..)
    try:
        login_response = my_dracoon.basic_auth(username, password)
    except core.requests.exceptions.RequestException as e:
        typer.echo(f'Connection error: {e}')  
        raise SystemExit(e)

    # get access token or quit if not successful
    if login_response.status_code == 200:
        success_txt = typer.style('Authenticated: 200', fg=typer.colors.BRIGHT_GREEN)
        typer.echo(f'{success_txt}')  
        auth_header = my_dracoon.api_call_headers
    else:
        error_txt = typer.style('Authentication error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} {login_response.json()["error"]}')  
        raise SystemExit()

    return auth_header

def auth_code_flow(client_id: str,  client_secret: str, target_url: str, code: str):
    
    my_dracoon = core.Dracoon(clientID=client_id, clientSecret=client_secret)

    my_dracoon.set_URLs(target_url)
    # try to authenticate - exit if request fails (timeout, connection error..)
    try:
        login_response = my_dracoon.oauth_code_auth(code)
    except core.requests.exceptions.RequestException as e:
        typer.echo(f'Connection error: {e}')  
        raise SystemExit(e)

    # get access token or quit if not successful
    if login_response.status_code == 200:
        success_txt = typer.style('Authenticated: 200', fg=typer.colors.BRIGHT_GREEN)
        typer.echo(f'{success_txt}')  
        auth_header = my_dracoon.api_call_headers
    else:
        error_txt = typer.style('Authentication error: ', bg=typer.colors.RED, fg=typer.colors.WHITE)
        typer.echo(f'{error_txt} {login_response.json()["error"]}')  
        raise SystemExit()

    return auth_header
