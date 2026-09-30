"""
Loads the trained grade-prediction model once and exposes predict_grade()
for use in views.

The model was trained on the UCI 0-20 grading scale. The rest of the app
works in a 0-100 weighted-score scale, so this module handles the
conversion in both directions -- nowhere else in the codebase should
touch the raw model's input/output scale directly.
"""

import os
import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'best_model.pkl')

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_grade(study_time, midterm_score_100, preboard_score_100):
    """
    study_time: 1-4 (SemesterStudyTime scale, same as the UCI studytime feature)
    midterm_score_100, preboard_score_100: weighted scores on the app's 0-100 scale

    Returns the predicted final grade on the app's 0-100 scale, rounded to
    1 decimal place, or None if any input is missing.
    """
    if study_time is None or midterm_score_100 is None or preboard_score_100 is None:
        return None

    model = _get_model()

    features = pd.DataFrame([{
        'studytime': study_time,
        'G1': midterm_score_100 / 5,
        'G2': preboard_score_100 / 5,
    }])

    predicted_g3_20 = model.predict(features)[0]
    predicted_g3_100 = predicted_g3_20 * 5

    return round(max(0, min(100, predicted_g3_100)), 1)