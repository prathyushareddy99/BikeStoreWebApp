# -------------------------
# BikeStore Web App - Main Application File
# Added comments for readability and code organization
# -------------------------


from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
import bcrypt

from database import engine, get_user
from middleware import add_session
from auth import login_user, logout_user, require_login

app = FastAPI()
add_session(app)

templates = Jinja2Templates(directory="templates")


# ------------------------------
# LOGIN PAGE
# ------------------------------
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = get_user(email)

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })

    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })

    login_user(request, user["user_id"], user["email"])
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/", status_code=302)


# ------------------------------
# DASHBOARD (Protected)
# ------------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not require_login(request):
        return RedirectResponse("/", status_code=302)

    with engine.connect() as conn:

        total_customers = conn.execute(
            text("SELECT COUNT(*) FROM sales.customers")
        ).scalar()

        total_orders = conn.execute(
            text("SELECT COUNT(*) FROM sales.orders")
        ).scalar()

        total_products = conn.execute(
            text("SELECT COUNT(*) FROM production.products")
        ).scalar()

        total_stores = conn.execute(
            text("SELECT COUNT(*) FROM sales.stores")
        ).scalar()

        rows = conn.execute(text("""
            SELECT TOP 5 s.store_name, COUNT(o.order_id) AS total_orders
            FROM sales.orders o
            JOIN sales.stores s ON o.store_id = s.store_id
            GROUP BY s.store_name
            ORDER BY total_orders DESC
        """)).mappings().all()

    mini_labels = ["Customers", "Orders", "Products", "Stores"]
    mini_values = [total_customers, total_orders, total_products, total_stores]

    chart_labels = [r["store_name"] for r in rows]
    chart_values = [r["total_orders"] for r in rows]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "mini_labels": mini_labels,
        "mini_values": mini_values,
        "chart_labels": chart_labels,
        "chart_values": chart_values
    })


# ------------------------------
# CUSTOMERS LIST
# ------------------------------
@app.get("/customers", response_class=HTMLResponse)
def customers(request: Request, page: int = 1, search: str = ""):
    if not require_login(request):
        return RedirectResponse("/", status_code=302)

    page_size = 20
    offset = (page - 1) * page_size

    query = """
        SELECT customer_id, first_name, last_name, email, city
        FROM sales.customers
        WHERE first_name LIKE :search OR last_name LIKE :search OR email LIKE :search
        ORDER BY customer_id DESC
        OFFSET :offset ROWS FETCH NEXT :size ROWS ONLY
    """

    with engine.connect() as conn:
        rows = conn.execute(
            text(query),
            {"search": f"%{search}%", "offset": offset, "size": page_size}
        ).mappings().all()

    return templates.TemplateResponse("customers.html", {
        "request": request,
        "customers": rows,
        "page": page,
        "search": search
    })


# ------------------------------
# ADD CUSTOMER FORM
# ------------------------------
@app.get("/customers/add", response_class=HTMLResponse)
def add_form(request: Request):
    if not require_login(request):
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse("customer_add.html", {"request": request})


# ------------------------------
# ADD CUSTOMER (VALIDATED)
# ------------------------------
@app.post("/customers/add", response_class=HTMLResponse)
def add_customer(request: Request,
                 first_name: str = Form(""),
                 last_name: str = Form(""),
                 email: str = Form(""),
                 city: str = Form("")):

    errors = []
    if not first_name.strip():
        errors.append("First Name is required.")
    if not last_name.strip():
        errors.append("Last Name is required.")
    if not email.strip():
        errors.append("Email is required.")
    if not city.strip():
        errors.append("City is required.")

    if errors:
        return templates.TemplateResponse("customer_add.html", {
            "request": request,
            "errors": errors,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "city": city
        })

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO sales.customers (first_name, last_name, email, city)
            VALUES (:fn, :ln, :email, :city)
        """), {"fn": first_name, "ln": last_name, "email": email, "city": city})
        conn.commit()

    return RedirectResponse("/customers", status_code=302)


# ------------------------------
# EDIT CUSTOMER
# ------------------------------
@app.get("/customers/edit/{cid}", response_class=HTMLResponse)
def edit_customer(request: Request, cid: int):
    if not require_login(request):
        return RedirectResponse("/", status_code=302)

    with engine.connect() as conn:
        cust = conn.execute(
            text("SELECT * FROM sales.customers WHERE customer_id = :id"),
            {"id": cid}
        ).mappings().first()

    return templates.TemplateResponse("customer_edit.html", {
        "request": request,
        "cust": cust
    })


# ------------------------------
# SAVE EDIT (VALIDATED)
# ------------------------------
@app.post("/customers/edit/{cid}", response_class=HTMLResponse)
def save_edit(request: Request, cid: int,
              first_name: str = Form(""),
              last_name: str = Form(""),
              email: str = Form(""),
              city: str = Form("")):

    errors = []
    if not first_name.strip():
        errors.append("First Name is required.")
    if not last_name.strip():
        errors.append("Last Name is required.")
    if not email.strip():
        errors.append("Email is required.")
    if not city.strip():
        errors.append("City is required.")

    if errors:
        cust = {
            "customer_id": cid,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "city": city
        }

        return templates.TemplateResponse("customer_edit.html", {
            "request": request,
            "cust": cust,
            "errors": errors
        })

    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE sales.customers
            SET first_name=:fn, last_name=:ln, email=:email, city=:city
            WHERE customer_id=:id
        """), {"fn": first_name, "ln": last_name, "email": email, "city": city, "id": cid})
        conn.commit()

    return RedirectResponse("/customers", status_code=302)


# ------------------------------
# DELETE CUSTOMER
# ------------------------------
@app.get("/customers/delete/{cid}")
def delete_customer(cid: int):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM sales.customers WHERE customer_id=:id"), {"id": cid})
        conn.commit()

    return RedirectResponse("/customers", status_code=302)


# ------------------------------
# ANALYTICS (Customers by City)
# ------------------------------
@app.get("/analytics", response_class=HTMLResponse)
def analytics(request: Request, limit: int = 5):
    if not require_login(request):
        return RedirectResponse("/", status_code=302)

    top_clause = "" if limit == 0 else f"TOP {limit}"

    query = f"""
        SELECT {top_clause} city, COUNT(*) AS total_customers
        FROM sales.customers
        GROUP BY city
        ORDER BY total_customers DESC
    """

    with engine.connect() as conn:
        rows = conn.execute(text(query)).mappings().all()

    labels = [row["city"] for row in rows]
    values = [row["total_customers"] for row in rows]

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "labels": labels,
            "values": values,
            "limit": limit
        }
    )
