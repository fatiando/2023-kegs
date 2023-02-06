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
raw_data = pd.read_csv(path_gravity)
topography = xr.load_dataarray(path_topography)
geoid = xr.load_dataarray(path_geoid)

# Crop data
region = (25, 32, -27, -23)
region_pad = vd.pad_region(region, pad=5)
data = raw_data[vd.inside((raw_data.longitude, raw_data.latitude), region)]
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

pygmt.config(
    FONT_ANNOT="11p,Helvetica,black",
    FONT_TITLE="12p,Helvetica,black",
    FONT_LABEL="10p,Helvetica,black",
    MAP_TITLE_OFFSET="0p",
    MAP_FRAME_WIDTH="2p",
)

# --------------------------------
# Plot the downloaded gravity data
# --------------------------------
# Create figure with subplots
fig = pygmt.Figure()
projection = "M?"

# Get minmax values for the relief in the background
raw_region = vd.get_region((raw_data.longitude, raw_data.latitude))
large_relief = pygmt.datasets.load_earth_relief(resolution="01m", region=raw_region)
relief_series = [large_relief.values.min(), large_relief.values.max()]

with fig.subplot(
    nrows=1,
    ncols=2,
    figsize=("19c", "10c"),
    autolabel="(a)+jTC",
):
    with fig.set_panel(panel=0, fixedlabel="(a) Observed gravity"):
        pygmt.makecpt(
            cmap="gray",
            series=relief_series,
        )
        fig.grdimage(
            "@earth_relief_01m",
            region=raw_region,
            projection=projection,
            shading="+a45+nt0.7",
            cmap=True,
        )
        fig.coast(
            water="#8fcae7",
            transparency=50,
        )
        pygmt.makecpt(
            cmap="viridis",
            series=[raw_data.gravity_mgal.min(), raw_data.gravity_mgal.max()],
        )
        fig.plot(
            x=raw_data.longitude,
            y=raw_data.latitude,
            color=raw_data.gravity_mgal,
            cmap=True,
            style="c1.5p",
            projection=projection,
            frame="afg",
        )
        fig.plot(
            x=[region[0], region[1], region[1], region[0], region[0]],
            y=[region[3], region[3], region[2], region[2], region[3]],
            pen="1p,orangered1,-",
        )
        fig.colorbar(frame='af+l"mGal"')
    with fig.set_panel(panel=1, fixedlabel="(b) Obs. gravity on Bushveld"):
        pygmt.makecpt(
            cmap="gray",
            series=relief_series,
        )
        fig.grdimage(
            "@earth_relief_01m",
            region=region,
            projection=projection,
            shading="+a45+nt0.7",
            cmap=True,
        )
        pygmt.makecpt(
            cmap="viridis",
            series=[data.gravity_mgal.min(), data.gravity_mgal.max()],
        )
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            color=data.gravity_mgal,
            cmap=True,
            style="c2p",
            projection=projection,
            frame="afg",
        )
        fig.colorbar(frame='af+l"mGal"')

fig.savefig(filepath / ".." / "figs" / "southern-africa-gravity.png", dpi=300)
fig.show()

# #####################################################################################

# ------------------------------------------------
# Plot the disturbance and the bouguer disturbance
# ------------------------------------------------
# Create figure with subplots
fig = pygmt.Figure()
projection = "M?"

with fig.subplot(
    nrows=1,
    ncols=2,
    figsize=("19c", "8c"),
    autolabel="(a)+jTC",
    sharey="l",
):
    with fig.set_panel(panel=0, fixedlabel="(a) Gravity disturbance"):
        # Plot relief
        pygmt.makecpt(
            cmap="gray",
            series=relief_series,
        )
        fig.grdimage(
            "@earth_relief_01m",
            region=region,
            projection=projection,
            shading="+a45+nt0.7",
            cmap=True,
        )
        # Plot disturbance
        maxabs = vd.maxabs(data.gravity_disturbance_mgal)
        pygmt.makecpt(
            cmap="polar",
            series=[-maxabs, maxabs],
        )
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            color=data.gravity_disturbance_mgal,
            cmap=True,
            style="c2p",
            projection=projection,
            frame="afg",
        )
        fig.colorbar(frame='af+l"mGal"')
    with fig.set_panel(panel=1, fixedlabel="(b) Bouguer disturbance"):
        # Plot relief
        pygmt.makecpt(
            cmap="gray",
            series=relief_series,
        )
        fig.grdimage(
            "@earth_relief_01m",
            region=region,
            projection=projection,
            shading="+a45+nt0.7",
            cmap=True,
        )
        # Plot Bouguer disturbance
        maxabs = vd.maxabs(data.gravity_bouguer_mgal)
        pygmt.makecpt(
            cmap="polar",
            series=[-maxabs, maxabs],
        )
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            color=data.gravity_bouguer_mgal,
            cmap=True,
            style="c2p",
            projection=projection,
            frame="fg",
        )
        fig.colorbar(frame='af+l"mGal"')

fig.savefig(filepath / ".." / "figs" / "disturbance-and-bouguer.png", dpi=300)
fig.show()

# #####################################################################################

# ------------------------------------------
# Plot the residual and the gridded residual
# ------------------------------------------
# Create figure with subplots
fig = pygmt.Figure()
projection = "M?"

maxabs = vd.maxabs(data.gravity_residual_mgal, residual_grid.gravity_residual)

with fig.subplot(
    nrows=1,
    ncols=2,
    figsize=("19c", "8c"),
    autolabel="(a)+jTC",
    sharey="l",
):
    with fig.set_panel(panel=0, fixedlabel="(a) Gravity residuals"):
        # Plot relief
        pygmt.makecpt(
            cmap="gray",
            series=relief_series,
        )
        fig.grdimage(
            "@earth_relief_01m",
            region=region,
            projection=projection,
            shading="+a45+nt0.7",
            cmap=True,
        )
        # Plot residual
        pygmt.makecpt(
            cmap="polar",
            series=[-maxabs, maxabs],
        )
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            color=data.gravity_residual_mgal,
            cmap=True,
            style="c2p",
            projection=projection,
            frame="afg",
        )
        fig.colorbar(frame='af+l"mGal"')
    with fig.set_panel(panel=1, fixedlabel="(b) Gridded gravity residuals"):
        pygmt.makecpt(cmap="polar", series=[-maxabs, maxabs], no_bg=True)
        fig.grdimage(
            residual_grid.gravity_residual,
            shading="+a45+nt0.15",
            projection=projection,
            frame="f",
        )
        fig.colorbar(frame="af")
        fig.plot(
            x=data.longitude,
            y=data.latitude,
            style="c0.5p",
            color="black",
        )
        fig.colorbar(frame='af+l"mGal"')

fig.savefig(filepath / ".." / "figs" / "residual-and-grid.png", dpi=300)
fig.show()
