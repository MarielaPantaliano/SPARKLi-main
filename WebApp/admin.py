from django.contrib import admin
from .models import (
    Teacherrecords,
    Studentrecords,
    PreTestPassage,
    PreTestQuestions,
    PreTestAnswers,
    PostTestPassage,
    PostTestQuestions,
    PostTestAnswers
)

class PreTestPassageAdmin(admin.ModelAdmin):
    list_display = ('pretest_passage_title', 'pretest_grade_level', 'teacher')
    search_fields = ('pretest_passage_title', 'teacher__username')

class PreTestQuestionsAdmin(admin.ModelAdmin):
    list_display = ('pretest_question', 'pretest_grade_level', 'teacher')
    search_fields = ('pretest_question', 'teacher__username')

class PreTestAnswersAdmin(admin.ModelAdmin):
    list_display = ('pretest_answer', 'pretest_grade_level', 'teacher')
    search_fields = ('pretest_answer', 'teacher__username')

class PostTestPassageAdmin(admin.ModelAdmin):
    list_display = ('posttest_passage_title', 'posttest_grade_level', 'teacher')
    search_fields = ('posttest_passage_title', 'teacher__username')

class PostTestQuestionsAdmin(admin.ModelAdmin):
    list_display = ('posttest_question', 'posttest_grade_level', 'teacher')
    search_fields = ('posttest_question', 'teacher__username')

class PostTestAnswersAdmin(admin.ModelAdmin):
    list_display = ('posttest_answer', 'posttest_grade_level', 'teacher')
    search_fields = ('posttest_answer', 'teacher__username')

# Register your models here.
admin.site.register(Teacherrecords)
admin.site.register(Studentrecords)
admin.site.register(PreTestPassage, PreTestPassageAdmin)
admin.site.register(PreTestQuestions, PreTestQuestionsAdmin)
admin.site.register(PreTestAnswers, PreTestAnswersAdmin)
admin.site.register(PostTestPassage, PostTestPassageAdmin)
admin.site.register(PostTestQuestions, PostTestQuestionsAdmin)
admin.site.register(PostTestAnswers, PostTestAnswersAdmin)