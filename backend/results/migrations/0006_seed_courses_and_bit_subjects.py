from django.db import migrations


COURSES = [
    "BIT",
    "BBA",
    "MBA",
    "B.Tech IT",
    "B.Tech CSE",
    "M.Tech AI",
    "B.Sc Data Science",
]

BIT_SUBJECTS = {
    1: ["Introduction to Programming", "Mathematics I", "Computer Fundamentals", "Communication Skills"],
    2: ["Object Oriented Programming", "Mathematics II", "Digital Logic", "Web Development"],
    3: ["Data Structures", "Database Systems", "Operating System", "Statistics"],
    4: ["Software Engineering", "Computer Networking", "Human Computer Interaction", "Design"],
    5: ["Web Development II", "System Administration", "Data Analysis", "Management"],
    6: ["Machine Learning Fundamentals", "Cloud Computing", "Business", "Project Management"],
    7: ["Advanced Database", "Cybersecurity Fundamentals", "Mobile App Development", "Research Methodology"],
    8: ["Final Year Project", "Professional Practice", "Elective"],
}


def code_for(course_short, semester, index):
    return f"{course_short}{semester}{index:02d}"


def seed_courses_and_subjects(apps, schema_editor):
    Course = apps.get_model('students', 'Course')
    Subject = apps.get_model('results', 'Subject')

    course_objs = {}
    for name in COURSES:
        course, _ = Course.objects.get_or_create(name=name)
        course_objs[name] = course

    bit_course = course_objs["BIT"]
    for semester, subjects in BIT_SUBJECTS.items():
        for idx, subject_name in enumerate(subjects, start=1):
            Subject.objects.get_or_create(
                name=subject_name,
                course=bit_course,
                semester=semester,
                defaults={'code': code_for("BIT", semester, idx)},
            )


def remove_seed(apps, schema_editor):
    Course = apps.get_model('students', 'Course')
    Subject = apps.get_model('results', 'Subject')
    Subject.objects.filter(course__name="BIT").delete()
    Course.objects.filter(name__in=COURSES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_course_student_course'),
        ('results', '0005_subject_course_subject_semester'),
    ]

    operations = [
        migrations.RunPython(seed_courses_and_subjects, remove_seed),
    ]