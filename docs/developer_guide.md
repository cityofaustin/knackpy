# Developer Guide

Issues and pull requests are welcome. Know that your contributions are donated to the [public domain](https://github.com/cityofaustin/knackpy/blob/master/LICENSE.md).

## Environment Setup

Python release candidates are tested against Python 3.6+, so your safest bet when developing is to use v3.6. However, we encourage you to develop in the most current stable release of Python 3 so that you can help us identify potential future compatibility issues.

Install the development environment requirements from `requirements/dev.txt`. This will install the test suite and documentation tooling.

```bash
$ pip install -r requirements/dev.txt
```

Clone the Knackpy repo and create a new branch from the `dev` branch. Use the `-e` flag to install in development mode:

```bash
$ pip install -e knackpy
```

## Tests

We test with [`pytest`](docs.pytest.org/en/stable), [`coverage`](coverage.readthedocs.io), and [`pytest-env`](https://github.com/MobileDynasty/pytest-env).

### Knacky Development Knack Application

Tests for `app.py` and `api.py` are dependendent on a City of Austin-owned Knack application which we rely on for over-the-wire API tests. If you work for the City of Austin Transportation Department, the credentials for this app are in our password store, and the app is called "Knackpy Development".

Any modifications you make to the Knackpy Development app may impact tests. You should carefully review our `tests/` before you modify _anything_ in the development app.

Some tests rely on static `json` data stored in the tests directory. After modifying the app, you must refresh the static data by replacing `tests/_metadata.json` with the most current app metadata, as well as `tests._all_fields.json` with records exported from the `all_fields` object in the Knack app.

### Writing Tests

Ideally, you would add tests for your code to the appropriate test collection in the `tests/` directory. If you don't have access to our development Knack application, please at least write an example test in your pull request.

### Running Tests

You can run ad-hoc tests with:

```bash
$ coverage run -m pytest -c path/to/your/tests
```

Before you can run the entire test suite, you'll need to create a `pytest.ini` config with the appropriate environmental variables. You can model it after [this example](https://github.com/cityofaustin/knackpy/blob/dev/tests/pytest.ini_example).

To run the test suite from `pytest.ini`, use: `$ coverage run -m pytest -c tests/pytest.ini -x`.

After running the tests, you can use `$ coverage html` to generate HTML documentation of code coverage.

You can update the coverage badge image with:

```bash
$  coverage-badge -f -o coverage.svg
```

## Linting and Formatting

We use[`black`](https://black.readthedocs.io/en/stable/) for formatting and [`flake8`](https://flake8.pycqa.org/en/latest/) for formatting and linting code.

Use flake8's `--max-line-length` param so that the linter matches black's line length opinion:

```bash
$ flake8 --max-line-length=88
```

## Documentation

Use [Google docstring](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) format and [type hints](https://docs.python.org/3/library/typing.html).

We use [pydoc-markdown](https://github.com/NiklasRosenstein/pydoc-markdown) to generate the documentation HTML. You'll need to install [Hugo](https://gohugo.io/getting-started/quick-start/) in order to build/serve the documentation site. See also the [`pydoc-markdown.yml`](https://github.com/cityofaustin/knackpy/blob/dev/pydoc-markdown.yml) config.

Rebuild and commit the documentation HTML whenever you update module docstrings or the user guide.

```bash
# build html content
$ pydoc-markdown --build --site-dir docs
# or build and serve locally
$ pydoc-markdown --server
```

## Automated Tests and Deployment

We use [Github Actions](https://docs.github.com/en/actions) to test Knackpy builds and to publish to PyPI. The workflows are defined in `.github/workflows`.

Any commit/merge to the `dev` branch will trigger a PyPI publication to the `knackpy-dev` package. Any release on the `master` branch will trigger publication to the `knackpy` package on PyPI. Note that PyPI publications will fail if don't bump the version number in `setup.py`.
