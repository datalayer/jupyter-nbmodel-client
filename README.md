<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

<a href="https://datalayer.ai"><img alt="Datalayer" src="https://assets.datalayer.tech/datalayer-25.svg" height="22"/></a>

[![Become a Sponsor](https://img.shields.io/static/v1?label=Become%20a%20Sponsor&message=%E2%9D%A4&logo=GitHub&style=flat&color=1ABC9C)](https://github.com/sponsors/datalayer)
[![Github Actions Status](https://github.com/datalayer/jupyter-nbmodel-client/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-nbmodel-client/actions/workflows/build.yml)

[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-nbmodel-client?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/jupyter-nbmodel-client) [![Total PyPI downloads](https://img.shields.io/pepy/dt/jupyter-nbmodel-client?style=for-the-badge&logo=python&logoColor=white)](https://pepy.tech/project/jupyter-nbmodel-client) [![License](https://img.shields.io/badge/License-BSD_3--Clause-blue?style=for-the-badge&logo=open-source-initiative&logoColor=white)](https://opensource.org/licenses/BSD-3-Clause)

# 🪐 📄 Jupyter NbModel Client

[![Github Actions Status](https://github.com/datalayer/jupyter-nbmodel-client/workflows/Build/badge.svg)](https://github.com/datalayer/jupyter-nbmodel-client/actions/workflows/build.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/jupyter-nbmodel-client)](https://pypi.org/project/jupyter-nbmodel-client)

[![Built and maintained by Datalayer](https://img.shields.io/badge/Built%20and%20maintained%20by-Datalayer%20%C2%B7%20datalayer.ai-1ABC9C?style=for-the-badge&logo=jupyter&logoColor=white&labelColor=0E7C6B)](https://datalayer.ai)

**Stop losing your outputs to session timeouts or network loss.**

Your cells run on the server, so a reload, a closed laptop or a dropped connection no longer
costs you an execution — and the outputs are still there when you come back.

📖 [Documentation](https://jupyter-nbmodel-client.datalayer.tech) &nbsp;·&nbsp; 🔀 [Output reconciliation](https://jupyter-nbmodel-client.datalayer.tech/reconciliation) &nbsp;·&nbsp; 💬 [Community](https://jupyter-nbmodel-client.datalayer.tech/community)

- **⚡ Durable execution** — a cell keeps running with no browser connected to it.
- **🖥️ Terminal-faithful outputs** — progress bars overwrite their line, as they should.
- **🤖 Agent ready** — a REST API to run cells and read outputs, so an agent works
  from the same Notebook you do.

[![HOT NEWS](https://img.shields.io/badge/%F0%9F%94%A5%20HOT%20NEWS-Hosted%20MCP%20is%20live-E74C3C?style=for-the-badge&labelColor=922B21)](https://jupyter-mcp-server.datalayer.tech/hosted)

**Your agent can now reach these Notebooks without running anything.** Datalayer hosts a
Jupyter MCP endpoint at **`https://mcp.datalayer.run/mcp`** — durable execution included, so a cell keeps running after the agent disconnects.

[![Claude Code plugin](https://img.shields.io/badge/%F0%9F%A4%96%20Claude%20Code-plugin%20available-8E44AD?style=for-the-badge&labelColor=5B2C6F)](https://github.com/datalayer/jupyter-mcp-server/tree/main/ext/claude-plugin)
 
Claude Code connects with one command through
the [Datalayer plugin](https://github.com/datalayer/jupyter-mcp-server/tree/main/ext/claude-plugin).

---

**Free and open source, BSD 3-Clause** — install it in your own Jupyter, no account needed.
Built and maintained by [**Datalayer**](https://datalayer.ai), where the same durable execution powers always-on Notebooks that humans and AI agents work in together.

[![Install from PyPI](https://img.shields.io/badge/pip%20install-jupyter__nbmodel__client-306998?style=for-the-badge&logo=python&logoColor=white&labelColor=1E4064)](https://pypi.org/project/jupyter-nbmodel-client) [![Discover Datalayer](https://img.shields.io/badge/%E2%86%92%20Discover%20Datalayer-datalayer.ai-1ABC9C?style=for-the-badge&labelColor=0E7C6B)](https://datalayer.ai)

`Jupyter NbModel Client` is a python library to interact with a live Jupyter Notebooks.

To install the library, run the following command.

```bash
pip install jupyter_nbmodel_client
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
from jupyter_kernel_client import JupyterKernelClient
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

with JupyterKernelClient(server_url="http://localhost:8888", token="MY_TOKEN") as kernel:
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
from jupyter_kernel_client import JupyterKernelClient
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

with JupyterKernelClient(server_url="http://localhost:8888", token="MY_TOKEN") as kernel:
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
> Instead of using the nbmodel clients as context manager, you can call the `start()` and `stop()` methods.

```py
from jupyter_kernel_client import JupyterKernelClient
from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url

kernel = JupyterKernelClient(server_url="http://localhost:8888", token="MY_TOKEN")
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

To connect to a Datalayer collaborative room, you can use the helper function `get_datalayer_notebook_websocket_url`:

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

---

<div align="center">

**If this project is helpful to you, please give us a ⭐️**

Made with ❤️ by [Datalayer](https://datalayer.ai)

<img src="https://assets.datalayer.tech/datalayer-25.svg" alt="Datalayer Logo" width="200"/>

</div>
