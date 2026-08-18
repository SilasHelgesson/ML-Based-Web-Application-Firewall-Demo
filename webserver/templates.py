# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson

BASE_STYLE = """
<style>
  :root {
    color: #111;
    background: #f6f7f9;
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    line-height: 1.6;
  }

  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: radial-gradient(circle at top, #ffffff 0%, #f2f4f8 45%, #e8ebf1 100%);
  }

  main {
    width: min(96vw, 860px);
    margin: auto;
    background: #ffffff;
    border-radius: 24px;
    box-shadow: 0 24px 80px rgba(15, 23, 42, 0.08);
    padding: 2rem;
  }

  h1 {
    margin: 0 0 1rem;
    font-size: clamp(1.8rem, 2.2vw, 2.6rem);
    letter-spacing: -0.03em;
  }

  h2 {
    margin: 0.8rem 0 0.8rem;
    font-size: 1.1rem;
  }

  p,
  label,
  small,
  a,
  button,
  select,
  input,
  textarea {
    color: #334155;
  }

  img {
    max-width: 100%;
    height: auto;
    display: block;
  }

  p {
    margin: 0;
  }

  .page-copy {
    margin-bottom: 1.5rem;
    max-width: 44rem;
  }

  .controls,
  nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
    margin-top: 1.2rem;
  }

  a,
  button {
    border-radius: 999px;
    border: 1px solid transparent;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.18s ease;
  }

  button,
  select,
  input,
  textarea {
    font: inherit;
  }

  a.button,
  button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.95rem 1.25rem;
    background: #111827;
    color: white;
  }

  a.secondary {
    background: transparent;
    color: #111827;
    border-color: #d1d5db;
  }

  a.button:hover,
  button:hover {
    background: #1f2937;
  }

  a.secondary:hover {
    background: #f8fafc;
  }

  form {
    display: grid;
    gap: 1rem;
  }

  label {
    display: grid;
    gap: 0.5rem;
    font-size: 0.98rem;
  }

  input,
  textarea,
  select {
    width: 100%;
    border: 1px solid #d1d5db;
    border-radius: 16px;
    padding: 0.95rem 1rem;
    background: #f8fafc;
  }

  textarea {
    min-height: 120px;
    resize: vertical;
  }

  fieldset {
    border: none;
    padding: 0;
    margin: 0;
  }

  .product-grid {
    list-style: none;
    padding: 0;
    margin: 1.5rem 0 0;
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .product-card {
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    overflow: hidden;
    background: #f8fafc;
    display: grid;
    gap: 0.85rem;
    padding: 1rem;
  }

  .product-card img {
    width: 100%;
    max-height: 220px;
    object-fit: cover;
    border-radius: 16px;
  }

  .product-card h2 {
    margin: 0;
    font-size: 1.05rem;
  }

  .meta {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    font-size: 0.95rem;
    color: #64748b;
  }

  .comment-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 0.75rem;
  }

  .comment-item {
    padding: 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    background: #ffffff;
  }

  .comment-meta {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    color: #475569;
    font-size: 0.92rem;
  }

  .footer-links {
    margin-top: 2rem;
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  small {
    color: #64748b;
  }
</style>
"""

HOME_PAGE = BASE_STYLE + """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Volt-Electronics</title>
  </head>
  <body>
    <main>
      <h1>Volt-Electronics</h1>
      <p class="page-copy">This is a demonstration of a website vulnerable to sql injections.</p>
      <div class="controls">
        <a class="button" href="/login">Login</a>
        <a class="button" href="/products">Browse Products</a>
      </div>
      <div class="footer-links">
        <small>Please do not hack this !!!.</small>
      </div>
    </main>
  </body>
</html>
"""

PRODUCTS_PAGE = BASE_STYLE + """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Product Catalog</title>
  </head>
  <body>
    <main>
      <h1>Product Catalog</h1>
      <p class="page-copy">Browse product entries with a simple category filter and clean card layout.</p>
      <form method="get" action="/products" class="controls">
        <label for="category">
          Filter by category
          <select name="category" id="category" onchange="this.form.submit()">
            <option value="">All categories</option>
            {% for cat in categories %}
              <option value="{{ cat }}" {% if cat == selected_category %}selected{% endif %}>{{ cat }}</option>
            {% endfor %}
          </select>
        </label>
        <noscript><button type="submit">Apply</button></noscript>
      </form>
      <ul class="product-grid">
      {% for p in products %}
        <li class="product-card">
          <img src="{{ p['img_address'] }}" alt="{{ p['name'] }}" />
          <div>
            <h2><a class="button secondary" href="/product?id={{ p['id'] }}">{{ p['name'] }}</a></h2>
            <div class="meta"><span>{{ p['category'] }}</span><span>${{ p['price'] }}</span></div>
          </div>
        </li>
      {% else %}
        <li class="product-card">
          <p>No products found for this category.</p>
        </li>
      {% endfor %}
      </ul>
      <div class="footer-links">
        <a class="button secondary" href="/">Home</a>
      </div>
    </main>
  </body>
</html>
"""

LOGIN_FORM = BASE_STYLE + """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Login</title>
  </head>
  <body>
    <main>
      <h1>Login</h1>
      <p class="page-copy">Enter your credentials to access the demo login flow.</p>
      <form method="post" action="/login">
        <label>Username <input type="text" name="username" autocomplete="username" /></label>
        <label>Password <input type="text" name="password" autocomplete="current-password" /></label>
        <button type="submit">Sign In</button>
      </form>
      <div class="footer-links">
        <a class="button secondary" href="/">Back to Home</a>
      </div>
    </main>
  </body>
</html>
"""

SUCCESS_PAGE = BASE_STYLE + """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Login Success</title>
  </head>
  <body>
    <main>
      <h1>Success</h1>
      <p class="page-copy">Logged in successfully as <strong>{{ username }}</strong>. Here could be some confidential information ... better not try to break in ):<.</p>
      <div class="controls">
        <a class="button" href="/login">Back to Login</a>
        <a class="button secondary" href="/products">Browse Products</a>
      </div>
    </main>
  </body>
</html>
"""

FAIL_PAGE = BASE_STYLE + """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Login Failed</title>
  </head>
  <body>
    <main>
      <h1>Login Failed</h1>
      <p class="page-copy">Invalid username or password. Please try again with valid credentials.</p>
      <div class="controls">
        <a class="button" href="/login">Try Again</a>
        <a class="button secondary" href="/">Home</a>
      </div>
    </main>
  </body>
</html>
"""

PRODUCT_PAGE = BASE_STYLE + """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Product</title>
  </head>
  <body>
    <main>
      <h1>{{ product['name'] }}</h1>
      <div class="meta"><span>{{ product['category'] }}</span><span>${{ product['price'] }}</span></div>
      <img src="{{ product['img_address'] }}" alt="Product Image" />
      <p class="page-copy">Product details and community comments are shown here. Submit a review to add feedback.</p>
      <form method="post" action="/product">
        <input type="hidden" name="id" value="{{ product['id'] }}" />
        <label>Name <input type="text" name="username" /></label>
        <label>Comment <textarea name="content"></textarea></label>
        <button type="submit">Add Comment</button>
      </form>
      <section>
        <h2>Comments</h2>
        <ul class="comment-list">
        {% for c in comments %}
          <li class="comment-item">
            <div class="comment-meta">
              <strong>{{ c['username'] }}</strong>
              <span>{{ c['created_at'] |safe}}</span>
            </div>
            <p>{{ c['content'] }}</p>
          </li>
        {% else %}
          <li class="comment-item">
            <p>No comments yet.</p>
          </li>
        {% endfor %}
        </ul>
      </section>
      <div class="footer-links">
        <a class="button secondary" href="/products">Back to Catalog</a>
        <a class="button secondary" href="/">Home</a>
      </div>
    </main>
  </body>
</html>
"""
