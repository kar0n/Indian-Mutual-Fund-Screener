/**
 * MF Quant Core - Client-Side Workstation Controller
 */

// Global state
window.mfData = null;
let currentCategory = '';
let searchQuery = '';
let sortBy = 'rank';
let sortOrder = 'asc';
let categoryFunds = []; // Copy of the selected category funds with origRank mapped

// DOM Elements
const categoryPills = document.getElementById('category-pills');
const searchInput = document.getElementById('search-input');
const leaderName = document.getElementById('leader-name');
const leaderRating = document.getElementById('leader-rating');
const mean1yVal = document.getElementById('mean-1y');
const mean3yVal = document.getElementById('mean-3y');
const resultsCount = document.getElementById('results-count');
const tableBody = document.getElementById('table-body');
const drawerOverlay = document.getElementById('drawer-overlay');
const detailsDrawer = document.getElementById('details-drawer');
const closeDrawerBtn = document.getElementById('close-drawer');
const drawerContent = document.getElementById('drawer-content');
const headerMeta = document.getElementById('header-meta');

// Helper to check if a value is nil (null, undefined, NaN, or empty string)
function isNilOrNaN(val) {
    return val === null || val === undefined || (typeof val === 'number' && isNaN(val)) || val === '';
}

// Helper formatting utilities
function formatPercent(val) {
    if (isNilOrNaN(val)) return 'N/A';
    return (val > 0 ? '+' : '') + val.toFixed(2) + '%';
}

function formatPercentNoSign(val) {
    if (isNilOrNaN(val)) return 'N/A';
    return val.toFixed(2) + '%';
}

function formatNum(val, decimals = 2) {
    if (isNilOrNaN(val)) return 'N/A';
    return val.toFixed(decimals);
}

function formatAlpha(val) {
    if (isNilOrNaN(val)) return 'N/A';
    return (val > 0 ? '+' : '') + val.toFixed(2);
}

function formatManagerLinks(managersStr, showAll = false) {
    if (isNilOrNaN(managersStr) || managersStr === 'N/A') return 'N/A';
    const managers = managersStr.split(',').map(m => m.trim()).filter(Boolean);
    if (managers.length === 0) return 'N/A';
    
    const limit = showAll ? managers.length : 2;
    const displayed = managers.slice(0, limit);
    const links = displayed.map(name => {
        const encoded = encodeURIComponent(name + ' mutual fund manager');
        return `<a href="https://www.linkedin.com/search/results/all/?keywords=${encoded}" target="_blank" class="manager-linkedin-link" title="Verify tenure and career history for ${name} on LinkedIn" onclick="event.stopPropagation();">${name}</a>`;
    });
    
    if (!showAll && managers.length > limit) {
        const remaining = managers.slice(limit);
        const remainingLinks = remaining.map(name => {
            const encoded = encodeURIComponent(name + ' mutual fund manager');
            return `<a href="https://www.linkedin.com/search/results/all/?keywords=${encoded}" target="_blank" class="manager-linkedin-link" title="Verify tenure and career history for ${name} on LinkedIn" onclick="event.stopPropagation();">${name}</a>`;
        }).join(', ');
        const remainingCount = remaining.length;
        
        links.push(`<span class="manager-hidden-links" style="display: none;">, ${remainingLinks}</span><span class="manager-more-tag" title="${remaining.join(', ')}" onclick="event.stopPropagation(); this.style.display='none'; this.previousElementSibling.style.display='inline';">+ ${remainingCount} more</span>`);
    }
    
    return links.join(', ');
}

// Initializer
document.addEventListener('DOMContentLoaded', () => {
    init();
});

async function init() {
    try {
        const response = await fetch('./mf_universe_data.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        window.mfData = await response.json();
        
        // Populate header metadata
        renderHeaderMeta();
        
        // Populate categories selector
        populateCategories();
        
        // Initialize listeners
        setupEventListeners();
        
        // Initial render
        handleCategoryChange();
    } catch (error) {
        console.error('Failed to load mutual fund quant database:', error);
        tableBody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--danger); padding: 2rem;">Failed to load mutual fund database. Please make sure the data compiler has run successfully. Error: ${error.message}</td></tr>`;
    }
}

function renderHeaderMeta() {
    if (!window.mfData || !window.mfData.metadata) return;
    const meta = window.mfData.metadata;
    headerMeta.innerHTML = `
        <div>LIVE RFR: ${meta.risk_free_rate}% (${meta.rfr_status})</div>
        <div>BENCHMARK: ${meta.benchmark}</div>
        <div>COMPILED: ${meta.compile_date}</div>
    `;
}

function populateCategories() {
    if (!window.mfData || !window.mfData.categories) return;
    categoryPills.innerHTML = '';
    const categories = Object.keys(window.mfData.categories);
    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'category-pill';
        btn.textContent = cat.replace('Equity Scheme - ', '')
                             .replace('Hybrid Scheme - ', '')
                             .replace('Debt Scheme - ', '')
                             .replace('Dynamic Asset Allocation or Balanced Advantage', 'Balanced Advantage');
        btn.addEventListener('click', () => {
            document.querySelectorAll('.category-pill').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = cat;
            handleCategoryChange();
        });
        categoryPills.appendChild(btn);
    });
    if (categories.length > 0) {
        currentCategory = categories[0];
        const firstPill = categoryPills.querySelector('.category-pill');
        if (firstPill) firstPill.classList.add('active');
    }
}

function setupEventListeners() {
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        renderTableData();
    });

    // Close details drawer
    closeDrawerBtn.addEventListener('click', closeDrawer);
    drawerOverlay.addEventListener('click', closeDrawer);

    // Escape key closes drawer
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeDrawer();
    });

    // Column sorting listeners
    const headers = document.querySelectorAll('th.sortable');
    headers.forEach(th => {
        th.addEventListener('click', () => {
            const colName = th.getAttribute('data-sort');
            handleSort(colName, th);
        });
    });

    // Collapsible Methodology Guide Toggle
    const methodologyToggle = document.getElementById('methodology-toggle');
    const methodologyBox = document.getElementById('methodology-box');
    const toggleText = document.querySelector('.methodology-toggle-badge .toggle-text');
    const toggleArrow = document.querySelector('.methodology-toggle-badge .toggle-arrow');

    if (methodologyToggle && methodologyBox) {
        methodologyToggle.addEventListener('click', () => {
            const isExpanded = methodologyBox.classList.toggle('expanded');
            if (toggleText) toggleText.textContent = isExpanded ? 'Hide Guide' : 'Show Guide';
            if (toggleArrow) toggleArrow.textContent = isExpanded ? '▲' : '▼';
        });
    }
}

function handleCategoryChange() {
    if (!window.mfData || !window.mfData.categories || !currentCategory) return;
    
    // Reset search
    searchInput.value = '';
    searchQuery = '';
    
    // Get fresh list of funds and attach 1-based original rank based on compiler order
    const rawFunds = window.mfData.categories[currentCategory] || [];
    categoryFunds = rawFunds.map((fund, idx) => ({
        ...fund,
        origRank: idx + 1
    }));

    // Reset sort to 'rank' asc by default
    sortBy = 'rank';
    sortOrder = 'asc';
    updateHeaderSortUI();

    // Render stats cards and table
    renderCategoryStats();
    renderTableData();
}

function renderCategoryStats() {
    if (categoryFunds.length === 0) {
        leaderName.textContent = 'N/A';
        leaderRating.textContent = '-';
        mean1yVal.textContent = 'N/A';
        mean3yVal.textContent = 'N/A';
        return;
    }

    // Leader (first element in original array which is sorted by score)
    const leader = categoryFunds[0];
    leaderName.textContent = leader['Fund Name'];
    leaderRating.textContent = `${leader.Rating} (${leader.Rating_Score.toFixed(3)})`;

    // Averages
    let sumRoll = 0, countRoll = 0;
    let sumAlpha = 0, countAlpha = 0;

    categoryFunds.forEach(fund => {
        const rRoll = fund['3Y Rolling Return (%)'];
        if (!isNilOrNaN(rRoll)) {
            sumRoll += rRoll;
            countRoll++;
        }
        const alpha = fund['Alpha (3Y)'];
        if (!isNilOrNaN(alpha)) {
            sumAlpha += alpha;
            countAlpha++;
        }
    });

    mean1yVal.textContent = countRoll > 0 ? (sumRoll / countRoll).toFixed(2) + '%' : 'N/A';
    mean3yVal.textContent = countAlpha > 0 ? (sumAlpha / countAlpha).toFixed(2) : 'N/A';
}

function handleSort(column, thElement) {
    if (sortBy === column) {
        // Toggle sortOrder
        sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        sortBy = column;
        // Sensible default sort direction based on column type
        if (['rank', 'name', 'manager', 'downside'].includes(column)) {
            sortOrder = 'asc';
        } else {
            sortOrder = 'desc';
        }
    }
    updateHeaderSortUI(thElement);
    renderTableData();
}

function updateHeaderSortUI(activeTh) {
    const headers = document.querySelectorAll('th.sortable');
    headers.forEach(th => {
        th.classList.remove('sorted-asc', 'sorted-desc');
        const iconSpan = th.querySelector('.sort-icon');
        if (iconSpan) iconSpan.textContent = '';
    });

    const th = activeTh || document.querySelector(`th[data-sort="${sortBy}"]`);
    if (th) {
        th.classList.add(sortOrder === 'asc' ? 'sorted-asc' : 'sorted-desc');
        const iconSpan = th.querySelector('.sort-icon');
        if (iconSpan) {
            iconSpan.textContent = sortOrder === 'asc' ? ' ▲' : ' ▼';
        }
    }
}

function getSortValue(item, column) {
    switch (column) {
        case 'rank': return item.origRank;
        case 'rating': return item.Rating_Score;
        case 'name': return item['Fund Name'];
        case 'aum': return item['AUM (Cr)'];
        case 'manager': return item.Managers;
        case 'r3y_roll': return item['3Y Rolling Return (%)'];
        case 'r5y_roll': return item['5Y Rolling Return (%)'];
        case 'alpha': return item['Alpha (3Y)'];
        case 'downside': return item['Downside Capture (3Y)'];
        case 'ir': return item['Information Ratio (3Y)'];
        default: return null;
    }
}

function sortAndFilterFunds() {
    // 1. Filter
    let filtered = categoryFunds;
    if (searchQuery) {
        filtered = categoryFunds.filter(fund => 
            fund['Fund Name'].toLowerCase().includes(searchQuery)
        );
    }

    // 2. Sort
    filtered.sort((a, b) => {
        const valA = getSortValue(a, sortBy);
        const valB = getSortValue(b, sortBy);

        const isNullA = isNilOrNaN(valA);
        const isNullB = isNilOrNaN(valB);

        if (isNullA && isNullB) return 0;
        if (isNullA) return 1; // Put nulls at the bottom
        if (isNullB) return -1;

        if (typeof valA === 'string' && typeof valB === 'string') {
            return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        } else {
            return sortOrder === 'asc' ? valA - valB : valB - valA;
        }
    });

    return filtered;
}

function renderTableData() {
    const processedFunds = sortAndFilterFunds();
    resultsCount.textContent = `${processedFunds.length} ${processedFunds.length === 1 ? 'fund' : 'funds'}`;
    
    tableBody.innerHTML = '';
    
    if (processedFunds.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 2rem;">No funds matching search criteria.</td></tr>`;
        return;
    }

    processedFunds.forEach(fund => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-code', fund.code);
        
        // Colors & classes for percentages and decimals
        const r3yRollVal = fund['3Y Rolling Return (%)'];
        const r3yRollClass = isNilOrNaN(r3yRollVal) ? '' : (r3yRollVal > 0 ? 'percentage-val positive' : 'percentage-val negative');

        const r5yRollVal = fund['5Y Rolling Return (%)'];
        const r5yRollClass = isNilOrNaN(r5yRollVal) ? '' : (r5yRollVal > 0 ? 'percentage-val positive' : 'percentage-val negative');

        const alphaVal = fund['Alpha (3Y)'];
        const alphaClass = isNilOrNaN(alphaVal) ? '' : (alphaVal > 0 ? 'percentage-val positive' : 'percentage-val negative');

        const downsideVal = fund['Downside Capture (3Y)'];
        const downsideClass = isNilOrNaN(downsideVal) ? '' : (downsideVal < 100.0 ? 'percentage-val positive' : 'percentage-val negative');

        const aumVal = fund['AUM (Cr)'];
        const aumText = isNilOrNaN(aumVal) ? 'N/A' : aumVal.toLocaleString('en-IN') + ' Cr';
        
        const managerText = fund.Managers || 'N/A';
        const managerTitleText = managerText.replace(/"/g, '&quot;');

        tr.innerHTML = `
            <td>${fund.origRank}</td>
            <td class="scheme-name text-left">${fund['Fund Name']}</td>
            <td class="rating-stars">${fund.Rating}</td>
            <td class="aum-col">${aumText}</td>
            <td class="${r3yRollClass}">${formatPercent(r3yRollVal)}</td>
            <td class="${r5yRollClass}">${formatPercent(r5yRollVal)}</td>
            <td class="${alphaClass}">${formatAlpha(alphaVal)}</td>
            <td class="${downsideClass}">${formatPercentNoSign(downsideVal)}</td>
            <td>${formatNum(fund['Information Ratio (3Y)'])}</td>
            <td class="text-left manager-col" title="${managerTitleText}">${formatManagerLinks(managerText)}</td>
        `;
        
        tr.addEventListener('click', () => {
            showDrawer(fund);
        });

        tableBody.appendChild(tr);
    });
}

function showDrawer(fund) {
    const category = currentCategory;
    const isMidOrSmall = category.toLowerCase().includes('mid cap') || category.toLowerCase().includes('small cap');
    
    // Fetch average rolling 3Y return for the category to compute performance consistency sub-rating
    const validRollingReturns = categoryFunds
        .map(item => item['3Y Rolling Return (%)'])
        .filter(val => !isNilOrNaN(val));
    const avgRolling3Y = validRollingReturns.length > 0 
        ? validRollingReturns.reduce((sum, val) => sum + val, 0) / validRollingReturns.length 
        : 0.0;

    // Calculate sub-ratings based on Python engine guidelines (max 1.25 each)
    
    // 1. Performance Consistency
    let scoreRoll = 0.625;
    const r3yRoll = fund['3Y Rolling Return (%)'];
    if (!isNilOrNaN(r3yRoll)) {
        const diff = r3yRoll - avgRolling3Y;
        if (diff >= 3.0) scoreRoll = 1.25;
        else if (diff >= 0.0) scoreRoll = 0.9375;
        else if (diff >= -3.0) scoreRoll = 0.625;
        else if (diff >= -6.0) scoreRoll = 0.3125;
        else scoreRoll = 0.0;
    }

    // 2. Information Ratio
    let scoreIr = 0.625;
    const ir = fund['Information Ratio (3Y)'];
    if (!isNilOrNaN(ir)) {
        if (ir >= 1.0) scoreIr = 1.25;
        else if (ir >= 0.75) scoreIr = 0.9375;
        else if (ir >= 0.5) scoreIr = 0.625;
        else if (ir >= 0.0) scoreIr = 0.3125;
        else scoreIr = 0.0;
    }

    // 3. CAPM Alpha
    let scoreAlpha = 0.625;
    const expense = fund['Expense Ratio (%)'] || 0;
    const netAlpha = !isNilOrNaN(fund['Alpha (3Y)']) ? (fund['Alpha (3Y)'] - expense) : null;
    if (netAlpha !== null) {
        if (netAlpha >= 5.0) scoreAlpha = 1.25;
        else if (netAlpha >= 2.5) scoreAlpha = 0.9375;
        else if (netAlpha >= 0.0) scoreAlpha = 0.625;
        else if (netAlpha >= -2.0) scoreAlpha = 0.3125;
        else scoreAlpha = 0.0;
    }

    // 4. Downside Capital Protection
    let scoreDownside = 0.625;
    const downside = fund['Downside Capture (3Y)'];
    if (!isNilOrNaN(downside)) {
        if (downside <= 80.0) scoreDownside = 1.25;
        else if (downside <= 95.0) scoreDownside = 0.9375;
        else if (downside <= 100.0) scoreDownside = 0.78125;
        else if (downside <= 110.0) scoreDownside = 0.46875;
        else scoreDownside = 0.0;
    }

    function toStars(score) {
        const fullStars = Math.floor(score);
        const remainder = score - fullStars;
        const halfStar = remainder >= 0.25 ? '½' : '';
        if (fullStars === 0 && !halfStar) return '½';
        return '⭐'.repeat(fullStars) + halfStar;
    }

    // AUM warning check
    let aumWarningHtml = '';
    const aum = fund['AUM (Cr)'];
    if (isMidOrSmall && !isNilOrNaN(aum)) {
        if (category.toLowerCase().includes('small cap') && aum > 15000) {
            aumWarningHtml = `<div class="alert-value warning">⚠️ Bloated AUM: ${aum.toLocaleString()} Cr (-0.5★ Penalty Applied)</div>`;
        } else if (category.toLowerCase().includes('mid cap') && aum > 25000) {
            aumWarningHtml = `<div class="alert-value warning">⚠️ Bloated AUM: ${aum.toLocaleString()} Cr (-0.5★ Penalty Applied)</div>`;
        } else {
            aumWarningHtml = `<div class="alert-value success">✓ AUM: ${aum.toLocaleString()} Cr (Healthy size)</div>`;
        }
    } else if (!isNilOrNaN(aum)) {
        aumWarningHtml = `<div>${aum.toLocaleString()} Cr</div>`;
    } else {
        aumWarningHtml = `<div class="text-muted">N/A</div>`;
    }

    // Concentration warning check
    let concWarningHtml = '';
    const conc = fund['Top 10 Stocks Weight (%)'];
    if (isMidOrSmall && !isNilOrNaN(conc)) {
        if (conc < 20.0 || conc > 45.0) {
            concWarningHtml = `<div class="alert-value warning">⚠️ Concentration: ${conc.toFixed(2)}% (-0.25★ Penalty, outside 20-45% limits)</div>`;
        } else {
            concWarningHtml = `<div class="alert-value success">✓ Concentration: ${conc.toFixed(2)}% (Optimal 20-45%)</div>`;
        }
    } else if (!isNilOrNaN(conc)) {
        concWarningHtml = `<div>${conc.toFixed(2)}%</div>`;
    } else {
        concWarningHtml = `<div class="text-muted">N/A</div>`;
    }

    // Holdings list html
    let holdingsHtml = '';
    if (fund.Holdings && fund.Holdings.length > 0) {
        holdingsHtml = fund.Holdings.map(h => `
            <div class="holding-row">
                <div>
                    <div class="holding-name">${h.name || 'N/A'}</div>
                    <div class="holding-sector">${h.sector || 'N/A'}</div>
                </div>
                <div class="holding-weight">${!isNilOrNaN(h.weightage) ? h.weightage.toFixed(2) + '%' : 'N/A'}</div>
            </div>
        `).join('');
    } else {
        holdingsHtml = '<div class="text-muted" style="padding: 1rem 0; text-align: center;">No portfolio holdings data compiled for this scheme.</div>';
    }

    // Market cap indicators HTML
    const largeCap = fund['Large Cap (%)'];
    const midCap = fund['Mid Cap (%)'];
    const smallCap = fund['Small Cap (%)'];
    let mcapHtml = '';
    if (!isNilOrNaN(largeCap) || !isNilOrNaN(midCap) || !isNilOrNaN(smallCap)) {
        mcapHtml = `
            <div class="badge-grid">
                <span class="mcap-badge">Large: ${!isNilOrNaN(largeCap) ? largeCap.toFixed(1) + '%' : '0%'}</span>
                <span class="mcap-badge">Mid: ${!isNilOrNaN(midCap) ? midCap.toFixed(1) + '%' : '0%'}</span>
                <span class="mcap-badge">Small: ${!isNilOrNaN(smallCap) ? smallCap.toFixed(1) + '%' : '0%'}</span>
            </div>
        `;
    } else {
        mcapHtml = '<div class="text-muted">N/A</div>';
    }

    drawerContent.innerHTML = `
        <h2 class="drawer-title">${fund['Fund Name']}</h2>
        
        <div class="drawer-section">
            <div class="drawer-section-title">Quantitative Scorecard Breakdown</div>
            <div class="rating-detail-item">
                <span class="rating-detail-label">Overall Quant Rating</span>
                <span class="rating-detail-stars">${fund.Rating} (${fund.Rating_Score.toFixed(3)}★ / 5★)</span>
            </div>
            <div class="rating-detail-item">
                <span class="rating-detail-label">Performance Consistency (Rolling 3Y)</span>
                <span class="rating-detail-stars">${toStars(scoreRoll)} (${scoreRoll.toFixed(4)}★)</span>
            </div>
            <div class="rating-detail-item">
                <span class="rating-detail-label">Information Ratio (3Y Skill vs Luck)</span>
                <span class="rating-detail-stars">${toStars(scoreIr)} (${scoreIr.toFixed(4)}★)</span>
            </div>
            <div class="rating-detail-item">
                <span class="rating-detail-label">CAPM Net Alpha (3Y Risk-Adjusted)</span>
                <span class="rating-detail-stars">${toStars(scoreAlpha)} (${scoreAlpha.toFixed(4)}★)</span>
            </div>
            <div class="rating-detail-item">
                <span class="rating-detail-label">Capital Protection (Downside Capture)</span>
                <span class="rating-detail-stars">${toStars(scoreDownside)} (${scoreDownside.toFixed(4)}★)</span>
            </div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">Performance & Risk Summary</div>
            <div class="modal-grid">
                <div class="modal-item">
                    <span class="modal-item-label">1Y Return</span>
                    <span class="modal-item-value ${fund['1Y Return (%)'] > 0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatPercent(fund['1Y Return (%)'])}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">3Y Return</span>
                    <span class="modal-item-value ${fund['3Y Return (%)'] > 0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatPercent(fund['3Y Return (%)'])}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">5Y Return</span>
                    <span class="modal-item-value ${fund['5Y Return (%)'] > 0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatPercent(fund['5Y Return (%)'])}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">3Y Rolling Return</span>
                    <span class="modal-item-value ${fund['3Y Rolling Return (%)'] > 0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatPercent(fund['3Y Rolling Return (%)'])}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">5Y Rolling Return</span>
                    <span class="modal-item-value ${fund['5Y Rolling Return (%)'] > 0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatPercent(fund['5Y Rolling Return (%)'])}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">CAPM Alpha (3Y)</span>
                    <span class="modal-item-value ${fund['Alpha (3Y)'] > 0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatAlpha(fund['Alpha (3Y)'])}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">Beta (3Y)</span>
                    <span class="modal-item-value">${formatNum(fund['Beta (3Y)'])}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">Downside Capture (3Y)</span>
                    <span class="modal-item-value ${fund['Downside Capture (3Y)'] < 100.0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatPercentNoSign(fund['Downside Capture (3Y)'])}</span>
                </div>
            </div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">Qualitative Risk Profiles</div>
            <div class="modal-grid">
                <div class="modal-item">
                    <span class="modal-item-label">AUM</span>
                    <span class="modal-item-value">${aumWarningHtml}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">Expense Ratio</span>
                    <span class="modal-item-value">${!isNilOrNaN(fund['Expense Ratio (%)']) ? fund['Expense Ratio (%)'].toFixed(2) + '%' : 'N/A'}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">Portfolio Concentration</span>
                    <span class="modal-item-value">${concWarningHtml}</span>
                </div>
                <div class="modal-item">
                    <span class="modal-item-label">Market Cap Weight</span>
                    <span class="modal-item-value">${mcapHtml}</span>
                </div>
            </div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">Fund Management</div>
            <div class="modal-grid">
                <div class="modal-item" style="grid-column: span 2;">
                    <span class="modal-item-label">Current Managers & Tenure Profile (Click for LinkedIn Lookup)</span>
                    <span class="modal-item-value" style="font-size:0.9rem; font-weight:500; color:#e2e8f0; line-height: 1.4;">${formatManagerLinks(fund.Managers, true)}</span>
                </div>
            </div>
        </div>

        <div class="drawer-section">
            <div class="drawer-section-title">Top 15 Underlying Holdings</div>
            <div class="holdings-list">
                ${holdingsHtml}
            </div>
        </div>
    `;

    detailsDrawer.classList.add('active');
    drawerOverlay.classList.add('active');
}

function closeDrawer() {
    detailsDrawer.classList.remove('active');
    drawerOverlay.classList.remove('active');
}
