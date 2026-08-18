# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson

from flask import Blueprint, request, render_template_string
from database.db_handler import query_user, query_product, query_comments, add_comment, query_products
from templates import HOME_PAGE, LOGIN_FORM, FAIL_PAGE, SUCCESS_PAGE, PRODUCTS_PAGE, PRODUCT_PAGE
router = Blueprint("router", __name__)

CATEGORIES = ["peripherals", "displays", "accessories"]


@router.route("/")
def home():
    return render_template_string(HOME_PAGE)


@router.route("/login", methods=["GET"])
def login_form():
    return render_template_string(LOGIN_FORM)


@router.route("/login", methods=["POST"])
def login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not password:
        return render_template_string(FAIL_PAGE)

    user = query_user(username, password)
    if user:
        return render_template_string(SUCCESS_PAGE, username=user["username"])

    return render_template_string(FAIL_PAGE)


@router.route("/products", methods=["GET"])
def products_page():
    category = request.args.get("category", "").strip().lower()
    products = query_products(category if category else None)
    return render_template_string(PRODUCTS_PAGE, products=products, categories=CATEGORIES, selected_category=category)


@router.route("/product", methods=["GET", "POST"])
def product_page():
    if request.method == "POST":
        pid = request.form.get("id")
        username = request.form.get("username", "").strip()
        content = request.form.get("content", "").strip()
        if not pid or not username or not content:
            return "Missing fields", 400
        add_comment(pid, username, content)
        # fall through to render updated page

    pid = request.args.get("id") if request.method == "GET" else request.form.get("id")
    if not pid:
      return "Missing product id", 400

    prod = query_product(pid)
    if not prod:
      return "Product not found", 404

    comments = query_comments(pid)

    return render_template_string(PRODUCT_PAGE, product=prod, comments=comments)
