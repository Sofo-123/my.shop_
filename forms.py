from flask_wtf import FlaskForm
from wtforms import FileField, PasswordField, FloatField, SubmitField, StringField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange

class ProductForm(FlaskForm):
    img = FileField("Upload the product image:", default="static/image.png")
    name = StringField("Product name", validators=[DataRequired()])
    price = FloatField("Product price", validators=[DataRequired()])
    detail = StringField("About product", validators=[DataRequired()])
    submit = SubmitField("Create product")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")

class RegisterForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()])
    password = PasswordField("Create password", validators=[DataRequired(), Length(min=4, max=64)])
    repeat_password = PasswordField("Repeat password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Registration")

class CartItemQuantityForm(FlaskForm):
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)], default=1)
    submit = SubmitField("Update Quantity")


