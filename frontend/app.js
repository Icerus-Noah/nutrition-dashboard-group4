// app.js

// Define your API base URL
const API_BASE = "http://127.0.0.1:5000";

// Functions to interact with your API for insights, recipes, and clusters
async function getInsights(dietType = '') {
    console.log("Running getInsights with filter:", dietType);

    let url = `${API_BASE}/api/insights`;
    if (dietType) {
        url += `?diet_type=${dietType}`;
    }

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to fetch insights");
        const data = await res.json();

        const tableBody = document.getElementById("insightsTableBody");
        tableBody.innerHTML = ""; // clear previous data

        data.forEach(insight => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td class="p-2">${insight.Diet_type}</td>
                <td class="p-2">${insight['Protein(g)'].toFixed(2)}</td>
                <td class="p-2">${insight['Carbs(g)'].toFixed(2)}</td>
                <td class="p-2">${insight['Fat(g)'].toFixed(2)}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (err) {
        console.error(err);
    }
}

async function getRecipes() {
    const res = await fetch(`${API_BASE}/api/recipes`);
    const data = await res.json();
    
    const tableBody = document.getElementById("recipesTableBody");
    tableBody.innerHTML = "";  // Clear previous data

    // Populate the table with recipe data
    data.forEach(recipe => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td class="p-2">${recipe.Diet_type}</td>
            <td class="p-2">${recipe.Recipe_name}</td>
            <td class="p-2">${recipe['Protein(g)']}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Function to fetch and display Clusters data
async function getClusters() {
    const res = await fetch(`${API_BASE}/api/clusters`);
    const data = await res.json();
    
    const tableBody = document.getElementById("clustersTableBody");
    tableBody.innerHTML = "";  // Clear previous data

    // Populate the table with clusters data
    data.forEach(cluster => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td class="p-2">${cluster.Diet_type}</td>
            <td class="p-2">${cluster.Cuisine_type}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Setup event listeners for the buttons
document.getElementById("insightsBtn").addEventListener("click", getInsights);
document.getElementById("recipesBtn").addEventListener("click", getRecipes);
document.getElementById("clustersBtn").addEventListener("click", getClusters);

// On input field change
dietInput.addEventListener("input", () => {
    const filter = dietInput.value.trim();
    getInsights(filter);
});

// On dropdown change
dietSelect.addEventListener("change", () => {
    const filter = dietSelect.value;
    getInsights(filter);
});