import re
from datetime import datetime 
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, session
from models import db, User, Product, Category, Cart, Order, Transaction

from app import app 

def auth_required(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    if 'user_id' not in session:
      flash("Please login to continue.")
      return redirect(url_for('login'))
    return func(*args, **kwargs)
  return wrapper

def admin_required(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    
    if 'user_id' not in session:
      flash("You need to login first")
      return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
      return redirect(url_for('index'))
    return func(*args, **kwargs)
  return wrapper

@app.route('/')
@auth_required
def index():
  user = User.query.get(session['user_id'])
  if not user.is_admin:
    parameter = request.args.get('parameter')
    query = request.args.get('query')
    parameters = {
      'category': 'Category Name',
      'product': "Product Name",
      'price': "Max Price"
    }
    if not parameter or not query:
      return render_template('index.html', user=user, categories=Category.query.all(), parameters= parameters)
    
    print(parameter, query)
    if parameter == 'category':
      categories = Category.query.filter(Category.name.ilike('%' + query + '%')).all()
      return render_template('index.html', user=user, categories= categories, query=query, parameter=parameter,  parameters=parameters)
    
    if parameter == 'product':
      return render_template('index.html', user=user, categories=Category.query.all(), name=query, query=query, parameter=parameter, parameters=parameters)
    
    if parameter == 'price':

      return render_template('index.html', user=user, categories=Category.query.all(), price=float(query), query=query,parameter=parameter, parameters=parameters)

    
    return render_template('admin.html', user=user, categories=Category.query.all())
  return render_template('admin.html', user=user, categories=Category.query.all())

@app.route('/admin')
@admin_required
def admin():
  return render_template('admin.html', user = User.query.get(session['user_id']), categories = Category.query.all())

@app.route('/category/add')
@admin_required
def add_category():
  return render_template('/category/add.html', user= User.query.get(session['user_id']))

@app.route('/category/add', methods=['POST'])
@admin_required
def post_add_category():
  name = request.form.get('name')
  if name.strip() == '':
    flash("Name cannot be empty")
    return redirect(url_for('add_category'))
  
  if len(name) > 30:
    flash("Category name cannot be greater than 30 characters")
    return redirect(url_for('add_category'))
  
  category = Category(name = name)
  db.session.add(category)
  db.session.commit()
  flash("Category successfully Added")
  return redirect(url_for('admin'))
    

@app.route('/category/<int:id>/delete')
@admin_required
def delete_category(id):
  category = Category.query.get(id)
  if not category:
    flash("Category doesn't exist")
    return redirect(url_for('admin'))
  return render_template('/category/delete.html', category =category , user= User.query.get(session['user_id']))

@app.route('/category/<int:id>/delete', methods=['POST'])
@admin_required
def post_delete_category(id):
  category = Category.query.get(id)
  if not category:
    flash("Category does not exist")
    return redirect(url_for('admin'))
  db.session.delete(category)
  db.session.commit()
  flash("Category Deleted Successfully")
  return redirect(url_for('admin'))


@app.route('/category/<int:id>/edit')
@admin_required
def edit_category(id):
  return render_template('/category/edit.html', category = Category.query.get(id))

@app.route('/category/<int:id>/edit', methods=['POST'])
@admin_required
def post_edit_category(id):
  category = Category.query.get(id)
  name = request.form.get('name')
  if name.strip() == '':
    flash("Category name cannot be empty")
    return redirect(url_for('edit_category', id= id ))
  if len(name) > 30:
    flash("Category name cannot be more than 30 characters")
    return redirect(url_for('edit_category', id=id))
  
  category.name = name
  db.session.commit()
  flash("Category updated successfully")
  return redirect(url_for('admin'))
 
  


@app.route('/category/<int:id>/products/show')
@admin_required
def show_category(id):
  return render_template('/category/show.html', user= User.query.get(session['user_id']), category=Category.query.get(id), products= Product.query.all())

@app.route('/product/add')
@admin_required
def add_product():
  args = request.args 
  if 'category_id' in args:
    category_id = int(args.get('category_id'))
    if Category.query.get(category_id):
      return render_template('/product/add.html', 
                         user=User.query.get(session['user_id']), 
                         category_id=category_id, 
                         categories=Category.query.all(),
                         now=datetime.now().strftime("%Y-%m-%d")
                         )
  flash("Please select a valid category.")
  return redirect(url_for('add_product'))

@app.route('/product/add', methods=['POST'])
@admin_required
def post_add_product():
  name = request.form.get('name')
  price = request.form.get('price')
  quantity = request.form.get('quantity')
  category_id = request.form.get('category')
  man_date = request.form.get('manufacture_date')
  category = Category.query.get(category_id)

  if name.strip() == '':
    flash("Name cannot be empty")
    return redirect(url_for('add_product'))
  if len(name) > 30:
    flash("Product name cannot be greater than 30 characters.")
    return redirect(url_for("add_product"))
  
  if quantity == '':
    flash("Quantity cannot be empty")
    return redirect(url_for("add_product"))
  
  if not quantity.isdigit():
    flash("Quantity must be a number.")
    return redirect(url_for('add_product')) 
  quantity = int(quantity)

  if price == '':
    flash("Price cannot be empty")
    return redirect(url_for('add_product'))

  if not re.match(r'^\d+(\.\d*)?$' , price):
    flash("Price must be a number.")
    return redirect(url_for("add_product"))
  price = float(price)
  
  if category == '':
    flash('Category cannot be empty')
    return redirect(url_for("add_product"))

  if not category:
    flash("Category does not exist.")
    return redirect(url_for("add_product"))
  if man_date == '':
    flash("Manufacture date cannot be empty.")
    return redirect(url_for('add_product'))
  try:
    man_date = datetime.strptime(man_date, '%Y-%m-%d')
  except ValueError as e:
    flash("Invalid manufacture date.")
    return redirect(url_for('add_product'))
  
  product = Product(name=name, quantity=quantity, price=price, category=category, man_date=man_date)
  db.session.add(product)
  db.session.commit()
  flash('Product added successfully')
  return redirect(url_for('show_category', id=category_id))
  
@app.route('/product/<int:id>/edit')
@admin_required
def edit_product(id):
  product = Product.query.get(id)
  if not product:
    flash("Product does not exist")
    return redirect(url_for('admin'))
  return render_template('/product/edit.html', user=User.query.get(session['user_id']), categories=Category.query.all(),product=product, now=datetime.now().strftime("%Y-%m-%d"))

@app.route('/product/<int:id>/edit', methods=['POST'])
@admin_required
def post_edit_product(id):
  product = Product.query.get(id)
  
  if not product:
    flash("Product does not exist..")
    return redirect(url_for('admin'))
  
  name = request.form.get('name')
  price = request.form.get('price')
  quantity = request.form.get('quantity')
  category_id = request.form.get('category')
  man_date = request.form.get('manufacture_date')
  category = Category.query.get(category_id)

  if name.strip() == '':
    flash("Name cannot be empty")
    return redirect(url_for('add_product'))
  if len(name) > 30:
    flash("Product name cannot be greater than 30 characters.")
    return redirect(url_for("add_product"))
  
  if quantity == '':
    flash("Quantity cannot be empty")
    return redirect(url_for("add_product"))
  
  if not quantity.isdigit():
    flash("Quantity must be a number.")
    return redirect(url_for('add_product')) 
  quantity = int(quantity)

  if price == '':
    flash("Price cannot be empty")
    return redirect(url_for('add_product'))

  if not re.match(r'^\d+(\.\d*)?$' , price):
    flash("Price must be a number.")
    return redirect(url_for("add_product"))
  price = float(price)
  
  if category == '':
    flash('Category cannot be empty')
    return redirect(url_for("add_product"))

  if not category:
    flash("Category does not exist.")
    return redirect(url_for("add_product"))
  if man_date == '':
    flash("Manufacture date cannot be empty.")
    return redirect(url_for('add_product'))
  try:
    man_date = datetime.strptime(man_date, '%Y-%m-%d')
  except ValueError as e:
    flash("Invalid manufacture date.")
    return redirect(url_for('add_product'))
  
  product.name = name
  product.quantity = quantity 
  product.price = price 
  product.category_id = category_id
  product.man_date = man_date 
  db.session.commit()
  flash("Product updated Successfully")
  return redirect(url_for('show_category',id=category_id))
  
  
@app.route('/product/<int:id>/delete')
@admin_required
def delete_product(id):
  product = Product.query.get(id)
  if not product:
    flash("Product does not exist.")
    return redirect(url_for('admin')) 
  return render_template('/product/delete.html', user=User.query.get(session['user_id']),  product=product)

@app.route('/product/<int:id>/delete', methods=['POST'])
@admin_required
def post_delete_product(id):
  product = Product.query.get(id)
  if not product:
    flash("Product does not exist.")
    return redirect(url_for('admin'))
  db.session.delete(product)
  db.session.commit()
  flash("Product deleted successfully.")
  return redirect(url_for('admin'))
    


@app.route('/register')
def register():
  # if 'user_id' not in session:
  #   return render_template('index.html', user= User.query.get(session['user_id']))
  return render_template('register.html')

@app.route('/login')
def login():
  # if 'user_id' in session:
  #   return render_template('index.html', user= User.query.get(session['user_id']))
  return render_template('login.html')

@app.route('/login', methods = ['POST'])
def post_login():
  username = request.form.get("username")
  password = request.form.get("password")
  if username == '' or password == '':
    flash("Username or password cannot be empty")
    return redirect(url_for('register'))
  
  user = User.query.filter_by(username=username).first()
  if not user:
    flash("User doesn't exist")
    return redirect(url_for('login'))
  
  if not user.check_password(password):
    flash("Incorrect password")
    return redirect(url_for('login'))
  
  #login successful
  session['user_id'] = user.id 
  return redirect(url_for('index'))
   
@app.route('/register', methods = ['POST'])
def post_register():
  username = request.form.get('username')
  password = request.form.get('password')
  name = request.form.get('name')
  
  if username.strip() == '' or password.strip() == '':
    flash("Username or password cannot be empty")
    return redirect(url_for('register'))

  if User.query.filter_by(username = username).first():
    flash("User with this username already exists. Please choose some other username.")
    return redirect(url_for('register'))
  
  user = User(username=username, password=password, name=name)
  
  db.session.add(user)
  db.session.commit()
  
  flash("User successfully registered")
  return redirect(url_for("login"))
  
  
@app.route('/profile')
@auth_required
def profile():
  return render_template('profile.html', user=User.query.get(session['user_id']))

@app.route('/profile', methods=['POST'])  
@auth_required
def post_profile():
  user = User.query.get(session['user_id'])
  name = request.form.get('name')
  username = request.form.get('username')
  password = request.form.get('password')
  cpassword = request.form.get('cpassword')
  
  if User.query.filter_by(username=username).first() and username != user.username:
    flash("Username already exists, Please choose some other username.")
    return redirect(url_for('profile'))
    
  if username.strip() == '' or cpassword.strip() == '':
    flash("Username or password cannot be empty")
    return redirect(url_for('profile'))
  
  if not user.check_password(cpassword):
    flash("Incorrect Password")
    return redirect(url_for('profile'))  

  user.username = username 
  
  if name:
    user.name = name 
  
  if password:
    user.password = password
  
  db.session.commit()
  flash("Profile Updated Successfully")
  return redirect(url_for('profile'))


@app.route('/cart')
@auth_required
def cart():
  carts = Cart.query.filter_by(user_id=session['user_id']).all()
  total = sum([cart.product.price * cart.quantity for cart in carts]) 
  return render_template('cart.html', user=User.query.get(session['user_id']), carts=carts, total=total)

@app.route('/cart/<int:product_id>/delete', methods=['POST'])
@auth_required
def delete_from_cart(product_id):
  cart = Cart.query.filter_by(user_id=session['user_id']).filter_by(product_id=product_id).first()
  if not cart:
    flash('Product does not exist in cart.')
    return redirect(url_for('cart'))
  db.session.delete(cart)
  db.session.commit()
  flash('Product deleted from cart successfully.')
  return redirect(url_for('cart'))

@app.route('/cart/<int:product_id>/add', methods=['POST'])
@auth_required
def add_to_cart(product_id):
  quantity = request.form.get('quantity')
  if not quantity or quantity == '':
    flash('Quantity cannot be empty')
    return redirect(url_for('index'))
  if quantity.isdigit() == False:
    flash('Quantity must be a number')
    return redirect(url_for('index'))
  quantity = int(quantity)
  if (quantity) <= 0:
    flash('Quantity must be greater than 0.')
    return redirect(url_for('index'))
  product = Product.query.get(product_id)
  
  if not product:
    flash('Product does not exist')
    return redirect(url_for('index'))
  if product.quantity < quantity:
    flash('Quantity must be less than or equal to ' + str(product.quantity) + '.')
    return redirect(url_for('index'))
  
  cart = Cart.query.filter_by(user_id = session['user_id']).filter_by(product_id=product.id).first()
  if cart:
    if cart.quantity + quantity > product.quantity:
      flash('Quantity msut be less than or equal to ' + str(product.quantity - cart.quantity) + '.')
      return redirect(url_for('index'))
    cart.quantity += quantity
    db.session.commit()
    flash('Product added to cart successfully')
    return redirect(url_for('index'))
  cart = Cart(user_id = session['user_id'], product_id = product_id, quantity=quantity)
  db.session.add(cart)
  db.session.commit()
  flash('Product added to cart successfully')
  return redirect(url_for('index'))
  
@app.route("/orders")
@auth_required
def orders():
  user = User.query.get(session['user_id'])
  transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.datetime.desc()).all()
  
  return render_template('orders.html', user=user, transactions=transactions)
  
@app.route('/cart/place_order', methods=['POST'])
@auth_required
def place_order():
  items = Cart.query.filter_by(user_id=session['user_id']).all()
  if not items:
    flash('Cart is empty.')
    return redirect(url_for('cart'))
  for item in items:
    if item.quantity > item.product.quantity:
      flash('Quantity of ' + item.product.name + 'must be less than or equal to' + str(item.product.quantity) + '.')
      return redirect(url_for('cart'))
  transaction = Transaction(user_id=session['user_id'], total = 0)
  for item in items:
    item.product.quantity -= item.quantity 
    order = Order(transaction=transaction, product_id = item.product_id, quantity=item.quantity, price=item.product.price)
    db.session.add(order)
    transaction.total += order.price * order.quantity
    db.session.delete(item)
    db.session.commit()
  flash('Order placed successfully.')
  return redirect(url_for('orders')) 
  
@app.route('/logout')
def logout():
  session.pop('user_id', None)
  return redirect(url_for('login'))