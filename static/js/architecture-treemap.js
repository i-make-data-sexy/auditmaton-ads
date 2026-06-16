// ========================================================================
//   App Architecture Treemap
//
//   Renders the live category -> subcategory -> check-count taxonomy as a
//   clickable Plotly treemap. Reads the server-rendered JSON data block
//   (#architecture-treemap-data) and mounts into #architecture-treemap.
//   Ported from the ML Model Picker's overview/browse treemap: orange
//   category headers, light leaves, branchvalues 'total', a phantom-root
//   crop, hover suppression on the synthesized root, click-to-navigate,
//   and the dark hover tooltip.
// ========================================================================

(function () {
    "use strict";

    var dataEl = document.getElementById("architecture-treemap-data");
    var mount = document.getElementById("architecture-treemap");
    if (!dataEl || !mount || typeof Plotly === "undefined") return;

    var data = JSON.parse(dataEl.textContent);

    // Relative cell URLs are stitched to the app's mount prefix client-side.
    var ROOT = window.APP_ROOT || "";

    var ids = [], labels = [], parents = [], values = [], colors = [];
    var fontSizes = [], fontColors = [], customdata = [], hoverText = [];

    data.categories.forEach(function (cat) {
        ids.push(cat.slug);
        labels.push(cat.name);
        parents.push("");
        values.push(cat.total_checks);
        colors.push("#FFA500");
        // 16px fits every category cell at the 7-category layout, so Plotly
        // doesn't auto-shrink headers to fit. That keeps all category labels
        // the same size (Plotly shrinks per-cell when text overflows).
        fontSizes.push(16);
        fontColors.push("#ffffff");
        customdata.push({
            type: "cat",
            name: cat.name,
            count: cat.total_checks,
            url: ROOT + cat.url
        });
        hoverText.push(
            cat.num_subcategories + " subcategor" + (cat.num_subcategories === 1 ? "y" : "ies") +
            " · " + cat.total_checks + " check" + (cat.total_checks === 1 ? "" : "s")
        );

        cat.subcategories.forEach(function (sub) {
            ids.push(cat.slug + "/" + sub.slug);
            labels.push(sub.name);
            parents.push(cat.slug);
            values.push(sub.count);
            colors.push("#ffd994");
            fontSizes.push(12);
            fontColors.push("#2a2a2a");
            customdata.push({
                type: "sub",
                name: sub.name,
                count: sub.count,
                url: ROOT + sub.url
            });
            hoverText.push(sub.count + " check" + (sub.count === 1 ? "" : "s"));
        });
    });

    var trace = {
        type: "treemap",
        ids: ids,
        labels: labels,
        parents: parents,
        values: values,
        customdata: customdata,
        text: hoverText,
        branchvalues: "total",
        marker: {
            colors: colors,
            line: { width: 0 },
            pad: { t: 32, l: 2, r: 2, b: 2 }
        },
        tiling: { pad: 2 },
        textinfo: "label",
        textfont: { family: "EkMukta-Light, Helvetica, sans-serif", size: fontSizes, color: fontColors },
        hovertemplate: "<b>%{label}</b><br>%{text}<extra></extra>",
        hoverlabel: {
            bgcolor: "#2a2a2a",
            bordercolor: "#2a2a2a",
            font: { color: "#ffffff", size: 13, family: "EkMukta-Light, Helvetica, sans-serif" }
        },
        pathbar: { visible: false }
    };

    // Plotly's implicit root takes 32px at the top (the marker.pad.t we need
    // for category-label spacing inside category cells). We render the chart
    // 32px taller than the visible window and crop the top via translateY +
    // the wrap's overflow: hidden, which hides the root band cleanly. Hover
    // on that hidden zone is suppressed below via plotly_hover.
    Plotly.newPlot(mount, [trace], {
        margin: { t: 4, l: 4, r: 4, b: 4 },
        height: 512,
        paper_bgcolor: "white",
        font: { family: "EkMukta-Light, Helvetica, sans-serif" }
    }, {
        displayModeBar: false,
        responsive: true
    }).then(function (gd) {
        if (gd.firstElementChild) {
            gd.firstElementChild.style.transform = "translateY(-32px)";
        }
        // Suppress hover on Plotly's synthesized root cell (it has no
        // customdata.url, so the hovertemplate would render empty %{text}).
        gd.on("plotly_hover", function (eventData) {
            if (!eventData.points || !eventData.points[0]) return;
            var cd = eventData.points[0].customdata;
            if (!cd || !cd.url) {
                Plotly.Fx.hover(gd, []);
            }
        });
        gd.on("plotly_treemapclick", function (eventData) {
            if (!eventData.points || !eventData.points[0]) return false;
            var cd = eventData.points[0].customdata;
            if (!cd || !cd.url) return false;
            window.location.href = cd.url;
            return false;
        });
    });
})();
