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
                "options": "choices",
            },
        },
        "multi": {
            "defaults": {
                "type": "multi",
                "otherField": False,
            },
            "rewrites": {
                "options": "choices",
            },
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
        return {}

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
            steps.append(
                {
                    "type": "question",
                    "title": question.question,
                    "answerFormat": {
                        **f.get("defaults", {}),
                        **{
                            k: question_format.get(v)
                            for k, v in f.get("rewrites", {}).items()
                            if v in question_format
                        },
                    },
                    "stepIdentifier": {"id": str(question.id)},
                }
            )

        return {
            "id": str(survey.id),
            "type": "navigable",
            "rules": [],
            "steps": steps,
        }
