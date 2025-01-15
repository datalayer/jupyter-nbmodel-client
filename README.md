<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# Jupyter NbModel Client

[![Github Actions Status](https://github.com/datalayer/jupyter-nbmodel-client/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-nbmodel-client/actions/workflows/build.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-nbmodel-client)](https://pypi.org/project/jupyter-nbmodel-client)

Client to interact with a Jupyter Notebook model.

To install the library, run the following command.

```bash
pip install jupyter_nbmodel_client
```

## Usage

1. Ensure you have the needed packages in your environment to run the example here after.

```sh
pip install jupyterlab jupyter-collaboration ipykernel matplotlib
```

2. Start a JupyterLab server, setting a `port` and a `token` to be reused by the agent, and create a notebook `test.ipynb`.

```sh
jupyter lab --port 8888 --IdentityProvider.token MY_TOKEN
```

3. Open a Python REPL and execute the following snippet to add a cell.

```py
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

with NbModelClient(
    get_jupyter_notebook_websocket_url(
        server_url="http://localhost:8888",
        token="MY_TOKEN",
        path="test.ipynb"
    )
) as notebook:
    notebook.add_code_cell("print('hello world')")
```

> Check `test.ipynb` in JupyterLab.

5. The previous example does not involve kernels. Put that now in the picture, adding a cell and executing within a kernel process.

```py
from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

with KernelClient(server_url="http://localhost:8888", token="MY_TOKEN") as kernel:
    with NbModelClient(
        get_jupyter_notebook_websocket_url(
            server_url="http://localhost:8888",
            token="MY_TOKEN",
            path="test.ipynb"
        )
    ) as notebook:
        cell_index = notebook.add_code_cell("print('hello world')")
        results = notebook.execute_cell(cell_index, kernel)

        assert results["status"] == "ok"
        assert len(results["outputs"]) > 0
```

> Check `test.ipynb` in JupyterLab.

You can go further and create a plot with Matplotlib.

```py
from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

CODE = """import matplotlib.pyplot as plt

fig, ax = plt.subplots()

fruits = ['apple', 'blueberry', 'cherry', 'orange']
counts = [40, 100, 30, 55]
bar_labels = ['red', 'blue', '_red', 'orange']
bar_colors = ['tab:red', 'tab:blue', 'tab:red', 'tab:orange']

ax.bar(fruits, counts, label=bar_labels, color=bar_colors)

ax.set_ylabel('fruit supply')
ax.set_title('Fruit supply by kind and color')
ax.legend(title='Fruit color')

plt.show()
"""

with KernelClient(server_url="http://localhost:8888", token="MY_TOKEN") as kernel:
    with NbModelClient(
        get_jupyter_notebook_websocket_url(
            server_url="http://localhost:8888",
            token="MY_TOKEN",
            path="test.ipynb"
        )
    ) as notebook:
        cell_index = notebook.add_code_cell(CODE)
        results = notebook.execute_cell(cell_index, kernel)

        assert results["status"] == "ok"
        assert len(results["outputs"]) > 0
```

> Check `test.ipynb` in JupyterLab.

> [!NOTE]
>
> Instead of using the clients as context manager, you can call the `start()` and `stop()` methods.

```py
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

kernel = KernelClient(server_url="http://localhost:8888", token="MY_TOKEN")
kernel.start()

try:
    notebook = NbModelClient(
        get_jupyter_notebook_websocket_url(
            server_url="http://localhost:8888",
            token="MY_TOKEN",
            path="test.ipynb"
        )
    )
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

To remove the library, run the following.

```bash
pip uninstall jupyter_nbmodel_client
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

### Packaging the library

See [RELEASE](RELEASE.md)
