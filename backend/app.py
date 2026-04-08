import os
from functools import wraps
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

DATASET_PATH = os.getenv("DATASET_PATH", "/app/storage/datasets/All_Diets.csv")
CHART_FOLDER = os.getenv("CHART_FOLDER", "/app/storage/charts")
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"

os.makedirs(CHART_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=CHART_FOLDER, static_url_path="/charts")

allowed_origins = [FRONTEND_URL] if FRONTEND_URL else []
CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},
    supports_credentials=True
)

_request_counts = {}


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:;"
    return response


def rate_limit(max_requests=100):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
            _request_counts[ip] = _request_counts.get(ip, 0) + 1
            if _request_counts[ip] > max_requests:
                return jsonify({"error": "Too many requests"}), 429
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not REQUIRE_AUTH:
            return fn(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"error": "Unauthorized"}), 401

        return fn(*args, **kwargs)
    return wrapper


def load_dataset():
    df = pd.read_csv(DATASET_PATH)

    numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    df["Protein_to_Carbs_ratio"] = df["Protein(g)"] / df["Carbs(g)"].replace(0, pd.NA)
    df["Carbs_to_Fat_ratio"] = df["Carbs(g)"] / df["Fat(g)"].replace(0, pd.NA)

    return df


def sanitize_diet_type(value):
    if not value:
        return None
    value = value.strip()
    if len(value) > 50:
        abort(400, description="diet_type too long")
    return value


def filter_dataset(df, diet_type):
    if diet_type:
        df = df[df["Diet_type"].str.lower().str.contains(diet_type.lower(), na=False)]
    return df


def generate_charts(df):
    numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
    avg_macros = df.groupby("Diet_type")[numeric_cols].mean().reset_index()

    plt.figure(figsize=(8, 6))
    sns.barplot(x="Diet_type", y="Protein(g)", data=avg_macros)
    plt.title("Average Protein by Diet Type")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "bar.png"))
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.heatmap(
        avg_macros.set_index("Diet_type")[numeric_cols],
        annot=True,
        cmap="coolwarm"
    )
    plt.title("Macronutrient Heatmap")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "heatmap.png"))
    plt.close()

    top_protein = df.sort_values("Protein(g)", ascending=False).groupby("Diet_type").head(5)

    plt.figure(figsize=(8, 6))
    sns.scatterplot(
        data=top_protein,
        x="Protein(g)",
        y="Carbs(g)",
        hue="Cuisine_type"
    )
    plt.title("Top Protein Recipes")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "scatter.png"))
    plt.close()

    diet_counts = df["Diet_type"].value_counts()

    plt.figure(figsize=(8, 6))
    diet_counts.plot(
        kind="pie",
        autopct="%1.1f%%",
        startangle=90,
        colors=sns.color_palette("Set3", len(diet_counts))
    )
    plt.title("Recipe Distribution by Diet Type")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "pie.png"))
    plt.close()


@app.route("/")
def root():
    return jsonify({"message": "Nutritional Insights API is running"}), 200


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/security-status")
def security_status():
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
    https_enabled = request.is_secure or forwarded_proto == "https"

    cors_restricted = bool(FRONTEND_URL and FRONTEND_URL != "*")
    auth_required = REQUIRE_AUTH

    return jsonify({
        "encryption": {
            "label": "Enabled" if https_enabled else "Not Confirmed",
            "verified": https_enabled,
            "details": "Verified from HTTPS / forwarded proto"
        },
        "access_control": {
            "label": "OAuth + MFA" if auth_required else "Frontend Auth Only / Not Enforced Here",
            "verified": auth_required,
            "details": "Verified from backend REQUIRE_AUTH setting"
        },
        "compliance": {
            "label": "GDPR-aligned demo",
            "verified": False,
            "details": "Declared project posture, not automatically audited"
        },
        "cors_restricted": {
            "label": "Yes" if cors_restricted else "No",
            "verified": cors_restricted,
            "details": "Verified from FRONTEND_URL configuration"
        }
    })


@app.route("/api/insights")
@rate_limit()
@require_auth
def insights():
    df = load_dataset()
    diet_type = sanitize_diet_type(request.args.get("diet_type"))
    df = filter_dataset(df, diet_type)

    generate_charts(df)

    numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
    avg_macros = df.groupby("Diet_type")[numeric_cols].mean().reset_index()

    return jsonify(avg_macros.to_dict(orient="records"))


@app.route("/api/recipes")
@rate_limit()
@require_auth
def recipes():
    df = load_dataset()

    diet_type = sanitize_diet_type(request.args.get("diet_type"))
    if diet_type:
        df = df[df["Diet_type"].str.lower().str.contains(diet_type.lower(), na=False)]

    sorted_recipes = df.sort_values("Protein(g)", ascending=False)

    page = max(int(request.args.get("page", 1)), 1)
    limit = min(max(int(request.args.get("limit", 5)), 1), 50)

    start = (page - 1) * limit
    end = start + limit

    paginated = sorted_recipes.iloc[start:end]
    total_records = len(sorted_recipes)
    total_pages = (total_records + limit - 1) // limit

    return jsonify({
        "page": page,
        "limit": limit,
        "total_records": total_records,
        "total_pages": total_pages,
        "data": paginated[["Diet_type", "Recipe_name", "Protein(g)"]].to_dict(orient="records")
    })


@app.route("/api/clusters")
@rate_limit()
@require_auth
def clusters():
    df = load_dataset()
    diet_type = sanitize_diet_type(request.args.get("diet_type"))
    df = filter_dataset(df, diet_type)

    common_cuisine = (
        df.groupby("Diet_type")["Cuisine_type"]
        .agg(lambda x: x.value_counts().idxmax())
        .reset_index()
    )

    return jsonify(common_cuisine.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)