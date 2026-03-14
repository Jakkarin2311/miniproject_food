from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ตารางที่ 1: เก็บข้อมูลสมาชิก
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    # ความสัมพันธ์: 1 User สามารถเพิ่มอาหารได้หลายอย่าง (One-to-Many)
    foods = db.relationship('Food', backref='author', lazy=True)

# ตารางที่ 2: เก็บข้อมูลอาหาร
class Food(db.Model):
    __tablename__ = 'foods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    
    # --- เปลี่ยนจาก description เป็น food_type ---
    food_type = db.Column(db.String(50), nullable=False, default='ของคาว') 
    
    image_url = db.Column(db.String(500), nullable=True)
    year_origin = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)