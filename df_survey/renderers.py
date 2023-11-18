# This is temporary as we should use standard DRF renderers
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
            "format": {
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

    @staticmethod
    def generate_task_from_template(template):
        steps = []
        for question in template.questions.all():
            try:
                f = SurveyKitRenderer.FORMATS[question.type]
            except KeyError:
                raise exceptions.ValidationError(
                    f"Unrecognized question type '{question.type}'"
                )

            steps.append(
                {
                    "type": "question",
                    "title": question.question,
                    "answerFormat": {
                        **f.get("defaults", {}),
                        **{k: f.format.get(v) for k, v in f.get("rewrites", {})},
                    },
                    "stepIdentifier": {"id": str(question.id)},
                }
            )

        return {
            "id": str(template.id),
            "type": "navigable",
            "rules": [],
            "steps": steps,
        }
