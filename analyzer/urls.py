from django.urls import path
from . import views

app_name = 'analyzer'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('analyze/', views.AnalyzeView.as_view(), name='analyze'),
    path('results/', views.ResultsView.as_view(), name='results'),
    path('upload/', views.handle_upload, name='upload'),
    path('plot/', views.generate_plot, name='plot'),
    path('analyze/<int:dataset_id>/', views.analyze_dataset, name='analyze_dataset'),
    path('stats/', views.get_stats, name='get_stats'),
    path('preview/', views.get_data_preview, name='get_data_preview'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('download-pdf/<int:dataset_id>/', views.download_pdf, name='download_pdf'),
    path('analysis/<int:analysis_id>/', views.get_analysis_details, name='analysis_details'),
]