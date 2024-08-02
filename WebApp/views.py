from django.http import HttpResponse
import json
import random
import string
from django.utils.html import strip_tags
from django.shortcuts import render, redirect
import speech_recognition as sr
from .utils import analyze_reading_mistakes, calculate_reading_speed, wer
from datetime import datetime
from django.utils import timezone
import dateutil.parser
from django.shortcuts import render
import spacy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from fuzzywuzzy import fuzz
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import numpy as np
import re
from .models import PostTestAnswers, PostTestPassage, PostTestQuestions, PreTestAnswers, Studentrecords
from .models import PreTestPassage, PreTestQuestions
from .forms import PostTestAnswerForm, PostTestPassageForm, PostTestQuestionForm, PreTestAnswerForm, PreTestPassageForm, PreTestQuestionForm, TeacherForm
from django.contrib.auth import update_session_auth_hash
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import TeacherForm, PasswordChangeForm, VerificationCodeForm
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ContentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .utils import generate_otp
from django.contrib.auth.hashers import identify_hasher
import pytz
import logging
import pickle
import pandas as pd
from django.contrib.auth import logout
from .models import PreTestQuestions, PreTestAnswers
import logging
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .default_answers import GRADE2_POST_ANSWERS, GRADE3_POST_ANSWERS, GRADE4_POST_ANSWERS, GRADE2_PRE_ANSWERS, GRADE3_PRE_ANSWERS, GRADE4_PRE_ANSWERS
from django.utils import timezone


logger = logging.getLogger(__name__)


Teacherrecordss = get_user_model()


def error_400(request, exception):
    logger.error('400 Error Handler Called')
    request.session['last_error'] = '400'
    return render(request, 'WebApp/error_400.html', {'status_code': 400}, status=400)


def error_403(request, exception):
    logger.error('403 Error Handler Called')
    request.session['last_error'] = '403'
    return render(request, 'WebApp/error_403.html', {'status_code': 403}, status=403)


def error_404(request, exception):
    logger.error('404 Error Handler Called')
    request.session['last_error'] = '404'
    return render(request, 'WebApp/error_404.html', {'status_code': 404}, status=404)


def error_500(request):
    logger.error('500 Error Handler Called')
    request.session['last_error'] = '500'
    return render(request, 'WebApp/error_500.html', {'status_code': 500}, status=500)


def index(request):
    context = {}
    return render(request, "WebApp/index.html", context)


MAX_LOGIN_ATTEMPTS = 3


def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')


        try:
            # Retrieve user by email to inspect password hash
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                logger.info(f"User found: {user}")
                logger.info(f"Password hash for user {email}: {user.password}")
                hasher = identify_hasher(user.password)
                logger.info(f"Password hasher identified: {hasher}")
            except User.DoesNotExist:
                logger.warning(f"No user found with email: {email}")


            # Attempt to authenticate user
            teacherrecords = authenticate(request, username=email, password=password)


            if teacherrecords is not None:
                # Successful login
                login(request, teacherrecords)


                # Fetch teacher's name
                teacher_name = teacherrecords.name


                # Fetch associated student records
                students = Studentrecords.objects.filter(teacher_id=teacherrecords.id)


                return render(request, "WebApp/dashboard_page.html", {"teacher": teacherrecords, "students": students})
            else:
                # Failed login attempt
                if 'login_attempts' in request.session:
                    request.session['login_attempts'] += 1
                else:
                    request.session['login_attempts'] = 1


                if request.session['login_attempts'] >= 3:  # Assuming 3 as MAX_LOGIN_ATTEMPTS
                    messages.error(request, 'You have entered the wrong email and password three times. Please reset your password.')
                    return redirect('password_reset')  # Redirect to your password reset view
                else:
                    messages.error(request, 'Invalid email or password. Please try again.')
                    return redirect('login_page')  # Redirect back to your login page


        except ValueError as e:
            # Log the error
            logger.error(f"Error during authentication: {e}")
            messages.error(request, 'An error occurred during login. Please try again later.')
            return redirect('login_page')


    else:
        # Handle GET request for login page
        return render(request, "WebApp/login_page.html")




def logout_view(request):
    logout(request)
    return redirect('login_page')


def forgot_password_page(request):
    context = {}
    return render(request, "WebApp/forgot_password_page.html", context)


def about_page(request):
    context = {}
    return render(request, "WebApp/about_page.html", context)


@login_required
def dashboard_view(request):
    teacher = request.user
    students = Studentrecords.objects.filter(teacher=teacher)
    return render(request, 'WebApp/dashboard_page.html', {'students': students, 'teacher': teacher})


@login_required
def profile_page(request):
    teacher = request.user


    context = {
        'teacher_name': teacher.name,
        'teacher_username': teacher.username,
        'teacher_email': teacher.email,
    }
    return render(request, "WebApp/profile_page.html", context)
   
def change_password(request):
    teacher = request.user
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.POST)
        if password_form.is_valid():
            old_password = password_form.cleaned_data['old_password']
            new_password = password_form.cleaned_data['new_password']
            confirm_password = password_form.cleaned_data['confirm_password']
           
            if teacher.check_password(old_password) and new_password == confirm_password:
                verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                request.session['verification_code'] = verification_code
                request.session['new_password'] = new_password
               
                EmailMultiAlternatives(
                    'Your Verification Code',
                    f'Your verification code is {verification_code}',
                    'from@example.com',
                    [teacher.email],
                    fail_silently=False,
                )
                return redirect('verify_code')
    else:
        password_form = PasswordChangeForm()
   
    context = {
        'password_form': password_form,
    }
    return render(request, 'WebApp/change_password.html', context)


@login_required
def student_records_view(request):
    students = Studentrecords.objects.all()
    return render(request, 'WebApp/dashboard_page.html', {'students': students})




def signup_page(request):
    if request.method == "POST":
        id = request.POST.get('id')
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')


        # Validate user input
        if not id.isdigit() or len(id) != 7:
            messages.error(request, "Teacher's ID must be exactly 7 digits.")
            return redirect('signup_page')
       
        if len(username) > 30:
            messages.error(request, "Last Name must be 30 characters or less.")
            return redirect('signup_page')
       
        if len(name) > 30:
            messages.error(request, " First Name must be 30 characters or less.")
            return redirect('signup_page')
       
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            messages.error(request, "Invalid email format.")
            return redirect('signup_page')


        if len(password) < 8 or len(password) > 16:
            messages.error(request, "Password must be between 8 and 16 characters long.")
            return redirect('signup_page')
       
        if not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one digit.")
            return redirect('signup_page')


        if not re.search(r'[A-Za-z]', password):
            messages.error(request, "Password must contain at least one letter.")
            return redirect('signup_page')
       
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect('signup_page')


        if password != password1:
            messages.error(request, "Passwords don't match.")
            return redirect('signup_page')
       
        if Teacherrecordss.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup_page')


        # Generate OTP
        otp = generate_otp()


        # Store user information and OTP in session
        request.session['signup_data'] = {
            'id': id,
            'username': username,
            'name': name,
            'email': email,
            'password': password,
        }
        request.session['otp'] = otp
        request.session['otp_expiry'] = (timezone.now() + timezone.timedelta(minutes=10)).isoformat()


        # Render email template
        try:
            html_message = render_to_string('WebApp/otp_email.html', {'name': name, 'otp': otp})
            plain_message = strip_tags(html_message)
            subject = 'SPARKLI | Verify OTP'


            # Create email
            email_message = EmailMultiAlternatives(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()


            logger.info(f"OTP email sent to {email}")


        except Exception as e:
            logger.error(f"Failed to send OTP email: {e}")
            messages.error(request, "Failed to send OTP email. Please try again.")
            return redirect('signup_page')


        # Redirect to OTP verification page
        return redirect('verify_code')


    return render(request, 'WebApp/signup_page.html')




def verify_code(request):
    if request.method == "POST":
        otp1 = request.POST.get('otp1')
        otp2 = request.POST.get('otp2')
        otp3 = request.POST.get('otp3')
        otp4 = request.POST.get('otp4')
        otp5 = request.POST.get('otp5')
        otp6 = request.POST.get('otp6')


        # Combine OTP input fields
        otp = otp1 + otp2 + otp3 + otp4 + otp5 + otp6


        # Retrieve OTP and user data from session
        session_otp = request.session.get('otp')
        signup_data = request.session.get('signup_data')
        otp_expiry_str = request.session.get('otp_expiry')


        if not signup_data or not otp_expiry_str:
            messages.error(request, "OTP data missing or expired.")
            return redirect('signup_page')


        try:
            otp_expiry = datetime.fromisoformat(otp_expiry_str).astimezone(pytz.utc)
        except ValueError:
            messages.error(request, "OTP expiry date is invalid.")
            return redirect('signup_page')


        if timezone.now() > otp_expiry:
            messages.error(request, "OTP expired.")
            return redirect('signup_page')


        if otp == session_otp:
            # OTP is correct; create the user and clear OTP from session
            try:
                Teacherrecordss.objects.create_user(
                    id=signup_data['id'],
                    username=signup_data['username'],
                    name=signup_data['name'],
                    email=signup_data['email'],
                    password=signup_data['password']
                )
                messages.success(request, "Account activated successfully.")
                request.session.pop('otp', None)  # Clear OTP from session
                request.session.pop('signup_data', None)  # Clear signup data from session
                return redirect('login_page')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                return redirect('verify_code')
        else:
            messages.error(request, "Invalid OTP.")
            return redirect('verify_code')


    return render(request, 'WebApp/verify_code.html')

def input_student_info(request):
    if request.method == "POST":
        name = request.POST.get('name')
        age = request.POST.get('age')
        gradesection = request.POST.get('gradesection')
        date = request.POST.get('date')
        gradelevel = request.POST.get('gradelevel')
        assessment = request.POST.get('assessment')


        # Name validation
        if not re.match(r'^[a-zA-Z\s]{1,50}$', name):
            if len(name) > 50:
                messages.error(request, "Name must be less than 50 characters long.")
            else:
                messages.error(request, "Name contains invalid characters. Sorry, only letters (a-z) are allowed.")
            return redirect('/input_student_info.html')
       
        # Age validation
        if not age.isdigit() or not (1 <= int(age) <= 50):
            messages.error(request, "Age must be less than 50.")
            return redirect('/input_student_info.html')
       
        # Grade and section validation
        if not re.match(r'^\d+\s*-\s*[a-zA-Z\s]+$', gradesection.strip()):
            messages.error(request, "Grade and section must be in the format 'number - letters' (e.g., '2 - Rizal' or '2-Rizal').")
            return redirect('/input_student_info.html')
       
         # Date validation
        today = timezone.now().date()
        if not date or date != str(today):
            messages.error(request, "Pretest date must be today's date only.")
            return redirect('/input_student_info.html')




        teacher = request.user


        new_student = Studentrecords.objects.create(
            teacher=teacher,
            name=name,
            age=age,
            gradesection=gradesection,
            date=date,
            gradelevel=gradelevel,
            assessment=assessment
        )
        print('New student created:', new_student)


        request.session['student_id'] = new_student.id


        if gradelevel == 'grade 2':
            if assessment == 'Oral Reading':
                return redirect('g2_pretest_oral')
            elif assessment == 'Listening Comprehension':
                return redirect('g2_pretest_listening')
        elif gradelevel == 'grade 3':
            if assessment == 'Oral Reading':
                return redirect('g3_pretest_oral')
            elif assessment == 'Listening Comprehension':
                return redirect('g3_pretest_listening')
        elif gradelevel == 'grade 4':
            if assessment == 'Oral Reading':
                return redirect('g4_pretest_oral')
            elif assessment == 'Listening Comprehension':
                return redirect('g4_pretest_listening')
        else:
            return redirect('/ReadReadRead.html')


    return render(request, "WebApp/input_student_info.html")

def save_reading_data(request):
    if request.method == 'POST':
        student_id = request.session.get('student_id')
        total_miscues = request.POST.get('total_miscues')
        oral_reading_score = request.POST.get('oral_reading_score')
        reading_level = request.POST.get('reading_level')

        try:
            student_record = Studentrecords.objects.get(id=student_id)
            student_record.total_miscues = total_miscues
            student_record.oral_reading_score = oral_reading_score
            student_record.reading_level = reading_level
            student_record.save()
            return JsonResponse({'status': 'success'})
        except Studentrecords.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student record not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def save_post_reading_data(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        post_total_miscues = request.POST.get('post_total_miscues')
        post_oral_reading_score = request.POST.get('post_oral_reading_score')
        
        print(f"Received data: {student_id}, {post_total_miscues}, {post_oral_reading_score}")


        # Validate input data
        if not student_id:
            return JsonResponse({'status': 'error', 'message': 'Student ID is missing'})
        if not all([post_total_miscues, post_oral_reading_score]):
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'})

        try:
            student_record = Studentrecords.objects.get(id=student_id)
            
            # Assuming these fields are integers, adjust if necessary
            student_record.post_total_miscues = int(post_total_miscues)
            student_record.post_oral_reading_score = float(post_oral_reading_score)
            
            student_record.save() 
            return JsonResponse({'status': 'success'})
        except Studentrecords.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student record not found'})
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid data format: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
@login_required
def save_post_reading_level(request):
    if request.method == 'POST':
        student_id = request.session.get('student_id')
        post_reading_level = request.POST.get('post_reading_level')

        try:
            student_record = Studentrecords.objects.get(id=student_id)
            student_record.post_reading_level = post_reading_level
            student_record.save()
            return JsonResponse({'status': 'success'})
        except Studentrecords.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student record not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def save_reading_level(request):
    if request.method == 'POST':
        student_id = request.session.get('student_id')
        reading_level = request.POST.get('reading_level')

        try:
            student_record = Studentrecords.objects.get(id=student_id)
            student_record.reading_level = reading_level
            student_record.save()
            return JsonResponse({'status': 'success'})
        except Studentrecords.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student record not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def g2_pretest_oral(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)
            word_error_rate = wer(reference_text, transcript)

            print(f"Word Error Rate (WER): {word_error_rate:.2f}")

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'word_error_rate': word_error_rate,
                'mispronunciation_words': reading_mistakes.get('Mispronunciation Words', []),
                'omission_words': reading_mistakes.get('Omission Words', []),
                'substitution_words': reading_mistakes.get('Substitution Words', []),
                'insertion_words': reading_mistakes.get('Insertion Words', []),
                'total_miscues': reading_mistakes.get('Total Miscues', 0),
                'oral_reading_score': reading_mistakes.get('Oral Reading Score', 0),
            }

            return render(request, 'WebApp/g2_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g2_pretest_oral.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "There are many liquids that are good for our health like water, fruit juice and milk. "
        "Milk makes our bones strong. Juice gives us vitamins, while water cleans our body. "
        "Let’s drink milk, juice and water to make us healthy!"
    )

    pretest_passage, created = PreTestPassage.objects.get_or_create(
        pretest_grade_level=2,
        teacher=teacher,
        defaults={
            'pretest_passage': initial_reference_text,
            'pretest_passage_title': 'Liquids Good For You',
            'pretest_passage_prompt': 'Do you want to know the liquids that are good for your health? Read the selection below.'
        }
    )

    default_questions = [
        "What liquids are good for our health?",
        "What can milk do to us?",
        "What does water do to our body?",
        "What might happen if you don’t drink milk, juice or water?",
        "What would you do if your friend offers you softdrink for recess?"
    ]

    questions_map = {}

    for question_text in default_questions:
        question, created = PreTestQuestions.objects.get_or_create(
            pretest_passage=pretest_passage,
            teacher=teacher,
            pretest_question=question_text,
            defaults={
                'pretest_grade_level': 2
            }
        )
        questions_map[question_text] = question

    # Adding default answers based on the grade
    GRADE2_PRE_ANSWERS = {
        "What liquids are good for our health?": ["Milk, juice and water", "milk and water", "milk", "juice and water", "juice", "water"],
        "What can milk do to us?": ["milk makes our bone strong.", "milk strengthens bones.", "milk provides essential nutrients.", "milk provides essential nutrients.",
                                    "drinking milk helps our muscles grow", "milk aids in nerve function and energy levels"],
        "What does water do to our body?": ["Water cleans our body.", "Drinking water flushes out bad stuff from our bodies",
                                            "Water helps flush out waste and toxins from our bodies", "Drinking water keeps us hydrated", "Water helps regulate our body temperature."],
        "What might happen if you don’t drink milk, juice or water?": ["I will get sick.", "I will not grow big and healthy",
                                                                      "your body can become dehydrated", "you might feel tired and sluggish", "prone to getting sick"],
        "What would you do if your friend offers you softdrink for recess?": ["I will not get it because it is not good for snacks.",
                                                                            "Softdrink is not good for our health.",
                                                                            "Thanks for offering, but I prefer to drink water or juice during recess.",
                                                                            "I'll pass on the soda, but I'd love some water or juice if you have any",
                                                                            "Softdrink is bad to our health",
                                                                            "I'll pass on it because it's not a good choice for snacks."]
    }

    for question_text, answers in GRADE2_PRE_ANSWERS.items():
        question = questions_map.get(question_text)
        if question:
            for answer in answers:
                PreTestAnswers.objects.get_or_create(
                    pretest_passage=pretest_passage,
                    teacher=teacher,
                    pretest_grade_level=2,
                    pretest_question=question,
                    defaults={
                        'pretest_answer': answer
                    }
                )

    context = {
        'reference_text': pretest_passage.pretest_passage,
        'pretest_passage_title': pretest_passage.pretest_passage_title,
        'pretest_passage_prompt': pretest_passage.pretest_passage_prompt,
        'pretest_passage_id': pretest_passage.pretest_passage_id
    }

    return render(request, 'WebApp/g2_pretest_oral.html', context)


@login_required
def g2_preoral_questions(request):
    teacher = request.user
    pretest_grade_level = 2   
    passage = get_object_or_404(PreTestPassage, pretest_grade_level=pretest_grade_level, teacher=teacher)
    questions = PreTestQuestions.objects.filter(pretest_passage=passage)

    context = {
        'passage': passage,
        'questions': questions
    }
    
    return render(request, "WebApp/g2_preoral_questions.html", context)



@login_required
def g2_pretest_summary(request):
    teacher = request.user
    questions = PreTestQuestions.objects.filter(pretest_grade_level=2, teacher=teacher)
    context = {
        'questions': questions
    }
    return render(request, "WebApp/g2_pretest_summary.html", context)



def g2_pretest_overall(request):
    student_id = request.GET.get('student')
    if not student_id:
        return HttpResponse("No student ID provided.", status=400)
    
    try:
        student_id = int(student_id)
    except ValueError:
        return HttpResponse("Invalid student ID.", status=400)

    student = get_object_or_404(Studentrecords, id=student_id)
    
    # Prepare context for the template
    context = {
        'student': student,
        'student_id': student_id,
        'total_miscues': student.total_miscues,
        'oral_reading_score': student.oral_reading_score,
        'pre_literal_scores': student.pre_literal_scores,
        'pre_inferential_scores': student.pre_inferential_scores,
        'pre_applied_scores': student.pre_applied_scores,
        'pre_total_scores': student.pre_total_scores,
        'reading_level': student.reading_level,
        'pre_literal_fb': student.pre_literal_fb,
        'pre_inferential_fb': student.pre_inferential_fb,
        'pre_applied_fb': student.pre_applied_fb,
        'pre_level_fb': student.pre_level_fb,
    }
    
    # Render the template with context
    return render(request, "WebApp/g2_pretest_overall.html", context)

@login_required
def g3_pretest_oral(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)
            word_error_rate = wer(reference_text, transcript)

            print(f"Word Error Rate (WER): {word_error_rate:.2f}")

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'word_error_rate': word_error_rate,
                'mispronunciation_words': reading_mistakes.get('Mispronunciation Words', []),
                'omission_words': reading_mistakes.get('Omission Words', []),
                'substitution_words': reading_mistakes.get('Substitution Words', []),
                'insertion_words': reading_mistakes.get('Insertion Words', []),
                'total_miscues': reading_mistakes.get('Total Miscues', 0),
                'oral_reading_score': reading_mistakes.get('Oral Reading Score', 0),
            }

            return render(request, 'WebApp/g3_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g3_pretest_oral.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "“Our Foundation Day will be on September 30,” said Miss Cruz, “What are we going to present?” "
        "“I suggest that we render some folksongs and folk dances,” answered Perla. "
        "“Good. These will remind us of our Filipino culture,” added Ruben. "
        "“Let’s start our practice early. That’s a deal,” insisted Susan."
    )

    pretest_passage, created = PreTestPassage.objects.get_or_create(
        pretest_grade_level=3,
        teacher=teacher,
        defaults={
            'pretest_passage': initial_reference_text,
            'pretest_passage_title': 'A Deal',
            'pretest_passage_prompt': 'How do you celebrate Foundation Day? Read the selection below.'
        }
    )

    g3_default_questions = [
        "Who announced about the foundation day? ",
        "When will be the foundation day?",
        "What was the deal?",
        "Why will they present folksongs and dances?",
        "What other Filipino customs and traditions do you practice?"
    ]

    for question_text in g3_default_questions:
        PreTestQuestions.objects.get_or_create(
            pretest_passage=pretest_passage,
            teacher=teacher,
            pretest_question=question_text,
            defaults={
                'pretest_grade_level': 3
            }
        )

    context = {
        'reference_text': pretest_passage.pretest_passage,
        'pretest_passage_title': pretest_passage.pretest_passage_title,
        'pretest_passage_prompt': pretest_passage.pretest_passage_prompt,
        'pretest_passage_id': pretest_passage.pretest_passage_id
    }

    return render(request, 'WebApp/g3_pretest_oral.html', context)

@login_required
def g3_preoral_questions(request):
    teacher = request.user
    pretest_grade_level = 3   
    passage = get_object_or_404(PreTestPassage, pretest_grade_level=pretest_grade_level, teacher=teacher)
    questions = PreTestQuestions.objects.filter(pretest_passage=passage)

    context = {
        'passage': passage,
        'questions': questions
    }

    return render(request, "WebApp/g3_preoral_questions.html", context)

@login_required
def g3_pretest_summary(request):
    teacher = request.user
    questions = PreTestQuestions.objects.filter(pretest_grade_level=3, teacher=teacher)
    context = {
        'questions': questions
    }
    return render(request, "WebApp/g3_pretest_summary.html", context)

@login_required
def g3_pretest_overall(request):
    student_id = request.GET.get('student')
    if not student_id:
        return HttpResponse("No student ID provided.", status=400)
    try:
        student_id = int(student_id)
    except ValueError:
        return HttpResponse("Invalid student ID.", status=400)

    student = get_object_or_404(Studentrecords, id=student_id)
    
    context = {
        'student': student,
        'total_miscues': student.total_miscues,
        'oral_reading_score': student.oral_reading_score,
        'pre_literal_scores': student.pre_literal_scores,
        'pre_inferential_scores': student.pre_inferential_scores,
        'pre_applied_scores': student.pre_applied_scores,
        'pre_total_scores': student.pre_total_scores,
        'reading_level': student.reading_level,
        'pre_literal_fb': student.pre_literal_fb,
        'pre_inferential_fb': student.pre_inferential_fb,
        'pre_applied_fb': student.pre_applied_fb,
        'pre_level_fb': student.pre_level_fb,
    }
    
    return render(request, "WebApp/g3_pretest_overall.html", context)

@login_required
def g4_pretest_oral(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)
            word_error_rate = wer(reference_text, transcript)

            print(f"Word Error Rate (WER): {word_error_rate:.2f}")

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'word_error_rate': word_error_rate,
                'mispronunciation_words': reading_mistakes.get('Mispronunciation Words', []),
                'omission_words': reading_mistakes.get('Omission Words', []),
                'substitution_words': reading_mistakes.get('Substitution Words', []),
                'insertion_words': reading_mistakes.get('Insertion Words', []),
                'total_miscues': reading_mistakes.get('Total Miscues', 0),
                'oral_reading_score': reading_mistakes.get('Oral Reading Score', 0),
            }

            return render(request, 'WebApp/g4_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g4_pretest_oral.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "Berlin, Germany\n"
        "May 30, 2008\n"
        "\n"
        "Dear Betty,\n"
        "Our family will celebrate our grandparent’s golden wedding anniversary at our ancestral home on Saturday, June 21, 2008. We shall have a party in their honor.\n"
        "A special activity for kids is the Children’s Hour at 3 o’clock P.M.\n"
        "Come, let’s have fun! Be one of our child guests.\n"
        "\n"
        "Sincerely,\n"
        "Shiela"
    )

    pretest_passage, created = PreTestPassage.objects.get_or_create(
        pretest_grade_level=4,
        teacher=teacher,
        defaults={
            'pretest_passage': initial_reference_text,
            'pretest_passage_title': 'An Invitation Letter', 
            'pretest_passage_prompt': 'Have you ever tried inviting a friend to your party? Read this invitation letter. Find out what occasion is.'
        }
    )

    g4_default_questions = [
        "What will the family celebrate?",
        "When will they celebrate the Golden Wedding Anniversary?",
        "What activity in the anniversary is Betty invited to come?",
        "Who wrote the letter?",
        "What is another word for guests?",
        "Why do you think is a golden wedding anniversary celebrated?",
        "What should you do when you are invited?"
    ]

    for question_text in g4_default_questions:
        PreTestQuestions.objects.get_or_create(
            pretest_passage=pretest_passage,
            teacher=teacher,
            pretest_question=question_text,
            defaults={
                'pretest_grade_level': 4
            }
        )

    context = {
        'reference_text': pretest_passage.pretest_passage,
        'pretest_passage_title': pretest_passage.pretest_passage_title,
        'pretest_passage_prompt': pretest_passage.pretest_passage_prompt,
        'pretest_passage_id': pretest_passage.pretest_passage_id
    }

    return render(request, 'WebApp/g4_pretest_oral.html', context)

@login_required
def g4_preoral_questions(request):
    teacher = request.user
    pretest_grade_level = 4   
    passage = get_object_or_404(PreTestPassage, pretest_grade_level=pretest_grade_level, teacher=teacher)
    questions = PreTestQuestions.objects.filter(pretest_passage=passage)

    context = {
        'passage': passage,
        'questions': questions
    }

    return render(request, "WebApp/g4_preoral_questions.html", context)

@login_required
def g4_pretest_summary(request):
    teacher = request.user
    questions = PreTestQuestions.objects.filter(pretest_grade_level=4, teacher=teacher)
    context = {
        'questions': questions
    }
    return render(request, "WebApp/g4_pretest_summary.html", context)

@login_required
def g4_pretest_overall(request):
    student_id = request.GET.get('student')
    if not student_id:
        return HttpResponse("No student ID provided.", status=400)
    
    try:
        student_id = int(student_id)
    except ValueError:
        return HttpResponse("Invalid student ID.", status=400)

    student = get_object_or_404(Studentrecords, id=student_id)
    
    context = {
        'student': student,
        'total_miscues': student.total_miscues,
        'oral_reading_score': student.oral_reading_score,
        'pre_literal_scores': student.pre_literal_scores,
        'pre_inferential_scores': student.pre_inferential_scores,
        'pre_applied_scores': student.pre_applied_scores,
        'pre_total_scores': student.pre_total_scores,
        'reading_level': student.reading_level,
        'pre_literal_fb': student.pre_literal_fb,
        'pre_inferential_fb': student.pre_inferential_fb,
        'pre_applied_fb': student.pre_applied_fb,
        'pre_level_fb': student.pre_level_fb,
    }
    
    return render(request, "WebApp/g4_pretest_overall.html", context)

def g2_posttest_oral(request):
    teacher = request.user

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')


        # Debugging prints
        print("Transcript:", transcript)
        print("Start Time String:", start_time_str)
        print("End Time String:", end_time_str)
        print("student_id:", student_id)

        if start_time_str and end_time_str:
            try:
                start_time = dateutil.parser.parse(start_time_str)
                end_time = dateutil.parser.parse(end_time_str)
            except ValueError as e:
                return render(request, 'WebApp/g2_posttest_oral.html', {'error': f'Error parsing time: {e}'})

            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)
            word_error_rate = wer(reference_text, transcript)

            # Debugging prints
            print(f"Word Error Rate (WER): {word_error_rate:.2f}")

            post_total_miscues = reading_mistakes.get('Total Miscues', 0)
            post_oral_reading_score = reading_mistakes.get('Oral Reading Score', 0)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'word_error_rate': word_error_rate,
                'mispronunciation_words': reading_mistakes.get('Mispronunciation Words', []),
                'omission_words': reading_mistakes.get('Omission Words', []),
                'substitution_words': reading_mistakes.get('Substitution Words', []),
                'insertion_words': reading_mistakes.get('Insertion Words', []),
                'total_miscues': post_total_miscues,
                'oral_reading_score': post_oral_reading_score,
                'student_id': student_id,  

            }

            print("Context Data for Rendering:", context)

            return render(request, 'WebApp/g2_posttest_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g2_posttest_oral.html', {'error': 'Start and end times are required for analysis.'})

    # Handle GET request
    initial_reference_text = (
        "Miss Cruz asked her Science class, “What do plants need in order to live and grow?” John answered, “Air and Sunlight,” “Good answer,” said Miss Cruz. “Green plants need sunlight to make their food. They also need water and air.”"
    )
    
    posttest_passage, created = PostTestPassage.objects.get_or_create(
        posttest_grade_level=22, 
        teacher=teacher,
        defaults={
            'posttest_passage': initial_reference_text,
            'posttest_passage_title': 'Air and Sunlight',
            'posttest_passage_prompt': 'Do you know what plants need in order to grow? Find out from the selection below.'
        }
    )

    g2_posttest_default_questions = [
        "What do plants need in order to live and grow? ",
        "What did Miss Cruz say about John’s answer?",
        "What else do plants need aside from air and sunlight? ",
        "Why do green plants need sunlight?",
        "What is likely to happen with green plants if there is no sunlight?",
    ]

    for question_text in g2_posttest_default_questions:
        PostTestQuestions.objects.get_or_create(
            posttest_passage=posttest_passage,
            teacher=teacher,
            posttest_question=question_text,
            defaults={
                'posttest_grade_level': 22
            }
        )

    context = {
        'reference_text': posttest_passage.posttest_passage,
        'posttest_passage_title': posttest_passage.posttest_passage_title,
        'posttest_passage_prompt': posttest_passage.posttest_passage_prompt,
    }

    print("Initial Context Data for Rendering:", context)

    return render(request, 'WebApp/g2_posttest_oral.html', context)



@login_required
def g2_postoral_questions(request):
    teacher = request.user
    student_id = request.GET.get('student_id')
    posttest_grade_level = 22  
    passage = get_object_or_404(PostTestPassage, posttest_grade_level=posttest_grade_level, teacher=teacher)
    questions = PostTestQuestions.objects.filter(posttest_passage=passage)

    context = {
        'passage': passage,
        'questions': questions,
        'student_id': student_id  
    }
    return render(request, "WebApp/g2_postoral_questions.html", context)


@login_required
def g2_posttest_summary(request):
    student_id = request.GET.get('student_id')
    teacher = request.user
    questions = PostTestQuestions.objects.filter(posttest_grade_level=22, teacher=teacher)
    context = {
        'questions': questions,
        'student_id': student_id
        
    }
    return render(request, "WebApp/g2_posttest_summary.html", context)

def g2_posttest_overall(request):
    student_id = request.GET.get('student')
    if not student_id:
        return HttpResponse("No student ID provided.", status=400)
    
    try:
        student_id = int(student_id)
    except ValueError:
        return HttpResponse("Invalid student ID.", status=400)

    student = get_object_or_404(Studentrecords, id=student_id)
    
    context = {
        'student': student,
        'post_total_miscues': student.post_total_miscues,
        'post_oral_reading_score': student.post_oral_reading_score,
        'post_literal_scores': student.post_literal_scores,
        'post_inferential_scores': student.post_inferential_scores,
        'post_applied_scores': student.post_applied_scores,
        'post_total_scores': student.post_total_scores,
        'post_reading_level': student.post_reading_level,
        'post_literal_fb': student.post_literal_fb,
        'post_inferential_fb': student.post_inferential_fb,
        'post_applied_fb': student.post_applied_fb,
        'post_level_fb': student.post_level_fb,
    }
    
    return render(request, "WebApp/g2_posttest_overall.html", context)

@login_required
def g3_posttest_oral(request):
    teacher = request.user

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')


        # Debugging prints
        print("Transcript:", transcript)
        print("Start Time String:", start_time_str)
        print("End Time String:", end_time_str)
        print("student_id:", student_id)

        if start_time_str and end_time_str:
            try:
                start_time = dateutil.parser.parse(start_time_str)
                end_time = dateutil.parser.parse(end_time_str)
            except ValueError as e:
                return render(request, 'WebApp/g3_posttest_oral.html', {'error': f'Error parsing time: {e}'})

            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)
            word_error_rate = wer(reference_text, transcript)

            # Debugging prints
            print(f"Word Error Rate (WER): {word_error_rate:.2f}")

            post_total_miscues = reading_mistakes.get('Total Miscues', 0)
            post_oral_reading_score = reading_mistakes.get('Oral Reading Score', 0)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'word_error_rate': word_error_rate,
                'mispronunciation_words': reading_mistakes.get('Mispronunciation Words', []),
                'omission_words': reading_mistakes.get('Omission Words', []),
                'substitution_words': reading_mistakes.get('Substitution Words', []),
                'insertion_words': reading_mistakes.get('Insertion Words', []),
                'total_miscues': post_total_miscues,
                'oral_reading_score': post_oral_reading_score,
                'student_id': student_id,  

            }

            print("Context Data for Rendering:", context)
            return render(request, 'WebApp/g3_posttest_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g3_posttest_oral.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "Our annual celebrations are of two types: civic and religious. These two are different as can be seen from the examples below. \n"
        "\n"
        "CIVIC\n"
        "Independence Day, National Heroes, Fall of Bataan, Labor Day\n"
        "\n"
        "RELIGIOUS\n"
        "Christmas, New Year, Holy Week, All Souls, Fiesta of the different religions\n"
        "\n"
        "Can you give the difference?"
    )

    posttest_passage, created = PostTestPassage.objects.get_or_create(
        posttest_grade_level=33,
        teacher=teacher,
        defaults={
            'posttest_passage': initial_reference_text,
            'posttest_passage_title': 'National Celebrations',
            'posttest_passage_prompt': 'What are the civic and religious celebrations in our country? Find out from the selection.'
        }
    )

    g3_posttest_default_questions = [
        "What is the selection about?",
        "What are the types of celebrations?",
        "What can be seen in the chart?",
        "What is the importance of knowing these celebrations?",
        "How is National Heroes Day celebrated in your school?",
    ]

    for question_text in g3_posttest_default_questions:
        PostTestQuestions.objects.get_or_create(
            posttest_passage=posttest_passage,
            teacher=teacher,
            posttest_question=question_text,
            defaults={
                'posttest_grade_level': 33
            }
        )

    context = {
        'reference_text': posttest_passage.posttest_passage,
        'posttest_passage_title': posttest_passage.posttest_passage_title,
        'posttest_passage_prompt': posttest_passage.posttest_passage_prompt
    }

    return render(request, 'WebApp/g3_posttest_oral.html', context)

@login_required
def g3_postoral_questions(request):
    student_id = request.GET.get('student_id')
    teacher = request.user
    posttest_grade_level = 33  
    passage = get_object_or_404(PostTestPassage, posttest_grade_level=posttest_grade_level, teacher=teacher)
    questions = PostTestQuestions.objects.filter(posttest_passage=passage)

    context = {
         'passage': passage,
        'questions': questions,
        'student_id': student_id 
    }
    return render(request, "WebApp/g3_postoral_questions.html", context)

@login_required
def g3_posttest_summary(request):
    student_id = request.GET.get('student_id')
    teacher = request.user
    questions = PostTestQuestions.objects.filter(posttest_grade_level=33, teacher=teacher)
    context = {
        'questions': questions,
        'student_id': student_id
    }
    return render(request, "WebApp/g3_posttest_summary.html", context)

@login_required
def g3_posttest_overall(request):
    student_id = request.GET.get('student')
    if not student_id:
        return HttpResponse("No student ID provided.", status=400)
    
    try:
        student_id = int(student_id)
    except ValueError:
        return HttpResponse("Invalid student ID.", status=400)

    student = get_object_or_404(Studentrecords, id=student_id)
    
    context = {
        'student': student,
        'post_total_miscues': student.post_total_miscues,
        'post_oral_reading_score': student.post_oral_reading_score,
        'post_literal_scores': student.post_literal_scores,
        'post_inferential_scores': student.post_inferential_scores,
        'post_applied_scores': student.post_applied_scores,
        'post_total_scores': student.post_total_scores,
        'post_reading_level': student.post_reading_level,
        'post_literal_fb': student.post_literal_fb,
        'post_inferential_fb': student.post_inferential_fb,
        'post_applied_fb': student.post_applied_fb,
        'post_level_fb': student.post_level_fb,
    }
    
    return render(request, "WebApp/g3_posttest_overall.html", context)

@login_required
def g4_posttest_oral(request):
    teacher = request.user

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')


        # Debugging prints
        print("Transcript:", transcript)
        print("Start Time String:", start_time_str)
        print("End Time String:", end_time_str)
        print("student_id:", student_id)

        if start_time_str and end_time_str:
            try:
                start_time = dateutil.parser.parse(start_time_str)
                end_time = dateutil.parser.parse(end_time_str)
            except ValueError as e:
                return render(request, 'WebApp/g2_posttest_oral.html', {'error': f'Error parsing time: {e}'})

            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)
            word_error_rate = wer(reference_text, transcript)

            # Debugging prints
            print(f"Word Error Rate (WER): {word_error_rate:.2f}")

            post_total_miscues = reading_mistakes.get('Total Miscues', 0)
            post_oral_reading_score = reading_mistakes.get('Oral Reading Score', 0)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'word_error_rate': word_error_rate,
                'mispronunciation_words': reading_mistakes.get('Mispronunciation Words', []),
                'omission_words': reading_mistakes.get('Omission Words', []),
                'substitution_words': reading_mistakes.get('Substitution Words', []),
                'insertion_words': reading_mistakes.get('Insertion Words', []),
                'total_miscues': post_total_miscues,
                'oral_reading_score': post_oral_reading_score,
                'student_id': student_id,  

            }

            print("Context Data for Rendering:", context)

            return render(request, 'WebApp/g4_posttest_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g4_posttest_oral.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "“One hundred years of existence!” exclaimed Ann as she reads the streamer below. \n"
        "\n"
        "CENTENNIAL ROLL\n"
        "Event                         Date\n"
        "Philippine Independence  -  (June 12, 1898 to June 12, 1998) \n"
        "Commission on Audit  -  (May 16, 1899 to May 19, 1999) \n "
        "Siliman University, Dumaguete  -  (August 28, 1901 to August 28, 2001) \n"
        "Saint Paul University, Dumaguete  -  (October 29, 1904 to October 29, 2004) \n"
        "Teacher’s Camp, Baguio  -  (1908 to 2008) \n"
        "\n"
        "“We are indeed blessed to be a part of these celebrations. They happen once in a lifetime,” added Liza. "    
    )

    posttest_passage, created = PostTestPassage.objects.get_or_create(
        posttest_grade_level=44,
        teacher=teacher,
        defaults={
            'posttest_passage': initial_reference_text,
            'posttest_passage_title': 'Centennial Celebrations',
            'posttest_passage_prompt': 'Have you ever seen or participated in town or school celebrations? Read the text below. Find out what celebration is mentioned.'
        }
    )

    g4_posttest_default_questions = [
        "What did Ann and Liza read?",
        "What was in the streamer?",
        "What did Liza tell Ann that they were blessed?",
        "How many years does it take to have a centennial celebration?",
        "What’s another word for roll?",
        "Would you go for a grand or big celebration during centennial anniversaries?",
        "If you were asked about some activities to be included in centennial celebrations, what activities would you include for children and the youth?"
    ]

    for question_text in g4_posttest_default_questions:
        PostTestQuestions.objects.get_or_create(
            posttest_passage=posttest_passage,
            teacher=teacher,
            posttest_question=question_text,
            defaults={
                'posttest_grade_level': 44
            }
        )

    context = {
        'reference_text': posttest_passage.posttest_passage,
        'posttest_passage_title': posttest_passage.posttest_passage_title,
        'posttest_passage_prompt': posttest_passage.posttest_passage_prompt
    }

    return render(request, 'WebApp/g4_posttest_oral.html', context)

@login_required
def g4_postoral_questions(request):
    teacher = request.user
    posttest_grade_level = 44  
    passage = get_object_or_404(PostTestPassage, posttest_grade_level=posttest_grade_level, teacher=teacher)
    questions = PostTestQuestions.objects.filter(posttest_passage=passage)

    context = {
        'passage': passage,
        'questions': questions
    }
    return render(request, "WebApp/g4_postoral_questions.html", context)

@login_required
def g4_posttest_summary(request):
    teacher = request.user
    questions = PostTestQuestions.objects.filter(posttest_grade_level=44, teacher=teacher)
    context = {
        'questions': questions
    }
    return render(request, "WebApp/g4_posttest_summary.html", context)

@login_required
def g4_posttest_overall(request):
    student_id = request.GET.get('student')
    if not student_id:
        return HttpResponse("No student ID provided.", status=400)
    
    try:
        student_id = int(student_id)
    except ValueError:
        return HttpResponse("Invalid student ID.", status=400)

    student = get_object_or_404(Studentrecords, id=student_id)
    
    context = {
        'student': student,
        'post_total_miscues': student.post_total_miscues,
        'post_oral_reading_score': student.post_oral_reading_score,
        'post_literal_scores': student.post_literal_scores,
        'post_inferential_scores': student.post_inferential_scores,
        'post_applied_scores': student.post_applied_scores,
        'post_total_scores': student.post_total_scores,
        'post_reading_level': student.post_reading_level,
        'post_literal_fb': student.post_literal_fb,
        'post_inferential_fb': student.post_inferential_fb,
        'post_applied_fb': student.post_applied_fb,
        'post_level_fb': student.post_level_fb,
    }
    return render(request, "WebApp/g4_posttest_overall.html", context)

def read_page(request):
    context ={}
    return render(request, "WebApp/read_page.html", context)

def the_bee(request):
    return render(request, 'WebApp/the_bee.html')

def tag_rules(request):
    return render(request, 'WebApp/tag_rules.html')

def good_habit(request):
    return render(request, 'WebApp/max_good_habit.html')

def ocean_waves(request):
    return render(request, 'WebApp/ocean_waves.html')

def rocks(request):
    return render(request, 'WebApp/rocks.html')

def hero(request):
    return render(request, 'WebApp/civil_war_hero.html')

@login_required
def g2_pretest_listening(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            # Analyze reading mistakes and calculate reading speed
            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'reference_text': reference_text  
            }

            return render(request, 'WebApp/g2_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g2_pretest_listening.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "There are many liquids that are good for our health like water, fruit juice and milk. "
        "Milk makes our bones strong. Juice gives us vitamins, while water cleans our body. "
        "Let’s drink milk, juice and water to make us healthy!"
    )

    pretest_passage, created = PreTestPassage.objects.get_or_create(
        pretest_grade_level=2,
        teacher=teacher,
        defaults={'pretest_passage': initial_reference_text, 'pretest_passage_title': 'Liquids Good For You'}
    )

    return render(request, 'WebApp/g2_pretest_listening.html', {'reference_text': pretest_passage.pretest_passage, 'pretest_passage_title': pretest_passage.pretest_passage_title})

@login_required
def g3_pretest_listening(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            # Analyze reading mistakes and calculate reading speed
            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'reference_text': reference_text  
            }

            return render(request, 'WebApp/g3_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g3_pretest_listening.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "“Our Foundation Day will be on September 30,” said Miss Cruz, “What are we going to present?” "
        "“I suggest that we render some folksongs and folk dances,” answered Perla. "
        "“Good. These will remind us of our Filipino culture,” added Ruben. "
        "“Let’s start our practice early. That’s a deal,” insisted Susan."
    )

    pretest_passage, created = PreTestPassage.objects.get_or_create(
        pretest_grade_level=3,
        teacher=teacher,
        defaults={'pretest_passage': initial_reference_text, 'pretest_passage_title': 'A Deal'}
    )

    return render(request, 'WebApp/g3_pretest_listening.html', {'reference_text': pretest_passage.pretest_passage, 'pretest_passage_title': pretest_passage.pretest_passage_title})

@login_required
def g4_pretest_listening(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            # Analyze reading mistakes and calculate reading speed
            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'reference_text': reference_text  
            }

            return render(request, 'WebApp/g4_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g4_pretest_listening.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "Berlin, Germany \n"
        "May 30, 2008 \n"
        "\n"
        "Dear Betty, \n"
        "Our family will celebrate our grandparent’s golden wedding anniversary at our ancestral home on Saturday, June 21, 2008. We shall have a party in their honor. A special activity for kids is the Children’s Hour at 3 o’clock P.M. \n"
        "Come, let’s have fun! Be one of our child guests. \n"
        "\n"
        "Sincerely, \n"
        "Shiela"
    )

    pretest_passage, created = PreTestPassage.objects.get_or_create(
        pretest_grade_level=4,
        teacher=teacher,
        defaults={'pretest_passage': initial_reference_text, 'pretest_passage_title': 'An Invitation Letter'}
    )

    return render(request, 'WebApp/g4_pretest_listening.html', {'reference_text': pretest_passage.pretest_passage, 'pretest_passage_title': pretest_passage.pretest_passage_title})

@login_required
def g2_posttest_listening(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            # Analyze reading mistakes and calculate reading speed
            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'reference_text': reference_text  
            }

            return render(request, 'WebApp/g2_posttest_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g2_posttest_listening.html', {'error': 'Start and end times are required for analysis.'})

    initial_reference_text = (
        "Miss Cruz asked her Science class, “What do plants need in order to live and grow?” John answered, “Air and Sunlight,” “Good answer,” said Miss Cruz. “Green plants need sunlight to make their food. They also need water and air.”"
    )

    posttest_passage, created = PostTestPassage.objects.get_or_create(
        posttest_grade_level=22,
        teacher=teacher,
        defaults={
            'posttest_passage': initial_reference_text,
            'posttest_passage_title': 'Air and Sunlight',
        }
    )

    context = {
        'reference_text': posttest_passage.posttest_passage,
        'posttest_passage_title': posttest_passage.posttest_passage_title,
        'posttest_passage_prompt': posttest_passage.posttest_passage_prompt
    }

    return render(request, 'WebApp/g2_posttest_listening.html', context)

@login_required
def g3_posttest_listening(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            # Analyze reading mistakes and calculate reading speed
            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'reference_text': reference_text,
                'posttest_passage_title': 'Grade 3 Posttest Listening Comprehension'  # Add or override title for analysis page
            }

            return render(request, 'WebApp/g3_posttest_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g3_posttest_listening.html', {'error': 'Start and end times are required for analysis.'})

    else:
        initial_reference_text = (
        "Our annual celebrations are of two types: civic and religious. These two are different as can be seen from the examples below.\n"
        "\n"
        "CIVIC \n"
        "Independence Day, National Heroes, Fall of Bataan, Labor Day \n"
        "\n"
        "RELIGIOUS \n"
        "Christmas, New Year, Holy Week, All Souls, Fiesta of the different religions \n"
        "\n"
        "Can you give the difference?"
        )
        posttest_passage, created = PostTestPassage.objects.get_or_create(
            posttest_grade_level=33, 
            teacher=teacher,
            defaults={
                'posttest_passage': initial_reference_text,
                'posttest_passage_title': 'National Celebrations',  
            }
        )

        context = {
            'reference_text': posttest_passage.posttest_passage,
            'posttest_passage_title': posttest_passage.posttest_passage_title,
        }
        
        return render(request, 'WebApp/g3_posttest_listening.html', context)

@login_required
def g4_posttest_listening(request):
    teacher = request.user

    if request.method == 'POST':
        reference_text = request.POST.get('reference_text')
        transcript = request.POST.get('transcript')
        start_time_str = request.POST.get('start_time', '')
        end_time_str = request.POST.get('end_time', '')

        print("Transcript:", transcript)
        print("Start Time:", start_time_str)
        print("End Time:", end_time_str)

        if start_time_str and end_time_str:
            start_time = dateutil.parser.parse(start_time_str)
            end_time = dateutil.parser.parse(end_time_str)

            # Analyze reading mistakes
            reading_mistakes = analyze_reading_mistakes(reference_text, transcript)
            reading_speed = calculate_reading_speed(transcript, start_time, end_time)

            context = {
                'transcript': transcript,
                'reading_mistakes': reading_mistakes,
                'reading_speed': reading_speed,
                'reference_text': reference_text,
                'posttest_passage_title': 'Grade 4 Posttest Listening Comprehension'  # Adjust title for grade 4
            }

            return render(request, 'WebApp/g4_posttest_analyze_reading.html', context)
        else:
            return render(request, 'WebApp/g4_posttest_listening.html', {'error': 'Start and end times are required for analysis.'})
        
    else:
        initial_reference_text = (
        "“One hundred years of existence!” exclaimed Ann as she reads the streamer below. \n"
        "\n"
        "CENTENNIAL ROLL \n"
        "Event                         Date \n"
        "Philippine Independence  -  (June 12, 1898 to June 12, 1998) \n"
        "Commission on Audit  -  (May 16, 1899 to May 19, 1999) \n "
        "Siliman University, Dumaguete  -  (August 28, 1901 to August 28, 2001) \n"
        "Saint Paul University, Dumaguete  -  (October 29, 1904 to October 29, 2004) \n"
        "Teacher’s Camp, Baguio  -  (1908 to 2008) \n"
        "\n"
        "“We are indeed blessed to be a part of these celebrations. They happen once in a lifetime,” added Liza. "    
        )
        
        posttest_passage, created = PostTestPassage.objects.get_or_create(
            posttest_grade_level=4,
            teacher=teacher,
            defaults={
                'posttest_passage': initial_reference_text,
                'posttest_passage_title': 'Centennial Celebrations'  
            }
        )

        context = {
            'reference_text': posttest_passage.posttest_passage,
            'posttest_passage_title': posttest_passage.posttest_passage_title,
        }

        return render(request, 'WebApp/g4_posttest_listening.html', context)

def manage_contents_page(request):
    teacher_id = request.user.id  
    context = {
        'teacher_id': teacher_id,
    }
    return render(request, 'WebApp/manage_contents_page.html', context)

#pretest view
@login_required
def manage_preans_view_content(request, grade):
    teacher = request.user  # Assuming the user is logged in and is a teacher
    answers = PreTestAnswers.objects.filter(pretest_grade_level=grade, teacher=teacher)
    return render(request, 'WebApp/manage_preans_view_content.html', {'answers': answers, 'grade': grade})

@login_required
def manage_prepass_view_content(request, grade):
    teacher = request.user  # Assuming the user is logged in and is a teacher
    passages = PreTestPassage.objects.filter(pretest_grade_level=grade, teacher=teacher)
    return render(request, 'WebApp/manage_prepass_view_content.html', {'passages': passages, 'grade': grade})

def manage_preque_view_content(request, grade):
    teacher = request.user  # Assuming the user is logged in and is a teacher
    questions = PreTestQuestions.objects.filter(pretest_grade_level=grade, teacher=teacher)
    return render(request, 'WebApp/manage_preque_view_content.html', {'questions': questions, 'grade': grade})

#pretest dalete
def manage_preans_delete_content(request, answer_id):
    answer = get_object_or_404(PreTestAnswers, pk=answer_id)
    grade = answer.pretest_grade_level
    answer.delete()
    return redirect(reverse('manage_preans_delete_content', kwargs={'grade': grade}))

def manage_prepass_delete_content(request, passage_id):
    passage = get_object_or_404(PreTestPassage, pk=passage_id)
    grade = passage.pretest_grade_level
    passage.delete()
    return redirect(reverse('manage_prepass_delete_content', kwargs={'grade': grade}))

def manage_preque_delete_content(request, question_id):
    question = get_object_or_404(PreTestQuestions, pk=question_id)
    grade = question.pretest_grade_level
    question.delete()
    return redirect(reverse('manage_preque_delete_content', kwargs={'grade': grade}))

#pretest update
def manage_preans_update_content(request, answer_id):
    answer = get_object_or_404(PreTestAnswers, pk=answer_id)
    if request.method == 'POST':
        form = PreTestAnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            return redirect('manage_preans_view_content', grade=answer.pretest_grade_level)
    else:
        form = PreTestAnswerForm(instance=answer)
    context = {
        'form': form,
        'answer': answer
    }
    return render(request, 'WebApp/manage_preans_update_content.html', context)

def manage_prepass_update_content(request, passage_id):
    passage = get_object_or_404(PreTestPassage, pk=passage_id)
    if request.method == 'POST':
        form = PreTestPassageForm(request.POST, instance=passage)
        if form.is_valid():
            form.save()
            return redirect('manage_prepass_view_content', grade=passage.pretest_grade_level)
    else:
        form = PreTestPassageForm(instance=passage)
    context = {
        'form': form,
        'passage': passage
    }
    return render(request, 'WebApp/manage_prepass_update_content.html', context)

def manage_preque_update_content(request, question_id):
    question = get_object_or_404(PreTestQuestions, pk=question_id)
    if request.method == 'POST':
        form = PreTestQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('manage_preque_view_content', grade=question.pretest_grade_level)
    else:
        form = PreTestQuestionForm(instance=question)
    context = {
        'form': form,
        'question': question
    }
    return render(request, 'WebApp/manage_preque_update_content.html', context)

#pretest add
def manage_preans_add_content(request):
    teacher = request.user  # Assuming request.user is your logged-in teacher object

    if request.method == 'POST':
        form = PreTestAnswerForm(request.POST)
        if form.is_valid():
            pretest_answer = form.cleaned_data['pretest_answer']
            pretest_question = form.cleaned_data['pretest_question']
            pretest_passage = form.cleaned_data['pretest_passage']
            pretest_grade_level = form.cleaned_data['pretest_grade_level']

            # Assign the logged-in teacher's ID to the form instance
            form.instance.teacher_id = teacher.id  # Adjust based on your actual field name

            # Save the form
            form.save()
            return redirect('manage_preans_view_content', grade=pretest_grade_level)
    else:
        form = PreTestAnswerForm()
    
    context = {
        'form': form
    }
    return render(request, 'WebApp/manage_preans_add_content.html', context)

def manage_prepass_add_content(request):
    teacher = request.user  # Assuming request.user is your logged-in teacher object

    if request.method == 'POST':
        form = PreTestPassageForm(request.POST)
        if form.is_valid():
            pretest_passage = form.cleaned_data['pretest_passage']
            pretest_grade_level = form.cleaned_data['pretest_grade_level']

            # Assign the logged-in teacher's ID to the form instance
            form.instance.teacher_id = teacher.id  # Adjust based on your actual field name

            # Save the form
            form.save()
            return redirect('manage_prepass_view_content', grade=pretest_grade_level)
    else:
        form = PreTestPassageForm()
    
    context = {
        'form': form
    }
    return render(request, 'WebApp/manage_prepass_add_content.html', context)

def manage_preque_add_content(request):
    teacher = request.user  # Assuming request.user is your logged-in teacher object

    if request.method == 'POST':
        form = PreTestQuestionForm(request.POST)
        if form.is_valid():
            pretest_question = form.cleaned_data['pretest_question']
            pretest_passage = form.cleaned_data['pretest_passage']
            pretest_grade_level = form.cleaned_data['pretest_grade_level']

            # Assign the logged-in teacher's ID to the form instance
            form.instance.teacher_id = teacher.id  # Adjust based on your actual field name

            # Save the form
            form.save()
            return redirect('manage_preque_view_content', grade=pretest_grade_level)
    else:
        form = PreTestQuestionForm()
    
    context = {
        'form': form
    }
    return render(request, 'WebApp/manage_preque_add_content.html', context)

#pretest add record
def manage_preans_addrecord_content(request):
    context ={

    }
    return render(request, 'WebApp/manage_preans_addrecord_content.html', context)

def manage_prepass_addrecord_content(request):
    context ={

    }
    return render(request, 'WebApp/manage_prepass_addrecord_content.html', context)

def manage_preque_addrecord_content(request):
    context ={

    }
    return render(request, 'WebApp/manage_preque_addrecord_content.html', context)

#POSTTEST
# posttest view
@login_required
def manage_postans_view_content(request, grade):
    teacher = request.user  # Assuming the user is logged in and is a teacher
    answers = PostTestAnswers.objects.filter(posttest_grade_level=grade, teacher=teacher)
    return render(request, 'WebApp/manage_postans_view_content.html', {'answers': answers, 'grade': grade})

@login_required
def manage_postpass_view_content(request, grade):
    teacher = request.user  # Assuming the user is logged in and is a teacher
    passages = PostTestPassage.objects.filter(posttest_grade_level=grade, teacher=teacher)
    return render(request, 'WebApp/manage_postpass_view_content.html', {'passages': passages, 'grade': grade})

@login_required
def manage_postque_view_content(request, grade):
    questions = PostTestQuestions.objects.filter(posttest_grade_level=grade, teacher=request.user)
    context = {
        'questions': questions,
    }
    return render(request, 'WebApp/manage_postque_view_content.html', context)

# posttest delete
@login_required
def manage_postans_delete_content(request, answer_id):
    answer = get_object_or_404(PostTestAnswers, pk=answer_id)
    grade = answer.posttest_grade_level
    answer.delete()
    return redirect('manage_postans_view_content', grade=grade)

@login_required
def manage_postpass_delete_content(request, passage_id):
    passage = get_object_or_404(PostTestPassage, pk=passage_id)
    grade = passage.posttest_grade_level
    passage.delete()
    return redirect('manage_postpass_view_content', grade=grade)

@login_required
def manage_postque_delete_content(request, question_id):
    question = get_object_or_404(PostTestQuestions, pk=question_id)
    grade = question.posttest_grade_level
    question.delete()
    return redirect('manage_postque_view_content', grade=grade)

# posttest update
@login_required
def manage_postans_update_content(request, answer_id):
    answer = get_object_or_404(PostTestAnswers, pk=answer_id)
    if request.method == 'POST':
        form = PostTestAnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            return redirect('manage_postans_view_content', grade=answer.posttest_grade_level)
    else:
        form = PostTestAnswerForm(instance=answer)
    context = {
        'form': form,
        'answer': answer
    }
    return render(request, 'WebApp/manage_postans_update_content.html', context)

@login_required
def manage_postpass_update_content(request, passage_id):
    passage = get_object_or_404(PostTestPassage, pk=passage_id)
    if request.method == 'POST':
        form = PostTestPassageForm(request.POST, instance=passage)
        if form.is_valid():
            form.save()
            return redirect('manage_postpass_view_content', grade=passage.posttest_grade_level)
    else:
        form = PostTestPassageForm(instance=passage)
    context = {
        'form': form,
        'passage': passage
    }
    return render(request, 'WebApp/manage_postpass_update_content.html', context)

@login_required
def manage_postque_update_content(request, question_id):
    question = get_object_or_404(PostTestQuestions, pk=question_id)
    if request.method == 'POST':
        form = PostTestQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('manage_postque_view_content', grade=question.posttest_grade_level)
    else:
        form = PostTestQuestionForm(instance=question)
    context = {
        'form': form,
        'question': question
    }
    return render(request, 'WebApp/manage_postque_update_content.html', context)

# posttest add
@login_required
def manage_postans_add_content(request):
    teacher = request.user  # Assuming request.user is your logged-in teacher object

    if request.method == 'POST':
        form = PostTestAnswerForm(request.POST)
        if form.is_valid():
            posttest_answer = form.cleaned_data['posttest_answer']
            posttest_question = form.cleaned_data['posttest_question']
            posttest_passage = form.cleaned_data['posttest_passage']
            posttest_grade_level = form.cleaned_data['posttest_grade_level']

            # Assign the logged-in teacher's ID to the form instance
            form.instance.teacher_id = teacher.id  # Adjust based on your actual field name

            # Save the form
            form.save()
            return redirect('manage_postans_view_content', grade=posttest_grade_level)
    else:
        form = PostTestAnswerForm()
    
    context = {
        'form': form
    }
    return render(request, 'WebApp/manage_postans_add_content.html', context)

@login_required
def manage_postpass_add_content(request):
    teacher = request.user  # Assuming request.user is your logged-in teacher object

    if request.method == 'POST':
        form = PostTestPassageForm(request.POST)
        if form.is_valid():
            posttest_passage = form.cleaned_data['posttest_passage']
            posttest_grade_level = form.cleaned_data['posttest_grade_level']

            # Assign the logged-in teacher's ID to the form instance
            form.instance.teacher_id = teacher.id  # Adjust based on your actual field name

            # Save the form
            form.save()
            return redirect('manage_postpass_view_content', grade=posttest_grade_level)
    else:
        form = PostTestPassageForm()
    
    context = {
        'form': form
    }
    return render(request, 'WebApp/manage_postpass_add_content.html', context)

@login_required
def manage_postque_add_content(request):
    teacher = request.user  # Assuming request.user is your logged-in teacher object

    if request.method == 'POST':
        form = PostTestQuestionForm(request.POST)
        if form.is_valid():
            posttest_question = form.cleaned_data['posttest_question']
            posttest_passage = form.cleaned_data['posttest_passage']
            posttest_grade_level = form.cleaned_data['posttest_grade_level']

            # Assign the logged-in teacher's ID to the form instance
            form.instance.teacher_id = teacher.id  # Adjust based on your actual field name

            # Save the form
            form.save()
            return redirect('manage_postque_view_content', grade=posttest_grade_level)
    else:
        form = PostTestQuestionForm()
    
    context = {
        'form': form
    }
    return render(request, 'WebApp/manage_postque_add_content.html', context)

# posttest add record
@login_required
def manage_postans_addrecord_content(request):
    context ={

    }
    return render(request, 'WebApp/manage_postans_addrecord_content.html', context)

@login_required
def manage_postpass_addrecord_content(request):
    context ={

    }
    return render(request, 'WebApp/manage_postpass_addrecord_content.html', context)

@login_required
def manage_postque_addrecord_content(request):
    context ={

    }
    return render(request, 'WebApp/manage_postque_addrecord_content.html', context)



def manage_save_content(request):
    return render(request, 'WebApp/manage_save_content.html')
    


def game_index(request):
    return render(request, 'WebApp/game_index.html')

def game_claveria(request):
    return render(request, 'WebApp/game_claveria.html')

def claveria_c1(request):
    return render(request, 'WebApp/c-1.html')

def claveria_c2(request):
    return render(request, 'WebApp/c-2.html')

def claveria_c3(request):
    return render(request, 'WebApp/c-3.html')

def claveria_c4(request):
    return render(request, 'WebApp/c-4.html')

def claveria_c5(request):
    return render(request, 'WebApp/c-5.html')

def claveria_c6(request):
    return render(request, 'WebApp/c-6.html')

def claveria_c7(request):
    return render(request, 'WebApp/c-7.html')

def claveria_c8(request):
    return render(request, 'WebApp/c-8.html')

def claveria_c9(request):
    return render(request, 'WebApp/c-9.html')

def claveria_c10(request):
    return render(request, 'WebApp/c-10.html')

def game_results(request):
    return render(request, 'WebApp/game_results.html')

def game_marungko(request):
    return render(request, 'WebApp/game_marungko.html')

def marungko_m1(request):
    return render(request, 'WebApp/m-1.html')

def marungko_m2(request):
    return render(request, 'WebApp/m-2.html')

def marungko_m3(request):
    return render(request, 'WebApp/m-3.html')

def marungko_m4(request):
    return render(request, 'WebApp/m-4.html')

def marungko_m5(request):
    return render(request, 'WebApp/m-5.html')

def marungko_m6(request):
    return render(request, 'WebApp/m-6.html')

def marungko_m7(request):
    return render(request, 'WebApp/m-7.html')

def marungko_m8(request):
    return render(request, 'WebApp/m-8.html')

def marungko_m9(request):
    return render(request, 'WebApp/m-9.html')

def marungko_m10(request):
    return render(request, 'WebApp/m-10.html')

def marungko_m11(request):
    return render(request, 'WebApp/m-11.html')

def marungko_m12(request):
    return render(request, 'WebApp/m-12.html')

def marungko_m13(request):
    return render(request, 'WebApp/m-13.html')

def marungko_m14(request):
    return render(request, 'WebApp/m-14.html')

def marungko_m15(request):
    return render(request, 'WebApp/m-15.html')

def game_puzzle(request):
    return render(request, 'WebApp/game_puzzle.html')

def puzzle_p1(request):
    return render(request, 'WebApp/p-1.html')

def puzzle_p2(request):
    return render(request, 'WebApp/p-2.html')

def puzzle_p3(request):
    return render(request, 'WebApp/p-3.html')

def puzzle_p4(request):
    return render(request, 'WebApp/p-4.html')

def puzzle_p5(request):
    return render(request, 'WebApp/p-5.html')

def puzzle_p6(request):
    return render(request, 'WebApp/p-6.html')

def puzzle_p7(request):
    return render(request, 'WebApp/p-7.html')

def puzzle_p8(request):
    return render(request, 'WebApp/p-8.html')

def puzzle_p9(request):
    return render(request, 'WebApp/p-9.html')

def puzzle_p10(request):
    return render(request, 'WebApp/p-10.html')

def puzzle_p11(request):
    return render(request, 'WebApp/p-11.html')

def puzzle_p12(request):
    return render(request, 'WebApp/p-12.html')

def puzzle_p13(request):
    return render(request, 'WebApp/p-13.html')

def puzzle_p14(request):
    return render(request, 'WebApp/p-14.html')

def puzzle_p15(request):
    return render(request, 'WebApp/p-15.html')





nlp = spacy.load('en_core_web_md')

def preprocess_answer(answer):
    return re.sub(r'[^\w\s]', '', answer).lower()

def calculate_literal_similarity(user_answer, expected_answer, comparison_results, key):
    expected_doc = nlp(preprocess_answer(','.join(expected_answer)))
    user_doc = nlp(preprocess_answer(user_answer))

    word_embeddings_similarity = user_doc.similarity(expected_doc)
    
    # Adjust tokenization ratios to focus on date format
    tokenization_ratios = [
        fuzz.token_sort_ratio(
            preprocess_answer(user_answer),
            preprocess_answer(expected_token)
        ) / 100.0
        if expected_token.isdigit() else 0.0
        for expected_token in expected_answer
    ]
    
    pos_tag_similarity = calculate_pos_similarity(user_doc, expected_doc)  # Define your own POS similarity function if needed
    
    max_word_embeddings_similarity = max([word_embeddings_similarity])
    max_tokenization_ratio = max(tokenization_ratios)
    
    exact_match = preprocess_answer(user_answer) == preprocess_answer(','.join(expected_answer))
    
    if any(preprocess_answer(expected).lower() in preprocess_answer(user_answer).lower() for expected in expected_answer) or exact_match:
        combined_similarity = 1.0
    else:
        combined_similarity = (
            0.6 * max_word_embeddings_similarity +
            0.1 * max_tokenization_ratio +
            0.3 * pos_tag_similarity
        )
        
    result = "Correct" if combined_similarity >= 0.6 else "Incorrect"
    
    comparison_results[key] = {
        "user_answer": user_answer,
        "expected_answer": ', '.join(expected_answer),
        "result": result,
        "combined_similarity": combined_similarity
    }


def calculate_inferential_similarity(user_answer, expected_answer, comparison_results, key):
    expected_doc = nlp(preprocess_answer(','.join(expected_answer)))
    user_doc = nlp(preprocess_answer(user_answer))

    word_embeddings_similarity = user_doc.similarity(expected_doc)
    tokenization_ratio = fuzz.token_sort_ratio(preprocess_answer(user_answer), preprocess_answer(','.join(expected_answer))) / 100.0
    cosine_similarity = user_doc.vector.dot(expected_doc.vector) / (user_doc.vector_norm * expected_doc.vector_norm)
    contextual_embeddings_similarity = user_doc.similarity(expected_doc)
    
    exact_match = preprocess_answer(user_answer) == preprocess_answer(','.join(expected_answer))


    if any(preprocess_answer(expected) in preprocess_answer(user_answer) for expected in expected_answer) or exact_match:
        combined_similarity = 1.0
    else:
        combined_similarity = (
            0.4 * contextual_embeddings_similarity  +
            0.2 * word_embeddings_similarity +
            0.2 * cosine_similarity +
            0.2 * tokenization_ratio
        )

    result = "Correct" if combined_similarity >= 0.6 else "Incorrect"

    comparison_results[key] = {
        "user_answer": user_answer,
        "expected_answer": ', '.join(expected_answer),
        "result": result,
        "combined_similarity": combined_similarity
    }

    
def calculate_applied_similarity(user_answer, expected_answer, comparison_results, key):
    expected_doc = nlp(preprocess_answer(','.join(expected_answer)))
    user_doc = nlp(preprocess_answer(user_answer))

    word_embeddings_similarity = user_doc.similarity(expected_doc)
    tokenization_ratio = fuzz.token_sort_ratio(preprocess_answer(user_answer), preprocess_answer(','.join(expected_answer))) / 100.0
    cosine_similarity = user_doc.vector.dot(expected_doc.vector) / (user_doc.vector_norm * expected_doc.vector_norm)
    contextual_embeddings_similarity = user_doc.similarity(expected_doc)

    exact_match = preprocess_answer(user_answer) == preprocess_answer(','.join(expected_answer))

    if any(preprocess_answer(expected) in preprocess_answer(user_answer) for expected in expected_answer) or exact_match:
            combined_similarity = 1.0
    else:
            combined_similarity = (
                0.4 * contextual_embeddings_similarity +
                0.4 * word_embeddings_similarity +
                0.1 * cosine_similarity +
                0.1 * tokenization_ratio
            )

    result = "Correct" if combined_similarity >= 0.6 else "Incorrect"

    comparison_results[key] = {
        "user_answer": user_answer,
        "expected_answer": ', '.join(expected_answer),
        "result": result,
        "combined_similarity": combined_similarity
    }


GRADE_ANSWERS = {
    "2": (GRADE2_PRE_ANSWERS),
    "22": (GRADE2_POST_ANSWERS),
    "3": (GRADE3_PRE_ANSWERS),
    "33": (GRADE3_POST_ANSWERS),
    "4": (GRADE4_PRE_ANSWERS),
    "44": (GRADE4_POST_ANSWERS)
}


@csrf_exempt
def analyze_similarity(request):
    if request.method == "POST":
        try:
            # Load the trained RandomForestClassifier models
            with open(r'C:\Users\Sarah Pantaliano\Downloads\SPARKLi-main\SPARKLi-main\models\rf_classifier.pkl', 'rb') as f:
                rf_classifier = pickle.load(f)

            with open(r'C:\Users\Sarah Pantaliano\Downloads\SPARKLi-main\SPARKLi-main\models\rf_literal_feedback.pkl', 'rb') as f:
                rf_literal_feedback = pickle.load(f)

            with open(r'C:\Users\Sarah Pantaliano\Downloads\SPARKLi-main\SPARKLi-main\models\rf_inferential_feedback.pkl', 'rb') as f:
                rf_inferential_feedback = pickle.load(f)

            with open(r'C:\Users\Sarah Pantaliano\Downloads\SPARKLi-main\SPARKLi-main\models\rf_applied_feedback.pkl', 'rb') as f:
                rf_applied_feedback = pickle.load(f)

            with open(r'C:\Users\Sarah Pantaliano\Downloads\SPARKLi-main\SPARKLi-main\models\rf_level_feedback.pkl', 'rb') as f:
                rf_level_feedback = pickle.load(f)

        except FileNotFoundError as e:
            return JsonResponse({"error": f"File not found: {e}"}, status=500)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {e}"}, status=500)

        user_answers = {
            f"answ{i+1}": request.POST.get(f"answ{i+1}", "").strip()
            for i in range(7)
        }
        user_answers["grade_level"] = request.POST.get("grade_level", "")

        grade_level = user_answers["grade_level"]
        #pretest_answers, posttest_answers = GRADE_ANSWERS.get(grade_level, ({}, {}))
        posttest_answers = GRADE_ANSWERS.get(grade_level, ({}))
        pretest_answers = GRADE_ANSWERS.get(grade_level, ({}))

        pretest_questions = list(PreTestQuestions.objects.filter(pretest_grade_level=grade_level))
        pretest_expected_answers = {
            f"answ{index+1}": pretest_answers.get(f"answ{index+1}", [])
            for index, _ in enumerate(pretest_questions)
        }

        posttest_questions = list(PostTestQuestions.objects.filter(posttest_grade_level=grade_level))
        posttest_expected_answers = {
            f"answ{index+1+len(pretest_questions)}": posttest_answers.get(f"answ{index+1+len(pretest_questions)}", [])
            for index, _ in enumerate(posttest_questions)   
        }

        expected_answers = {**pretest_expected_answers, **posttest_expected_answers}
        comparison_results = {}

        for key, expected_answer in expected_answers.items():
            user_answer = user_answers.get(key, "").strip().lower()

            if not user_answer:
                comparison_results[key] = {
                    "user_answer": "No answer provided",
                    "expected_answer": ', '.join(expected_answer),
                    "result": "No answer provided",
                    "combined_similarity": 0.0
                }
                continue

            if not expected_answer:  # Check if expected_answer is empty
                comparison_results[key] = {
                    "user_answer": user_answer,
                    "expected_answer": "No expected answer",
                    "result": "No expected answer",
                    "combined_similarity": 0.0
                }
                continue

            similarity = max(
                fuzz.ratio(user_answer, ans.lower())
                for ans in expected_answer
            )

            result = "Correct" if similarity > 80 else "Incorrect"  # Adjust threshold as needed

            comparison_results[key] = {
                "user_answer": user_answer,
                "expected_answer": ', '.join(expected_answer),
                "result": result,
                "combined_similarity": similarity / 100.0
            }

        total_correct_answers = sum(1 for result in comparison_results.values() if result['result'] == 'Correct')

        (overall_scores, literal_scores, inferential_scores, applied_scores,
         overall_percentage, literal_percentage, inferential_percentage, applied_percentage) = calculate_total_score(comparison_results, grade_level)

        feedback_input = pd.DataFrame([{
            "LiteralScore": literal_percentage,
            "InferentialScore": inferential_percentage,
            "AppliedScore": applied_percentage,
            "OverallScore": overall_percentage
        }])

        predicted_comprehension_level = rf_classifier.predict(feedback_input)[0]
        predicted_literal_feedback = rf_literal_feedback.predict(feedback_input)[0]
        predicted_inferential_feedback = rf_inferential_feedback.predict(feedback_input)[0]
        predicted_applied_feedback = rf_applied_feedback.predict(feedback_input)[0]
        predicted_level_feedback = rf_level_feedback.predict(feedback_input)[0]

        return JsonResponse({
            "results": comparison_results,
            "feedback": {
                "literal": predicted_literal_feedback,
                "inferential": predicted_inferential_feedback,
                "applied": predicted_applied_feedback,
                "level": predicted_level_feedback
            },
            "correct_answers": {
                "overall": {
                    "total_count": overall_scores,
                    "percentage": overall_percentage
                },
                "literal": {
                    "total_count": literal_scores,
                    "percentage": literal_percentage
                },
                "inferential": {
                    "total_count": inferential_scores,
                    "percentage": inferential_percentage
                },
                "applied": {
                    "total_count": applied_scores,
                    "percentage": applied_percentage
                }
            },
            "predicted_comprehension_level": predicted_comprehension_level
        })

    return JsonResponse({"error": "Invalid request method"}, status=405)

def calculate_total_score(comparison_results, grade_level):
    category_scores = {
        'literal': [],
        'inferential': [],
        'applied': []
    }

    total_questions = {
        'literal': 0,
        'inferential': 0,
        'applied': 0
    }

    for key, result in comparison_results.items():
        if grade_level in ["22", "33", "2", "3"]:
            if key in ['answ1', 'answ2', 'answ3']:
                category_scores['literal'].append(result['result'])
                total_questions['literal'] += 1
            elif key == 'answ4':
                category_scores['inferential'].append(result['result'])
                total_questions['inferential'] += 1
            elif key == 'answ5':
                category_scores['applied'].append(result['result'])
                total_questions['applied'] += 1
                
        elif grade_level in ["4", "44"]:
            if key in ['answ1', 'answ2', 'answ3']:
                category_scores['literal'].append(result['result'])
                total_questions['literal'] += 1
            elif key in ['answ4', 'answ5']:
                category_scores['inferential'].append(result['result'])
                total_questions['inferential'] += 1
            elif key in ['answ6', 'answ7']:
                category_scores['applied'].append(result['result'])
                total_questions['applied'] += 1
    
    # Count correct answers in each category
    literal_scores = category_scores['literal'].count('Correct')
    inferential_scores = category_scores['inferential'].count('Correct')
    applied_scores = category_scores['applied'].count('Correct')

    # Total possible scores
    total_literal_questions = total_questions['literal']
    total_inferential_questions = total_questions['inferential']
    total_applied_questions = total_questions['applied']
    total_possible_scores = total_literal_questions + total_inferential_questions + total_applied_questions

    # Format scores as "X out of Y"
    literal_score_str = f"{literal_scores} out of {total_literal_questions}"
    inferential_score_str = f"{inferential_scores} out of {total_inferential_questions}"
    applied_score_str = f"{applied_scores} out of {total_applied_questions}"
    overall_score_str = f"{literal_scores + inferential_scores + applied_scores} out of {total_possible_scores}"

    # Calculate percentages
    literal_percentage = calculate_percentage_score(category_scores['literal'])
    inferential_percentage = calculate_percentage_score(category_scores['inferential'])
    applied_percentage = calculate_percentage_score(category_scores['applied'])
    overall_percentage = sum([literal_percentage, inferential_percentage, applied_percentage]) / 3
    
    return overall_score_str, literal_score_str, inferential_score_str, applied_score_str, \
           overall_percentage, literal_percentage, inferential_percentage, applied_percentage

def calculate_percentage_score(category_results):
    total_correct = sum(1 for result in category_results if result == 'Correct')
    total_questions = len(category_results)
    return (total_correct / total_questions) * 100 if total_questions > 0 else 0

def calculate_pos_similarity(doc1, doc2):
    pos_tags1 = set([token.pos_ for token in doc1])
    pos_tags2 = set([token.pos_ for token in doc2])

    common_pos_tags = pos_tags1.intersection(pos_tags2)
    jaccard_similarity = len(common_pos_tags) / (len(pos_tags1.union(pos_tags2)) or 1)

    return jaccard_similarity

def wer(reference, hypothesis):
    ref_words = reference.split()
    hyp_words = hypothesis.split()

    d = np.zeros((len(ref_words) + 1, len(hyp_words) + 1), dtype=np.uint8)
    for i in range(len(ref_words) + 1):
        for j in range(len(hyp_words) + 1):
            if i == 0:
                d[i][j] = j
            elif j == 0:
                d[i][j] = i

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                substitution = d[i - 1][j - 1] + 1
                insertion = d[i][j - 1] + 1
                deletion = d[i - 1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)

    return d[len(ref_words)][len(hyp_words)] / len(ref_words)


from django.views.decorators.http import require_POST
from .models import Studentrecords, Teacherrecords
from django.shortcuts import get_object_or_404

@csrf_exempt
@require_POST
def save_pre_assessment(request):
    try:
        # Parse the JSON data from the request body
        data = json.loads(request.body)

        # Retrieve student_id from session or directly from data
        student_id = request.session.get('student_id') or data.get('student_id')

        # Check if student_id is available
        if not student_id:
            return JsonResponse({'status': 'error', 'message': 'Student ID is missing'})

        # Retrieve the student record
        student_record = get_object_or_404(Studentrecords, id=student_id)

        # Retrieve other fields from the JSON data
        pre_total_scores = data.get('overallScores', '')
        pre_literal_scores = data.get('literalScores', '')
        pre_inferential_scores = data.get('inferentialScores', '')
        pre_applied_scores = data.get('appliedScores', '')
        pre_literal_fb = data.get('literalFeedback', '')
        pre_inferential_fb = data.get('inferentialFeedback', '')
        pre_applied_fb = data.get('appliedFeedback', '')
        pre_level_fb = data.get('levelFeedback', '')
        pre_reading_level = data.get('readingLevel', '')

        # Update student record fields
        student_record.pre_total_scores = pre_total_scores
        student_record.pre_literal_scores = pre_literal_scores
        student_record.pre_inferential_scores = pre_inferential_scores
        student_record.pre_applied_scores = pre_applied_scores
        student_record.pre_literal_fb = pre_literal_fb
        student_record.pre_inferential_fb = pre_inferential_fb
        student_record.pre_applied_fb = pre_applied_fb
        student_record.pre_level_fb = pre_level_fb
        student_record.reading_level = pre_reading_level

        # Save the updated record
        student_record.save()

        return JsonResponse({'status': 'success', 'message': 'Pre-assessment data saved successfully'})
    except Studentrecords.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student record not found'})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid data format: {str(e)}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'})
    
@csrf_exempt
@require_POST
def save_post_assessment(request):
    try:
        # Parse the JSON data from the request body
        data = json.loads(request.body)

        # Retrieve student_id from session or directly from data
        student_id = request.session.get('student_id') or data.get('student_id')

        # Debugging output
        print(f"Session student_id: {request.session.get('student_id')}")
        print(f"Request data student_id: {data.get('student_id')}")
        print(f"Resolved student_id: {student_id}")

        # Check if student_id is available
        if not student_id:
            return JsonResponse({'status': 'error', 'message': 'Student ID is missing'})

        # Retrieve the student record
        student_record = get_object_or_404(Studentrecords, id=student_id)

        # Retrieve other fields from the JSON data
        post_total_scores = data.get('overallScores', '')
        post_literal_scores = data.get('literalScores', '')
        post_inferential_scores = data.get('inferentialScores', '')
        post_applied_scores = data.get('appliedScores', '')
        post_literal_fb = data.get('literalFeedback', '')
        post_inferential_fb = data.get('inferentialFeedback', '')
        post_applied_fb = data.get('appliedFeedback', '')
        post_level_fb = data.get('levelFeedback', '')
        post_reading_level = data.get('readingLevel', '')

        # Update student record fields
        student_record.post_total_scores = post_total_scores
        student_record.post_literal_scores = post_literal_scores
        student_record.post_inferential_scores = post_inferential_scores
        student_record.post_applied_scores = post_applied_scores
        student_record.post_literal_fb = post_literal_fb
        student_record.post_inferential_fb = post_inferential_fb
        student_record.post_applied_fb = post_applied_fb
        student_record.post_level_fb = post_level_fb
        student_record.post_reading_level = post_reading_level

        # Save the updated record
        student_record.save()

        return JsonResponse({'status': 'success', 'message': 'Pre-assessment data saved successfully'})
    except Studentrecords.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student record not found'})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid data format: {str(e)}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'})


def get_reading_level(request):
    student_id = request.GET.get('studentId')
    try:
        student_record = Studentrecords.objects.get(id=student_id)
        reading_level = student_record.reading_level  # Replace with the actual field name
        return JsonResponse({'readingLevel': reading_level})
    except Studentrecords.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    