from WebApp import views
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views 

handler400 = 'WebApp.views.error_400'
handler403 = 'WebApp.views.error_403'
handler404 = 'WebApp.views.error_404'
handler500 = 'WebApp.views.error_500'

urlpatterns = [
    path("", views.index, name="index"),
    path("login_page.html", views.login_page, name="login_page"),
    path('logout/', views.logout_view, name='logout_view'),
    path("forgot_password_page.html", views.forgot_password_page, name="forgot_password_page"),
    path("dashboard_page.html", views.dashboard_view, name="dashboard_view"),
    path("profile_page.html", views.profile_page, name="profile_page"),
    path('change_password.html', views.change_password, name='change_password'),
    path("verify_code.html", views.verify_code, name="verify_code"),
    path("about_page.html", views.about_page, name="about_page"),
    path("signup_page.html", views.signup_page, name="signup_page"),
    path("input_student_info.html", views.input_student_info, name="input_student_info"),

    path('save_reading_data/', views.save_reading_data, name='save_reading_data'),
    path('save_post_reading_data/', views.save_post_reading_data, name='save_post_reading_data'),
    path('save_post_reading_level/', views.save_post_reading_level, name='save_post_reading_level'),
    path('save_reading_level/', views.save_reading_level, name='save_reading_level'),
    

    path("g2_pretest_oral.html", views.g2_pretest_oral, name='g2_pretest_oral'),
    path("g2_analyze_reading.html", views.g2_pretest_oral, name='g2_analyze_reading'),
    path('g2_preoral_questions.html', views.g2_preoral_questions, name='g2_preoral_questions'),
    path('g2_pretest_summary.html', views.g2_pretest_summary, name='g2_pretest_summary'),
    path('g3_pretest_oral.html', views.g3_pretest_oral, name='g3_pretest_oral'),
    path("g3_analyze_reading.html", views.g3_pretest_oral, name='g3_analyze_reading'),
    path('g3_preoral_questions.html', views.g3_preoral_questions, name='g3_preoral_questions'),
    path('g3_pretest_summary.html', views.g3_pretest_summary, name='g3_pretest_summary'),
    path('analyze_similarity/', views.analyze_similarity, name='analyze_similarity'),
    path('g4_pretest_oral.html', views.g4_pretest_oral, name='g4_pretest_oral'),
    path("g4_analyze_reading.html", views.g4_pretest_oral, name='g4_analyze_reading'),
    path('g4_preoral_questions.html', views.g4_preoral_questions, name='g4_preoral_questions'),
    path('g4_pretest_summary.html', views.g4_pretest_summary, name='g4_pretest_summary'),
    path('g2_posttest_oral.html', views.g2_posttest_oral, name='g2_posttest_oral'),
    path("g2_posttest_analyze_reading.html", views.g2_posttest_oral, name='g2_posttest_analyze_reading'),
    path('g2_postoral_questions.html', views.g2_postoral_questions, name='g2_postoral_questions'),
    path('g2_posttest_summary.html', views.g2_posttest_summary, name='g2_posttest_summary'),
    path('g3_posttest_oral.html', views.g3_posttest_oral, name='g3_posttest_oral'),
    path("g3_posttest_analyze_reading.html", views.g3_posttest_oral, name='g3_posttest_analyze_reading'),
    path('g3_postoral_questions.html', views.g3_postoral_questions, name='g3_postoral_questions'),
    path('g3_posttest_summary.html', views.g3_posttest_summary, name='g3_posttest_summary'),
    path('g4_posttest_oral.html', views.g4_posttest_oral, name='g4_posttest_oral'),
    path("g4_posttest_analyze_reading.html", views.g4_posttest_oral, name='g4_posttest_analyze_reading'),
    path('g4_postoral_questions.html', views.g4_postoral_questions, name='g4_postoral_questions'),
    path('g4_posttest_summary.html', views.g4_posttest_summary, name='g4_posttest_summary'),
    path('read_page.html', views.read_page, name='read_page'),
    path('the_bee.html', views.the_bee, name='the_bee'),
    path('tag_rules.html', views.tag_rules, name='tag_rules'),
    path('max_good_habit.html', views.good_habit, name='good_habit'),
    path('ocean_waves.html', views.ocean_waves, name='ocean_waves'),
    path('rocks.html', views.rocks, name='rocks'),
    path('civil_war_hero.html', views.hero, name='hero'),
    path('g2_pretest_listening.html', views.g2_pretest_listening, name='g2_pretest_listening'),
    path('g3_pretest_listening.html', views.g3_pretest_listening, name='g3_pretest_listening'),
    path('g4_pretest_listening.html', views.g4_pretest_listening, name='g4_pretest_listening'),
    path('g2_posttest_listening.html', views.g2_posttest_listening, name='g2_posttest_listening'),
    path('g3_posttest_listening.html', views.g3_posttest_listening, name='g3_posttest_listening'),
    path('g4_posttest_listening.html', views.g4_posttest_listening, name='g4_posttest_listening'),
    path('manage_contents_page/', views.manage_contents_page, name='manage_contents_page'),


    #Pretest paths
    path('manage_preans_view_content/<int:grade>/', views.manage_preans_view_content, name='manage_preans_view_content'),
    path('manage_prepass_view_content/<int:grade>/', views.manage_prepass_view_content, name='manage_prepass_view_content'),
    path('manage_preque_view_content/<int:grade>/', views.manage_preque_view_content, name='manage_preque_view_content'),
    path('update/answer/<int:answer_id>/', views.manage_preans_update_content, name='manage_preans_update_content'),
    path('update/passage/<int:passage_id>/', views.manage_prepass_update_content, name='manage_prepass_update_content'),
    path('update/question/<int:question_id>/', views.manage_preque_update_content, name='manage_preque_update_content'),
    path('manage_preans_delete_content/answer/<int:answer_id>/', views.manage_preans_delete_content, name='manage_preans_delete_content'),
    path('manage_prepass_delete_content/passage/<int:passage_id>/', views.manage_prepass_delete_content, name='manage_prepass_delete_content'),
    path('manage_preque_delete_content/<int:question_id>/', views.manage_preque_delete_content, name='manage_preque_delete_content'),
    path('manage_preans_add_content/', views.manage_preans_add_content, name='manage_preans_add_content'),
    path('manage_prepass_add_content/', views.manage_prepass_add_content, name='manage_prepass_add_content'),
    path('manage_preque_add_content/', views.manage_preque_add_content, name='manage_preque_add_content'),


    # Posttest paths
    path('manage_postans_view_content/<int:grade>/', views.manage_postans_view_content, name='manage_postans_view_content'),
    path('manage_postpass_view_content/<int:grade>/', views.manage_postpass_view_content, name='manage_postpass_view_content'),
    path('manage_postque_view_content/<int:grade>/', views.manage_postque_view_content, name='manage_postque_view_content'),
    path('update_postans/<int:answer_id>/', views.manage_postans_update_content, name='manage_postans_update_content'),
    path('update_postpass/<int:passage_id>/', views.manage_postpass_update_content, name='manage_postpass_update_content'),
    path('update_postque/<int:question_id>/', views.manage_postque_update_content, name='manage_postque_update_content'),
    path('manage_postans_delete_content/<int:answer_id>/', views.manage_postans_delete_content, name='manage_postans_delete_content'),
    path('manage_postpass_delete_content/<int:passage_id>/', views.manage_postpass_delete_content, name='manage_postpass_delete_content'),
    path('manage_postque_delete_content/<int:question_id>/', views.manage_postque_delete_content, name='manage_postque_delete_content'),
    path('manage_postans_add_content/', views.manage_postans_add_content, name='manage_postans_add_content'),
    path('manage_postpass_add_content/', views.manage_postpass_add_content, name='manage_postpass_add_content'),
    path('manage_postque_add_content/', views.manage_postque_add_content, name='manage_postque_add_content'),


    path('save-pre-assessment/', views.save_pre_assessment, name='save_pre_assessment'),
    path('save-post-assessment/', views.save_post_assessment, name='save_post_assessment'),


    path('game_index.html', views.game_index, name='game_index'),
    path('game_claveria.html', views.game_claveria, name='game_claveria'),
    path('c-1.html', views.claveria_c1, name='claveria_c1'),
    path('c-2.html', views.claveria_c2, name='claveria_c2'),    
    path('c-3.html', views.claveria_c3, name='claveria_c3'),
    path('c-4.html', views.claveria_c4, name='claveria_c4'),
    path('c-5.html', views.claveria_c5, name='claveria_c5'),
    path('c-6.html', views.claveria_c6, name='claveria_c6'),
    path('c-7.html', views.claveria_c7, name='claveria_c7'),
    path('c-8.html', views.claveria_c8, name='claveria_c8'),
    path('c-9.html', views.claveria_c9, name='claveria_c9'),
    path('c-10.html', views.claveria_c10, name='claveria_c10'),
    path('game_results.html', views.game_results, name='game_results'),
    path('game_marungko.html', views.game_marungko, name='game_marungko'),
    path('m-1.html', views.marungko_m1, name='marungko_m1'),
    path('m-2.html', views.marungko_m2, name='marungko_m2'),
    path('m-3.html', views.marungko_m3, name='marungko_m3'),
    path('m-4.html', views.marungko_m4, name='marungko_m4'),
    path('m-5.html', views.marungko_m5, name='marungko_m5'),
    path('m-6.html', views.marungko_m6, name='marungko_m6'),
    path('m-7.html', views.marungko_m7, name='marungko_m7'),
    path('m-8.html', views.marungko_m8, name='marungko_m8'),
    path('m-9.html', views.marungko_m9, name='marungko_m9'),
    path('m-10.html', views.marungko_m10, name='marungko_m10'),
    path('m-11.html', views.marungko_m11, name='marungko_m11'),
    path('m-12.html', views.marungko_m12, name='marungko_m12'),
    path('m-13.html', views.marungko_m13, name='marungko_m13'),
    path('m-14.html', views.marungko_m14, name='marungko_m14'),
    path('m-15.html', views.marungko_m15, name='marungko_m15'),
    path('game_puzzle.html', views.game_puzzle, name='game_puzzle'),
    path('p-1.html', views.puzzle_p1, name='puzzle_p1'),
    path('p-2.html', views.puzzle_p2, name='puzzle_p2'),
    path('p-3.html', views.puzzle_p3, name='puzzle_p3'),
    path('p-4.html', views.puzzle_p4, name='puzzle_p4'),
    path('p-5.html', views.puzzle_p5, name='puzzle_p5'),
    path('p-6.html', views.puzzle_p6, name='puzzle_p6'),
    path('p-7.html', views.puzzle_p7, name='puzzle_p7'),
    path('p-8.html', views.puzzle_p8, name='puzzle_p8'),
    path('p-9.html', views.puzzle_p9, name='puzzle_p9'),
    path('p-10.html', views.puzzle_p10, name='puzzle_p10'),
    path('p-11.html', views.puzzle_p11, name='puzzle_p11'),
    path('p-12.html', views.puzzle_p12, name='puzzle_p12'),
    path('p-13.html', views.puzzle_p13, name='puzzle_p13'),
    path('p-14.html', views.puzzle_p14, name='puzzle_p14'),
    path('p-15.html', views.puzzle_p15, name='puzzle_p15'),
    
    path('g2_pretest_overall.html', views.g2_pretest_overall, name='g2_pretest_overall'),
    path('g3_pretest_overall.html', views.g3_pretest_overall, name='g3_pretest_overall'),
    path('g4_pretest_overall.html', views.g4_pretest_overall, name='g4_pretest_overall'),
    path('g2_posttest_overall/<int:student_id>/', views.g2_posttest_overall, name='g2_posttest_overall'),
    path('g2_posttest_overall.html', views.g2_posttest_overall, name='g2_posttest_overall'),
    path('g3_posttest_overall.html', views.g3_posttest_overall, name='g3_posttest_overall'),
    path('g4_posttest_overall.html', views.g4_posttest_overall, name='g4_posttest_overall'),
    path('api/get-reading-level/', views.get_reading_level, name='get_reading_level'),
    

    #password
    path('password_reset/',auth_views.PasswordResetView.as_view(template_name="WebApp/password_reset_form.html"), name='password_reset'),
    path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(template_name="WebApp/password_reset_done.html"),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="WebApp/password_reset_confirm.html"),name='password_reset_confirm'),
    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(template_name="WebApp/password_reset_complete.html"),name='password_reset_complete'),
    ]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
