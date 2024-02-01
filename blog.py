from flask import (
    Flask,
    render_template,
    flash,
    redirect,
    url_for,
    session,
    logging,
    request,
)
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


# Kullanıcı Girişi Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Sayfayı Görüntülemek İçin Lütfen Giriş Yapın", "danger")
            return redirect(url_for("login"))

    return decorated_function


# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim-Soyisim: ",validators=[validators.length(min= 2,max=20),validators.DataRequired(message= "Devam etmek için lütfen burayı doldurunuz..!")])
    username = StringField("Kullanıcı Adı: ",validators=[validators.length(min= 5,max=15),validators.DataRequired(message="Devam etmek için lütfen burayı doldurunuz..!")])
    email = StringField("E-Posta: ",validators=[validators.Email(message="Lütfen Geçerli Bir E-Posta Adresi Giriniz..!")])
    password = PasswordField("Parola: ", validators=[
        validators.length(min=6,max=18,message="Lütfen 6-18 Karakter Arası Bir Şifre Belirleyiniz!"),
        validators.DataRequired(message= "Burası Boş Bırakılamaz!!"),
        validators.EqualTo(fieldname="confirm",message="Parolalar Uyuşmuyor!Tekrar Deneyiniz.."),
        validators.Regexp(
            regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*()-_+=])[A-Za-z0-9!@#$%^&*()-_+=]{6,18}$',
            message="Şifrenizde en az bir küçük harf, bir büyük harf, bir özel karakter ve bir sayı bulunmalıdır."
        ),
    ])
    confirm = PasswordField("Parolayı Tekrar Giriniz: ")


#Login Form
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

#Makale Ekleme Form
class ArticleForm(Form):
   title = StringField("Makale Adı ",validators=[validators.length(min=5,max=50,message="Makale Adı 5-50 Karakter Arasındadır!"),validators.DataRequired(message="Makale Adı Boş Bırakılamaz!")])
   content = TextAreaField("Makale İçeriği ",validators=[validators.length(min=10,message="Makale En Az 10 Karakterden Oluşmalıdır!"),validators.DataRequired(message="İçerik Boş Bırakılamaz!")])


app = Flask(__name__)

app.secret_key = "fasfasfasFSAFSFSAFASF"

app.config["MYSQL_DATABASE_HOST"] = "localhost"
app.config["MYSQL__DATABASE_USER"] = "irem_"
app.config["MYSQL_DATABASE_PASSWORD"] = "test"
app.config["MYSQL_DATABASE_DB"] = "ybblok"
app.config["MYSQL_DATABASE_CHARSET"] = "utf8"

mysql = MySQL(app)

#Dashboard Sayfası 
@app.route("/")
def index():
    return render_template("index.html")

    
# About Sayfası
@app.route("/about")
def about():
    return render_template("about.html")

#Makale Sayfası
@app.route("/articles")
def articles():
    db = mysql.get_db()
    cursor = db.cursor()
    sorgu = "SELECT * FROM articles"
    cursor.execute(sorgu)

    articles = cursor.fetchall()
    print(articles)
    
    if articles:
        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html", articles=[])



# register sayfası için,form verileri alma
@app.route("/register/", methods=["GET", "POST"])
def register():
    Form = RegisterForm(request.form)

    if request.method == "POST" and Form.validate():
        name = Form.name.data
        username = Form.username.data
        email = Form.email.data
        password = sha256_crypt.encrypt(Form.password.data)

        # Veritabanı bağlantısını al
        db = mysql.get_db()

        cursor = db.cursor()

        sorgu = "INSERT into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(
            sorgu,
            (
                name,
                email,
                username,
                password,
            ),
        )
        # Veritabanını güncelle
        db.commit()

        cursor.close()
        flash("Başarılı", "success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html", form=Form)


# login işlemi
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
       username = form.username.data
       password_entered = form.password.data

       db = mysql.get_db()

        # Cursor oluştur
       cursor = db.cursor()

       sorgu = "Select * From users where username = %s"

       result=cursor.execute(sorgu,(username,))

       if result > 0: #result 0'dan büyük ise kullanıcı var.
           data = cursor.fetchone() #Kullanıcının bütün bilgilerini ulaşabilir...
           real_pass = data[4] #Verinin üzerinde gezinerek password'u çekiyoruz...
           if sha256_crypt.verify(password_entered,real_pass): #verify() ile parolanın eşleşip eşleşmediğini kontrol ediyoruz
               flash("Giriş Başarılı! Hoşgeldiniz..","success")
               
               session["logged_in"] = True
               session["username"] = username
               return redirect(url_for("index")) 
           else:
               flash("Kullanıcı Bulunmuyor","danger")
               return redirect(url_for("login")) 
            

       else: #result 0 ise kullanıcı yok
           flash("Kullanıcı Adı Hatalı!","danger")
           return redirect(url_for("login"))        

    return render_template("login.html",form= form)

@app.route("/dashboard")
@login_required #Kullanıcı girişi kontrolü gerektiren bütün fonksiyonlardan önce bu decorator kullanılabilir
def dashboard():
    db = mysql.get_db()
    cursor = db.cursor()
    sorgu = "Select * from articles where author=%s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")




#Detay sayfası
@app.route("/article/<string:id>")
def detail(id):
    db = mysql.get_db()
    cursor = db.cursor()
    sorgu = "SELECT * FROM articles WHERE id = %s"

    result = cursor.execute(sorgu, (id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html", article=None)

# logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Makale Ekleme
@app.route("/dashboard/addarticle", methods=["GET", "POST"])
@login_required
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.get_db().cursor()

        sorgu = "INSERT INTO articles (title, author, content) VALUES (%s, %s, %s)"
        cursor.execute(sorgu, (title, session["username"], content))

        db = mysql.get_db()
        db.commit()

        cursor.close()
        flash("Makale Kaydedildi", "success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form=form)

#Makale Silme
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    db = mysql.get_db()
    cursor = db.cursor()
    sorgu="Select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))
    if result>0:
       db = mysql.get_db()
       cursor = db.cursor()
       sorgu2="Delete from articles where id=%s"
       cursor.execute(sorgu2,(id,))
       db = mysql.get_db()
       db.commit()
       
       
       return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işeleme yetkiniz yok")
        return redirect(url_for("index"))
    
#Makale Güncellme
@app.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def uptade(id):
    if request.method == "GET":
        db = mysql.get_db()
        cursor = db.cursor()
        
        sorgu="Select * from articles where  id=%s and author=%s "
        result=cursor.execute(sorgu,(id,session["username"]))
        if result==0:
            flash("Böyle bir makale yok veya bu işeleme yetkiniz yok")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article[0]  # Birinci sütun: title
            form.content.data = article[1]  # İkinci sütun: content

            return render_template("update.html",form=form)
    else:
        #PostRequest
        form=ArticleForm(request.form)
        newTitle=form.title.data
        newContent=form.content.data
        sorgu2 = "UPDATE articles SET title=%s, content=%s WHERE id=%s"
        db = mysql.get_db()
        cursor = db.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        
        db.commit()
        flash("Makale Başarıyla Güncellendi","success")
        return redirect(url_for("dashboard"))

#Arama URL
@app.route("/search",methods=["GET","POST"])
def search(): 
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")
        db = mysql.get_db()
        cursor = db.cursor()
        sorgu="Select * from articles where title like  '%" + keyword + "%' "
        result=cursor.execute(sorgu)
        if result==0:
            flash("Aranan makaleye ulaşılamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)

if __name__ == "__main__":
    app.run(debug=True)
