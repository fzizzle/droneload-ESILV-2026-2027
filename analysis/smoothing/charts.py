# Plotly charts for the smoothing study. Each takes study.summarise() rows or a study.trace().
import plotly.graph_objects as go

from analysis.smoothing.study import OUTPUT_DIR

# Shake levels are ordered, so they share one blue ramp, light (clean) to dark (severe)
LEVEL_COLOURS = {"clean": "#86b6ef", "mild": "#3987e5", "moderate": "#1c5cab", "severe": "#0d366b"}
TRACE_COLOURS = {"truth": "#52514e", "raw": "#1baf7a", 0.6: "#2a78d6", 1.0: "#eb6834"}
EXTRA_COLOURS = ["#e87ba4", "#6250d6"]  # further weights in a trace
SURFACE       = "#fcfcfb"
INK           = "#0b0b0b"
MUTED         = "#898781"
GRID          = "#e1e0d9"
AXIS          = "#c3c2b7"
PNG_SCALE     = 2

def _style(fig, title, x_title, y_title):
    fig.update_layout(
        title=dict(text=title, x=0, xref="paper", xanchor="left"),
        template="simple_white", paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family="Inter, Arial, sans-serif", size=13, color=INK),
        hovermode="x unified", width=820, height=480, margin=dict(l=70, r=90, t=70, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
    )
    for axis, text in ((fig.update_xaxes, x_title), (fig.update_yaxes, y_title)):
        axis(title_text=text, showgrid=True, gridcolor=GRID, linecolor=AXIS,
             tickcolor=AXIS, tickfont=dict(color=MUTED), zeroline=False)
    return fig

def _rgba(hex_colour, alpha):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"

def _rows(summary, footage, level=None):
    return [s for s in summary if s["footage"] == footage and s["weight"] is not None
            and (level is None or s["level"] == level)]

def metric_vs_weight(summary, footage, metric, title, y_title):
    """One line per shake level: the mean over seeds, with a min-max band."""
    fig = go.Figure()
    for level, colour in LEVEL_COLOURS.items():
        rows = _rows(summary, footage, level)
        if not rows:
            continue
        x = [r["weight"] for r in rows]
        fig.add_trace(go.Scatter(x=x + x[::-1], y=[r[f"{metric}_max"] for r in rows]
                                 + [r[f"{metric}_min"] for r in rows][::-1],
                                 fill="toself", fillcolor=_rgba(colour, 0.15), line=dict(width=0),
                                 hoverinfo="skip", showlegend=False, legendgroup=level))
        fig.add_trace(go.Scatter(x=x, y=[r[f"{metric}_mean"] for r in rows], name=level,
                                 legendgroup=level, mode="lines+markers",
                                 line=dict(color=colour, width=2), marker=dict(size=8),
                                 hovertemplate=f"{level}: %{{y:.1f}}<extra></extra>"))
    _style(fig, title, "Smoothing weight (1.0 = no smoothing)", y_title)
    return fig.update_xaxes(dtick=0.1)

def tradeoff(summary, footage, level="moderate"):
    """Jitter against frame error, one point per weight, with the true jitter as a dashed line."""
    rows = _rows(summary, footage, level)
    colour = LEVEL_COLOURS[level]
    fig = go.Figure(go.Scatter(
        x=[r["frame_err_px_mean"] for r in rows], y=[r["jitter_px_mean"] for r in rows],
        mode="lines+markers+text", text=[f"{r['weight']:.1f}" for r in rows], textposition="top center",
        textfont=dict(color=INK), line=dict(color=colour, width=2), marker=dict(size=9, color=colour),
        name=f"{level} shake", hovertemplate="weight %{text}: error %{x:.1f} px, jitter %{y:.1f} px<extra></extra>"))
    true_jitter = sum(r["true_jitter_px_mean"] for r in rows) / len(rows)
    fig.add_hline(y=true_jitter, line=dict(color=MUTED, dash="dash", width=2),
                  annotation_text=f"true marker motion {true_jitter:.1f} px", annotation_position="top left",
                  annotation_font_color=MUTED)
    _style(fig, f"{footage}, {level} shake: jitter against frame error (labels are weights)",
           "Frame error (px)", "Jitter, RMS step per frame (px)")
    return fig.update_layout(hovermode="closest", showlegend=False)

def trace_chart(trace, window=None):
    """One marker's x position per frame: truth, raw detections and each weight.

    window=(first, last) limits the chart to those frames, so single frames can be seen."""
    first, last = window or (0, len(trace["frames"]))
    part = slice(first, last)
    frames = trace["frames"][part]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=frames, y=trace["truth_x"][part], name="true position", mode="lines",
                             line=dict(color=TRACE_COLOURS["truth"], width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=frames, y=trace["raw_x"][part], name="raw detection", mode="markers",
                             marker=dict(color=TRACE_COLOURS["raw"], size=8, symbol="circle-open")))
    extra = iter(EXTRA_COLOURS)
    for weight, xs in trace["weights"].items():
        colour = TRACE_COLOURS.get(weight) or next(extra)
        fig.add_trace(go.Scatter(x=frames, y=xs[part], name=f"reported, weight {weight:.1f}",
                                 mode="lines+markers", connectgaps=False, marker=dict(size=5),
                                 line=dict(color=colour, width=2)))
    title = f"Marker {trace['marker_id']}: x position, frames {frames[0]}-{frames[-1]}"
    _style(fig, title, "Frame", "x position (px)")
    return fig.update_traces(hovertemplate="%{y:.1f} px")

def save(fig, name, png=True):
    """Write the chart as HTML and, if a Chromium-based browser is found, as PNG."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = [OUTPUT_DIR / f"{name}.html"]
    fig.write_html(paths[0], include_plotlyjs="cdn")
    if png:
        try:
            fig.write_image(OUTPUT_DIR / f"{name}.png", scale=PNG_SCALE)
            paths.append(OUTPUT_DIR / f"{name}.png")
        except Exception as error:  # kaleido raises several types when no browser is found
            print(f"[WARN] {name}.png not written ({error}). PNG export needs Chrome, Chromium, "
                  "Edge, Brave or Vivaldi; run plotly_get_chrome to download one.")
    return paths
