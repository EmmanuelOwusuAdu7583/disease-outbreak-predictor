# Disease Outbreak Prediction System

An AI-powered web-based disease outbreak prediction system built with Python Flask and machine learning. Analyzes historical disease data and environmental risk factors to predict outbreak risks across Ghana’s regions.

## Features

### Predictive Analytics

- Linear regression based disease trend forecasting
- 30-day outbreak predictions for 5 major diseases
- Risk score calculation using multiple factors
- Confidence scoring for all predictions

### Risk Assessment

- Regional risk scores across all Ghana regions
- Disease-specific risk analysis
- Environmental risk factor integration (rainfall, temperature, healthcare access, sanitation)
- Top 10 high-risk outbreak scenario identification

### Interactive Dashboard

- Real-time disease trend visualization
- Interactive 30-day forecasts switchable by disease
- Regional risk score cards with visual indicators
- Comprehensive risk table with trend indicators

### Diseases Monitored

- Malaria
- Cholera
- Typhoid
- Meningitis
- COVID-19

### Regions Covered

- Greater Accra
- Ashanti
- Northern
- Western
- Eastern

## How to Run

1. Install Python 3 on your computer
1. Install Flask:
   pip install flask
1. Navigate to this folder in your terminal
1. Run the application:
   python app.py
1. Open your browser and go to:
   <http://127.0.0.1:5000>

## Technologies Used

- Python 3
- Flask (web framework)
- SQLite3 (database)
- Linear Regression (machine learning algorithm)
- HTML5 and CSS3
- JavaScript
- Chart.js (data visualization)

## Machine Learning Approach

This system uses linear regression to identify trends in historical disease data and project them forward. Risk scores are calculated using a weighted combination of:

- Recent case counts and trends
- Seasonal patterns
- Environmental factors (rainfall, temperature)
- Healthcare access scores
- Sanitation scores

## Research Context

This project was built as part of research into predictive analytics for public health in Sub-Saharan Africa. It demonstrates how data-driven approaches can support early warning systems and evidence-based health policy decisions in low-resource settings.

## Author

Emmanuel Owusu Adu
Computer Science Graduate | Health Informatics Researcher
Interests: Health Informatics, Information Systems, Information Science
<https://www.linkedin.com/in/emmanuel-owusu-adu-037084341>