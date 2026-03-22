from flask_migrate import Migrate
import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from models import db, User, Food

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_super_secret_key_123' 

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local_database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db) 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    foods = Food.query.order_by(Food.created_at.desc()).all()
    return render_template('index.html', foods=foods)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password') 
        
        if password != confirm_password:
            flash('รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน กรุณาลองใหม่')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('ชื่อผู้ใช้นี้มีคนใช้แล้ว กรุณาใช้ชื่ออื่น')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        
        flash('สมัครสมาชิกสำเร็จและเข้าสู่ระบบเรียบร้อย!')
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_food', methods=['GET', 'POST'])
@login_required
def add_food():
    if request.method == 'POST':
        name = request.form.get('name')
        country = request.form.get('country')
        food_type = request.form.get('food_type') 
        image_url = request.form.get('image_url')
        year_origin = request.form.get('year_origin')
        
        if image_url and len(image_url) > 500:
            flash('ใช้รูปภาพไม่ได้ (ลิงก์ยาวเกินไป กรุณาคลิกขวาแล้วเลือก "คัดลอกที่อยู่รูปภาพ" แทนครับ)')
            return redirect(url_for('add_food'))
        
        new_food = Food(
            name=name, 
            country=country, 
            food_type=food_type, 
            image_url=image_url,
            year_origin=year_origin,
            user_id=current_user.id
        )
        
        db.session.add(new_food)
        db.session.commit()
        
        flash('บันทึกเมนูอาหารเรียบร้อยแล้ว!')
        return redirect(url_for('index'))
        
    return render_template('add_food.html')

@app.route('/edit_food/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_food(id):
    food = Food.query.get_or_404(id)
    
    if food.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์แก้ไขเมนูนี้ เนื่องจากคุณไม่ได้เป็นคนสร้างครับ!')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        food.name = request.form.get('name')
        food.country = request.form.get('country')
        food.food_type = request.form.get('food_type')
        food.image_url = request.form.get('image_url')
        food.year_origin = request.form.get('year_origin')

        if food.image_url and len(food.image_url) > 500:
            flash('ใช้รูปภาพไม่ได้ (ลิงก์ยาวเกินไป กรุณาคลิกขวาแล้วเลือก "คัดลอกที่อยู่รูปภาพ" แทนครับ)')
            return redirect(url_for('edit_food', id=food.id))
        
        db.session.commit()
        flash('อัปเดตข้อมูลเมนูอาหารเรียบร้อยแล้ว!')
        return redirect(url_for('index'))
        
    return render_template('edit_food.html', food=food)


@app.route('/delete_food/<int:id>', methods=['POST'])
@login_required
def delete_food(id):
    food = Food.query.get_or_404(id)
    if food.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ลบเมนูนี้ เนื่องจากคุณไม่ได้เป็นคนสร้างครับ!')
        return redirect(url_for('index'))
    
    db.session.delete(food)
    db.session.commit()
    
    flash('ลบเมนูอาหารออกจากระบบเรียบร้อยแล้ว!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

