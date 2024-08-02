from django.core.management.base import BaseCommand
from WebApp.models import PreTestPassage, PreTestQuestions, PreTestAnswers, Teacherrecords
from SPARKLi.WebApp.questions import QUESTIONS_AND_ANSWERS

class Command(BaseCommand):
    help = 'Populate default questions and answers for specific passages'

    def handle(self, *args, **kwargs):
        teacher = Teacherrecords.objects.first()  # Adjust this to get the correct teacher

        for grade_level, content in QUESTIONS_AND_ANSWERS.items():
            passage = PreTestPassage.objects.get(pretest_grade_level=grade_level, teacher=teacher)
            
            for idx, question_text in enumerate(content["questions"], start=1):
                question, created = PreTestQuestions.objects.get_or_create(
                    pretest_passage=passage,
                    pretest_grade_level=grade_level,
                    pretest_question=question_text,
                    teacher=teacher
                )
                
                answers = content["answers"].get(f"answ{idx}", [])
                for answer_text in answers:
                    try:
                        answer = PreTestAnswers.objects.get(
                            pretest_question=question,
                            pretest_passage=passage,
                            pretest_grade_level=grade_level,
                            pretest_answer=answer_text,
                            teacher=teacher
                        )
                    except PreTestAnswers.DoesNotExist:
                        answer = PreTestAnswers.objects.create(
                            pretest_question=question,
                            pretest_passage=passage,
                            pretest_grade_level=grade_level,
                            pretest_answer=answer_text,
                            teacher=teacher
                        )

        self.stdout.write(self.style.SUCCESS('Successfully populated questions and answers'))