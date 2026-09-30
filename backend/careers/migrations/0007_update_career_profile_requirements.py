from django.db import migrations


PROFILE_UPDATES = {
    "Software Engineer": {
        "required_technical_skills": "programming_skill,web_dev_skill",
        "required_programming_languages": "Python,Java,JavaScript",
        "min_study_time": 3,
    },
    "Data Analyst": {
        "required_technical_skills": "programming_skill,database_skill",
        "required_programming_languages": "Python,SQL",
        "min_study_time": 3,
    },
    "UI/UX Designer": {
        "required_technical_skills": "web_dev_skill",
        "required_programming_languages": "HTML,CSS,JavaScript",
        "min_study_time": 2,
    },
    "Network Administrator": {
        "required_technical_skills": "networking_skill",
        "required_programming_languages": "",
        "min_study_time": 2,
    },
    "Business Analyst": {
        "required_technical_skills": "database_skill",
        "required_programming_languages": "SQL",
        "min_study_time": 2,
    },
}


def update_career_profiles(apps, schema_editor):
    CareerProfile = apps.get_model('careers', 'CareerProfile')
    for name, updates in PROFILE_UPDATES.items():
        CareerProfile.objects.filter(name=name).update(**updates)


def revert_career_profiles(apps, schema_editor):
    CareerProfile = apps.get_model('careers', 'CareerProfile')
    CareerProfile.objects.filter(name__in=PROFILE_UPDATES.keys()).update(
        required_technical_skills="", required_programming_languages="", min_study_time=None
    )


class Migration(migrations.Migration):

    dependencies = [
        ('careers', '0006_careerassessment_database_skill_and_more'),
    ]

    operations = [
        migrations.RunPython(update_career_profiles, revert_career_profiles),
    ]