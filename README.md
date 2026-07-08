# Disease Outbreak Prediction System

An AI-powered web-based disease outbreak prediction system built with Python Flask and machine learning. Analyzes historical disease data and environmental risk factors to predict outbreak risks across Ghana's regions — and now includes a community case reporting system that allows real users to submit live observations for ongoing analysis and research.

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

### Community Case Reporting (New)
- Public submission form at `/submit` allowing anyone to report observed disease cases
- Collects reporter name, email, organization, region, disease, case count, date observed, and free-text notes
- No password required for public users — low friction reporting designed to maximize participation
- Automatically links repeat submissions from the same email to a single submitter profile

### Admin Review Dashboard (New)
- Password-protected admin panel at `/admin` for reviewing all community submissions
- Summary statistics: total submissions, unique submitters, total cases reported
- Visual breakdown of reported cases by region and by disease
- Full submissions table with submitter details and notes
- One-click CSV export of all submissions for external analysis and reporting

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
2. Install Flask:
   pip install flask
3. Navigate to this folder in your terminal
4. Run the application:
   python app.py
5. Open your browser and go to:
   http://127.0.0.1:5000

### Additional Routes
- Public submission form: http://127.0.0.1:5000/submit
- Admin login: http://127.0.0.1:5000/admin/login
- Admin dashboard (after login): http://127.0.0.1:5000/admin

**Note:** Before deploying publicly, change the `ADMIN_PASSWORD` and `app.secret_key` values in app.py to your own private values.

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

## Community Data Collection
Beyond the historical simulated dataset used for the prediction engine, this system now collects real, user-submitted case observations through a public reporting form. This allows for:
- Ground-truth validation of model predictions against real reported cases
- A growing, exportable dataset for ongoing research analysis
- Community participation in public health monitoring, particularly valuable in low-resource settings where formal reporting infrastructure may be limited

Submissions are reviewed through a password-protected admin dashboard and can be exported to CSV for further analysis in tools such as Pandas, Excel, or statistical software.

## Research Context
This project was built as part of research into predictive analytics and community-driven data collection for public health in Sub-Saharan Africa. It demonstrates how data-driven approaches, combined with participatory reporting, can support early warning systems and evidence-based health policy decisions in low-resource settings.

## Author
Emmanuel Owusu Adu
Computer Science Graduate | Health Informatics Researcher
Interests: Health Informatics, Information Systems, Information Science
https://www.linkedin.com/in/emmanuel-owusu-adu-037084341
