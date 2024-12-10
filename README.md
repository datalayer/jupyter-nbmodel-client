<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

# jupyter_nbmodel_client

[![Github Actions Status](https://github.com/datalayer/jupyter-nbmodel-client/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-nbmodel-client/actions/workflows/build.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-nbmodel-client)](https://pypi.org/project/jupyter-nbmodel-client)

Client to interact with Jupyter notebook model.

## Install

To install the extension, execute:

```bash
pip install jupyter_nbmodel_client
```

## Usage

1. Ensure you have an environment with `jupyter-server-ydoc` installed.

> To reproduce the above video you will need to install `jupyterlab`, `jupyter-collaboration` and `scikit-learn` and `matplotlib` for the notebook demo.

1. Start the server `jupyter server` (or JupyterLab like in the video)

1. Write down the URL (usually `http://localhost:8888`) and the server token

1. Open a Python terminal

1. Execute the following snippet to add a cell

```py
from jupyter_nbmodel_client import NbModelClient

with NbModelClient(server_url="http://localhost:8888", token="...", path="test.ipynb") as notebook:
    notebook.add_code_cell("print('hello world')")
```

1. Another example adding a cell and executing within a kernel process

```py
from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import NbModelClient

with KernelClient(server_url="http://localhost:8888", token="...") as kernel:
    with NbModelClient(server_url="http://localhost:8888", token="...", path="test.ipynb") as notebook:
        cell_index = notebook.add_code_cell("print('hello world')")
        results = notebook.execute_cell(cell_index, kernel)

        assert results["status"] == "ok"
        assert len(results["outputs"]) > 0
```

> [!NOTE]
> Instead of using the clients as context manager, you can call the ``start()`` and ``stop()`` methods.

```py
from jupyter_nbmodel_client import NbModelClient

kernel = KernelClient(server_url="http://localhost:8888", token="...")
kernel.start()
try:
    notebook = NbModelClient(server_url="http://localhost:8888", token="...", path="test.ipynb"):
    notebook.start()
    try:
        cell_index = notebook.add_code_cell("print('hello world')")
        results = notebook.execute_cell(cell_index, kernel)
    finally:
        notebook.stop()
finally:
    kernel.stop()
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
