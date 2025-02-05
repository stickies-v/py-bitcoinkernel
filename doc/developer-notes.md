# Developer Notes

## Testing

This project uses `pytest` for its test suite. The dependencies are
defined in `pyproject.toml`, and the test settings are in `pytest.ini`.

To install the project and its test dependencies, run:

```sh
pip install ".[test]"
```

> [!NOTE] This project supports [editable
> installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).

Then, the test suite can be ran with:

```sh
pytest
```

### Test Coverage

Test coverage can be generated with the pre-configured
[`coverage.py`](https://coverage.readthedocs.io/) tool. Follow the
installation instructions in [Testing](#testing), and then just append
`--cov`:

```sh
pytest --cov
```
