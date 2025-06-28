<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

[![Datalayer](https://assets.datalayer.tech/datalayer-25.svg)](https://datalayer.io)

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)

# 🪐 Jupyter NbModel Client

[![Github Actions Status](https://github.com/datalayer/jupyter-nbmodel-client/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-nbmodel-client/actions/workflows/build.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-nbmodel-client)](https://pypi.org/project/jupyter-nbmodel-client)

`Jupyter NbModel Client` is a python library to interact with a live Jupyter Notebooks.

To install the library, run the following command.

```bash
pip install jupyter_nbmodel_client
```

We ask you to take additional actions to overcome limitations and bugs of the pycrdt library.

```bash
# Ensure you create a new shell after running the following commands.
pip uninstall -y pycrdt datalayer_pycrdt
pip install datalayer_pycrdt
```

## Usage with Jupyter

1. Ensure you have the needed packages in your environment to run the example here after.

```sh
pip install jupyterlab jupyter-collaboration matplotlib
```

2. Start a JupyterLab server, setting a `port` and a `token` to be reused by the agent, and create a notebook `test.ipynb`.

```sh
# make jupyterlab
jupyter lab --port 8888 --ServerApp.port_retries 0 --IdentityProvider.token MY_TOKEN --ServerApp.root_dir ./dev
```

3. Open a IPython (needed for async functions) REPL in a terminal with `ipython` (or `jupyter console`). Execute the following snippet to add a cell in the `test.ipynb` notebook.

```py
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

ws_url = get_jupyter_notebook_websocket_url(
    server_url="http://localhost:8888",
    token="MY_TOKEN",
    path="test.ipynb"
)

async with NbModelClient(ws_url) as nbmodel:
    nbmodel.add_code_cell("print('hello world')")
```

> Check `test.ipynb` in JupyterLab, you should see a cell with content `print('hello world')` appended to the notebook.

5. The previous example does not involve kernels. Put that now in the picture, adding a cell and executing the cell code within a kernel process.

```py
from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

with KernelClient(server_url="http://localhost:8888", token="MY_TOKEN") as kernel:
    ws_url = get_jupyter_notebook_websocket_url(
        server_url="http://localhost:8888",
        token="MY_TOKEN",
        path="test.ipynb"
    )
    async with NbModelClient(ws_url) as notebook:
        cell_index = notebook.add_code_cell("print('hello world')")
        results = notebook.execute_cell(cell_index, kernel)
        print(results)
        assert results["status"] == "ok"
        assert len(results["outputs"]) > 0
```

> Check `test.ipynb` in JupyterLab. You should see an additional cell with content `print('hello world')` appended to the notebook, but this time the cell is executed, so the output should show `hello world`.

You can go further and create a plot with eg matplotlib.

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
    ws_url = get_jupyter_notebook_websocket_url(
        server_url="http://localhost:8888",
        token="MY_TOKEN",
        path="test.ipynb"
    )
    async with NbModelClient(ws_url) as notebook:
        cell_index = notebook.add_code_cell(CODE)
        results = notebook.execute_cell(cell_index, kernel)
        print(results)
        assert results["status"] == "ok"
        assert len(results["outputs"]) > 0
```

> Check `test.ipynb` in JupyterLab for the cell with the matplotlib.

> [!NOTE]
>
> Instead of using the clients as context manager, you can call the `start()` and `stop()` methods.

```py
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

kernel = KernelClient(server_url="http://localhost:8888", token="MY_TOKEN")
kernel.start()

try:
    ws_url = get_jupyter_notebook_websocket_url(
        server_url="http://localhost:8888",
        token="MY_TOKEN",
        path="test.ipynb"
    )
    notebook = NbModelClient(ws_url)
    await notebook.start()
    try:
        cell_index = notebook.add_code_cell("print('hello world')")
        results = notebook.execute_cell(cell_index, kernel)
    finally:
        await notebook.stop()
finally:
    kernel.stop()
```

## Usage with Datalayer

To connect to a [Datalayer collaborative room](https://docs.datalayer.app/platform#notebook-editor), you can use the helper function `get_datalayer_notebook_websocket_url`:

- The `server` is `https://prod1.datalayer.run` for the Datalayer production SaaS.
- The `room_id` is the id of your notebook shown in the URL browser bar.
- The `token` is the assigned token for the notebook.

All those details can be retrieved from a Notebook sidebar on the Datalayer SaaS.

```py
from jupyter_nbmodel_client import NbModelClient, get_datalayer_notebook_websocket_url

ws_url = get_datalayer_notebook_websocket_url(
    server_url=server,
    room_id=room_id,
    token=token
)

async with NbModelClient(ws_url) as notebook:
    notebook.add_code_cell("1+1")
```

## Uninstall

To remove the library, run the following.

```bash
pip uninstall jupyter_nbmodel_client
```

## Data Models

The following json schema describes the data model used in cells and notebook metadata to communicate between user clients and an Jupyter AI Agent.

For that, you will need the [Jupyter AI Agents](https://github.com/datalayer/jupyter-ai-agents) extension installed.

```json
{
  "datalayer": {
    "type": "object",
    "properties": {
      "ai": {
        "type": "object",
        "properties": {
          "prompts": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "title": "Prompt unique identifier",
                  "type": "string"
                },
                "prompt": {
                  "title": "User prompt",
                  "type": "string"
                },
                "username": {
                  "title": "Unique identifier of the user making the prompt.",
                  "type": "string"
                },
                "timestamp": {
                  "title": "Number of milliseconds elapsed since the epoch; i.e. January 1st, 1970 at midnight UTC.",
                  "type": "integer"
                }
              },
              "required": ["id", "prompt"]
            }
          },
          "messages": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "parent_id": {
                  "title": "Prompt unique identifier",
                  "type": "string"
                },
                "message": {
                  "title": "AI reply",
                  "type": "string"
                },
                "type": {
                  "title": "Type message",
                  "enum": [0, 1, 2]
                },
                "timestamp": {
                  "title": "Number of milliseconds elapsed since the epoch; i.e. January 1st, 1970 at midnight UTC.",
                  "type": "integer"
                }
              },
              "required": ["id", "prompt"]
            }
          }
        }
      }
    }
  }
}
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
