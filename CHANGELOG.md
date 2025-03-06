<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 0.11.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.10.0...09b91fca7b1923784074478be28ad1602dd43e74))

### Enhancements made

- Expose username and server URL [#32](https://github.com/datalayer/jupyter-nbmodel-client/pull/32) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2025-03-06&to=2025-03-06&type=c))

[@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2025-03-06..2025-03-06&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 0.10.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.9.0...65ebc13104b997d700a7ea814bf55426dd90db2b))

### Enhancements made

- Add awareness support [#31](https://github.com/datalayer/jupyter-nbmodel-client/pull/31) ([@fcollonval](https://github.com/fcollonval))
- Improve notebook client [#30](https://github.com/datalayer/jupyter-nbmodel-client/pull/30) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2025-02-20&to=2025-03-06&type=c))

[@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2025-02-20..2025-03-06&type=Issues)

## 0.9.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.8.0...26bda1a49cb6aa5e1e0c3cd52468fb6a0f68bcdd))

### Enhancements made

- Add datalayer helper [#28](https://github.com/datalayer/jupyter-nbmodel-client/pull/28) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2025-02-20&to=2025-02-20&type=c))

[@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2025-02-20..2025-02-20&type=Issues)

## 0.8.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.7.0...440c1c349070470ba179d2010cbd25c783df046e))

### Enhancements made

- Switch to datalayer-pycrdt [#27](https://github.com/datalayer/jupyter-nbmodel-client/pull/27) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2025-02-18&to=2025-02-20&type=c))

[@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2025-02-18..2025-02-20&type=Issues)

## 0.7.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.6.0...3a97512947e6055e09be6b7360a809b434f16274))

> [!IMPORTANT]
> **Breaking changes**
> The client is now asynchronous instead of running the websocket communication in a thread. This is a workaround
> due to the limitation of the underlying code not supporting multi-threading.

### Enhancements made

- Switch to async for notebook client [#26](https://github.com/datalayer/jupyter-nbmodel-client/pull/26) ([@fcollonval](https://github.com/fcollonval))
- Add reacting model and test it [#22](https://github.com/datalayer/jupyter-nbmodel-client/pull/22) ([@fcollonval](https://github.com/fcollonval))

### Bugs fixed

- Prevent leaking query args [#23](https://github.com/datalayer/jupyter-nbmodel-client/pull/23) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2025-01-16&to=2025-02-18&type=c))

[@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2025-01-16..2025-02-18&type=Issues)

## 0.6.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.4.0...3a3b7df9b472fa4ff861da7e26b91641f5d2a37b))

> [!IMPORTANT]
> Breaking changes :warning:
> The API to create a notebook model client changed to receive directly
> the websocket URL for the notebook. In the case of the Jupyter Server,
> a helper is provided to generate that websocket URL.

```patch
  from jupyter_nbmodel_client import (
      NbModelClient,
+     get_jupyter_notebook_websocket_url
  )
  
- NbModelClient(server_url="http://localhost:8888", token="MY_TOKEN", path="test.ipynb"):
+ NbModelClient(
+   get_jupyter_notebook_websocket_url(
+       server_url="http://localhost:8888",
+       token="MY_TOKEN",
+       path="test.ipynb"
+     )
+ )
```

### Enhancements made

- Make the client more generic to connect to any Y websocket server [#20](https://github.com/datalayer/jupyter-nbmodel-client/pull/20) ([@fcollonval](https://github.com/fcollonval))
- insert cell methods [#21](https://github.com/datalayer/jupyter-nbmodel-client/pull/21) ([@eleonorecharles](https://github.com/eleonorecharles))

### Other merged PRs

- Update jupyter-server-ydoc requirement from ~=1.0.0 to >=1.0,\<1.2 in the pip group [#19](https://github.com/datalayer/jupyter-nbmodel-client/pull/19) ([@dependabot](https://github.com/dependabot))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2024-12-18&to=2025-01-16&type=c))

[@dependabot](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Adependabot+updated%3A2024-12-18..2025-01-16&type=Issues) | [@eleonorecharles](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Aeleonorecharles+updated%3A2024-12-18..2025-01-16&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2024-12-18..2025-01-16&type=Issues)

## 0.4.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.3.0...20ff2d14a92d9339e8ddf8e7c091c102d3ea13fa))

### Enhancements made

- docs: readme [#13](https://github.com/datalayer/jupyter-nbmodel-client/pull/13) ([@echarles](https://github.com/echarles))

### Bugs fixed

- Use a lock to prevent document access or change between threads [#16](https://github.com/datalayer/jupyter-nbmodel-client/pull/16) ([@fcollonval](https://github.com/fcollonval))
- Revert "Use multithreading flag" [#15](https://github.com/datalayer/jupyter-nbmodel-client/pull/15) ([@fcollonval](https://github.com/fcollonval))
- Use multithreading flag [#14](https://github.com/datalayer/jupyter-nbmodel-client/pull/14) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2024-12-10&to=2024-12-18&type=c))

[@echarles](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Aecharles+updated%3A2024-12-10..2024-12-18&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2024-12-10..2024-12-18&type=Issues)

## 0.3.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.2.0...cfc7a804957b777900c105cada76993ce0f6d0c0))

### Enhancements made

- Add execution options [#11](https://github.com/datalayer/jupyter-nbmodel-client/pull/11) ([@fcollonval](https://github.com/fcollonval))

### Documentation improvements

- Add pypi badge [#10](https://github.com/datalayer/jupyter-nbmodel-client/pull/10) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2024-12-09&to=2024-12-10&type=c))

[@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2024-12-09..2024-12-10&type=Issues)

## 0.2.0

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/v0.1.1...590550c1b7d76656f10a0ad59b133d5fe6ab5556))

### Enhancements made

- Polish API [#9](https://github.com/datalayer/jupyter-nbmodel-client/pull/9) ([@fcollonval](https://github.com/fcollonval))

### Other merged PRs

- Bump apache/skywalking-eyes from e19b828cea6a6027cceae78f05d81317347d21be to 3ea9df11bb3a5a85665377d1fd10c02edecf2c40 in the actions group [#5](https://github.com/datalayer/jupyter-nbmodel-client/pull/5) ([@dependabot](https://github.com/dependabot))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2024-12-04&to=2024-12-08&type=c))

[@dependabot](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Adependabot+updated%3A2024-12-04..2024-12-08&type=Issues) | [@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2024-12-04..2024-12-08&type=Issues)

## 0.1.1

([Full Changelog](https://github.com/datalayer/jupyter-nbmodel-client/compare/aef1fe634cfe585219a2c8ec8a3f9373e6834fec...aae60dc27cc23cf84fe6b4d263506495adb97dd6))

### Enhancements made

- Return outputs from `execute_cell` [#8](https://github.com/datalayer/jupyter-nbmodel-client/pull/8) ([@fcollonval](https://github.com/fcollonval))
- Make client inherit from model directly [#7](https://github.com/datalayer/jupyter-nbmodel-client/pull/7) ([@fcollonval](https://github.com/fcollonval))
- Add releaser workflows [#6](https://github.com/datalayer/jupyter-nbmodel-client/pull/6) ([@fcollonval](https://github.com/fcollonval))

### Documentation improvements

- Return outputs from `execute_cell` [#8](https://github.com/datalayer/jupyter-nbmodel-client/pull/8) ([@fcollonval](https://github.com/fcollonval))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/datalayer/jupyter-nbmodel-client/graphs/contributors?from=2024-12-02&to=2024-12-04&type=c))

[@fcollonval](https://github.com/search?q=repo%3Adatalayer%2Fjupyter-nbmodel-client+involves%3Afcollonval+updated%3A2024-12-02..2024-12-04&type=Issues)
