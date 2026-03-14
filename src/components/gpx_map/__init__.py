import os
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
_RELEASE = False

if not _RELEASE:
    # We use the absolute path to the frontend directory
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(parent_dir, "frontend")
    _gpx_map = components.declare_component("gpx_map", path=frontend_dir)
else:
    # When we're distributing a production version of the component, we'll
    # replace the `path` param with `url` that points to the served frontend.
    pass

def gpx_map(api_key, name, lat, lon, gpx_points, table_points=None, gpx_duration=None, key=None):
    """
    Creates a new instance of the gpx_map component.
    """
    component_value = _gpx_map(
        api_key=api_key,
        name=name,
        lat=lat,
        lon=lon,
        gpxPoints=gpx_points,
        tablePoints=table_points,
        gpxDuration=gpx_duration,
        key=key,
        default=None
    )
    return component_value
