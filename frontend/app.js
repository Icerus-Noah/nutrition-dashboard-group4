const API_BASE = "https://nutrition-backend.salmonsky-a7f44c9d.canadacentral.azurecontainerapps.io";

const dietInput = document.getElementById("dietInput");
const dietSelect = document.getElementById("dietSelect");

let currentRecipePage = 1;
const recipePageSize = 5;
let totalRecipePages = 1;

function getActiveDietFilter() {
    const textFilter = dietInput ? dietInput.value.trim() : "";
    const dropdownFilter = dietSelect ? dietSelect.value.trim() : "";
    return textFilter || dropdownFilter;
}

async function getInsights(dietType = "") {
    let url = `${API_BASE}/api/insights`;
    if (dietType) {
        url += `?diet_type=${encodeURIComponent(dietType)}`;
    }

    try {
        const res = await fetch(url, { credentials: "include" });
        if (!res.ok) throw new Error("Failed to fetch insights");
        const data = await res.json();

        const tableBody = document.getElementById("insightsTableBody");
        tableBody.innerHTML = "";

        data.forEach(insight => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td class="p-2">${insight.Diet_type}</td>
                <td class="p-2">${Number(insight["Protein(g)"]).toFixed(2)}</td>
                <td class="p-2">${Number(insight["Carbs(g)"]).toFixed(2)}</td>
                <td class="p-2">${Number(insight["Fat(g)"]).toFixed(2)}</td>
            `;
            tableBody.appendChild(row);
        });

        document.getElementById("barChart").src = `${API_BASE}/charts/bar.png?t=${Date.now()}`;
        document.getElementById("scatterPlot").src = `${API_BASE}/charts/scatter.png?t=${Date.now()}`;
        document.getElementById("heatmap").src = `${API_BASE}/charts/heatmap.png?t=${Date.now()}`;
        document.getElementById("pieChart").src = `${API_BASE}/charts/pie.png?t=${Date.now()}`;
    } catch (err) {
        console.error("Insights error:", err);
    }
}

async function getRecipes(page = 1, dietType = "") {
    if (page < 1) page = 1;

    let url = `${API_BASE}/api/recipes?page=${page}&limit=${recipePageSize}`;
    if (dietType) {
        url += `&diet_type=${encodeURIComponent(dietType)}`;
    }

    try {
        const res = await fetch(url, { credentials: "include" });
        if (!res.ok) throw new Error("Failed to fetch recipes");

        const result = await res.json();

        const tableBody = document.getElementById("recipesTableBody");
        tableBody.innerHTML = "";

        result.data.forEach(recipe => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td class="p-2">${recipe.Diet_type}</td>
                <td class="p-2">${recipe.Recipe_name}</td>
                <td class="p-2">${recipe["Protein(g)"]}</td>
            `;
            tableBody.appendChild(row);
        });

        currentRecipePage = result.page;
        totalRecipePages = result.total_pages;

        updatePaginationUI();
    } catch (err) {
        console.error("Recipes error:", err);
    }
}

async function getClusters(dietType = "") {
    try {
        let url = `${API_BASE}/api/clusters`;
        if (dietType) {
            url += `?diet_type=${encodeURIComponent(dietType)}`;
        }

        const res = await fetch(url, { credentials: "include" });
        if (!res.ok) throw new Error("Failed to fetch clusters");

        const data = await res.json();

        const tableBody = document.getElementById("clustersTableBody");
        tableBody.innerHTML = "";

        data.forEach(cluster => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td class="p-2">${cluster.Diet_type}</td>
                <td class="p-2">${cluster.Cuisine_type}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (err) {
        console.error("Clusters error:", err);
    }
}

async function loadSecurityStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/security-status`, { credentials: "include" });
        if (!res.ok) throw new Error("Failed to fetch security status");

        const data = await res.json();

        function setStatus(id, statusObj) {
            const el = document.getElementById(id);
            if (!el) return;

            const badgeColor = statusObj.verified ? "text-green-600" : "text-yellow-600";
            el.innerHTML = `
                <span class="font-semibold ${badgeColor}">${statusObj.label}</span>
                <span class="block text-xs text-gray-500">${statusObj.details}</span>
            `;
        }

        setStatus("secEncryption", data.encryption);
        setStatus("secAccess", data.access_control);
        setStatus("secCompliance", data.compliance);
        setStatus("secCors", data.cors_restricted);

    } catch (err) {
        console.error("Security status error:", err);
    }
}

async function loadUserInfo() {
    try {
        const res = await fetch("/.auth/me", { credentials: "include" });
        if (!res.ok) return;

        const data = await res.json();
        const userInfo = document.getElementById("userInfo");

        const principal = data?.clientPrincipal;
        if (principal) {
            userInfo.innerHTML = `Signed in as <strong>${principal.userDetails || principal.identityProvider}</strong>`;
        } else {
            userInfo.textContent = "Not signed in";
        }
    } catch (err) {
        console.error("Failed to load user info", err);
    }
}

function updatePaginationUI() {
    const pageInfo = document.getElementById("pageInfo");
    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");

    if (pageInfo) {
        pageInfo.textContent = `Page ${currentRecipePage} of ${totalRecipePages}`;
    }

    if (prevBtn) {
        prevBtn.disabled = currentRecipePage <= 1;
    }

    if (nextBtn) {
        nextBtn.disabled = currentRecipePage >= totalRecipePages;
    }
}

document.getElementById("insightsBtn")?.addEventListener("click", () => {
    const filter = getActiveDietFilter();
    getInsights(filter);
});

document.getElementById("recipesBtn")?.addEventListener("click", () => {
    const filter = getActiveDietFilter();
    getRecipes(1, filter);
});

document.getElementById("clustersBtn")?.addEventListener("click", () => {
    const filter = getActiveDietFilter();
    getClusters(filter);
});

document.getElementById("prevPageBtn")?.addEventListener("click", () => {
    const filter = getActiveDietFilter();
    getRecipes(currentRecipePage - 1, filter);
});

document.getElementById("nextPageBtn")?.addEventListener("click", () => {
    const filter = getActiveDietFilter();
    getRecipes(currentRecipePage + 1, filter);
});

dietInput?.addEventListener("input", () => {
    const filter = dietInput.value.trim();
    if (dietSelect) dietSelect.value = "";

    getInsights(filter);
    getRecipes(1, filter);
    getClusters(filter);
});

dietSelect?.addEventListener("change", () => {
    const filter = dietSelect.value;
    if (dietInput) dietInput.value = "";

    getInsights(filter);
    getRecipes(1, filter);
    getClusters(filter);
});

document.getElementById("cleanupBtn")?.addEventListener("click", () => {
    document.getElementById("cleanupInfo")?.classList.toggle("hidden");
});

loadSecurityStatus();
loadUserInfo();