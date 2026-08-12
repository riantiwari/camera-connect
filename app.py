import os, time, math
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE, 'camera_connect.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(100), nullable=False); email=db.Column(db.String(160), unique=True, nullable=False); password=db.Column(db.String(255), nullable=False); role=db.Column(db.String(30), default='photographer'); city=db.Column(db.String(100), default=''); bio=db.Column(db.Text, default=''); specialties=db.Column(db.String(255), default=''); avatar=db.Column(db.String(255), default=''); is_admin=db.Column(db.Boolean, default=False); created_at=db.Column(db.Integer, default=lambda:int(time.time()))
class Car(db.Model):
    id=db.Column(db.Integer, primary_key=True); owner_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False); year=db.Column(db.Integer); make=db.Column(db.String(80)); model=db.Column(db.String(100)); color=db.Column(db.String(80)); city=db.Column(db.String(100)); state=db.Column(db.String(30)); price=db.Column(db.Integer, default=0); description=db.Column(db.Text, default=''); shoot_types=db.Column(db.String(255), default='Photography'); image=db.Column(db.String(255), default=''); active=db.Column(db.Boolean, default=True); created_at=db.Column(db.Integer, default=lambda:int(time.time())); owner=db.relationship('User', backref='cars')
class Portfolio(db.Model):
    id=db.Column(db.Integer, primary_key=True); user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False); image=db.Column(db.String(255)); caption=db.Column(db.String(255), default=''); user=db.relationship('User', backref='portfolio')
class Job(db.Model):
    id=db.Column(db.Integer, primary_key=True); owner_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False); title=db.Column(db.String(160)); city=db.Column(db.String(100)); date=db.Column(db.String(50)); budget=db.Column(db.Integer, default=0); category=db.Column(db.String(80), default='Automotive'); description=db.Column(db.Text, default=''); active=db.Column(db.Boolean, default=True); owner=db.relationship('User', backref='jobs')
class Application(db.Model):
    id=db.Column(db.Integer, primary_key=True); job_id=db.Column(db.Integer, db.ForeignKey('job.id')); photographer_id=db.Column(db.Integer, db.ForeignKey('user.id')); message=db.Column(db.Text, default=''); status=db.Column(db.String(30), default='pending'); job=db.relationship('Job', backref='applications'); photographer=db.relationship('User')
class ShootRequest(db.Model):
    id=db.Column(db.Integer, primary_key=True); car_id=db.Column(db.Integer, db.ForeignKey('car.id')); photographer_id=db.Column(db.Integer, db.ForeignKey('user.id')); date=db.Column(db.String(50)); message=db.Column(db.Text); status=db.Column(db.String(30), default='requested'); car=db.relationship('Car'); photographer=db.relationship('User')
class Review(db.Model):
    id=db.Column(db.Integer, primary_key=True); reviewer_id=db.Column(db.Integer, db.ForeignKey('user.id')); reviewee_id=db.Column(db.Integer, db.ForeignKey('user.id')); rating=db.Column(db.Integer); comment=db.Column(db.Text); created_at=db.Column(db.Integer, default=lambda:int(time.time())); reviewer=db.relationship('User', foreign_keys=[reviewer_id])
class Blog(db.Model):
    id=db.Column(db.Integer, primary_key=True); title=db.Column(db.String(180)); slug=db.Column(db.String(180), unique=True); excerpt=db.Column(db.Text); body=db.Column(db.Text); published=db.Column(db.Boolean, default=True); created_at=db.Column(db.Integer, default=lambda:int(time.time()))
class Contact(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(100)); email=db.Column(db.String(160)); message=db.Column(db.Text); created_at=db.Column(db.Integer, default=lambda:int(time.time()))
class Event(db.Model):
    id=db.Column(db.Integer, primary_key=True); user_id=db.Column(db.Integer, nullable=True); event_type=db.Column(db.String(60)); target_type=db.Column(db.String(40)); target_id=db.Column(db.Integer); created_at=db.Column(db.Integer, default=lambda:int(time.time()))

def me(): return db.session.get(User, session.get('user_id')) if session.get('user_id') else None
def login_required(f):
    @wraps(f)
    def inner(*a,**k):
        if not me(): return redirect(url_for('login', next=request.path))
        return f(*a,**k)
    return inner
def admin_required(f):
    @wraps(f)
    def inner(*a,**k):
        u=me()
        if not u or not u.is_admin: abort(403)
        return f(*a,**k)
    return inner
def track(kind,target_type='',target_id=0):
    db.session.add(Event(user_id=session.get('user_id'),event_type=kind,target_type=target_type,target_id=target_id)); db.session.commit()
def score(uid):
    rows=Review.query.filter_by(reviewee_id=uid).all(); n=len(rows); avg=sum(r.rating for r in rows)/n if n else 0
    prior, weight=4.5,5
    bayes=(weight*prior+n*avg)/(weight+n) if n else prior
    completed=ShootRequest.query.filter_by(photographer_id=uid,status='completed').count()
    return round(min(100,bayes*16 + min(n,20)*.7 + min(completed,20)*.6),1), round(avg,1), n
@app.context_processor
def inject(): return {'me':me(),'score':score}

@app.route('/')
def home(): return render_template('index.html', cars=Car.query.filter_by(active=True).order_by(Car.id.desc()).limit(6).all(), photographers=User.query.filter_by(role='photographer').limit(4).all())
@app.route('/cars')
def cars():
    q=request.args.get('q','').strip(); city=request.args.get('city','').strip(); query=Car.query.filter_by(active=True)
    if q: query=query.filter(db.or_(Car.make.ilike(f'%{q}%'),Car.model.ilike(f'%{q}%')))
    if city: query=query.filter(Car.city.ilike(f'%{city}%'))
    return render_template('cars.html', cars=query.order_by(Car.id.desc()).all())
@app.route('/cars/<int:cid>')
def car_detail(cid): track('car_view','car',cid); return render_template('car.html', car=Car.query.get_or_404(cid))
@app.route('/photographers')
def photographers(): return render_template('photographers.html', users=User.query.filter_by(role='photographer').all())
@app.route('/profile/<int:uid>')
def profile(uid): track('profile_view','user',uid); return render_template('profile.html', user=User.query.get_or_404(uid), reviews=Review.query.filter_by(reviewee_id=uid).order_by(Review.id.desc()).all())
@app.route('/jobs')
def jobs(): return render_template('jobs.html', jobs=Job.query.filter_by(active=True).order_by(Job.id.desc()).all())
@app.route('/page/<kind>')
def landing(kind):
    allowed={'photographers','owners','movie','style','pricing','contact'}
    if kind not in allowed: abort(404)
    return render_template('landing.html',kind=kind)
@app.route('/blog')
def blog(): return render_template('blog.html', posts=Blog.query.filter_by(published=True).order_by(Blog.id.desc()).all())
@app.route('/blog/<slug>')
def blog_post(slug): return render_template('blog_post.html', post=Blog.query.filter_by(slug=slug,published=True).first_or_404())

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        if User.query.filter_by(email=request.form['email'].lower()).first(): flash('Email already exists.'); return redirect(url_for('signup'))
        u=User(name=request.form['name'],email=request.form['email'].lower(),password=generate_password_hash(request.form['password']),role=request.form['role'],city=request.form.get('city',''))
        db.session.add(u); db.session.commit(); session['user_id']=u.id; return redirect(url_for('dashboard'))
    return render_template('auth.html',mode='signup')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(email=request.form['email'].lower()).first()
        if u and check_password_hash(u.password,request.form['password']): session['user_id']=u.id; return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid email or password.')
    return render_template('auth.html',mode='login')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))
@app.route('/dashboard')
@login_required
def dashboard():
    u=me(); incoming=[]
    if u.role=='owner': incoming=ShootRequest.query.join(Car).filter(Car.owner_id==u.id).order_by(ShootRequest.id.desc()).all()
    else: incoming=ShootRequest.query.filter_by(photographer_id=u.id).order_by(ShootRequest.id.desc()).all()
    return render_template('dashboard.html',requests=incoming)
@app.post('/profile/edit')
@login_required
def edit_profile():
    u=me(); u.name=request.form['name']; u.city=request.form.get('city',''); u.bio=request.form.get('bio',''); u.specialties=request.form.get('specialties',''); db.session.commit(); return redirect(url_for('profile',uid=u.id))

def save_upload(field):
    f=request.files.get(field)
    if not f or not f.filename: return ''
    name=f'{int(time.time()*1000)}-{secure_filename(f.filename)}'; f.save(os.path.join(app.config['UPLOAD_FOLDER'],name)); return name
@app.route('/uploads/<path:name>')
def uploads(name): return send_from_directory(app.config['UPLOAD_FOLDER'],name)
@app.post('/portfolio/add')
@login_required
def add_portfolio():
    image=save_upload('image')
    if image: db.session.add(Portfolio(user_id=me().id,image=image,caption=request.form.get('caption',''))); db.session.commit()
    return redirect(url_for('profile',uid=me().id))
@app.post('/cars/add')
@login_required
def add_car():
    u=me()
    if u.role!='owner': abort(403)
    image=save_upload('image'); c=Car(owner_id=u.id,year=request.form.get('year',type=int),make=request.form['make'],model=request.form['model'],color=request.form.get('color',''),city=request.form.get('city',u.city),state=request.form.get('state',''),price=request.form.get('price',0,type=int),description=request.form.get('description',''),shoot_types=request.form.get('shoot_types','Photography'),image=image)
    db.session.add(c); db.session.commit(); return redirect(url_for('car_detail',cid=c.id))
@app.post('/jobs/add')
@login_required
def add_job():
    u=me()
    if u.role!='owner': abort(403)
    j=Job(owner_id=u.id,title=request.form['title'],city=request.form.get('city',u.city),date=request.form.get('date',''),budget=request.form.get('budget',0,type=int),category=request.form.get('category','Automotive'),description=request.form.get('description',''))
    db.session.add(j); db.session.commit(); return redirect(url_for('jobs'))
@app.post('/jobs/<int:jid>/apply')
@login_required
def apply_job(jid):
    u=me()
    if u.role!='photographer': abort(403)
    if not Application.query.filter_by(job_id=jid,photographer_id=u.id).first(): db.session.add(Application(job_id=jid,photographer_id=u.id,message=request.form.get('message','Interested in this shoot.'))); db.session.commit(); track('apply','job',jid)
    return redirect(url_for('jobs'))
@app.post('/cars/<int:cid>/request')
@login_required
def request_car(cid):
    u=me()
    if u.role!='photographer': abort(403)
    db.session.add(ShootRequest(car_id=cid,photographer_id=u.id,date=request.form.get('date',''),message=request.form.get('message',''))); db.session.commit(); track('request','car',cid); return redirect(url_for('dashboard'))
@app.post('/requests/<int:rid>/<action>')
@login_required
def request_action(rid,action):
    r=ShootRequest.query.get_or_404(rid); u=me()
    if r.car.owner_id!=u.id and r.photographer_id!=u.id: abort(403)
    if action not in {'accepted','declined','completed'}: abort(400)
    r.status=action; db.session.commit(); return redirect(url_for('dashboard'))
@app.post('/review/<int:uid>')
@login_required
def add_review(uid):
    db.session.add(Review(reviewer_id=me().id,reviewee_id=uid,rating=max(1,min(5,request.form.get('rating',5,type=int))),comment=request.form.get('comment',''))); db.session.commit(); return redirect(url_for('profile',uid=uid))
@app.post('/contact')
def contact_submit(): db.session.add(Contact(name=request.form['name'],email=request.form['email'],message=request.form['message'])); db.session.commit(); flash('Message sent.'); return redirect(url_for('landing',kind='contact'))

@app.route('/admin')
@admin_required
def admin(): return render_template('admin.html',users=User.query.order_by(User.id.desc()).all(),cars=Car.query.order_by(Car.id.desc()).all(),jobs=Job.query.order_by(Job.id.desc()).all(),posts=Blog.query.order_by(Blog.id.desc()).all(),contacts=Contact.query.order_by(Contact.id.desc()).all())
@app.post('/admin/blog')
@admin_required
def admin_blog():
    slug='-'.join(request.form['title'].lower().split())
    db.session.add(Blog(title=request.form['title'],slug=slug,excerpt=request.form.get('excerpt',''),body=request.form.get('body',''),published=True)); db.session.commit(); return redirect(url_for('admin'))
@app.post('/admin/car/<int:cid>/toggle')
@admin_required
def admin_car_toggle(cid): c=Car.query.get_or_404(cid); c.active=not c.active; db.session.commit(); return redirect(url_for('admin'))

@app.cli.command('seed')
def seed():
    db.create_all()
    if User.query.count(): print('Database already has users.'); return
    pw=generate_password_hash('demo123')
    admin=User(name='PhotoWhips Admin',email='admin@demo.com',password=pw,role='owner',city='Los Angeles',is_admin=True)
    maya=User(name='Maya Chen',email='maya@demo.com',password=pw,role='photographer',city='Los Angeles',bio='Automotive and lifestyle photographer.',specialties='Automotive, Rolling, Editorial')
    leo=User(name='Leo Martinez',email='leo@demo.com',password=pw,role='photographer',city='Phoenix',bio='Film, night work and rolling shots.',specialties='Automotive, Film, Night')
    jake=User(name='Jake Morrison',email='jake@demo.com',password=pw,role='owner',city='Los Angeles',bio='Classic Porsche and BMW collector.')
    db.session.add_all([admin,maya,leo,jake]); db.session.commit()
    db.session.add_all([Car(owner_id=jake.id,year=1988,make='Porsche',model='911 Carrera',color='Guards Red',city='Los Angeles',state='CA',price=220,description='Air-cooled icon available for stills, editorial and controlled rolling shots.',shoot_types='Photography, Style, Film'),Car(owner_id=admin.id,year=1994,make='Toyota',model='Supra',color='Silver',city='Los Angeles',state='CA',price=245,description='Tasteful street build for automotive and lifestyle shoots.',shoot_types='Photography, Commercial, Music Video'),Job(owner_id=jake.id,title='Golden hour Porsche shoot',city='Los Angeles',date='Saturday',budget=250,category='Automotive',description='Looking for an automotive photographer for golden-hour stills and detail shots.'),Blog(title='How PhotoWhips works',slug='how-photowhips-works',excerpt='A better way for car owners and photographers to collaborate.',body='PhotoWhips connects distinctive cars with photographers and creative productions. Browse, request, shoot, review, and build your reputation.')]); db.session.commit(); print('Seeded. Demo password: demo123')

with app.app_context(): db.create_all()
if __name__=='__main__': app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT',8000)))
