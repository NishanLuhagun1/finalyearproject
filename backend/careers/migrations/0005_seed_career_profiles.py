from django.db import migrations


CAREER_PROFILES = [
    {
        "name": "Software Engineer",
        "description": "Designs, builds, and maintains software applications and systems.",
        "min_predicted_score": 65,
        "required_subjects": "Programming,Data Structures,Software Engineering,Web Development",
        "required_soft_skills": "problem_solving_skill,critical_thinking_skill,adaptability_skill,time_management_skill",
    },
    {
        "name": "Data Analyst",
        "description": "Collects, cleans, and interprets data to support business decisions.",
        "min_predicted_score": 65,
        "required_subjects": "Statistics,Database,Data Structures,Mathematics",
        "required_soft_skills": "problem_solving_skill,critical_thinking_skill,communication_skill",
    },
    {
        "name": "UI/UX Designer",
        "description": "Designs usable, engaging interfaces and experiences for digital products.",
        "min_predicted_score": 60,
        "required_subjects": "Web Development,Human Computer Interaction,Design",
        "required_soft_skills": "creativity_skill,communication_skill,adaptability_skill",
    },
    {
        "name": "Network Administrator",
        "description": "Sets up, maintains, and secures an organization's computer networks.",
        "min_predicted_score": 60,
        "required_subjects": "Networking,Operating System,System Administration",
        "required_soft_skills": "problem_solving_skill,time_management_skill,adaptability_skill",
    },
    {
        "name": "Business Analyst",
        "description": "Bridges business needs and technical solutions through analysis and planning.",
        "min_predicted_score": 60,
        "required_subjects": "Management,Business,Database,Statistics",
        "required_soft_skills": "communication_skill,critical_thinking_skill,leadership_skill,teamwork_skill",
    },
]


def seed_career_profiles(apps, schema_editor):
    CareerProfile = apps.get_model('careers', 'CareerProfile')
    for profile in CAREER_PROFILES:
        CareerProfile.objects.update_or_create(
            name=profile["name"],
            defaults={
                "description": profile["description"],
                "min_predicted_score": profile["min_predicted_score"],
                "required_subjects": profile["required_subjects"],
                "required_soft_skills": profile["required_soft_skills"],
            },
        )


def remove_career_profiles(apps, schema_editor):
    CareerProfile = apps.get_model('careers', 'CareerProfile')
    names = [p["name"] for p in CAREER_PROFILES]
    CareerProfile.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('careers', '0004_alter_careerassessment_interest_area'),
    ]

    operations = [
        migrations.RunPython(seed_career_profiles, remove_career_profiles),
    ]