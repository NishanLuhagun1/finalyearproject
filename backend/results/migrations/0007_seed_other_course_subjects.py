from django.db import migrations


COURSE_SUBJECTS = {
    "BBA": {
        "prefix": "BBA",
        "subjects": {
            1: ["Principles of Management", "Business Communication", "Financial Accounting", "Microeconomics"],
            2: ["Organizational Behavior", "Business Mathematics", "Macroeconomics", "Business Law"],
            3: ["Marketing Management", "Human Resource Management", "Cost Accounting", "Business Statistics"],
            4: ["Financial Management", "Operations Management", "Consumer Behavior", "Business Ethics"],
            5: ["Strategic Management", "International Business", "Taxation", "Entrepreneurship"],
            6: ["Management Information Systems", "Supply Chain Management", "Investment Management", "Research Methodology"],
            7: ["Project Management", "Digital Marketing", "Corporate Governance", "Elective I"],
            8: ["Business Policy", "Capstone Project", "Elective II", "Professional Practice"],
        },
    },
    "MBA": {
        "prefix": "MBA",
        "subjects": {
            1: ["Managerial Economics", "Organizational Behavior", "Financial Accounting", "Business Communication"],
            2: ["Marketing Management", "Human Resource Management", "Operations Management", "Business Research Methods"],
            3: ["Strategic Management", "Financial Management", "Business Analytics", "Elective I"],
            4: ["International Business", "Entrepreneurship", "Capstone Project", "Elective II"],
        },
    },
    "B.Tech IT": {
        "prefix": "BTI",
        "subjects": {
            1: ["Engineering Mathematics I", "Programming in C", "Physics", "Engineering Drawing"],
            2: ["Engineering Mathematics II", "Data Structures", "Digital Electronics", "Object Oriented Programming"],
            3: ["Database Management Systems", "Computer Organization", "Discrete Mathematics", "Operating Systems"],
            4: ["Software Engineering", "Computer Networks", "Design and Analysis of Algorithms", "Web Technologies"],
            5: ["Java Programming", "Information Security", "Cloud Computing", "Human Computer Interaction"],
            6: ["Machine Learning", "Mobile Application Development", "Big Data Analytics", "Software Testing"],
            7: ["Internet of Things", "Cybersecurity", "Project Management", "Elective I"],
            8: ["Major Project", "Professional Ethics", "Elective II", "Industrial Training"],
        },
    },
    "B.Tech CSE": {
        "prefix": "BTC",
        "subjects": {
            1: ["Engineering Mathematics I", "Programming Fundamentals", "Physics", "Engineering Graphics"],
            2: ["Engineering Mathematics II", "Data Structures and Algorithms", "Digital Logic Design", "Object Oriented Programming"],
            3: ["Database Management Systems", "Computer Organization and Architecture", "Discrete Structures", "Operating Systems"],
            4: ["Design and Analysis of Algorithms", "Computer Networks", "Theory of Computation", "Software Engineering"],
            5: ["Compiler Design", "Artificial Intelligence", "Web Development", "Computer Graphics"],
            6: ["Machine Learning", "Distributed Systems", "Cryptography and Network Security", "Elective I"],
            7: ["Cloud Computing", "Deep Learning", "Capstone Project I", "Elective II"],
            8: ["Capstone Project II", "Professional Ethics", "Industrial Training", "Elective III"],
        },
    },
    "M.Tech AI": {
        "prefix": "MTA",
        "subjects": {
            1: ["Mathematical Foundations for AI", "Machine Learning", "Advanced Data Structures", "Research Methodology"],
            2: ["Deep Learning", "Natural Language Processing", "Computer Vision", "Big Data Systems"],
            3: ["Reinforcement Learning", "AI Ethics and Governance", "Advanced Elective I", "Thesis Phase I"],
            4: ["Advanced Elective II", "Thesis Phase II", "Seminar", "Industry Internship"],
        },
    },
    "B.Sc Data Science": {
        "prefix": "BDS",
        "subjects": {
            1: ["Introduction to Programming", "Calculus", "Statistics I", "Communication Skills"],
            2: ["Data Structures", "Linear Algebra", "Statistics II", "Database Fundamentals"],
            3: ["Python for Data Science", "Data Visualization", "Statistical Inference", "Operating Systems"],
            4: ["Machine Learning Fundamentals", "Data Warehousing", "Data Ethics", "Web Scraping and APIs"],
            5: ["Big Data Technologies", "Deep Learning", "Business Intelligence", "Data Mining"],
            6: ["Natural Language Processing", "Cloud Computing for Data Science", "Time Series Analysis", "Elective I"],
            7: ["MLOps and Model Deployment", "Data Governance", "Capstone Project I", "Elective II"],
            8: ["Capstone Project II", "Data Science in Industry", "Professional Ethics", "Elective III"],
        },
    },
}


def code_for(prefix, semester, index):
    return f"{prefix}{semester}{index:02d}"


def seed_subjects(apps, schema_editor):
    Course = apps.get_model('students', 'Course')
    Subject = apps.get_model('results', 'Subject')

    for course_name, data in COURSE_SUBJECTS.items():
        try:
            course = Course.objects.get(name=course_name)
        except Course.DoesNotExist:
            continue

        for semester, subjects in data["subjects"].items():
            for idx, subject_name in enumerate(subjects, start=1):
                Subject.objects.get_or_create(
                    name=subject_name,
                    course=course,
                    semester=semester,
                    defaults={'code': code_for(data["prefix"], semester, idx)},
                )


def remove_subjects(apps, schema_editor):
    Course = apps.get_model('students', 'Course')
    Subject = apps.get_model('results', 'Subject')
    Subject.objects.filter(course__name__in=COURSE_SUBJECTS.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0006_seed_courses_and_bit_subjects'),
    ]

    operations = [
        migrations.RunPython(seed_subjects, remove_subjects),
    ]