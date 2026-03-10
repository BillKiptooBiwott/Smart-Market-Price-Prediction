"""
Random Forest Model for Price Prediction
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class KenyanFarmersPricePredictor:
    def __init__(self):
        self.model = None
        self.crop_encoder = LabelEncoder()
        self.market_encoder = LabelEncoder()
        self.feature_importance = None
        self.model_performance = {}
        
    def generate_training_data(self):
        """Generate realistic training data"""
        np.random.seed(42)
        
        crops = ['Maize', 'Tomatoes', 'Onions', 'Bananas']
        markets = ['Nairobi', 'Kirinyaga', 'Uasin Gishu', 'Kisumu', 'Mombasa', 
                   'Nakuru', 'Kiambu', 'Meru', 'Bungoma', 'Machakos']
        
        start_date = datetime(2022, 1, 1)
        dates = [start_date + timedelta(days=i) for i in range(730)]
        
        data = []
        for date in dates:
            for crop in crops:
                for market in markets:
                    month = date.month
                    
                    if month in [3, 4, 5]:
                        rainfall = np.random.uniform(100, 300)
                        season_factor = 0.9
                    elif month in [10, 11, 12]:
                        rainfall = np.random.uniform(50, 150)
                        season_factor = 1.0
                    else:
                        rainfall = np.random.uniform(0, 30)
                        season_factor = 1.2
                    
                    if market in ['Nairobi', 'Mombasa', 'Kisumu']:
                        market_factor = np.random.uniform(1.1, 1.3)
                    elif market in ['Kirinyaga', 'Meru', 'Kiambu']:
                        market_factor = np.random.uniform(0.85, 1.0)
                    else:
                        market_factor = np.random.uniform(0.95, 1.1)
                    
                    base_prices = {
                        'Maize': 40,
                        'Tomatoes': 80,
                        'Onions': 100,
                        'Bananas': 50
                    }
                    
                    price = (base_prices[crop] * season_factor * market_factor 
                            + np.random.normal(0, 5))
                    price = max(10, round(price, 2))
                    
                    data.append({
                        'date': date,
                        'crop': crop,
                        'market': market,
                        'price_kes': price,
                        'rainfall_mm': round(rainfall, 2),
                        'temperature_c': round(np.random.uniform(18, 30), 2),
                        'month': month,
                        'is_rainy_season': 1 if month in [3,4,5,10,11,12] else 0,
                        'is_dry_season': 1 if month in [1,2,6,7,8,9] else 0
                    })
        
        return pd.DataFrame(data)
    
    def train(self):
        """Train the Random Forest model"""
        print("Generating training data...")
        df = self.generate_training_data()
        
        print(f"Training data shape: {df.shape}")
        
        df['crop_code'] = self.crop_encoder.fit_transform(df['crop'])
        df['market_code'] = self.market_encoder.fit_transform(df['market'])
        
        features = [
            'crop_code', 'market_code', 'month',
            'is_rainy_season', 'is_dry_season',
            'rainfall_mm', 'temperature_c'
        ]
        
        X = df[features]
        y = df['price_kes']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print("Training Random Forest model...")
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        
        self.model_performance = {
            'MAE': round(mean_absolute_error(y_test, y_pred), 2),
            'RMSE': round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
            'R2': round(r2_score(y_test, y_pred), 3),
            'samples': len(X_train)
        }
        
        self.feature_importance = pd.DataFrame({
            'feature': features,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("Model training complete!")
        print(f"MAE: {self.model_performance['MAE']} KES")
        print(f"R2: {self.model_performance['R2']}")
        
        return self.model
    
    def predict(self, crop, market, days=7, month=None, rainfall=None, temperature=None):
        """Make price prediction"""
        if self.model is None:
            self.train()
        
        if month is None:
            month = datetime.now().month
        
        if rainfall is None:
            rainfall = 100 if month in [3,4,5,10,11,12] else 20
        
        if temperature is None:
            temperature = 24
        
        try:
            crop_code = self.crop_encoder.transform([crop])[0]
        except:
            crop_code = 0
            
        try:
            market_code = self.market_encoder.transform([market])[0]
        except:
            market_code = 0
        
        features = pd.DataFrame([[
            crop_code, market_code, month,
            1 if month in [3,4,5,10,11,12] else 0,
            1 if month in [1,2,6,7,8,9] else 0,
            rainfall, temperature
        ]], columns=[
            'crop_code', 'market_code', 'month',
            'is_rainy_season', 'is_dry_season',
            'rainfall_mm', 'temperature_c'
        ])
        
        price = self.model.predict(features)[0]
        
        tree_preds = []
        for tree in self.model.estimators_[:50]:
            tree_preds.append(tree.predict(features)[0])
        
        lower = np.percentile(tree_preds, 5)
        upper = np.percentile(tree_preds, 95)
        
        top_features = self.feature_importance.head(3)['feature'].tolist()
        
        explanation = "Based on seasonal patterns and market conditions"
        
        return {
            'crop': crop,
            'market': market,
            'price': round(price, 2),
            'min_price': round(lower, 2),
            'max_price': round(upper, 2),
            'days': days,
            'top_factors': top_features,
            'explanation': explanation,
            'month': month
        }
    
    def save_model(self, filename='model.pkl'):
        """Save the model"""
        joblib.dump({
            'model': self.model,
            'crop_encoder': self.crop_encoder,
            'market_encoder': self.market_encoder,
            'performance': self.model_performance,
            'feature_importance': self.feature_importance
        }, filename)
        print(f"Model saved to {filename}")
    
    def load_model(self, filename='model.pkl'):
        """Load the model"""
        if os.path.exists(filename):
            data = joblib.load(filename)
            self.model = data['model']
            self.crop_encoder = data['crop_encoder']
            self.market_encoder = data['market_encoder']
            self.model_performance = data['performance']
            self.feature_importance = data['feature_importance']
            print("Model loaded from file")
            return True
        return False