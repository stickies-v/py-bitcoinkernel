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

## Docstring conventions

### Ownership of returned wrappers

Any method or function whose return type is a `KernelOpaquePtr`
subclass must end its `Returns:` section with one of the following
sentences, so that callers can reason about lifetimes without reading
the implementation:

- `Owned handle.` — the caller receives an independent handle. The
  underlying C memory is freed when the returned object is garbage
  collected.
- `View into <parent>.` — the returned object borrows its C memory
  from `<parent>`. Use `detach()` (or `copy.copy()`) to promote it to
  an owned handle if it needs to outlive its parent. See
  [Object Lifetimes](lifetimes.md) for context.

## Linting and Type Checking

Code style is enforced with [`ruff`](https://docs.astral.sh/ruff/) and
types are checked with [`ty`](https://docs.astral.sh/ty/). Both are
run in CI and can be run locally:

```sh
ruff check .
ruff format --check .
uv run --extra type ty check
```
