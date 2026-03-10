"""
Smart Market Price Prediction System
Main Application File
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from database import db, User, PredictionHistory
from auth import auth_bp, bcrypt
from admin import admin_bp
from price_predictor import KenyanFarmersPricePredictor
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# SIMPLIFIED DATABASE PATH - creates file in main folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

predictor = KenyanFarmersPricePredictor()
model_path = 'model.pkl'
if os.path.exists(model_path):
    predictor.load_model(model_path)
else:
    print("Training new model...")
    predictor.train()
    predictor.save_model(model_path)

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ Database created successfully!")
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=hashed_password,
            full_name='System Administrator',
            is_admin=True,
            is_farmer=False
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created (username: admin, password: admin123)")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    recent_predictions = PredictionHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(PredictionHistory.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', recent_predictions=recent_predictions)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        crop = data.get('crop')
        market = data.get('market')
        days = int(data.get('days', 7))
        month = data.get('month')
        rainfall = data.get('rainfall')
        temperature = data.get('temperature')
        
        if month:
            month = int(month)
        if rainfall:
            rainfall = float(rainfall)
        if temperature:
            temperature = float(temperature)
        
        result = predictor.predict(
            crop=crop,
            market=market,
            days=days,
            month=month,
            rainfall=rainfall,
            temperature=temperature
        )
        
        if current_user.is_authenticated:
            history = PredictionHistory(
                user_id=current_user.id,
                crop=crop,
                market=market,
                days_ahead=days,
                predicted_price=result['price'],
                min_price=result['min_price'],
                max_price=result['max_price']
            )
            db.session.add(history)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'prediction': result
        })
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/metrics')
def metrics():
    return jsonify(predictor.model_performance)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("SMART MARKET PRICE PREDICTION SYSTEM")
    print("="*50)
    print("\nServer starting...")
    print("Open your browser and go to: http://127.0.0.1:5000")
    print("\nDefault Admin Login:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nPress CTRL+C to stop the server")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)