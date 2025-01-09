from django.urls import reverse
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.utils import ImageReader
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect, get_object_or_404
import numpy as np
import pandas as pd
import io
import base64
from .models import DataFile
from django.shortcuts import render
from django.contrib.auth import login, authenticate, logout
from .forms import UserLoginForm, UserRegistrationForm
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import matplotlib
matplotlib.use('Agg')

@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView):
    template_name = 'analyzer/home.html'

class AnalyzeView(TemplateView):
   template_name = 'analyzer/analyze.html'
   
   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       dataset_id = self.request.session.get('current_dataset_id')
       if dataset_id:
           dataset = DataFile.objects.get(id=dataset_id)
           context['columns'] = dataset.columns
       return context

class ResultsView(TemplateView):
   template_name = 'analyzer/results.html'
   
   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['datasets'] = DataFile.objects.all().order_by('-uploaded_at')
       return context

@csrf_exempt
def get_data_preview(request):
    try:
        dataset_id = request.session.get('current_dataset_id')
        dataset = DataFile.objects.get(id=dataset_id)
        df = pd.DataFrame(dataset.data_json)
        
        # Statistics for all columns
        column_stats = {}
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                stats = df[column].describe()
                column_stats[column] = {
                    'type': 'numeric',
                    'mean': round(float(stats['mean']), 2),
                    'median': round(float(df[column].median()), 2),
                    'std': round(float(stats['std']), 2),
                    'min': round(float(stats['min']), 2),
                    'max': round(float(stats['max']), 2),
                    'q1': round(float(stats['25%']), 2),
                    'q3': round(float(stats['75%']), 2),
                    'skewness': round(float(df[column].skew()), 2),
                    'kurtosis': round(float(df[column].kurtosis()), 2),
                    'missing_values': int(df[column].isna().sum()),
                    'missing_percentage': round(df[column].isna().mean() * 100, 2)
                }
            else:
                value_counts = df[column].value_counts()
                value_percentages = df[column].value_counts(normalize=True) * 100
                column_stats[column] = {
                    'type': 'categorical',
                    'unique_count': int(len(value_counts)),
                    'most_common': [
                        {
                            'value': str(value),
                            'count': int(count),
                            'percentage': round(float(value_percentages[value]), 2)
                        }
                        for value, count in value_counts.head(5).items()
                    ],
                    'missing_values': int(df[column].isna().sum()),
                    'missing_percentage': round(df[column].isna().mean() * 100, 2)
                }

        # Basic dataset info
        dataset_info = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),  # In MB
            'duplicated_rows': int(df.duplicated().sum())
        }

        # Save stats to analysis results
        dataset.analysis_results['dataset_stats'] = {
            'column_stats': column_stats,
            'dataset_info': dataset_info
        }
        dataset.save()

        return JsonResponse({
            'columns': df.columns.tolist(),
            'data': df.head(10).to_dict('records'),
            'total_rows': len(df),
            'stats': {
                'column_stats': column_stats,
                'dataset_info': dataset_info
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({'success': True, 'redirect': reverse('analyzer:home')})
        return JsonResponse({'success': False, 'message': 'Nom d\'utilisateur ou mot de passe incorrect'})
    return render(request, 'analyzer/login.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({'success': True, 'redirect': reverse('analyzer:home')})
        else:
            print(form.errors)  # Imprimez les erreurs du formulaire pour déboguer
            errors = {field: form.errors[field][0] for field in form.errors}
            return JsonResponse({'success': False, 'errors': errors})
    return render(request, 'analyzer/login.html')

def logout_view(request):
    logout(request)
    return redirect('analyzer:login')

@csrf_exempt
@login_required
def handle_upload(request):
   try:
       file = request.FILES['file']
       content = file.read().decode('utf-8')
       df = pd.read_csv(io.StringIO(content))
       
       data_file = DataFile(
           file=file,
           filename=file.name,
           data_json=df.to_dict('records'),
           columns=df.columns.tolist(),
           analysis_results={},
           user=request.user  # Add this line
       )
       data_file.save()
       request.session['current_dataset_id'] = data_file.id
       
       return JsonResponse({
           'success': True,
           'columns': df.columns.tolist()
       })
   except Exception as e:
       return JsonResponse({'error': str(e)}, status=400)

def generate_plot(request):
  try:
      dataset_id = request.session.get('current_dataset_id')
      dataset = DataFile.objects.get(id=dataset_id)
      df = pd.DataFrame(dataset.data_json)
      
      columns = request.GET.get('columns', '').split(',')
      plot_type = request.GET.get('type')
      
      plt.figure(figsize=(2.7, 3.2))
      plt.clf()
      
      # Supprime l'ancien graphique
      if dataset.analysis_results:
          dataset.analysis_results = {k:v for k,v in dataset.analysis_results.items() 
                                    if not k.startswith(f'plot_{plot_type}')}
            
      if plot_type == 'pie':
          counts = df[columns[0]].value_counts()
          plt.pie(counts, labels=counts.index, autopct='%1.1f%%',
                 colors=plt.cm.Pastel1(np.linspace(0, 1, len(counts))))
          
      elif plot_type == 'bar':
          if len(columns) == 2:
              df[columns[1]] = pd.to_numeric(df[columns[1]], errors='coerce')
              grouped = df.groupby(columns[0])[columns[1]].sum()
              ax = grouped.plot(kind='bar', color='#FF6B6B')
              plt.xticks(rotation=45, ha='right')
              plt.ylabel(columns[1])
              for i, v in enumerate(grouped):
                  ax.text(i, v + v*0.02, f'{v:,.0f}', ha='center', fontsize=10)
          else:
              counts = df[columns[0]].value_counts()
              ax = counts.plot(kind='bar', color='#FF6B6B')
              plt.xticks(rotation=45, ha='right')
              plt.ylabel('Fréquence')
              for i, v in enumerate(counts):
                  ax.text(i, v + v*0.02, f'{v:,.0f}', ha='center', fontsize=10)
                  
      elif plot_type == 'line':
          df[columns[1]] = pd.to_numeric(df[columns[1]], errors='coerce')
          plt.plot(df[columns[0]], df[columns[1]], marker='o', color='#FF6B6B')
          plt.xticks(rotation=45, ha='right')
          plt.ylabel(columns[1])
          
      elif plot_type == 'histogram':
          df[columns[0]] = pd.to_numeric(df[columns[0]], errors='coerce')
          plt.hist(df[columns[0]], bins=30, edgecolor='black', color='#FF6B6B')
          plt.xlabel(columns[0])
          plt.ylabel('Fréquence')

      plt.grid(True, alpha=0.3)
      plt.tight_layout()
      
      buf = io.BytesIO()
      plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
      plt.close()
      
      buf.seek(0)
      image = base64.b64encode(buf.getvalue()).decode('utf-8')
      buf.close()
      
      # Sauvegarde le nouveau graphique
      dataset.analysis_results[f'plot_{plot_type}_{",".join(columns)}'] = {
          'type': plot_type,
          'columns': columns,
          'image': image
      }
      dataset.save()
      
      return JsonResponse({'success': True, 'image': image})
      
  except Exception as e:
      plt.close()
      return JsonResponse({'success': False, 'error': str(e)}, status=400)
  
def login_register(request):
    return render(request, 'analyzer/login.html')

def get_stats(request):
    try:
        dataset_id = request.session.get('current_dataset_id')
        dataset = get_object_or_404(DataFile, id=dataset_id)
        df = pd.DataFrame(dataset.data_json)
        
        column = request.GET.get('column')
        
        # Check if column is numeric
        if pd.api.types.is_numeric_dtype(df[column]):
            stats = {
                'type': 'numeric',
                'mean': float(df[column].mean()),     # Moyenne
                'median': float(df[column].median()), # Médiane
                'std': float(df[column].std()),      # Ecart-type
                'min': float(df[column].min()),      # Minimum
                'max': float(df[column].max()),      # Maximum
                'q1': float(df[column].quantile(0.25)),  # Premier quartile
                'q3': float(df[column].quantile(0.75)),  # Troisième quartile
                'skewness': float(df[column].skew()),    # Asymétrie
                'kurtosis': float(df[column].kurtosis()), # Kurtosis
                'missing_values': int(df[column].isna().sum()) # Valeurs manquantes
            }
        else:
            # Si la colonne est catégorique, calculer les statistiques appropriées
            value_counts = df[column].value_counts()
            stats = {
                'type': 'categorical',
                'unique_count': int(len(value_counts)),  # Nombre de valeurs uniques
                'most_common': [
                    {'value': str(value), 'count': int(count)}
                    for value, count in value_counts.head(5).items()  # 5 valeurs les plus fréquentes
                ],
                'missing_values': int(df[column].isna().sum()) # Valeurs manquantes
            }
            
        # Save stats to analysis results
        dataset.analysis_results[f'stats_{column}'] = stats
        dataset.save()
        
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_analysis_details(request, analysis_id):
   try:
       dataset = DataFile.objects.get(id=analysis_id)
       return JsonResponse({
           'filename': dataset.filename,
           'upload_date': dataset.uploaded_at.strftime('%Y-%m-%d %H:%M'),
           'analysis_results': dataset.analysis_results or {},
           'columns': dataset.columns
       })
   except DataFile.DoesNotExist:
       return JsonResponse({'error': 'Analysis not found'}, status=404)

# generate_pdf
def generate_pdf(request):
    try:
        dataset_id = request.session.get('current_dataset_id')
        dataset = DataFile.objects.get(id=dataset_id)
        df = pd.DataFrame(dataset.data_json)
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # En-tête
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, height - 50, f"Analyse du fichier: {dataset.filename}")
        p.drawString(50, height - 80, f"Date: {dataset.uploaded_at.strftime('%d/%m/%Y %H:%M')}")

        # 1. Aperçu des données
        y_position = height - 120
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y_position, "1. Aperçu des données")
        
        cols = df.columns.tolist()
        col_width = (width - 100) / len(cols)
        y_position -= 30

        p.setFont("Helvetica-Bold", 10)
        for i, col in enumerate(cols):
            p.drawString(50 + (i * col_width), y_position, str(col))

        for _, row in df.head(10).iterrows():
            y_position -= 20
            if y_position < 50:
                p.showPage()
                y_position = height - 50
            for i, val in enumerate(row):
                text = str(val)[:15]
                p.drawString(50 + (i * col_width), y_position, text)

        # 2. Statistiques
        p.showPage()
        y_position = height - 50
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y_position, "2. Statistiques par colonne")

        for col in df.columns:
            y_position -= 40
            if y_position < 100:
                p.showPage()
                y_position = height - 50

            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y_position, f"Colonne: {col}")

            if pd.api.types.is_numeric_dtype(df[col]):
                stats = df[col].describe()
                stats_text = [
                    f"Moyenne: {stats['mean']:.2f}",
                    f"Médiane: {stats['50%']:.2f}",
                    f"Écart-type: {stats['std']:.2f}",
                    f"Min: {stats['min']:.2f}",
                    f"Max: {stats['max']:.2f}",
                    f"Q1: {stats['25%']:.2f}",
                    f"Q3: {stats['75%']:.2f}",
                ]
            else:
                value_counts = df[col].value_counts()
                stats_text = [
                    f"Nombre de valeurs uniques: {len(value_counts)}",
                    "Valeurs les plus fréquentes:"
                ]
                for val, count in value_counts.head(5).items():
                    percentage = (count / len(df)) * 100
                    stats_text.append(f"  - {val}: {count} ({percentage:.1f}%)")

            p.setFont("Helvetica", 12)
            for stat in stats_text:
                y_position -= 20
                p.drawString(70, y_position, stat)

        # 3. Graphiques générés par l'utilisateur
        if dataset.analysis_results:
            plots = {k: v for k, v in dataset.analysis_results.items() if k.startswith('plot_')}
            
            if plots:
                # Prendre le dernier graphique généré
                last_plot = list(plots.items())[-1][1]
                
                p.showPage()
                y_position = height - 50
                
                p.setFont("Helvetica-Bold", 16)
                p.drawString(50, y_position, f"3. Graphique généré: {last_plot['type'].title()}")
                
                y_position -= 30
                p.setFont("Helvetica", 12)
                p.drawString(50, y_position, f"Colonnes sélectionnées: {', '.join(last_plot['columns'])}")
                
                img_data = base64.b64decode(last_plot['image'])
                img_buffer = io.BytesIO(img_data)
                p.drawImage(ImageReader(img_buffer), 50, height-400, width=400, height=300)

        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"{dataset.filename}_analyse.pdf")
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# download_pdf 
def download_pdf(request, dataset_id):
   try:
       dataset = get_object_or_404(DataFile, id=dataset_id)
       df = pd.DataFrame(dataset.data_json)
       
       buffer = io.BytesIO()
       p = canvas.Canvas(buffer, pagesize=A4)
       width, height = A4
       
       def new_page():
           p.showPage()
           p.setFont("Helvetica-Bold", 16)
           return height - 50

       # Title Page
       y_position = height - 50
       p.setFont("Helvetica-Bold", 20)
       p.drawString(50, y_position, f"Analyse du fichier: {dataset.filename}")
       y_position -= 30
       p.setFont("Helvetica", 14)
       p.drawString(50, y_position, f"Date d'analyse: {dataset.uploaded_at.strftime('%d/%m/%Y %H:%M')}")
       
       # Stats section
       y_position -= 50
       p.setFont("Helvetica-Bold", 16)
       p.drawString(50, y_position, "Statistiques descriptives")
       
       for col in dataset.columns:
           if pd.api.types.is_numeric_dtype(df[col]):
               stats = df[col].describe()
               if y_position < 100:
                   y_position = new_page()
               y_position -= 30
               p.setFont("Helvetica-Bold", 14)
               p.drawString(50, y_position, f"Colonne: {col}")
               y_position -= 20
               p.setFont("Helvetica", 12)
               stats_text = [
                   f"Moyenne: {stats['mean']:.2f}",
                   f"Médiane: {stats['50%']:.2f}",
                   f"Écart-type: {stats['std']:.2f}",
                   f"Min: {stats['min']:.2f}",
                   f"Max: {stats['max']:.2f}"
               ]
               for stat in stats_text:
                   p.drawString(70, y_position, stat)
                   y_position -= 20

       # Data Preview on new page
       y_position = new_page()
       p.setFont("Helvetica-Bold", 16)
       p.drawString(50, y_position, "Aperçu des données (10 premières lignes)")
       y_position -= 30
       
       cols = df.columns.tolist()
       col_width = (width - 100) / len(cols)
       x_positions = [50 + (i * col_width) for i in range(len(cols))]
       
       p.setFont("Helvetica-Bold", 10)
       for i, col in enumerate(cols):
           p.drawString(x_positions[i], y_position, str(col))
       
       p.setFont("Helvetica", 10)
       for _, row in df.head(10).iterrows():
           y_position -= 20
           if y_position < 50:
               y_position = new_page()
           for i, val in enumerate(row):
               text = str(val)
               if len(text) > 20:
                   text = text[:17] + "..."
               p.drawString(x_positions[i], y_position, text)

       # Draw all graphs, one per page
       if dataset.analysis_results:
           for key, value in dataset.analysis_results.items():
               if key.startswith('plot_'):
                   p.showPage()
                   y_position = height - 50
                   p.setFont("Helvetica-Bold", 14)
                   plot_title = f"Graphique: {value['type'].title()}"
                   p.drawString(50, y_position, plot_title)
                   
                   y_position -= 20
                   p.setFont("Helvetica", 12)  
                   p.drawString(50, y_position, f"Colonnes: {', '.join(value['columns'])}")
                   
                   img_data = base64.b64decode(value['image'])
                   img_buffer = io.BytesIO(img_data)
                   p.drawImage(ImageReader(img_buffer), 50, 100, width=width-100, height=height-200)

       p.save()
       buffer.seek(0)
       return FileResponse(buffer, as_attachment=True, filename=f"{dataset.filename}_analyse.pdf")
   except Exception as e:
       return JsonResponse({'error': str(e)}, status=500)

def download_pdf(request, dataset_id):
  try:
      dataset = get_object_or_404(DataFile, id=dataset_id)
      df = pd.DataFrame(dataset.data_json)
      
      buffer = io.BytesIO()
      p = canvas.Canvas(buffer, pagesize=A4)
      width, height = A4
      
      def new_page():
          p.showPage()
          p.setFont("Helvetica-Bold", 16)
          return height - 50

      # Title Page
      y_position = height - 50
      p.setFont("Helvetica-Bold", 20)
      p.drawString(50, y_position, f"Analyse du fichier: {dataset.filename}")
      
      y_position -= 30
      p.setFont("Helvetica", 14)
      p.drawString(50, y_position, f"Date d'analyse: {dataset.uploaded_at.strftime('%d/%m/%Y %H:%M')}")
      
      # Stats section
      y_position -= 50
      p.setFont("Helvetica-Bold", 16)
      p.drawString(50, y_position, "Statistiques descriptives")
      
      for col in dataset.columns:
          if pd.api.types.is_numeric_dtype(df[col]):
              stats = df[col].describe()
              if y_position < 100:
                  y_position = new_page()
              y_position -= 30
              p.setFont("Helvetica-Bold", 14)
              p.drawString(50, y_position, f"Colonne: {col}")
              y_position -= 20
              p.setFont("Helvetica", 12)
              stats_text = [
                  f"Moyenne: {stats['mean']:.2f}",
                  f"Médiane: {stats['50%']:.2f}",
                  f"Écart-type: {stats['std']:.2f}",
                  f"Min: {stats['min']:.2f}",
                  f"Max: {stats['max']:.2f}"
              ]
              for stat in stats_text:
                  p.drawString(70, y_position, stat)
                  y_position -= 20

      # Data Preview 
      y_position = new_page()
      p.setFont("Helvetica-Bold", 16)
      p.drawString(50, y_position, "Aperçu des données (10 premières lignes)")
      
      y_position -= 30
      cols = df.columns.tolist()
      col_width = (width - 100) / len(cols)
      x_positions = [50 + (i * col_width) for i in range(len(cols))]
      
      p.setFont("Helvetica-Bold", 10)
      for i, col in enumerate(cols):
          p.drawString(x_positions[i], y_position, str(col))
      
      p.setFont("Helvetica", 10)
      for _, row in df.head(10).iterrows():
          y_position -= 20
          if y_position < 50:
              y_position = new_page()
          for i, val in enumerate(row):
              text = str(val)
              if len(text) > 20:
                  text = text[:17] + "..."
              p.drawString(x_positions[i], y_position, text)

      # Graphs
      if dataset.analysis_results:
          for key, value in dataset.analysis_results.items():
              if key.startswith('plot_'):
                  p.showPage()
                  y_position = height - 100
                  
                  p.setFont("Helvetica-Bold", 16)
                  plot_title = f"Graphique: {value['type'].title()}"
                  p.drawString(50, y_position, plot_title)
                  
                  y_position -= 30
                  p.setFont("Helvetica", 12)
                  p.drawString(50, y_position, f"Colonnes: {', '.join(value['columns'])}")
                  
                  img_data = base64.b64decode(value['image'])
                  img_buffer = io.BytesIO(img_data)
                  graph_width = width - 100
                  graph_height = 400
                  x_position = 50
                  y_position = 150
                  
                  p.drawImage(ImageReader(img_buffer),
                            x_position,
                            y_position,
                            width=graph_width,
                            height=graph_height,
                            preserveAspectRatio=True)

      p.save()
      buffer.seek(0)
      return FileResponse(buffer, as_attachment=True, filename=f"{dataset.filename}_analyse.pdf")
      
  except Exception as e:
      return JsonResponse({'error': str(e)}, status=500)

def analyze_dataset(request, dataset_id):
   dataset = get_object_or_404(DataFile, id=dataset_id) 
   request.session['current_dataset_id'] = dataset.id
   return redirect('analyzer:analyze')