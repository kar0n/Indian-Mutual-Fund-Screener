/**
 * IMF Screener - Client-Side Controller
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
    return (val > 0 ? '+' : '') + val.toFixed(2) + '%';
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
    const benchName = meta.benchmark_mapping ? (meta.benchmark_mapping[currentCategory] || 'Nifty 50 Index') : (meta.benchmark || 'Nifty 50 Index');
    headerMeta.innerHTML = `
        <div>LIVE RFR: ${meta.risk_free_rate}% (${meta.rfr_status})</div>
        <div class="benchmark-pill">BENCHMARK: ${benchName}</div>
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

    // Setup global tooltip element
    const tooltip = document.getElementById('rating-tooltip');
    
    // Helper to find fund by code
    const findFundByCode = (code) => {
        if (!window.mfData || !window.mfData.categories) return null;
        for (const cat in window.mfData.categories) {
            const fund = window.mfData.categories[cat].find(f => String(f.code) === String(code));
            if (fund) return fund;
        }
        return null;
    };

    let activeTooltipTrigger = null;

    // Global event delegation for hovering over rating elements
    document.addEventListener('mouseover', (e) => {
        const trigger = e.target.closest('.rating-tooltip-trigger');
        if (!trigger) {
            if (activeTooltipTrigger && tooltip) {
                tooltip.style.display = 'none';
                tooltip.style.opacity = '0';
                activeTooltipTrigger = null;
            }
            return;
        }

        if (trigger === activeTooltipTrigger) return; // Already showing for this trigger
        activeTooltipTrigger = trigger;

        const fundCode = trigger.getAttribute('data-fund-code');
        const fund = findFundByCode(fundCode);
        if (!fund || !tooltip) return;

        // Build adjustment rows if applicable
        let overlayHtml = '';
        if (fund.AUM_Adj && fund.AUM_Adj !== 0) {
            const sign = fund.AUM_Adj > 0 ? '+' : '';
            const cls = fund.AUM_Adj > 0 ? 'text-success' : 'text-danger';
            overlayHtml += `
                <div class="tooltip-row overlay-row">
                    <span>AUM Scale Adjustment</span>
                    <span class="${cls}">${sign}${fund.AUM_Adj.toFixed(2)}★</span>
                </div>
            `;
        }
        // Format sub-ratings safely
        const rollVal = typeof fund.Sub_Rating_Performance === 'number' ? fund.Sub_Rating_Performance : 0;
        const irVal = typeof fund.Sub_Rating_IR === 'number' ? fund.Sub_Rating_IR : 0;
        const alphaVal = typeof fund.Sub_Rating_Alpha === 'number' ? fund.Sub_Rating_Alpha : 0;
        const dcVal = typeof fund.Sub_Rating_Protection === 'number' ? fund.Sub_Rating_Protection : 0;

        // Get category-specific weights dynamically
        const getCategoryWeights = (categoryName) => {
            const catLower = (categoryName || '').toLowerCase();
            if (catLower.includes('hybrid') || catLower.includes('balanced advantage') || catLower.includes('dynamic asset')) {
                return { roll: 25, ir: 25, alpha: 15, dc: 35 };
            } else if (catLower.includes('debt') || catLower.includes('liquid') || catLower.includes('arbitrage')) {
                return { roll: 35, ir: 20, alpha: 5, dc: 40 };
            } else if (catLower.includes('small cap') || catLower.includes('mid cap')) {
                return { roll: 20, ir: 25, alpha: 35, dc: 20 };
            } else {
                return { roll: 25, ir: 25, alpha: 25, dc: 25 };
            }
        };
        const w = getCategoryWeights(currentCategory);

        tooltip.innerHTML = `
            <div class="tooltip-header">
                <div class="tooltip-fund-name">${fund['Fund Name']}</div>
                <div class="tooltip-overall">
                    <span class="stars">${fund.Rating}</span>
                    <span class="score">(${fund.Rating_Score.toFixed(3)} / 5.0)</span>
                </div>
            </div>
            <div class="tooltip-divider"></div>
            <div class="tooltip-body">
                <div class="tooltip-row">
                    <span>Performance Consistency (${w.roll}%)</span>
                    <span>${rollVal.toFixed(2)}★</span>
                </div>
                <div class="tooltip-row">
                    <span>Information Ratio (${w.ir}%)</span>
                    <span>${irVal.toFixed(2)}★</span>
                </div>
                <div class="tooltip-row">
                    <span>CAPM Alpha (${w.alpha}%)</span>
                    <span>${alphaVal.toFixed(2)}★</span>
                </div>
                <div class="tooltip-row">
                    <span>Downside Protection (${w.dc}%)</span>
                    <span>${dcVal.toFixed(2)}★</span>
                </div>
                ${overlayHtml}
            </div>
        `;

        tooltip.style.display = 'block';

        // Position tooltip centered above the trigger element
        const triggerRect = trigger.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let x = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2);
        let y = triggerRect.top - tooltipRect.height - 10;

        // Boundary checks relative to viewport width/height
        if (x < 10) x = 10;
        if (x + tooltipRect.width > window.innerWidth - 10) {
            x = window.innerWidth - tooltipRect.width - 10;
        }
        
        // If tooltip would go off top of screen, show it below the trigger instead
        if (y < 10) {
            y = triggerRect.bottom + 10;
        }

        // Apply coordinates accounting for absolute scroll offsets
        tooltip.style.left = `${x + window.scrollX}px`;
        tooltip.style.top = `${y + window.scrollY}px`;
        tooltip.style.opacity = '1';
    });

    // Hide tooltip on scroll
    window.addEventListener('scroll', () => {
        if (tooltip) {
            tooltip.style.display = 'none';
            tooltip.style.opacity = '0';
            activeTooltipTrigger = null;
        }
    }, { passive: true });

    // Hide tooltip on mouse leave
    document.addEventListener('mouseout', (e) => {
        const trigger = e.target.closest('.rating-tooltip-trigger');
        if (trigger && tooltip && !e.relatedTarget?.closest('.rating-tooltip-trigger')) {
            tooltip.style.display = 'none';
            tooltip.style.opacity = '0';
            activeTooltipTrigger = null;
        }
    });

    // ─── Column Header Description Tooltip (2-second hover delay) ───
    const colTooltip = document.getElementById('column-tooltip');
    let colTooltipTimer = null;
    let activeColHeader = null;

    const showColumnTooltip = (th) => {
        const desc = th.getAttribute('data-col-desc');
        if (!desc || !colTooltip) return;

        // Get the visible column label text (excluding sort icon)
        const sortIcon = th.querySelector('.sort-icon');
        const labelText = th.textContent.replace(sortIcon ? sortIcon.textContent : '', '').trim();

        colTooltip.innerHTML = `
            <div class="col-tooltip-title">
                <span class="col-tooltip-icon">ⓘ</span>
                <span>${labelText}</span>
            </div>
            <div class="col-tooltip-desc">${desc}</div>
        `;

        colTooltip.style.display = 'block';

        // Position tooltip below the header
        const thRect = th.getBoundingClientRect();
        const tooltipW = colTooltip.getBoundingClientRect().width;

        let x = thRect.left + (thRect.width / 2) - (tooltipW / 2);
        let y = thRect.bottom + 8;

        // Boundary checks
        if (x < 10) x = 10;
        if (x + tooltipW > window.innerWidth - 10) {
            x = window.innerWidth - tooltipW - 10;
        }

        colTooltip.style.left = `${x + window.scrollX}px`;
        colTooltip.style.top = `${y + window.scrollY}px`;
        colTooltip.style.opacity = '1';
    };

    const hideColumnTooltip = () => {
        if (colTooltipTimer) {
            clearTimeout(colTooltipTimer);
            colTooltipTimer = null;
        }
        if (colTooltip) {
            colTooltip.style.display = 'none';
            colTooltip.style.opacity = '0';
        }
        activeColHeader = null;
    };

    // Event delegation on the thead
    const thead = document.querySelector('.quant-table thead');
    if (thead && colTooltip) {
        thead.addEventListener('mouseover', (e) => {
            const th = e.target.closest('th[data-col-desc]');
            if (!th) {
                hideColumnTooltip();
                return;
            }
            if (th === activeColHeader) return; // Already timing/showing for this header

            // Clear any previous timer
            hideColumnTooltip();
            activeColHeader = th;

            // Start 2-second delay
            colTooltipTimer = setTimeout(() => {
                showColumnTooltip(th);
            }, 1000);
        });

        thead.addEventListener('mouseout', (e) => {
            const th = e.target.closest('th[data-col-desc]');
            if (th && !e.relatedTarget?.closest('th[data-col-desc]')) {
                hideColumnTooltip();
            }
        });
    }

    // Also hide column tooltip on table scroll
    const tableWrapper = document.querySelector('.table-wrapper');
    if (tableWrapper) {
        tableWrapper.addEventListener('scroll', () => {
            hideColumnTooltip();
        }, { passive: true });
    }
}

function handleCategoryChange() {
    if (!window.mfData || !window.mfData.categories || !currentCategory) return;
    
    // Reset search
    searchInput.value = '';
    searchQuery = '';
    
    // Update Header Meta to reflect dynamic benchmark for this category
    renderHeaderMeta();
    
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
    leaderRating.innerHTML = `<span class="rating-stars rating-tooltip-trigger" data-fund-code="${leader.code}">${leader.Rating}</span> <span class="score-val">(${leader.Rating_Score.toFixed(3)})</span>`;

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
        case 'r1y_roll': return item['1Y Rolling Return (%)'];
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
        tableBody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--text-muted); padding: 2rem;">No funds matching search criteria.</td></tr>`;
        return;
    }

    processedFunds.forEach(fund => {
        const tr = document.createElement('tr');
        tr.setAttribute('data-code', fund.code);
        
        // Colors & classes for percentages and decimals
        const r1yRollVal = fund['1Y Rolling Return (%)'];
        const r1yRollClass = isNilOrNaN(r1yRollVal) ? '' : (r1yRollVal > 0 ? 'percentage-val positive' : 'percentage-val negative');

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
        
        let managerHtml = formatManagerLinks(managerText);
        if (fund.Manager_Changed_Recently) {
            managerHtml += ` <span class="manager-change-badge" title="New Lead Manager appointed recently (on ${fund.Manager_Change_Date || 'N/A'})">⚠️ New Manager</span>`;
        }

        tr.innerHTML = `
            <td>${fund.origRank}</td>
            <td class="scheme-name text-left">${fund['Fund Name']}</td>
            <td class="rating-cell rating-tooltip-trigger" data-fund-code="${fund.code}">
                <div class="rating-stars">${fund.Rating}</div>
                <div class="rating-score-subtext">${fund.Rating_Score.toFixed(3)}</div>
            </td>
            <td class="aum-col">${aumText}</td>
            <td class="${r1yRollClass}">${formatPercent(r1yRollVal)}</td>
            <td class="${r3yRollClass}">${formatPercent(r3yRollVal)}</td>
            <td class="${r5yRollClass}">${formatPercent(r5yRollVal)}</td>
            <td class="${alphaClass}">${formatAlpha(alphaVal)}</td>
            <td class="${downsideClass}">${formatPercentNoSign(downsideVal)}</td>
            <td>${formatNum(fund['Information Ratio (3Y)'])}</td>
            <td class="text-left manager-col" title="${managerTitleText}">${managerHtml}</td>
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
    
    // Read compiled sub-ratings directly from the JSON database records
    const scoreRoll = fund.Sub_Rating_Performance !== undefined && fund.Sub_Rating_Performance !== null ? fund.Sub_Rating_Performance : 0.625;
    const scoreIr = fund.Sub_Rating_IR !== undefined && fund.Sub_Rating_IR !== null ? fund.Sub_Rating_IR : 0.625;
    const scoreAlpha = fund.Sub_Rating_Alpha !== undefined && fund.Sub_Rating_Alpha !== null ? fund.Sub_Rating_Alpha : 0.625;
    const scoreDownside = fund.Sub_Rating_Protection !== undefined && fund.Sub_Rating_Protection !== null ? fund.Sub_Rating_Protection : 0.625;

    function toStars(score) {
        const fullStars = Math.floor(score);
        const remainder = score - fullStars;
        const halfStar = remainder >= 0.25 ? '½' : '';
        if (fullStars === 0 && !halfStar) return '½';
        return '★'.repeat(fullStars) + halfStar;
    }

    // AUM warning & bonus check
    let aumWarningHtml = '';
    const aum = fund['AUM (Cr)'];
    const aumAdj = fund.AUM_Adj || 0;
    const catLower = category.toLowerCase();
    
    if (!isNilOrNaN(aum)) {
        if (catLower.includes('small cap') || catLower.includes('mid-cap') || catLower.includes('mid cap')) {
            if (aumAdj < 0) {
                aumWarningHtml = `<div class="alert-value warning">⚠️ Bloated AUM: ${aum.toLocaleString()} Cr (-0.5★ Size Penalty Applied)</div>`;
            } else {
                aumWarningHtml = `<div class="alert-value success">✓ AUM: ${aum.toLocaleString()} Cr (Healthy size)</div>`;
            }
        } else if (catLower.includes('liquid') || catLower.includes('debt') || catLower.includes('arbitrage')) {
            if (aumAdj > 0) {
                aumWarningHtml = `<div class="alert-value success">✓ AUM: ${aum.toLocaleString()} Cr (+0.25★ Safety Bonus Applied)</div>`;
            } else {
                aumWarningHtml = `<div class="alert-value success">✓ AUM: ${aum.toLocaleString()} Cr (Healthy size)</div>`;
            }
        } else {
            if (aumAdj > 0) {
                aumWarningHtml = `<div class="alert-value success">✓ AUM: ${aum.toLocaleString()} Cr (+0.25★ Scale Bonus Applied)</div>`;
            } else {
                aumWarningHtml = `<div class="alert-value success">✓ AUM: ${aum.toLocaleString()} Cr (Healthy size)</div>`;
            }
        }
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

    // Manager tenure alert block
    let managerTenureHtml = '';
    const tenureYears = fund.Manager_Tenure_Years;
    const tenureAdj = fund.Manager_Tenure_Adj || 0;
    if (tenureYears !== undefined && tenureYears !== null) {
        if (tenureAdj < 0) {
            managerTenureHtml = `<div class="alert-value warning" style="margin-top: 5px; font-size: 0.8rem;">⚠️ Lead Manager Tenure: ${tenureYears} years (Recent transition: -0.5★ advisory penalty)</div>`;
        } else if (tenureAdj > 0) {
            managerTenureHtml = `<div class="alert-value success" style="margin-top: 5px; font-size: 0.8rem;">✓ Lead Manager Tenure: ${tenureYears} years (Veteran stability: +0.25★ advisory bonus)</div>`;
        } else {
            managerTenureHtml = `<div class="alert-value success" style="margin-top: 5px; font-size: 0.8rem;">✓ Lead Manager Tenure: ${tenureYears} years (Stable tenure)</div>`;
        }
    } else {
        managerTenureHtml = `<div class="text-muted" style="margin-top: 5px; font-size: 0.8rem;">Tenure details: Stable / Neutral (3.5 year baseline assumed)</div>`;
    }

    // Manager change warning block
    let managerChangeWarningHtml = '';
    if (fund.Manager_Changed_Recently) {
        managerChangeWarningHtml = `
            <div class="alert-value warning" style="margin-top: 10px; font-size: 0.8rem; line-height: 1.5; padding: 10px; border-radius: 4px;">
                ⚠️ <strong>Lead Manager Changed Recently (${fund.Manager_Change_Date || 'N/A'})</strong><br/>
                Please note that historical risk-adjusted metrics (Information Ratio, Net Alpha, Downside Capture) reflect the performance of the previous manager. They may not represent the investment style and future performance of the newly appointed management.
            </div>
        `;
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
                <span class="rating-detail-label">Performance Consistency (Rolling Returns)</span>
                <span class="rating-detail-stars">${toStars(scoreRoll)} (${scoreRoll.toFixed(4)}★)</span>
            </div>
            <div class="rating-detail-item">
                <span class="rating-detail-label">Information Ratio (Skill vs Luck)</span>
                <span class="rating-detail-stars">${toStars(scoreIr)} (${scoreIr.toFixed(4)}★)</span>
            </div>
            <div class="rating-detail-item">
                <span class="rating-detail-label">CAPM Net Alpha (Risk-Adjusted)</span>
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
                    <span class="modal-item-label">1Y Rolling Return</span>
                    <span class="modal-item-value ${fund['1Y Rolling Return (%)'] > 0 ? 'percentage-val positive' : 'percentage-val negative'}">${formatPercent(fund['1Y Rolling Return (%)'])}</span>
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
                    <span class="modal-item-label">Current Managers (Click for LinkedIn Lookup)</span>
                    <span class="modal-item-value" style="font-size:0.9rem; font-weight:500; color:#e2e8f0; line-height: 1.4; margin-bottom: 5px;">${formatManagerLinks(fund.Managers, true)}</span>
                    ${managerTenureHtml}
                    ${managerChangeWarningHtml}
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

// Theme Toggle Logic
const themeToggleBtn = document.getElementById('theme-toggle');
const docBody = document.body;

// Check local storage for theme preference, default to light
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    docBody.classList.add('dark-theme');
} else {
    docBody.classList.remove('dark-theme');
}

if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        docBody.classList.toggle('dark-theme');
        
        if (docBody.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });
}
