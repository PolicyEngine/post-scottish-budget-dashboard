import { useState, useEffect, useRef } from "react";
import * as d3 from "d3";
import "./MansionTaxMap.css";

/**
 * Interactive D3 map showing Scottish Mansion Tax impact by Parliament Constituency.
 * Shows estimated revenue share from council tax reform for £1m+ properties.
 */
export default function MansionTaxMap() {
  const svgRef = useRef(null);
  const tooltipRef = useRef(null);
  const [geoData, setGeoData] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [maxPct, setMaxPct] = useState(12);

  // Load data
  useEffect(() => {
    async function loadData() {
      try {
        const [geoRes, impactRes] = await Promise.all([
          fetch("/data/scottish_parliament_constituencies.geojson"),
          fetch("/data/mansion_tax_constituency_impact.csv"),
        ]);

        if (geoRes.ok) {
          const geo = await geoRes.json();
          setGeoData(geo);
        }

        if (impactRes.ok) {
          const csvText = await impactRes.text();
          const lines = csvText.trim().split("\n");
          const headers = lines[0].split(",");
          const data = {};

          for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(",");
            const row = {};
            headers.forEach((h, idx) => {
              row[h.trim()] = values[idx]?.trim();
            });
            data[row.constituency] = {
              pct: parseFloat(row.share_pct) || 0,
              num: parseInt(row.estimated_sales) || 0,
              rev: parseInt(row.allocated_revenue) || 0,
              council: row.council || "Unknown",
            };
          }

          setImpactData(data);
          const max = Math.max(...Object.values(data).map(d => d.pct));
          setMaxPct(max);
        }
      } catch (err) {
        console.error("Error loading mansion tax data:", err);
      }
    }
    loadData();
  }, []);

  // Render D3 map
  useEffect(() => {
    if (!geoData || !impactData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = 600;
    const height = 900;
    const g = svg.append("g");

    // Calculate bounds
    let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
    geoData.features.forEach(feature => {
      const traverse = (coords) => {
        if (typeof coords[0] === "number") {
          xMin = Math.min(xMin, coords[0]);
          xMax = Math.max(xMax, coords[0]);
          yMin = Math.min(yMin, coords[1]);
          yMax = Math.max(yMax, coords[1]);
        } else {
          coords.forEach(traverse);
        }
      };
      traverse(feature.geometry.coordinates);
    });

    // Scale to fit
    const padding = 20;
    const dataWidth = xMax - xMin;
    const dataHeight = yMax - yMin;
    const geoScale = Math.min((width - 2 * padding) / dataWidth, (height - 2 * padding) / dataHeight) * 0.92;
    const geoOffsetX = (width - dataWidth * geoScale) / 2;
    const geoOffsetY = padding;

    const projection = d3.geoTransform({
      point: function(x, y) {
        this.stream.point(
          (x - xMin) * geoScale + geoOffsetX,
          height - ((y - yMin) * geoScale + geoOffsetY)
        );
      }
    });

    const pathGenerator = d3.geoPath().projection(projection);

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([1, 8])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Store zoom for external access
    svgRef.current._zoom = zoom;
    svgRef.current._svg = svg;
    svgRef.current._g = g;
    svgRef.current._pathGenerator = pathGenerator;

    // Color scale (log scale for better variation)
    const minPct = 0.01;
    const logScale = d3.scaleLog()
      .domain([minPct, maxPct])
      .range([0, 1])
      .clamp(true);

    const colorScale = (pct) => {
      if (pct === 0 || pct < 0.01) return "#e5e5e5";
      const t = logScale(Math.max(pct, minPct));
      if (t < 0.5) {
        return d3.interpolate("#E8F4F8", "#2E86AB")(t * 2);
      } else {
        return d3.interpolate("#2E86AB", "#1A535C")((t - 0.5) * 2);
      }
    };

    // Draw paths
    g.selectAll("path")
      .data(geoData.features)
      .join("path")
      .attr("class", "constituency-path")
      .attr("d", pathGenerator)
      .attr("fill", d => {
        const name = d.properties.SPC21NM;
        const data = impactData[name];
        return data ? colorScale(data.pct) : "#e5e5e5";
      })
      .attr("stroke", "white")
      .attr("stroke-width", 0.5)
      .attr("opacity", 0.9)
      .on("mouseenter", function(event, d) {
        const name = d.properties.SPC21NM;
        const data = impactData[name] || { pct: 0, num: 0, rev: 0, council: "Unknown" };
        showTooltip(name, data, event);
        d3.select(this).attr("opacity", 1).attr("stroke-width", 2);
      })
      .on("mousemove", function(event, d) {
        const name = d.properties.SPC21NM;
        const data = impactData[name] || { pct: 0, num: 0, rev: 0, council: "Unknown" };
        showTooltip(name, data, event);
      })
      .on("mouseleave", function() {
        d3.select(this).attr("opacity", 0.9).attr("stroke-width", 0.5);
        hideTooltip();
      });

    function showTooltip(name, data, event) {
      const tooltip = tooltipRef.current;
      if (!tooltip) return;

      tooltip.innerHTML = `
        <h4>${name}</h4>
        <div class="tooltip-council">${data.council}</div>
        <div class="tooltip-value">${data.pct.toFixed(2)}%</div>
        <div class="tooltip-row">
          <span>Est. sales</span>
          <span>${data.num.toLocaleString()}</span>
        </div>
        <div class="tooltip-row">
          <span>Est. revenue</span>
          <span>£${(data.rev / 1000000).toFixed(2)}m</span>
        </div>
      `;
      tooltip.style.display = "block";

      const rect = svgRef.current.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      tooltip.style.left = x + "px";
      tooltip.style.top = y + "px";
    }

    function hideTooltip() {
      const tooltip = tooltipRef.current;
      if (tooltip) {
        tooltip.style.display = "none";
      }
    }

  }, [geoData, impactData, maxPct]);

  // Handle search
  useEffect(() => {
    if (!impactData) return;

    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    const matches = Object.keys(impactData)
      .filter(name => name.toLowerCase().includes(searchQuery.toLowerCase()))
      .slice(0, 10);

    setSearchResults(matches);
    setShowResults(matches.length > 0);
  }, [searchQuery, impactData]);

  const handleSelectConstituency = (name) => {
    setSearchQuery(name);
    setShowResults(false);

    if (!svgRef.current || !geoData || !impactData) return;

    const { _zoom: zoom, _svg: svg, _g: g, _pathGenerator: pathGenerator } = svgRef.current;
    if (!zoom || !svg || !g) return;

    // Highlight selected
    g.selectAll(".constituency-path").attr("opacity", 0.9).attr("stroke-width", 0.5);
    g.selectAll(".constituency-path")
      .filter(d => d.properties.SPC21NM === name)
      .attr("opacity", 1).attr("stroke-width", 2);

    // Show tooltip
    const data = impactData[name] || { pct: 0, num: 0, rev: 0, council: "Unknown" };
    const tooltip = tooltipRef.current;
    if (tooltip) {
      tooltip.innerHTML = `
        <h4>${name}</h4>
        <div class="tooltip-council">${data.council}</div>
        <div class="tooltip-value">${data.pct.toFixed(2)}%</div>
        <div class="tooltip-row">
          <span>Est. sales</span>
          <span>${data.num.toLocaleString()}</span>
        </div>
        <div class="tooltip-row">
          <span>Est. revenue</span>
          <span>£${(data.rev / 1000000).toFixed(2)}m</span>
        </div>
      `;
      tooltip.style.display = "block";
      tooltip.style.left = "50%";
      tooltip.style.top = "40%";
    }

    // Zoom to constituency
    const feature = geoData.features.find(f => f.properties.SPC21NM === name);
    if (feature && pathGenerator) {
      const bounds = pathGenerator.bounds(feature);
      const dx = bounds[1][0] - bounds[0][0];
      const dy = bounds[1][1] - bounds[0][1];
      const x = (bounds[0][0] + bounds[1][0]) / 2;
      const y = (bounds[0][1] + bounds[1][1]) / 2;
      const scale = Math.max(1, Math.min(8, 0.9 / Math.max(dx / 600, dy / 900)));
      svg.transition().duration(750).call(
        zoom.transform,
        d3.zoomIdentity.translate(300, 450).scale(scale).translate(-x, -y)
      );
    }
  };

  const handleZoom = (action) => {
    if (!svgRef.current) return;
    const { _zoom: zoom, _svg: svg } = svgRef.current;
    if (!zoom || !svg) return;

    if (action === "in") {
      svg.transition().call(zoom.scaleBy, 1.5);
    } else if (action === "out") {
      svg.transition().call(zoom.scaleBy, 0.67);
    } else {
      svg.transition().call(zoom.transform, d3.zoomIdentity);
    }
  };

  if (!geoData || !impactData) {
    return (
      <div className="mansion-tax-map loading">
        <p>Loading mansion tax map...</p>
      </div>
    );
  }

  return (
    <div className="mansion-tax-map">
      <div className="map-header">
        <h3>Scottish mansion tax by parliament constituency</h3>
        <p>Share of estimated annual revenue from council tax reform for properties valued at £1m+</p>
      </div>

      <div className="map-top-bar">
        <div className="map-search-section">
          <label>Search constituency</label>
          <div className="search-container">
            <input
              type="text"
              className="constituency-search"
              placeholder="Type to search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowResults(true)}
            />
            {showResults && (
              <div className="search-results">
                {searchResults.map(name => {
                  const data = impactData[name] || { pct: 0, num: 0 };
                  return (
                    <button
                      key={name}
                      className="search-result-item"
                      onClick={() => handleSelectConstituency(name)}
                    >
                      <div className="result-name">{name}</div>
                      <div className="result-value">
                        {data.num.toLocaleString()} sales | {data.pct.toFixed(2)}%
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="map-legend">
          <div className="legend-gradient"></div>
          <div className="legend-labels">
            <span>0%</span>
            <span>{maxPct.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      <div className="map-canvas">
        <svg
          ref={svgRef}
          viewBox="0 0 600 900"
          preserveAspectRatio="xMidYMid meet"
        />
        <div className="map-controls">
          <button className="zoom-btn" onClick={() => handleZoom("in")} title="Zoom in">+</button>
          <button className="zoom-btn" onClick={() => handleZoom("out")} title="Zoom out">-</button>
          <button className="zoom-btn" onClick={() => handleZoom("reset")} title="Reset">↺</button>
        </div>
        <div className="tooltip" ref={tooltipRef}></div>
      </div>

      <div className="map-source">
        Source: Analysis based on Scottish Government Budget 2026-27 |{" "}
        <a href="https://github.com/PolicyEngine/scotland-mansion-tax" target="_blank" rel="noopener noreferrer">
          PolicyEngine
        </a>
      </div>
    </div>
  );
}
