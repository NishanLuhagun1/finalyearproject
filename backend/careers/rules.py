"""
Rule-based career gap analysis and roadmap building.

For each defined CareerProfile this compares a student's soft skills,
technical skills, known programming languages, subject performance, study
time and stated interest against what the profile expects, and produces:

  - a 0-100 match score (persisted as a CareerSuggestion),
  - a short one-line study tip (`suggestion.tip`),
  - a structured roadmap (`suggestion.roadmap`): which subjects to focus on
    and for how many hours a week, which skills/languages to build, and how
    the student's current study time compares with what the path needs.

It is intentionally rule-based (no ML) -- the machine learning model only
handles final grade prediction.
"""

from .models import CareerProfile, CareerSuggestion

SOFT_SKILL_FIELD_LABELS = {
    'communication_skill': 'Communication',
    'teamwork_skill': 'Teamwork',
    'problem_solving_skill': 'Problem solving',
    'leadership_skill': 'Leadership',
    'adaptability_skill': 'Adaptability',
    'time_management_skill': 'Time management',
    'critical_thinking_skill': 'Critical thinking',
    'creativity_skill': 'Creativity',
}

TECHNICAL_SKILL_FIELD_LABELS = {
    'programming_skill': 'Programming',
    'database_skill': 'Database',
    'web_dev_skill': 'Web development',
    'networking_skill': 'Networking',
}

CAREER_INTEREST_MAP = {
    'Software Engineer': ['software_engineering', 'mobile_development', 'game_development'],
    'Data Analyst': ['data_analytics', 'artificial_intelligence'],
    'UI/UX Designer': ['ui_ux_design'],
    'Network Administrator': ['network_administration', 'cybersecurity', 'cloud_computing'],
    'Business Analyst': ['business_analysis', 'project_management'],
}

SKILL_TARGET = 4  # out of 5 -- the rating considered "strong" for a required skill

# Study time scale (SemesterStudyTime): label, and the weekly hours a student
# on that band should at least be putting in.
STUDY_BANDS = {
    1: ('Less than 2 hours/week', 1),
    2: ('2 to 5 hours/week', 2),
    3: ('5 to 10 hours/week', 5),
    4: ('More than 10 hours/week', 10),
}

# Match score weighting -- must sum to 1.0
WEIGHT_SUBJECTS = 0.30
WEIGHT_SOFT_SKILLS = 0.20
WEIGHT_TECHNICAL_SKILLS = 0.20
WEIGHT_PROGRAMMING_LANGUAGES = 0.10
WEIGHT_INTEREST = 0.10
WEIGHT_STUDY_TIME = 0.10


def _csv(text):
    return [s.strip() for s in (text or '').split(',') if s.strip()]


def _lang_label(lang):
    return lang.upper() if len(lang) <= 3 else lang


def _subject_lookup(student_subjects, requirement):
    """Average score across *every* student subject matching `requirement`.

    Returns (score or None, [matched subject names]). Subjects that match
    but have no marks yet still count as matched (score stays None).
    """
    req = requirement.lower()
    names, scores = [], []
    for ss in student_subjects:
        subject_name = ss.subject.name.lower()
        if req in subject_name or subject_name in req:
            names.append(ss.subject.name)
            scores.extend(r.weighted_score for r in ss.results.all() if r.weighted_score is not None)
    score = round(sum(scores) / len(scores), 1) if scores else None
    return score, names


def _rating_match(assessment, field_labels, required_csv):
    """Shared logic for soft skill and technical skill matching -- both
    compare a set of 1-5 IntegerFields on the assessment against a target."""
    required_fields = _csv(required_csv)
    if not required_fields:
        return 100, []

    total = 0
    gaps = []
    for field in required_fields:
        rating = getattr(assessment, field, None) or 0
        total += min(rating / SKILL_TARGET, 1) * 100
        if rating < SKILL_TARGET:
            label = field_labels.get(field, field)
            gaps.append(f"{label} is {rating}/5, aim for {SKILL_TARGET}/5")

    return round(total / len(required_fields), 1), gaps


def _subject_match(student_subjects, career):
    required = _csv(career.required_subjects)
    if not required:
        return 100, []

    matched_scores = []
    gaps = []
    for req in required:
        found_score, _ = _subject_lookup(student_subjects, req)
        if found_score is not None:
            matched_scores.append(found_score)
            if found_score < career.min_predicted_score:
                gaps.append(
                    f"Raise {req.title()} score above {career.min_predicted_score}% "
                    f"(currently {found_score:.1f}%)"
                )
        else:
            gaps.append(f"No marks recorded yet for {req.title()}")

    if not matched_scores:
        return 0, gaps
    return round(sum(matched_scores) / len(matched_scores), 1), gaps


def _programming_language_match(assessment, career):
    required = [lang.lower() for lang in _csv(career.required_programming_languages)]
    if not required:
        return 100, []

    known = [lang.lower() for lang in _csv(assessment.programming_languages)]
    missing = [lang for lang in required if lang not in known]

    score = round(((len(required) - len(missing)) / len(required)) * 100, 1)
    gaps = []
    if missing:
        gaps.append(f"Learn {', '.join(m.upper() if len(m) <= 3 else m.title() for m in missing)}")
    return score, gaps


def _interest_match(assessment, career):
    matching_interests = CAREER_INTEREST_MAP.get(career.name, [])
    if assessment.interest_area and assessment.interest_area in matching_interests:
        return 100, []
    return 40, []


def _study_time_match(study_time, career):
    if career.min_study_time is None:
        return 100, []
    if study_time is None:
        return 60, ["Log your weekly study time for a more accurate match"]
    if study_time >= career.min_study_time:
        return 100, []
    return 50, ["This path typically needs more consistent weekly study time than you're currently logging"]


# --------------------------------------------------------------------------
# Roadmap
# --------------------------------------------------------------------------

def _subject_hours(score, target):
    """Suggested weekly study hours for one focus subject."""
    if score is None:
        return 2
    if score >= target + 10:
        return 1
    if score >= target:
        return 2
    if target - score <= 10:
        return 4
    return 6


def _focus_subjects(student_subjects, career):
    rows = []
    target = career.min_predicted_score
    for req in _csv(career.required_subjects):
        score, names = _subject_lookup(student_subjects, req)
        if score is None:
            status = 'no_marks'
        elif score < target:
            status = 'needs_work'
        elif score < target + 10:
            status = 'on_track'
        else:
            status = 'strong'
        rows.append({
            'name': names[0] if names else req.title(),
            'in_courses': bool(names),
            'current': score,
            'target': target,
            'status': status,
            'hours': _subject_hours(score, target),
        })
    # most urgent first: needs work (lowest score first), then unknowns, then the rest
    order = {'needs_work': 0, 'no_marks': 1, 'on_track': 2, 'strong': 3}
    rows.sort(key=lambda r: (order[r['status']], r['current'] or 0))
    return rows


def _skill_gaps(assessment, field_labels, required_csv, kind):
    gaps = []
    for field in _csv(required_csv):
        rating = getattr(assessment, field, None) or 0
        if rating < SKILL_TARGET:
            gaps.append({
                'label': field_labels.get(field, field), 'rating': rating,
                'target': SKILL_TARGET, 'kind': kind,
            })
    gaps.sort(key=lambda g: g['rating'])
    return gaps


def build_roadmap(assessment, student_subjects, career, study_time):
    focus = _focus_subjects(student_subjects, career)
    skills = (
        _skill_gaps(assessment, TECHNICAL_SKILL_FIELD_LABELS, career.required_technical_skills, 'Technical')
        + _skill_gaps(assessment, SOFT_SKILL_FIELD_LABELS, career.required_soft_skills, 'Soft')
    )

    required_langs = _csv(career.required_programming_languages)
    known = {lang.lower() for lang in _csv(assessment.programming_languages)}
    languages_missing = [_lang_label(l) for l in required_langs if l.lower() not in known]
    languages_have = [_lang_label(l) for l in required_langs if l.lower() in known]

    # weekly hours: subject work that still needs attention vs. what the student logs
    weekly_needed = sum(r['hours'] for r in focus if r['status'] != 'strong')
    weekly_needed = max(weekly_needed, STUDY_BANDS.get(career.min_study_time, (None, 0))[1])
    current_label = STUDY_BANDS[study_time][0] if study_time in STUDY_BANDS else None
    recommended_label = STUDY_BANDS[career.min_study_time][0] if career.min_study_time in STUDY_BANDS else None

    if study_time is None:
        study_status = 'unknown'
    elif career.min_study_time is not None and study_time < career.min_study_time:
        study_status = 'low'
    else:
        study_status = 'ok'

    study = {
        'current_label': current_label,
        'recommended_label': recommended_label,
        'weekly_hours': weekly_needed,
        'status': study_status,
    }

    steps = []
    urgent = [r for r in focus if r['status'] == 'needs_work']
    unknown = [r for r in focus if r['status'] == 'no_marks']
    if urgent or unknown:
        items = [f"{r['name']}: raise from {r['current']:.0f}% to {r['target']:.0f}%+ (~{r['hours']} h/week)" for r in urgent]
        items += [
            f"{r['name']}: enter your marks so progress can be tracked (start with ~{r['hours']} h/week)"
            if r['in_courses'] else
            f"{r['name']}: add it to your subjects, then enter marks (start with ~{r['hours']} h/week)"
            for r in unknown
        ]
        steps.append({'title': 'Now: fix your weakest subjects', 'items': items})
    if skills or languages_missing:
        items = [f"{g['label']}: {g['rating']}/5 to {g['target']}/5" for g in skills]
        if languages_missing:
            items.append(f"Learn {', '.join(languages_missing)}")
        steps.append({'title': 'Next: build the skills this path needs', 'items': items})
    maintain = [r for r in focus if r['status'] in ('on_track', 'strong')]
    if maintain:
        steps.append({
            'title': 'Keep up: protect what is already working',
            'items': [f"{r['name']}: {r['current']:.0f}% (~{r['hours']} h/week to maintain)" for r in maintain],
        })
    if study_status == 'low':
        steps.append({
            'title': 'Study routine',
            'items': [f"Move from {current_label} to at least {recommended_label}"],
        })

    return {'focus_subjects': focus, 'skills': skills, 'languages_missing': languages_missing,
            'languages_have': languages_have, 'study': study, 'steps': steps}


def _short_tip(roadmap):
    """One short, data-driven sentence for cards and summaries."""
    focus = roadmap['focus_subjects']
    weak = next((r for r in focus if r['status'] == 'needs_work'), None)
    if weak:
        tip = f"Raise {weak['name']} from {weak['current']:.0f}% to {weak['target']:.0f}%+ (~{weak['hours']} h/week)."
        if roadmap['study']['status'] == 'low':
            tip += f" Aim for {roadmap['study']['recommended_label']}."
        return tip
    unknown = next((r for r in focus if r['status'] == 'no_marks'), None)
    if unknown:
        if not unknown['in_courses']:
            return f"Add {unknown['name']} to your subjects to see how close you are."
        return f"Add marks for {unknown['name']} to see how close you are."
    if roadmap['study']['status'] == 'low':
        return f"Your grades fit, but this path needs {roadmap['study']['recommended_label']} of study."
    if roadmap['skills']:
        skill = roadmap['skills'][0]
        return f"Grades look solid. Next: lift {skill['label']} to {skill['target']}/5."
    if roadmap['languages_missing']:
        return f"Grades look solid. Next: learn {', '.join(roadmap['languages_missing'])}."
    return "Grades, skills and study time are on track for this path."


def generate_suggestions(assessment, student_subjects, study_time=None):
    """
    Returns the ranked list of CareerSuggestion objects for an assessment,
    each carrying in-memory `.tip` and `.roadmap` attributes. Safe to call
    repeatedly: rows are updated in place (not deleted and recreated), and
    rows for careers that no longer exist are removed.
    """
    careers = list(CareerProfile.objects.all())
    CareerSuggestion.objects.filter(assessment=assessment).exclude(career__in=careers).delete()

    suggestions = []
    for career in careers:
        soft_score, soft_gaps = _rating_match(assessment, SOFT_SKILL_FIELD_LABELS, career.required_soft_skills)
        tech_score, tech_gaps = _rating_match(assessment, TECHNICAL_SKILL_FIELD_LABELS, career.required_technical_skills)
        subject_score, subject_gaps = _subject_match(student_subjects, career)
        lang_score, lang_gaps = _programming_language_match(assessment, career)
        interest_score, interest_gaps = _interest_match(assessment, career)
        study_score, study_gaps = _study_time_match(study_time, career)

        match_score = round(
            (subject_score * WEIGHT_SUBJECTS) +
            (soft_score * WEIGHT_SOFT_SKILLS) +
            (tech_score * WEIGHT_TECHNICAL_SKILLS) +
            (lang_score * WEIGHT_PROGRAMMING_LANGUAGES) +
            (interest_score * WEIGHT_INTEREST) +
            (study_score * WEIGHT_STUDY_TIME), 1
        )

        all_gaps = soft_gaps + tech_gaps + subject_gaps + lang_gaps + interest_gaps + study_gaps
        gap_notes = "; ".join(all_gaps) or "No major gaps identified."

        suggestion, _ = CareerSuggestion.objects.update_or_create(
            assessment=assessment, career=career,
            defaults={'match_score': match_score, 'gap_notes': gap_notes},
        )
        suggestion.roadmap = build_roadmap(assessment, student_subjects, career, study_time)
        suggestion.tip = _short_tip(suggestion.roadmap)
        suggestions.append(suggestion)

    suggestions.sort(key=lambda s: s.match_score, reverse=True)
    return suggestions
