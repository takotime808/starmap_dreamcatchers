""" Streamlit app to generate star charts/maps based on user input date, time, and location data."""
import streamlit as st
from datetime import datetime
# from geopy import Nominatim
from geopy import Photon
try:
    from src.stardreamcatcher.tzwhere_v303 import tzwhere
except Exception as e:
    print(e)
    from tzwhere import tzwhere
from pytz import timezone, utc

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle

from skyfield.api import Star, load, wgs84
from skyfield.data import hipparcos, stellarium
from skyfield.projections import build_stereographic_projection
from skyfield.constants import GM_SUN_Pitjeva_2005_km3_s2 as GM_SUN

# import os
import argparse
import warnings
warnings.filterwarnings("ignore")

# from utils import mkdir_if_it_dne, load_data, load_data_cam, \
#     collect_celestial_data, create_star_chart


"""
# Custom Star Chart Generation #

Streamlit app to generate star charts/maps based on user input date, time, and location data.

"""


parser = argparse.ArgumentParser(description="Custom Star Chart Generation")
# TODO: mkdir_if_dne func and replace hardcoded paths with input params
# parser.add_argument("-d", "--data_path", type=str, default=r"./data/", metavar="str",
#                     help="dir where default data is stored. (default: './data/')")
# parser.add_argument("-o", "--output_dir", type=str, default=r"./figs/", metavar="str",
#                     help="dir to save generate figures. (default: './figs/')")
parser.add_argument("-fsx", "--figsize_x", type=int, default=12, metavar="int",
                    help="figsize to be is plt.figure(figsize=(fsx,fsy)). (default: 12)")
parser.add_argument("-fsy", "--figsize_y", type=int, default=12, metavar="int",
                    help="figsize to be is plt.figure(figsize=(fsx,fsy)). (default: 12)")
parser.add_argument("-mss", "--max_star_size", type=int, default=500, metavar="int",
                    help="maximum size to be used when plotting stars on map. (default: 500)")
args = parser.parse_args()
# DATA_PATH = os.getenv("DATA_PATH", "./data")
# FIGS_PATH = os.getenv("DATA_PATH", "./figs")

# st.markdown("----")
# st.markdown("we expect numpy==1.21.2, ans we get:")
# st.write(f"\n\n\nNUMPY VERSION:\n{np.__version__}\n\n\n")
# # st.markdown(f"tzwhere.__version__: {tzwhere.__version__}")
# import sys
# st.markdown(f"python version: {sys.version}")
# st.markdown("----")

def mkdir_if_it_dne(path):
    if not os.path.isdir(path):
        os.mkdir(path)
    return

def load_data():
    # load celestial data
    # de421 shows position of earth and sun in space/
    eph = load("./data/de421.bsp")

    # hipparcos dataset contains star location data.
    try:
        with load.open("./data/hip_main.dat") as f:
            stars = hipparcos.load_dataframe(f)
    except:
        # Pull data from online, if local copy of data fails to load.
        # NOTE: This causes issues with the share.streamlit.io hosted app.
        print("# HIT 1st EXCEPT in load_data()#")
        st.markdown("# HIT 1st EXCEPT in load_data()#")
        with load.open(hipparcos.URL) as f:
            stars = hipparcos.load_dataframe(f)

    # And the constellation outlines come from Stellarium.  We make a list
    # of the stars at which each edge stars, and the star at which each edge
    # ends.
    try:
        # Access local copy of [`constellationship.fab`](./data/constellationship.fab) data.
        with load.open("./data/constellationship.fab") as f:
            constellations = stellarium.parse_constellations(f)
    except:
        # Pull data from online, if local copy of data fails to load.
        # NOTE: This causes issues with the share.streamlit.io hosted app
        print("# HIT 2nd EXCEPT in load_data()#")
        st.markdown("# HIT 2nd EXCEPT in load_data()#")
        url = (
            "https://raw.githubusercontent.com/Stellarium/stellarium/master"
            "/skycultures/modern_st/constellationship.fab"
        )

        with load.open(url) as f:
            constellations = stellarium.parse_constellations(f)

    return eph, stars, constellations

def load_data_cam(url_or_other_path="./data/cam.constellationship.fab"):
    with load.open(url_or_other_path) as f:
        constellations_cam = stellarium.parse_constellations(f)
    return constellations_cam

def collect_celestial_data(location, when):
    # get latitude and longitude of our location
    # locator = Nominatim(user_agent="myGeocoder")
    locator = Photon(user_agent="myGeocoder")
    location = locator.geocode(location)
    lat, long = location.latitude, location.longitude

    # convert date string into datetime object
    dt = datetime.strptime(when, "%Y-%m-%d %H:%M")

    # define datetime and convert to utc based on our timezone
    timezone_str = tzwhere.tzwhere().tzNameAt(lat, long)
    local = timezone(timezone_str)

    # get UTC from local timezone and datetime
    local_dt = local.localize(dt, is_dst=None)
    utc_dt = local_dt.astimezone(utc)

    # load celestial data
    # eph, stars, constellations = load_data()

    # find location of earth and sun and set the observer position
    sun = eph["sun"]
    earth = eph["earth"]

    # define observation time from our UTC datetime
    ts = load.timescale()
    t = ts.from_datetime(utc_dt)

    # define an observer using the world geodetic system data
    observer = wgs84.latlon(latitude_degrees=lat, longitude_degrees=long).at(t)

    # define the position in the sky where we will be looking
    position = observer.from_altaz(alt_degrees=90, az_degrees=0)
    # center the observation point in the middle of the sky
    ra, dec, distance = observer.radec()
    center_object = Star(ra=ra, dec=dec)

    # find where our center object is relative to earth and build a projection with 180 degree view
    center = earth.at(t).observe(center_object)
    projection = build_stereographic_projection(center)
    field_of_view_degrees = 180.0

    # calculate star positions and project them onto a plain space
    star_positions = earth.at(t).observe(Star.from_dataframe(stars))
    stars["x"], stars["y"] = projection(star_positions)

    edges = [edge for name, edges in constellations for edge in edges]
    edges_star1 = [star1 for star1, star2 in edges]
    edges_star2 = [star2 for star1, star2 in edges]

    return stars, edges_star1, edges_star2

def create_star_chart(
    location,
    when,
    figsize_x,
    figsize_y,
    max_star_size,
    eph,
    stars,
    constellations,
    lines_xy_cam,
    savefig="./figs/pythonic_star_map.png",
):
    stars, edges_star1, edges_star2 = collect_celestial_data(location, when)
    limiting_magnitude = 10
    bright_stars = stars.magnitude <= limiting_magnitude
    magnitude = stars["magnitude"][bright_stars]
    fig, ax = plt.subplots(figsize=(figsize_x, figsize_y))

    # use the night sky color code
    border = plt.Circle((0, 0), 1, color="#041A40", fill=True)
    ax.add_patch(border)

    marker_size = max_star_size * 10 ** (magnitude / -2.5)

    ax.scatter(
        stars["x"][bright_stars],
        stars["y"][bright_stars],
        s=marker_size,
        color="white",
        marker=".",
        linewidths=0,
        zorder=2,
    )
    # Draw the constellation lines.
    xy1 = stars[["x", "y"]].loc[edges_star1].values
    xy2 = stars[["x", "y"]].loc[edges_star2].values
    lines_xy = np.rollaxis(np.array([xy1, xy2]), 1)

    ax.add_collection(LineCollection(lines_xy, colors="#ffff", linewidths=0.15))

    # if lines_xy_cam != None:
    ax.add_collection(LineCollection(lines_xy_cam, colors="#ff0000", linewidths=0.15))

    horizon = Circle((0, 0), radius=1, transform=ax.transData)
    for col in ax.collections:
        col.set_clip_path(horizon)

    # other settings
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    plt.axis("off")
    when_datetime = datetime.strptime(when, "%Y-%m-%d %H:%M")
    plt.title(
        f"Observation Location: {location}, Time: {when_datetime.strftime('%Y-%m-%d %H:%M')}",
        loc="right",
        fontsize=10,
    )

    if savefig:
        plt.savefig(savefig)
    # else:
    #     plt.show()
    return fig

# with st.echo(code_location='below'):
with st.form("caddy2_form", clear_on_submit=False):
    # progress_bar = st.progress(0)
    # # Make sure paths exist
    # mkdir_if_it_dne(args.data_path)
    # mkdir_if_it_dne(args.output_dir)

    # TODO: User input location.
    location = st.text_input(
        label="Input Desired Location:", value="Fort Lauderdale, FL",
    )

    # Data entry instructions.
    st.markdown("----")
    st.markdown("""
                Entered dates should have the format displayed by the examples:
                - Dates: `%Y-%m-%d`, `YYYY-mm-dd`
                - Times: `%H:%M`, military time `HH:MM`
                """)
    st.markdown("")

    # User input datetime.
    _date_ = st.date_input(
        label="Input Desired Date:", 
        # label="Input Desired Date:", value=datetime.date(2019, 3, 25),
        # # value = datetime.datetime(2019, 3, 25),
    )

    _time_ = st.text_input(
        label="Input Desired Time:", value="10:01",
    )

    # # Other definable parameters.
    # figsize = 12 # = args.figsize
    # max_star_size = 500 # = args.max_star_size
    # import subprocess
    # subprocess.run(["pip", "uninstall", "numpy"])
    # subprocess.run(["pip", "install", "numpy==1.21.2"])

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        progress_bar = st.progress(0)
        # import subprocess
        # subprocess.run(["pip", "install", "numpy==1.21.2"])
        # st.write(f'AGAIN:...run command `subprocess.run(["pip", "install", "numpy==1.21.2"])` and check np version again:')
        # st.write(f"\n\n\nNUMPY VERSION:\n{np.__version__}\n\n\n")
        when = f"{_date_} {_time_}"
        st.markdown(f"#### Submitted datetime: {when} ####")
        st.markdown(f"#### Submitted location: {location} ####")
        progress_bar.progress(10)

        # st.markdown("## REVERT to hard-coded...to troubleshoot")
        # location = 'Virginia Beach, VA'
        # when = '2021-05-17 00:00'
        # st.markdown(f"#### Submitted datetime: {when} ####")
        # st.markdown(f"#### Submitted location: {location} ####")

        # load celestial data
        eph, stars, constellations = load_data()

        # Make colored constellations.
        # TODO: Pull out into a utility function.
        stars, edges_star1, edges_star2 = collect_celestial_data(location, when)
        constellations_cam = load_data_cam("./data/constellationship_cam.fab")
        progress_bar.progress(25)
        edges_cam = [edge for name, edges in constellations_cam for edge in edges]
        edges_star1_cam = [star1 for star1, star2 in edges_cam]
        edges_star2_cam = [star2 for star1, star2 in edges_cam]
        progress_bar.progress(50)

        xy1_cam = stars[["x", "y"]].loc[edges_star1_cam].values
        xy2_cam = stars[["x", "y"]].loc[edges_star2_cam].values
        lines_xy_cam = np.rollaxis(np.array([xy1_cam, xy2_cam]), 1)
        progress_bar.progress(75)

        # Create star chart.
        # figname = location.replace(" ", "_").replace(",","_") + "_" + when.replace("-", "_").replace(":", "").replace(" ", "_")
        # figname = f"./figs/{figname.lower()}.png"
        figname = False
        star_chart = create_star_chart(
            location=location,
            when=when,
            figsize_x=args.figsize_x,
            figsize_y=args.figsize_y,
            max_star_size=args.max_star_size,
            eph=eph,
            stars=stars,
            constellations=constellations,
            lines_xy_cam=lines_xy_cam,
            savefig=figname,
        )
        st.pyplot(star_chart)
        progress_bar.progress(100)
