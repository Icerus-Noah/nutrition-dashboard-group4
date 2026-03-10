import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set the non-GUI Agg backend for matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder="storage/charts", static_url_path="/charts")

CORS(app)
# ======================
# Local storage paths
# ======================

DATASET_PATH = "storage/datasets/All_Diets.csv"
CHART_FOLDER = "storage/charts"

os.makedirs(CHART_FOLDER, exist_ok=True)

# ======================
# Load dataset
# ======================

def load_dataset():
    df = pd.read_csv(DATASET_PATH)
    numeric_cols = ['Protein(g)', 'Carbs(g)', 'Fat(g)']
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

    df['Protein_to_Carbs_ratio'] = df['Protein(g)'] / df['Carbs(g)']
    df['Carbs_to_Fat_ratio'] = df['Carbs(g)'] / df['Fat(g)']

    return df


# ======================
# Generate charts
# ======================

def generate_charts():

    df = load_dataset()

    numeric_cols = ['Protein(g)', 'Carbs(g)', 'Fat(g)']
    avg_macros = df.groupby('Diet_type')[numeric_cols].mean().reset_index()

    # BAR CHART
    plt.figure(figsize=(8,6))
    sns.barplot(x="Diet_type", y="Protein(g)", data=avg_macros)
    plt.title("Average Protein by Diet Type")
    plt.tight_layout()
    plt.savefig(f"{CHART_FOLDER}/bar.png")
    plt.close()

    # HEATMAP
    plt.figure(figsize=(8,6))
    sns.heatmap(avg_macros.set_index('Diet_type')[numeric_cols],
                annot=True,
                cmap="coolwarm")
    plt.title("Macronutrient Heatmap")
    plt.tight_layout()
    plt.savefig(f"{CHART_FOLDER}/heatmap.png")
    plt.close()

    # SCATTER
    top_protein = df.sort_values('Protein(g)', ascending=False).groupby('Diet_type').head(5)

    plt.figure(figsize=(8,6))
    sns.scatterplot(data=top_protein,
                    x='Protein(g)',
                    y='Carbs(g)',
                    hue='Cuisine_type')
    plt.title("Top Protein Recipes")
    plt.tight_layout()
    plt.savefig(f"{CHART_FOLDER}/scatter.png")
    plt.close()

    # PIE CHART
    diet_counts = df['Diet_type'].value_counts()

    plt.figure(figsize=(8,6))
    diet_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=sns.color_palette("Set3", len(diet_counts)))
    plt.title("Recipe Distribution by Diet Type")
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(f"{CHART_FOLDER}/pie.png")
    plt.close()


# ======================
# API Endpoints
# ======================

@app.route("/api/insights")
def insights():

    generate_charts()

    df = load_dataset()

    numeric_cols = ['Protein(g)', 'Carbs(g)', 'Fat(g)']
    avg_macros = df.groupby('Diet_type')[numeric_cols].mean().reset_index()

    return jsonify(avg_macros.to_dict(orient="records"))


@app.route("/api/recipes")
def recipes():

    df = load_dataset()

    top_protein = df.sort_values('Protein(g)', ascending=False).groupby('Diet_type').head(5)

    return jsonify(
        top_protein[['Diet_type','Recipe_name','Protein(g)']]
        .to_dict(orient="records")
    )


@app.route("/api/clusters")
def clusters():

    df = load_dataset()

    common_cuisine = (
        df.groupby('Diet_type')['Cuisine_type']
        .agg(lambda x: x.value_counts().idxmax())
        .reset_index()
    )

    return jsonify(common_cuisine.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True)