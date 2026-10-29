# Public capture tool

Install the pinned CSS parser and its encoding dependency before running the
capture CLI or capture tests (Python 3.10 or later):

```
python -m pip install -r app/requirements-capture.txt
```

The root `requirements.txt` includes the same pins for repository setup. From
`app/`, run `python scripts/capture.py` or `python scripts/capture.py --resume`.
Resume authenticates retained object bytes before reuse. A fresh capture makes
public requests to the existing fixed page list and discovered public assets;
it uses no credentials or form submission.

CSS dependencies come from tinycss2 URL tokens and quoted `url()` functions,
including nested blocks/functions and CSS escapes. Comments, ordinary strings,
invalid URL tokens, and other function names do not become resources. Only the
existing same-origin HTTPS font/image extensions are followed. JS chunk-path
discovery remains separate. This is static dependency discovery, not a browser
CSS evaluator: it does not resolve custom properties, assess media conditions,
or fetch arbitrary imports or external domains.

The offline regression runs the real `--resume` CLI with the retained stylesheet
and font objects, plus explicitly derived CSS containing inert lookalike URLs:

```
cd app
python -m unittest tests/test_capture_css_tokens.py
```

Its subprocess audit hook rejects network access instead of simulating responses.
All input and output objects live in temporary directories; retained evidence is
unchanged. Run the broader capture suite with
`python -m unittest discover -s tests -p 'test_capture*.py'`.
