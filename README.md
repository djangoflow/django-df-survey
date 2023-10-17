# Django DF Survey

   Django DF Survey - create and manage surveys and on-boarding forms in your DjangoFlow project


## Installation:

- Install the package

```
pip install django-df-survey
```


- Include default `INSTALLED_APPS` from `df_survey.defaults` to your `settings.py`

```python
from df_survey.defaults import DF_SURVEY_INSTALLED_APPS

INSTALLED_APPS = [
    ...
    *DF_SURVEY_INSTALLED_APPS,
    ...
]

```


## Development

Installing dev requirements:

```
pip install -e .[test]
```

Installing pre-commit hook:

```
pre-commit install
```

Running tests:

```
pytest
```
