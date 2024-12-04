<!--
  ~
-->

# jupyter_nbmodel_client

[![Github Actions Status](https://github.com/datalayer/jupyter-nbmodel-client/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-nbmodel-client/actions/workflows/build.yml)

Client to interact with Jupyter notebook model.

## Requirements

- Jupyter Server

## Install

To install the extension, execute:

```bash
pip install jupyter_nbmodel_client
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall jupyter_nbmodel_client
```

## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

## Contributing

### Development install

```bash
# Clone the repo to your local environment
# Change directory to the jupyter_nbmodel_client directory
# Install package in development mode - will automatically enable
# The server extension.
pip install -e ".[test,lint,typing]"
```

### Running Tests

Install dependencies:

```bash
pip install -e ".[test]"
```

To run the python tests, use:

```bash
pytest
```

### Development uninstall

```bash
pip uninstall jupyter_nbmodel_client
```

### Packaging the extension

See [RELEASE](RELEASE.md)
