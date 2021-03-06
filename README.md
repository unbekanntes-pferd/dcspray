
  <h3 align="center">DRACOON-PYTHON-API</h3>

  <p align="center">
    Python connector to DRACOON API
    <br />
    <a href="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API/issues">Report Bug</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)



<!-- ABOUT THE PROJECT -->
## About The Project
__Disclaimer: this is an unofficial repo and is not supported by DRACOON__<br>
This package provides a small CLI tool to copy a DRACOON branding from a source url to a target url. 
DRACOON is a cloud storage product / service (SaaS) by DRACOON GmbH (http://dracoon.com). 
DRACOON API documentation can be found here (Swagger UI):
https://dracoon.team/api/

Typer serves as the framework for the CLI, Pillow and resizeimage to handle image resizes and the requests based DRACOON module to authenticate in DRACOON.

### Built With

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
python3 -m pip install dracoonsprayer
```

### Prerequisites

You will need a working Python 3 installation - check your version:
* Python
```
python3 --version
```

### Installation

1. Install the package from PyPi
```
python3 -m pip install dracoonsprayer
```

<!-- USAGE EXAMPLES -->
## Usage

### Prerequisites

* Working DRACOON instance
* Config Manager role (DRACOON user)

### Quick start (minimal setup)
```
python -m dracoonsprayer [source_url] [target_url]
```
Minimal usage requires providing a source url to download the branding from and a target url to 
upload the copied branding.

Default configuration:
* Client id is by default set to DRACOON Legacy scripting – if desired, please activate the OAuth app in system settings
* Client secret is by default null / empty (works with DRACOON Legacy scripting)
* Full branding is by default off: Only styling (colors, header, login box postion and images) are copied
* Since DRACOON Legacy scripting is the default OAuth app, password flow will be used by default

### Options (optional settings)

#### Copy full branding
```
python -m dracoonsprayer [source_url] [target_url] --full-branding
```
To get a full branding including all texts, URLs and other meta information, use the --full-branding option.

#### Use custom OAuth app
```
python -m dracoonsprayer [source_url] [target_url] --full-branding --client-id someclientid --client-secret optionalsecret
```
To use a different OAuth app, provide a client id and a client secret via corresponding options --client-id and --client-secret.

#### Use custom OAuth app with authorization code flow
```
python -m dracoonsprayer [source_url] [target_url] --full-branding --client-id someclientid --client-secret optionalsecret --auth-code-flow
```
To use authorization code flow for your custom OAuth app, you first will need to ensure that
* the authorization code flow is activated for the app
* the redirect URL is set to $your-host/oauth/callback (e.g. https://demo.dracoon.com/oauth/callback)

Settings can be reviewed in your system setting under 'Apps'.

To use the authorization code flow (e.g. in order to use this with an OpenID user in DRACOON), pass the option --auth-code-flow.
It will provide a URL to retrieve an authorization code.
Authenticate via browser.
Paste the code into the CLI and authentication will be completed.

## Final notes
This tool serves as a tool to quick reset a branding back to a known default. 
Be aware that images and branding content may well be protected intellectual property.
Use with caution and consideration at own risk!


<!-- LICENSE -->
## License

Distributed under the MIT License. See [LICENSE](/LICENSE) for more information.
