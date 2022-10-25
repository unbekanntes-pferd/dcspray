
  <h3 align="center">DRACOON-BRANDING-SPRAYER</h3>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [License](#license)



<!-- ABOUT THE PROJECT -->
## About The Project
__Disclaimer: this is an unofficial repo and is not supported by DRACOON__<br>
This package provides a small CLI tool to copy a DRACOON branding from a source url to a target url. 
DRACOON is a cloud storage product / service (SaaS) by DRACOON GmbH (http://dracoon.com). 
DRACOON API documentation can be found here (Swagger UI):
https://dracoon.team/api/

Typer serves as the framework for the CLI, Pillow and resizeimage to handle image resizes and the requests based DRACOON module to authenticate in DRACOON.

## Built With

* [Python 3.7.3](https://www.python.org/)
* [requests module](https://requests.readthedocs.io/en/master/)
* [Typer](https://typer.tiangolo.com/)
* [Pillow](https://pillow.readthedocs.io/)
* [resizeimage](https://github.com/VingtCinq/python-resize-image)
* [DRACOON-PYTHON-API](https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API)

<!-- GETTING STARTED -->
## Getting Started

To get started, just install the package via pip install
```
python3 -m pip install dcspray
```
or 
```
pip install dcspray
```



## Prerequisites

You will need a working Python 3 installation - check your version:
* Python
```
python3 --version
```

## Installation

1. Install the package from PyPi
```
python3 -m pip install dcspray
```
or 
```
pip install dcspray
```

<!-- USAGE EXAMPLES -->
## Usage

### Prerequisites

* Working DRACOON instance
* Config Manager role (DRACOON user)

### Commands

* spray – copy a source branding to a target 
* save – download branding as zip
* load – upload a branding from saved zip file

### Quick start: spray (minimal setup)
```
dcspray spray SOURCE_URL TARGET_URL
```
Minimal usage requires providing a source url to download the branding from and a target url to 
upload the copied branding.

Default configuration:
* Client id is by default set to DRACOON Legacy scripting – if desired, please activate the OAuth app in system settings
* Client secret is by default null / empty (works with DRACOON Legacy scripting)
* Full branding is by default off: Only styling (colors, header, login box postion and images) are copied
* Since DRACOON Legacy scripting is the default OAuth app, password flow will be used by default

#### Get help
Using the help option provides a listing of all options and arguments:
```
dcspray spray --help
```

#### Command Line Overview

The CLI tool works as any other CLI tool:
```
dcspray spray [OPTIONS] SOURCE_URL TARGET_URL
```

#### Options (optional settings)

##### Copy full branding
```
dcspray spray --full-branding SOURCE_URL TARGET_URL
```
To get a full branding including all texts, URLs and other meta information, use the --full-branding option.

##### Use custom OAuth app
```
dcspray  spray --full-branding --client-id someclientid --client-secret optionalsecret SOURCE_URL TARGET_URL
```
To use a different OAuth app, provide a client id and a client secret via corresponding options --client-id and --client-secret.

##### Use custom OAuth app with authorization code flow
```
dcspray spray --full-branding --client-id someclientid --client-secret optionalsecret --auth-code SOURCE_URL TARGET_URL 
```
To use authorization code flow for your custom OAuth app, you first will need to ensure that
* the authorization code flow is activated for the app
* the redirect URL is set to ($your-dracoon-host)/oauth/callback (e.g. https://demo.dracoon.com/oauth/callback)

Settings can be reviewed in your system setting under 'Apps'.

To use the authorization code flow (e.g. in order to use this with an OpenID user in DRACOON), pass the option --auth-code.
It will provide a URL to retrieve an authorization code.
Authenticate via browser.
Paste the code into the CLI and authentication will be completed.

##### Get branding from on premises customer

```
dcspray spray --on-prem-source SOURCE_URL TARGET_URL
```

#### Options overview

* --full-branding – when active, full branding including all texts is copied to target (default is false)
* --client-id – when provided, will use this client id as OAuth app (default is DRACOON Legacy Scripting)
* --client-secret – when provided, will be used to authorize the client (default is none, if no secret is provided, password flow will be used)
* --auth-code – when provided, will use authorization code flow (requires client id and client secret and authorization code flow enabled in OAuth app)
* --on-prem-source – when provided, will obtain branding from an on premises customer using DRACOON Cloud branding
* --help – shows help text

#### Arguments overview

* SOURCE_URL – the URL of a DRACOON instance to load branding from
* TARGET_URL – the URL of a DRACOON instance to spray loaded branding to


### Quick start: save
```
dcspray save SOURCE_URL
```
Minimal usage requires providing a source url to download the branding from.

#### Get help
Using the help option provides a listing of all options and arguments:
```
dcspray save --help
```

#### Command Line Overview

The CLI tool works as any other CLI tool:
```
dcspray save [OPTIONS] SOURCE_URL
```

#### Options (optional settings)

##### Provide own zip file name (and path)
```
dcspray save --zip-name NAME_AND_OPTIONAL_ZIP_PATH SOURCE_URL TARGET_URL
```

#### Options overview
* --zip-name – when provided, will use given path and name to store zip
* --on-prem-source – when provided, will obtain branding from an on premises customer using DRACOON Cloud branding
* --help – shows help text

#### Arguments overview

* SOURCE_URL – the URL of a DRACOON instance to download branding to zip from

### Quick start: load (minimal setup)
```
dcspray load ZIP_FILE TARGET_URL
```
Minimal usage requires providing a zip file name (if no path: must be in current working directory, otherwise provide full path and name) containing a branding saved using the save cmommand in order to spray it to a target url.

Default configuration:
* Client id is by default set to DRACOON Legacy scripting – if desired, please activate the OAuth app in system settings
* Client secret is by default null / empty (works with DRACOON Legacy scripting)
* Full branding is by default off: Only styling (colors, header, login box postion and images) are copied
* Since DRACOON Legacy scripting is the default OAuth app, password flow will be used by default

#### Get help
Using the help option provides a listing of all options and arguments:
```
dcspray load --help
```

#### Command Line Overview

The CLI tool works as any other CLI tool:
```
dcspray load [OPTIONS] ZIP_FILE TARGET_URL
```

#### Options (optional settings)

##### Use custom OAuth app
```
dcspray load --client-id someclientid --client-secret optionalsecret ZIP_FILE TARGET_URL
```
To use a different OAuth app, provide a client id and a client secret via corresponding options --client-id and --client-secret.

##### Use custom OAuth app with authorization code flow
```
dcspray load --client-id someclientid --client-secret optionalsecret --auth-code ZIP_FILE TARGET_URL 
```
To use authorization code flow for your custom OAuth app, you first will need to ensure that
* the authorization code flow is activated for the app
* the redirect URL is set to ($your-dracoon-host)/oauth/callback (e.g. https://demo.dracoon.com/oauth/callback)

Settings can be reviewed in your system setting under 'Apps'.

To use the authorization code flow (e.g. in order to use this with an OpenID user in DRACOON), pass the option --auth-code.
It will provide a URL to retrieve an authorization code.
Authenticate via browser.
Paste the code into the CLI and authentication will be completed.

#### Options overview

* --client-id – when provided, will use this client id as OAuth app (default is DRACOON Legacy Scripting)
* --client-secret – when provided, will be used to authorize the client (default is none, if no secret is provided, password flow will be used)
* --auth-code – when provided, will use authorization code flow (requires client id and client secret and authorization code flow enabled in OAuth app)
* --help – shows help text

#### Arguments overview

* ZIP_FILE – the name (and optional path) to a zip file downloaded using the save command
* TARGET_URL – the URL of a DRACOON instance to spray loaded branding to


## Final notes
This tool serves as a tool to quick reset a branding back to a known default. 
Be aware that images and branding content may well be protected intellectual property.
Use with caution and consideration at own risk!


<!-- LICENSE -->
## License

Distributed under the MIT License. See [LICENSE](/LICENSE) for more information.
