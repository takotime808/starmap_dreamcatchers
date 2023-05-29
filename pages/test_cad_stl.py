""" Streamlit app to generate and download `stl` files."""
import streamlit as st
import cadquery as cq
import numpy as np
import datetime
import warnings
warnings.filterwarnings("ignore")

""" Streamlit app to generate and download `*.stl` files."""

# # Defaults
# FIG_PATH = "./figs/cad/cadquery"
FIG_PATH = "."
cad_file_extension_options=["STL", "DXF", "SVG", "STEP", "AMF", "TJS", "VRML", "VTP", "3MF",]
cad_file_generated = False

def generate_cad_file():
    s = cq.Workplane("XY")
    sPnts = [
        (2.75, 1.5),
        (2.5, 1.75),
        (2.0, 1.5),
        (1.5, 1.0),
        (1.0, 1.25),
        (0.5, 1.0),
        (0, 1.0)
    ]
    r = s.lineTo(3.0, 0).lineTo(3.0, 1.0).spline(sPnts, includeCurrent=True).close()
    result = r.extrude(0.5)
    return result


with st.form("cad_form", clear_on_submit=False):
    progress_bar = st.progress(0)

    # TODO: User input location.
    file_extension2 = st.text_input("(NOT used) Extension to save CAD file with:", value="stl",)
    
    file_extension = st.selectbox(label="Choose an extension to be used when saving the CAD file.", options=np.array(cad_file_extension_options))


    # User input datetime.
    _date_ = st.date_input(
        label="Input Desired Date:", value=datetime.date(2019, 3, 25),
    )
    st.markdown("# WHY DOES DATE EXAMPLE WORK HERE BUT NOT MAIN PAGE #")

    # init progress bar.
    progress_bar.progress(25)

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit me bb")
    if submitted:
        file_path_of_cad_object = f"{FIG_PATH}/spline_extrusion.{file_extension}"
        st.markdown(f"#### Submitted date: {_date_} ####")
        st.markdown(f"#### Chosen file extension: {file_extension} ####")
        st.markdown(f"**File saved to: {file_path_of_cad_object}**")
        progress_bar.progress(50)


        extrusion = generate_cad_file()
        # cq.exporters.export(extrusion, f"{FIG_PATH}/spline_extrusion.stl")
        cq.exporters.export(extrusion, file_path_of_cad_object)
        cad_file_generated = True # Set to True for downloading files.
        progress_bar.progress(75)


if cad_file_generated:
    # Download file.
    with open(file_path_of_cad_object, "rb") as file:
        btn = st.download_button(
                label=f"Download {file_extension} file",
                data=file,
                file_name=file_path_of_cad_object.split("/")[-1],
                # mime="image/png"
            )
    progress_bar.progress(100)
