import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, jsonify, request
from flask_cors import CORS

DATASET_PATH = os.getenv("DATASET_PATH", "/app/storage/datasets/All_Diets.csv")
CHART_FOLDER = os.getenv("CHART_FOLDER", "/app/storage/charts")
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

os.makedirs(CHART_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=CHART_FOLDER, static_url_path="/charts")
CORS(app, resources={r"/api/*": {"origins": FRONTEND_URL}})


def load_dataset():
    df = pd.read_csv(DATASET_PATH)

    numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    # avoid divide-by-zero issues
    df["Protein_to_Carbs_ratio"] = df["Protein(g)"] / df["Carbs(g)"].replace(0, pd.NA)
    df["Carbs_to_Fat_ratio"] = df["Carbs(g)"] / df["Fat(g)"].replace(0, pd.NA)

    return df


def filter_dataset(df, diet_type):
    if diet_type:
        df = df[df["Diet_type"].str.lower().str.contains(diet_type.lower(), na=False)]
    return df


def generate_charts(df):
    numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
    avg_macros = df.groupby("Diet_type")[numeric_cols].mean().reset_index()

    # BAR CHART
    plt.figure(figsize=(8, 6))
    sns.barplot(x="Diet_type", y="Protein(g)", data=avg_macros)
    plt.title("Average Protein by Diet Type")
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, "bar.png"))
    plt.close()

    # HEATMAP
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

    # SCATTER
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

    # PIE CHART
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


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/insights")
def insights():
    df = load_dataset()
    diet_type = request.args.get("diet_type")
    df = filter_dataset(df, diet_type)

    generate_charts(df)

    numeric_cols = ["Protein(g)", "Carbs(g)", "Fat(g)"]
    avg_macros = df.groupby("Diet_type")[numeric_cols].mean().reset_index()

    return jsonify(avg_macros.to_dict(orient="records"))


@app.route("/api/recipes")
def recipes():
    df = load_dataset()

    diet_type = request.args.get("diet_type")
    if diet_type:
        df = df[df["Diet_type"].str.lower().str.contains(diet_type.lower(), na=False)]

    sorted_recipes = df.sort_values("Protein(g)", ascending=False)

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 5))

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
def clusters():
    df = load_dataset()
    diet_type = request.args.get("diet_type")
    df = filter_dataset(df, diet_type)

    common_cuisine = (
        df.groupby("Diet_type")["Cuisine_type"]
        .agg(lambda x: x.value_counts().idxmax())
        .reset_index()
    )

    return jsonify(common_cuisine.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)