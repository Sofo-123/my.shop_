import os
import uuid

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from ext import app, db
from models import User, Product, Cart, CartItem
from forms import ProductForm, RegisterForm, LoginForm


@app.route('/add_to_cart/<int:product_id>', methods=['GET', 'POST'])
@login_required
def add_to_cart(product_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=1)
        db.session.add(item)
    db.session.commit()
    flash("პროდუქტი დამატებულია კალათაში", "success")
    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/cart')
@login_required
def view_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        items = []
        total = 0
    else:
        items = cart.items
        total = sum(item.product.price * item.quantity for item in items)
    return render_template("cart.html", items=items, total=total)


@app.route('/remove_from_cart/<int:item_id>', methods=['GET', 'POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)

    product_id = item.product_id

    if item.cart.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash("პროდუქტი წაიშალა კალათიდან", "info")
    else:
        flash("არ გაქვთ უფლება ამ ოპერაციისთვის", "danger")

    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/increase_quantity/<int:item_id>', methods=['GET', 'POST'])
@login_required
def increase_quantity(item_id):
    item = CartItem.query.get_or_404(item_id)
    product_id = item.product_id
    if item.cart.user_id == current_user.id:
        item.quantity += 1
        db.session.commit()
        flash("რაოდენობა გაიზარდა", "success")
    else:
        flash("არ გაქვთ უფლება ამ ოპერაციისთვის", "danger")
    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/decrease_quantity/<int:item_id>', methods=['GET', 'POST'])
@login_required
def decrease_quantity(item_id):
    item = CartItem.query.get_or_404(item_id)
    product_id = item.product_id
    if item.cart.user_id == current_user.id:
        if item.quantity > 1:
            item.quantity -= 1
            db.session.commit()
            flash("რაოდენობა შემცირდა", "warning")
        else:
            db.session.delete(item)
            db.session.commit()
            flash("პროდუქტი წაიშალა კალათიდან", "info")
    else:
        flash("არ გაქვთ უფლება ამ ოპერაციისთვის", "danger")
    return redirect(url_for('product_detail', product_id=product_id))


@app.route("/allproducts")
def all_products():
    query = request.args.get("q", "").strip()

    if query:
        products = Product.query.filter(
            (Product.name.ilike(f"%{query}%")) | (Product.detail.ilike(f"%{query}%"))
        ).all()
    else:
        products = Product.query.all()

    return render_template("allproducts.html", products=products)


@app.route("/product/<int:product_id>")
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = None

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart:
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()

    return render_template("detailed_page.html", product=product, cart_item=cart_item)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("შესვლა წარმატებულია", "success")

            if user.is_admin():
                return redirect(url_for("all_products"))  # Admin გადადის ყველა პროდუქტებზე
            else:
                return redirect(url_for("home", id=user.id))  # User გადადის თავის გვერდზე
        else:
            flash("არასწორი მონაცემები", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("ეს username უკვე არსებობს.სცადე სხვა", "danger")
            return redirect(url_for("register"))

        role = "admin" if username.lower() == "admin" else "user"

        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("რეგისტრაცია წარმატებით დასრულდა", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_product(id):
    if not current_user.role == "admin":
        flash("საჭიროა ადმინისტრატორის უფლებები", "danger")
        return redirect(url_for("all_products"))
    else:
        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        flash("პროდუქტი წაიშალა", "info")
        return redirect(url_for("all_products"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    if not current_user.role == "admin":
        flash("საჭიროა ადმინისტრატორის უფლებები", "danger")
        return redirect(url_for("all_products"))
    else:
        product = Product.query.get_or_404(id)
        form = ProductForm(name=product.name, price=product.price, detail=product.detail, img=product.img)

        if form.validate_on_submit():
            product.name = form.name.data
            product.price = form.price.data
            product.detail = form.detail.data
            img_file = form.img.data

            if img_file:
                filename = str(uuid.uuid4()) + os.path.splitext(img_file.filename)[1]
                upload_folder = os.path.join("static", "uploads")
                os.makedirs(upload_folder, exist_ok=True)
                img_path = os.path.join(upload_folder, filename)
                img_file.save(img_path)
                product.img = filename

            db.session.commit()
            flash("პროდუქტი წარმატებით განახლდა", "success")
            return redirect(url_for("all_products"))

        return render_template("addproduct.html", form=form, product=product)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_product():
    if not current_user.role == "admin":
        flash("საჭიროა ადმინისტრატორის უფლებები", "danger")
        return redirect(url_for("all_products"))

    form = ProductForm()
    if form.validate_on_submit():
        img_file = form.img.data
        filename = "default.png"
        if img_file:
            filename = str(uuid.uuid4()) + os.path.splitext(img_file.filename)[1]
            upload_folder = os.path.join("static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            img_path = os.path.join(upload_folder, filename)
            img_file.save(img_path)

        product = Product(
            name=form.name.data,
            price=form.price.data,
            img=filename,
            detail=form.detail.data
        )

        db.session.add(product)
        db.session.commit()
        flash("პროდუქტი წარმატებით დაემატა!", "success")
        return redirect(url_for("add_product"))

    return render_template("addproduct.html", form=form, product=None)


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/")
def main():
    return render_template("home.html")
