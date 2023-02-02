"""
Example on how to process gravity data with Fatiando tools

Based on tutorial available in
https://www.fatiando.org/tutorials/notebooks/gravity-processing.html
"""
import pathlib
import numpy as np
import pandas as pd
import xarray as xr
import pyproj
import pygmt
import ensaio
import verde as vd
import boule as bl
import harmonica as hm

# Download datasets
path_gravity = ensaio.fetch_southern_africa_gravity(version=1)
path_topography = ensaio.fetch_earth_topography(version=1)
path_geoid = ensaio.fetch_earth_geoid(version=1)

# Load data
data = pd.read_csv(path_gravity)
topography = xr.load_dataarray(path_topography)
geoid = xr.load_dataarray(path_geoid)

# Crop data
region = (25, 32, -27, -23)
region_pad = vd.pad_region(region, pad=5)
data = data[vd.inside((data.longitude, data.latitude), region)]
geoid = geoid.sel(longitude=slice(*region_pad[:2]), latitude=slice(*region_pad[2:]))
topography = topography.sel(
    longitude=slice(*region_pad[:2]), latitude=slice(*region_pad[2:])
)

# Project data
projection = pyproj.Proj(proj="merc", lat_ts=data.latitude.mean())
easting, northing = projection(data.longitude.values, data.latitude.values)
data = data.assign(easting_m=easting, northing_m=northing)
topography_proj = vd.project_grid(topography, projection, method="nearest")
geoid_proj = vd.project_grid(geoid, projection, method="nearest")

# Compute topography referenced on the ellipsoid
topography_geometric = topography_proj + geoid_proj

# Unravel the grid so that we can pass it to the interpolator
geoid_table = vd.grid_to_table(geoid_proj)
interpolator = vd.ScipyGridder(method="cubic")
interpolator.fit((geoid_table.easting, geoid_table.northing), geoid_table.geoid)

# Predict the geoid height at same locations as the observation points
data = data.assign(geoid_m=interpolator.predict((data.easting_m, data.northing_m)))
data = data.assign(height_geometric_m=data.height_sea_level_m + data.geoid_m)

# Gravity disturbance
data = data.assign(
    normal_gravity_mgal=bl.WGS84.normal_gravity(data.latitude, data.height_geometric_m)
)
data = data.assign(
    gravity_disturbance_mgal=data.gravity_mgal - data.normal_gravity_mgal
)

# Topographic correction
topography_density = np.where(topography_geometric > 0, 2670, -2670)
topography_density = np.where(topography_proj < 0, 1040 - 2670, topography_density)
topography_model = hm.prism_layer(
    coordinates=(topography_geometric.easting, topography_geometric.northing),
    surface=topography_geometric,
    reference=0,
    properties={"density": topography_density},
)

# Compute bouguer disturbance
coordinates = (data.easting_m, data.northing_m, data.height_geometric_m)
data = data.assign(
    terrain_effect_mgal=topography_model.prism_layer.gravity(coordinates, field="g_z"),
)
data = data.assign(
    gravity_bouguer_mgal=data.gravity_disturbance_mgal - data.terrain_effect_mgal
)

# Residual-regional separation
# Create a set of deep sources at a depth of 500 km
deep_sources = hm.EquivalentSources(damping=1000, depth=500e3)
# Fit the sources to the data
deep_sources.fit(
    (data.easting_m, data.northing_m, data.height_geometric_m),
    data.gravity_bouguer_mgal,
)

# Use the sources to predict the regional field
data = data.assign(
    gravity_regional_mgal=deep_sources.predict(
        (data.easting_m, data.northing_m, data.height_geometric_m)
    )
)
# Calculate a residual field (which is what we want)
data = data.assign(
    gravity_residual_mgal=data.gravity_bouguer_mgal - data.gravity_regional_mgal
)

# Grid the residual
eqs = hm.EquivalentSources(damping=10, depth=10e3)
eqs.fit(
    (data.easting_m, data.northing_m, data.height_geometric_m),
    data.gravity_residual_mgal,
)
grid_coords = vd.grid_coordinates(
    region=region,
    spacing=2 / 60,  # Decimal degrees
    extra_coords=2200,  # height in meters
)
residual_grid = eqs.grid(
    coordinates=grid_coords,
    data_names=["gravity_residual"],
    dims=("latitude", "longitude"),
    projection=projection,
)


# ====
# Plot
# ====

filepath = pathlib.Path(__file__).parent.resolve()
outfile = filepath / ".." / "figs" / "figure.png"

marker_style = ("c2p",)
projection = ("M?",)
frame = ("afg",)
kwargs = dict(
    style=marker_style,
    projection=projection,
    frame=frame,
    cmap=True,
)

# Create figure with subplots
fig = pygmt.Figure()
with fig.subplot(
    nrows=2,
    ncols=2,
    figsize=("18c", "15c"),
    autolabel="(a)+jTC",
    sharex="b",  # shared x-axis on the bottom side
    sharey="l",  # shared y-axis on the left side
):
    # Disturbance
    with fig.set_panel(panel=0, fixedlabel="(a) Gravity disturbance"):
        maxabs = vd.maxabs(data.gravity_disturbance_mgal)
        pygmt.makecpt(cmap="polar+h", series=[-maxabs, maxabs])
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            color=data.gravity_disturbance_mgal,
            **kwargs
        )
        fig.colorbar(frame="af")
    # Bouguer
    with fig.set_panel(panel=1, fixedlabel="(b) Bouguer disturbance"):
        maxabs = vd.maxabs(data.gravity_bouguer_mgal)
        pygmt.makecpt(cmap="polar", series=[-maxabs, maxabs])
        fig.plot(
            x=data.longitude, y=data.latitude, color=data.gravity_bouguer_mgal, **kwargs
        )
        fig.colorbar(frame="af")

    # Residual
    with fig.set_panel(panel=2, fixedlabel="(c) Residual field"):
        scale = vd.maxabs(data.gravity_residual_mgal, residual_grid.gravity_residual)
        pygmt.makecpt(cmap="polar", series=[-scale, scale])
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            color=data.gravity_residual_mgal,
            **kwargs
        )
        fig.colorbar(frame="af")

    # Residual grid
    with fig.set_panel(panel=3, fixedlabel="(d) Gridded residual field"):
        # scale = vd.maxabs(residual_grid.gravity_residual)
        pygmt.makecpt(cmap="polar", series=[-scale, scale], no_bg=True)
        fig.grdimage(
            residual_grid.gravity_residual,
            shading="+a45+nt0.15",
            projection=projection,
            frame=frame,
        )
        fig.colorbar(frame="af")
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            style="c0.5p",
            color="black",
        )

fig.savefig(outfile, dpi=300)
fig.show()
