# Progress tracker server

## Install dependencies

### Basic requirements

This Python project requires Python `>=3.7`. If not available on your system, you can install any compatible versions using [PyEnv](https://github.com/pyenv/pyenv).

The dependencies are managed through [Poetry](https://python-poetry.org/). To install it, use the following command (only Linux/Mac/BSD, for Windows see [on their website](https://python-poetry.org/docs/#installation)):

```sh
curl -sSL https://install.python-poetry.org | python3 -
```

### Using Poetry

Simply run `poetry install`, it will create a `virtualenv` with current Python version, and install all dependencies inside it. By default, the `virtalenv` will be located in your `~/.cache/pypoetry/virtualenvs`, but [it can be changed](https://python-poetry.org/docs/configuration/#virtualenvsin-project) to a `.venv` in this directory.

## Manage the server
