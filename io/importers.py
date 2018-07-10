"""Methods for importing files containing 2d precipitation fields.

The methods in this module implement the following interface:

  import_xxx(filename, optional arguments)

where xxx is the name (or abbreviation) of the file format and filename is the 
name of the input file.

The output of each method is a three-element tuple containing the two-dimensional 
precipitation field and georeferencing and metadata dictionaries.

The geodata dictionary contains the following mandatory key-value pairs:
    projection   PROJ.4-compatible projection definition
    x1           x-coordinate of the lower-left corner of the data raster
    y1           y-coordinate of the lower-left corner of the data raster
    x2           x-coordinate of the upper-right corner of the data raster
    y2           y-coordinate of the upper-right corner of the data raster
    xpixelsize   grid resolution in x-direction (meters)
    ypixelsize   grid resolution in y-direction (meters)
    yorigin      a string specifying the location of the first element in
                 the data raster w.r.t. y-axis:
                 'upper' = upper border
                 'lower' = lower border

The metadata dictionary contains the following mandatory key-value pairs:
    institution  name of the institution who provides the data
    timestep     time step of the input data (minutes)
    unit         the unit of the data: 'mm/h', 'mm' or 'dBZ'
"""

import datetime
import gzip
from matplotlib.pyplot import imread
import numpy as np
try:
    from netCDF4 import Dataset
    netcdf4_imported = True
except ImportError:
    netcdf4_imported = False
try:
    from PIL import Image
    pil_imported = True
except ImportError:
    pil_imported = False
try:
    import pyproj
    pyproj_imported = True
except ImportError:
    pyproj_imported = False

def import_pgm(filename, gzipped=False):
    """Import a 8-bit PGM radar reflectivity composite from the FMI archive and 
    optionally convert the reflectivity values to precipitation rates.

    Parameters
    ----------
    filename : str
        Name of the file to import.
    gzipped : bool
        If True, the input file is treated as a compressed gzip file.

    Returns
    -------
    out : tuple
        A three-element tuple containing the reflectivity field in dBZ imported 
        from the PGM file and the associated georeferencing data and metadata.
    """
    if not pyproj_imported:
        raise Exception("pyproj not imported")
    
    metadata = _import_pgm_metadata(filename, gzipped=gzipped)

    if gzipped == False:
        R = imread(filename)
    else:
        R = imread(gzip.open(filename, 'r'))
    geodata = _import_pgm_geodata(metadata)
    
    MASK = R == metadata["missingval"]
    R = R.astype(float)
    R[MASK] = np.nan
    R = (R - 64.0) / 2.0

    return R, geodata, metadata

def _import_pgm_geodata(metadata):
    geodata = {}

    projdef = ""

    if metadata["type"][0] != "stereographic":
        raise ValueError("unknown projection %s" % metadata["type"][0])
    projdef += "+proj=stere "
    projdef += " +lon_0=" + metadata["centrallongitude"][0] + 'E'
    projdef += " +lat_0=" + metadata["centrallatitude"][0] + 'N'
    projdef += " +lat_ts=" + metadata["truelatitude"][0]
    # These are hard-coded because the projection definition is missing from the 
    # PGM files.
    projdef += " +a=6371288"
    projdef += " +x_0=380886.310"
    projdef += " +y_0=3395677.920"
    projdef += " +no_defs"
    #
    geodata["projection"] = projdef
  
    ll_lon,ll_lat = [float(v) for v in metadata["bottomleft"]]
    ur_lon,ur_lat = [float(v) for v in metadata["topright"]]

    pr = pyproj.Proj(projdef)
    x1,y1 = pr(ll_lon, ll_lat)
    x2,y2 = pr(ur_lon, ur_lat)

    geodata["x1"] = x1
    geodata["y1"] = y1
    geodata["x2"] = x2
    geodata["y2"] = y2

    geodata["xpixelsize"] = float(metadata["metersperpixel_x"][0])
    geodata["ypixelsize"] = float(metadata["metersperpixel_y"][0])

    geodata["yorigin"] = "upper"
  
    return geodata

def _import_pgm_metadata(filename, gzipped=False):
    metadata = {}
  
    if gzipped == False:
        f = open(filename, 'r')
    else:
        f = gzip.open(filename, 'r')
  
    l = f.readline().decode()
    while l[0] != '#':
        l = f.readline().decode()
    while l[0] == '#':
        x = l[1:].strip().split(' ')
        if len(x) >= 2:
            k = x[0]
            v = x[1:]
            metadata[k] = v
        else:
            l = f.readline().decode()
            continue
        l = f.readline().decode()
    l = f.readline().decode()
    metadata["missingval"] = int(l)
    f.close()
    
    metadata["institution"] = "Finnish Meteorological Institute"
    metadata["timestep"]    = 5
    metadata["unit"]        = "dBZ"
    
    return metadata
    
def import_aqc(filename):
    """Import a 8-bit gif radar reflectivity composite (AQC) from the MeteoSwiss 
    archive.

    Parameters
    ----------
    filename : str
        Name of the file to import.
    dtype : type
        The output datatype for the dataset that is imported from the file.
    Returns
    -------
    out : tuple
        A three-element tuple containing the precipitation field in mm h-1 imported 
        from a MeteoSwiss AQC file, the associated georeferencing data and some 
        metadata.
    """
    if not pil_imported:
        raise Exception("PIL not imported")
    
    metadata = {}
    metadata["institution"] = "MeteoSwiss"
    metadata["timestep"]    = 5
    metadata["unit"]        = "mm/h"
    
    geodata = _import_aqc_geodata()
    
    B = Image.open(filename)
    B = np.array(B, dtype=int)
    
    # generate lookup table in mmh-1
    # valid for AQC product only
    lut = np.zeros(256)
    A = 316.0; b = 1.5
    for i in range(256):
        if (i < 2) or (i > 250 and i < 255):
            lut[i] = 0.0
        elif (i == 255):
            lut[i] = np.nan
        else:
            lut[i] = (10.**((i - 71.2)/20.0)/A)**(1.0/b)*60/5
            
    # apply lookup table [mm h-1]
    R = lut[B]
    
    return R, geodata, metadata
    
def _import_aqc_geodata():
    geodata = {}
    
    projdef = ""
    # These are all hard-coded because the projection definition is missing from the 
    # gif files.
    projdef += "+proj=somerc "
    projdef += " +lon_0=7.439583333333333"
    projdef += " +lat_0=46.95240555555556"
    projdef += " +k_0=1"
    projdef += " +x_0=600000"
    projdef += " +y_0=200000"
    projdef += " +ellps=bessel"
    projdef += " +towgs84=674.374,15.056,405.346,0,0,0,0"
    projdef += " +units=m"
    projdef += " +no_defs"
    #
    geodata["projection"] = projdef

    geodata["x1"] = 255000
    geodata["y1"] = 160000
    geodata["x2"] = 965000
    geodata["y2"] = 480000

    geodata["xpixelsize"] = 1000
    geodata["ypixelsize"] = 1000

    geodata["yorigin"] = "upper"
  
    return geodata


def import_bom_rf3(filename):
    """Import a netcdf radar rainfall product from the BoM Rainfields3.

    Parameters
    ----------
    filename : str
        Name of the file to import.

    Returns
    -------
    out : tuple
        A three-element tuple containing the rainfall field in mm imported from
        the Bureau RF3 netcdf and the associated georeferencing data and metadata.
        TO DO: Complete metadata decription as per the others methods

    """
    if not netcdf4_imported:
        raise Exception("netCDF4 not imported")
    
    R = _import_bom_rf3_data(filename)
    geodata = _import_bom_rf3_geodata(filename)
    metadata = _import_bom_rf3_metadata(filename)

    return R, geodata, metadata


def _import_bom_rf3_data(filename):
    print(filename)
    ds_rainfall = Dataset(filename)
    if ('precipitation' in ds_rainfall.variables.keys()):
        precipitation = ds_rainfall.variables['precipitation'][:]
        # estimate time-step to transform from mm to mm/h
        if ('valid_time' in ds_rainfall.variables.keys()):
            valid_time = datetime.datetime.utcfromtimestamp(
                ds_rainfall.variables['valid_time'][:])
        else:
            valid_time = None
        if ('start_time' in ds_rainfall.variables.keys()):
            start_time = datetime.datetime.utcfromtimestamp(
                ds_rainfall.variables['start_time'][:])
        else:
            start_time = None
        if start_time is not None:
            if valid_time is not None:
                time_step = (valid_time-start_time).seconds//60
        if time_step:
            factor_rain = 60./time_step
            precipitation = precipitation*factor_rain
    else:
        precipitation = None
    ds_rainfall.close()
    return precipitation

def _import_bom_rf3_geodata(filename):
    ds_rainfall = Dataset(filename)
    if ('proj' in ds_rainfall.variables.keys()):
        projection = ds_rainfall.variables['proj']
        if (getattr(projection, 'grid_mapping_name') ==
                "albers_conical_equal_area"):
            projdef = "+proj=aea "
            lon_0 = getattr(projection,
                            'longitude_of_central_meridian')
            projdef += " +lon_0=" + str(lon_0)
            lat_0 = getattr(projection,
                            'latitude_of_projection_origin')
            projdef += " +lat_0=" + str(lat_0) 
            standard_parallels = getattr(projection,
                                         'standard_parallel')
            projdef += " +lat_1=" + str(standard_parallels[0])
            projdef += " +lat_2=" + str(standard_parallels[1])
        else:
            projdef = None
    ds_rainfall.close()
    return projdef


def _import_bom_rf3_metadata(filename):
    metadata = {}
    # TODO: Set the correct time step.
    metadata["institution"] = "Bureau of Meteorology"
    metadata["timestep"]    = 0
    metadata["unit"]        = "mm/h"
    return metadata