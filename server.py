from flask_migrate import Migrate
import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# นำเข้า db และตารางที่เราสร้างไว้จากไฟล์ models.py
from models import db, User, Food

# โหลดค่าตัวแปรจากไฟล์ .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_super_secret_key_123' # คีย์สำหรับความปลอดภัย (ตอนขึ้น Render ค่อยเปลี่ยนให้ซับซ้อนขึ้น)

# ตั้งค่าฐานข้อมูล: โค้ดนี้จะใช้ PostgreSQL ถ้ามี URL ในไฟล์ .env แต่ถ้าไม่มีจะสร้างไฟล์ SQLite ชื่อ local_database.db ให้ทดสอบในเครื่องก่อน
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local_database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# เชื่อมต่อ db เข้ากับแอป
db.init_app(app)
migrate = Migrate(app, db)  # <--- เพิ่มบรรทัดนี้

# --- ตั้งค่าระบบ Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # ถ้าผู้ใช้ยังไม่ล็อกอินและพยายามเข้าหน้าหวงห้าม จะเด้งมาหน้านี้

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# สร้างตารางในฐานข้อมูล (ถ้ายังไม่มี)
with app.app_context():
    db.create_all()

# ==========================================
# ROUTES (เส้นทางหน้าเว็บต่างๆ)
# ==========================================

@app.route('/')
def index():
    # แสดงรายการอาหารทั้งหมด เรียงจากล่าสุดไปเก่าสุด
    foods = Food.query.order_by(Food.created_at.desc()).all()
    return render_template('index.html', foods=foods)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # เช็คว่ามี username นี้ในระบบหรือยัง
        user = User.query.filter_by(username=username).first()
        if user:
            flash('ชื่อผู้ใช้นี้มีคนใช้แล้ว กรุณาใช้ชื่ออื่น')
            return redirect(url_for('register'))
            
        # เข้ารหัสผ่านก่อนบันทึกลงฐานข้อมูล
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('สมัครสมาชิกสำเร็จ! กรุณาล็อกอิน')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # ตรวจสอบว่ามีผู้ใช้นี้ และรหัสผ่านที่ถอดรหัสแล้วตรงกัน
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
        food_type = request.form.get('food_type')  # <--- รับค่าประเภทอาหาร
        image_url = request.form.get('image_url')
        year_origin = request.form.get('year_origin')
        
        new_food = Food(
            name=name, 
            country=country, 
            food_type=food_type,  # <--- บันทึกประเภทอาหาร
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
    # ค้นหาข้อมูลอาหารจากไอดี
    food = Food.query.get_or_404(id)
    
    # เช็คสิทธิ์: ถ้าคนที่ล็อกอิน ไม่ใช่เจ้าของเมนู ให้เด้งกลับ!
    if food.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์แก้ไขเมนูนี้ เนื่องจากคุณไม่ได้เป็นคนสร้างครับ!')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        food.name = request.form.get('name')
        food.country = request.form.get('country')
        food.food_type = request.form.get('food_type')
        food.image_url = request.form.get('image_url')
        food.year_origin = request.form.get('year_origin')
        
        db.session.commit()
        flash('อัปเดตข้อมูลเมนูอาหารเรียบร้อยแล้ว!')
        return redirect(url_for('index'))
        
    return render_template('edit_food.html', food=food)


@app.route('/delete_food/<int:id>', methods=['POST'])
@login_required
def delete_food(id):
    # ค้นหาข้อมูลอาหารที่ต้องการลบ
    food = Food.query.get_or_404(id)
    
    # เช็คสิทธิ์: ถ้าคนที่ล็อกอิน ไม่ใช่เจ้าของเมนู ให้เด้งกลับ!
    if food.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ลบเมนูนี้ เนื่องจากคุณไม่ได้เป็นคนสร้างครับ!')
        return redirect(url_for('index'))
    
    # สั่งลบข้อมูลออกจากฐานข้อมูล
    db.session.delete(food)
    db.session.commit()
    
    flash('ลบเมนูอาหารออกจากระบบเรียบร้อยแล้ว!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # รันเซิร์ฟเวอร์
    app.run(debug=True)

