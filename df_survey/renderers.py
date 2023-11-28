# This is temporary as we should use standard DRF renderers
import json

from rest_framework import exceptions


class BaseRenderer:
    pass


class SurveyKitRenderer(BaseRenderer):
    FORMATS = {
        # A dictionary to rewrite internal type and format into survey kit's fmt
        "text": {
            "defaults": {
                "type": "text",
            },
        },
        "integer": {
            "defaults": {
                "type": "integer",
            },
            "rewrites": {
                "maximumValue": "max",
                "minimumValue": "min",
            },
        },
        "date": {
            "defaults": {
                "type": "date",
            },
            "rewrites": {"maxDate": "max", "minDate": "min"},
        },
        "single": {
            "defaults": {
                "type": "single",
                "otherField": False,
            },
            "rewrites": {
                "textChoices": "choices",
            },
        },
        "multi": {
            "defaults": {
                "type": "multiple",
                "otherField": False,
            },
            "rewrites": {
                "textChoices": "choices",
            },
        },
        "completion": {
            "defaults": {
                "type": "completion",
            },
            "rewrites": {
                "buttonText": "value",
            },
            "root": True,
        },
        "intro": {
            "defaults": {
                "type": "intro",
            },
            "rewrites": {
                "buttonText": "value",
            },
            "root": True,
        },
    }

    @classmethod
    def parse_format(self, fmt: str) -> dict:
        if fmt.startswith("{"):
            return json.loads(fmt)
        if ".." in fmt:
            min_, max_ = fmt.split("..")
            return {
                "min": min_,
                "max": max_,
            }
        if "|" in fmt:
            return {"choices": [{"value": v, "text": v} for v in fmt.split("|")]}
        return {
            "value": fmt,
        }

    @classmethod
    def generate_task_from_survey(cls, survey):
        steps = []
        for question in survey.question_set.all():
            try:
                f = SurveyKitRenderer.FORMATS[question.type]
            except KeyError:
                raise exceptions.ValidationError(
                    f"Unrecognized question type '{question.type}'"
                )

            question_format = cls.parse_format(question.format)
            step = {
                "type": "question",
                "title": question.question,
                "text": question.text,
                "stepIdentifier": {"id": str(question.id)},
            }
            data = {
                **f.get("defaults", {}),
                **{
                    k: question_format.get(v)
                    for k, v in f.get("rewrites", {}).items()
                    if v in question_format
                },
            }

            if f.get("root", False):
                step.update(data)
            else:
                step["answerFormat"] = data

            steps.append(step)

        return {
            "id": str(survey.id),
            "type": "navigable",
            "rules": [],
            "steps": steps,
        }
