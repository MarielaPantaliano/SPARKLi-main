from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.auth import get_user_model


class CustomUserManager(BaseUserManager):
    def create_user(self, username, name, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            name=name,
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
   
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)


        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')


        return self.create_user(email=email, password=password, **extra_fields)


class Teacherrecords(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(db_column='ID', primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser=models.BooleanField(default=True)


    objects = CustomUserManager()


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']


    class Meta:
        managed = False
        db_table = 'teacherrecords'


    def __str__(self):
        return self.email


class Studentrecords(models.Model):
    id = models.AutoField(primary_key=True)
    teacher = models.ForeignKey('Teacherrecords', on_delete=models.CASCADE)  # Add this line
    name = models.CharField(db_column='name', max_length=255, blank=True, null=True)
    age = models.IntegerField(db_column='age', blank=True, null=True)
    gradesection = models.CharField(db_column='gradesection', max_length=50, blank=True, null=True)
    date = models.DateField(db_column='date', blank=True, null=True)
    gradelevel = models.CharField(db_column='gradelevel', max_length=50, blank=True, null=True)
    assessment = models.CharField(db_column='assessment', max_length=255, blank=True, null=True)
    total_miscues = models.IntegerField(db_column='total_miscues', blank=True, null=True, default=0)
    oral_reading_score = models.IntegerField(db_column='oral_reading_score', blank=True, null=True, default=0)
    reading_level = models.CharField(db_column='reading_level', max_length=255, blank=True, null=True, default=0)
    post_total_miscues = models.IntegerField(db_column='post_total_miscues', blank=True, null=True, default=0)
    post_oral_reading_score = models.IntegerField(db_column='post_oral_reading_score', blank=True, null=True, default=0)
    post_reading_level = models.CharField(db_column='post_reading_level', max_length=255, blank=True, null=True, default=0)
    
    # Pre-assessment fields
    pre_total_scores = models.CharField(db_column='pre_total_scores', max_length=25, blank=True, null=True, default=0)
    pre_literal_scores = models.CharField(db_column='pre_literal_scores', max_length=25, blank=True, null=True, default=0)
    pre_inferential_scores = models.CharField(db_column='pre_inferential_scores', max_length=25, blank=True, null=True, default=0)
    pre_applied_scores = models.CharField(db_column='pre_applied_scores', max_length=25, blank=True, null=True, default=0)
    pre_literal_fb = models.CharField(db_column='pre_literal_fb', max_length=255, blank=True, null=True, default=0)
    pre_inferential_fb = models.CharField(db_column='pre_inferential_fb', max_length=255, blank=True, null=True, default=0)
    pre_applied_fb = models.CharField(db_column='pre_applied_fb', max_length=255, blank=True, null=True, default=0)
    pre_level_fb = models.CharField(db_column='pre_level_fb', max_length=255, blank=True, null=True, default=0)


    # Post-assessment fields
    post_total_scores = models.CharField(db_column='post_total_scores', max_length=25, blank=True, null=True, default=0)
    post_literal_scores = models.CharField(db_column='post_literal_scores', max_length=25, blank=True, null=True, default=0)
    post_inferential_scores = models.CharField(db_column='post_inferential_scores', max_length=25, blank=True, null=True, default=0)
    post_applied_scores = models.CharField(db_column='post_applied_scores', max_length=25, blank=True, null=True, default=0)
    post_literal_fb = models.CharField(db_column='post_literal_fb', max_length=255, blank=True, null=True, default=0)
    post_inferential_fb = models.CharField(db_column='post_inferential_fb', max_length=255, blank=True, null=True, default=0)
    post_applied_fb = models.CharField(db_column='post_applied_fb', max_length=255, blank=True, null=True, default=0)
    post_level_fb = models.CharField(db_column='post_level_fb', max_length=255, blank=True, null=True, default=0)

    class Meta:
        managed = False
        db_table = 'studentrecords'


class PreTestPassage(models.Model):
    pretest_passage_id = models.AutoField(primary_key=True)
    pretest_grade_level = models.IntegerField()
    pretest_passage_title = models.TextField()
    pretest_passage = models.TextField()
    pretest_passage_prompt = models.TextField()
    teacher = models.ForeignKey(Teacherrecords, on_delete=models.CASCADE)


    def __str__(self):
        return f"Grade {self.pretest_grade_level} Pre-Test Passage {self.pretest_passage_title} {self.pretest_passage}"


class PreTestQuestions(models.Model):
    pretest_questions_id = models.AutoField(primary_key=True)
    pretest_passage = models.ForeignKey(PreTestPassage, on_delete=models.CASCADE)
    pretest_grade_level = models.IntegerField()
    pretest_question = models.TextField()
    teacher = models.ForeignKey(Teacherrecords, on_delete=models.CASCADE)


    def __str__(self):
        return self.pretest_question


class PreTestAnswers(models.Model):
    pretest_answers_id = models.AutoField(primary_key=True)
    pretest_question = models.ForeignKey(PreTestQuestions, on_delete=models.CASCADE)
    pretest_passage = models.ForeignKey(PreTestPassage, on_delete=models.CASCADE)
    pretest_grade_level = models.IntegerField()
    pretest_answer = models.TextField()
    teacher = models.ForeignKey('Teacherrecords', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('pretest_question', 'pretest_answer', 'teacher')

    def __str__(self):
        return self.pretest_answer
    
class PostTestPassage(models.Model):
    posttest_passage_id = models.AutoField(primary_key=True)
    posttest_grade_level = models.IntegerField()
    posttest_passage_title = models.TextField()
    posttest_passage = models.TextField()
    posttest_passage_prompt = models.TextField()
    teacher = models.ForeignKey(Teacherrecords, on_delete=models.CASCADE)


    def __str__(self):
        return f"Grade {self.posttest_grade_level} Post-Test Passage: {self.posttest_passage_title}"


class PostTestQuestions(models.Model):
    posttest_questions_id = models.AutoField(primary_key=True)
    posttest_passage = models.ForeignKey(PostTestPassage, on_delete=models.CASCADE)
    posttest_grade_level = models.IntegerField()
    posttest_question = models.TextField()
    teacher = models.ForeignKey(Teacherrecords, on_delete=models.CASCADE)


    def __str__(self):
        return self.posttest_question


class PostTestAnswers(models.Model):
    posttest_answers_id = models.AutoField(primary_key=True)
    posttest_question = models.ForeignKey(PostTestQuestions, on_delete=models.CASCADE)
    posttest_passage = models.ForeignKey(PostTestPassage, on_delete=models.CASCADE)
    posttest_grade_level = models.IntegerField()
    posttest_answer = models.TextField()
    teacher = models.ForeignKey(Teacherrecords, on_delete=models.CASCADE)


    def __str__(self):
        return self.posttest_answer
