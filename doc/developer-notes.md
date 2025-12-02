# Developer Notes

## Testing

This project uses `pytest` for its test suite. The dependencies are
defined in `pyproject.toml`, and the test settings are in `pytest.ini`.

To install the project and its test dependencies in editable, run:

```sh
pip install -e ".[test]"
```

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
