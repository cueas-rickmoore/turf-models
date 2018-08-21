""" Classes for accessing hourly data from URMA grid files.
"""

from atmosci.hdf5.hourgrid import HourlyGridFileReader, \
                                  HourlyGridFileManager


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class URMAHourlyGridFileReader(HourlyGridFileReader):
    """ Provides read-only access to 3D gridded data in HDF5 files where
    the first dimension is time, the 2nd dimension is rows and the 3rd
    dimension is columns. Grids can contain any type of data. Indexing
    based on Time/Latitude/Longitude is available. Time indexes may be
    derived from date/time with earliest date at index 0. Row indexes
    may be derived from Latitude coordinates with minimum Latitude at
    row index 0. Columns indexes may be derived from Longitude
    coordinates with minimum Longitude at column index 0.

    Inherits all of the capabilities of Hdf5GridFileReader
    """

    def __init__(self, hdf5_filepath):
        HourlyGridFileReader.__init__(self, hdf5_filepath)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class URMAHourlyGridFileManager(HourlyGridFileManager):
    """ Provides read/write access to 3D gridded data in HDF5 files where
    the first dimension is time, the 2nd dimension is rows and the 3rd
    dimension is columns. Grids can contain any type of data. Indexing
    based on Time/Latitude/Longitude is available. Time indexes may be
    derived from date/time with earliest date at index 0. Row indexes
    may be derived from Latitude coordinates with minimum Latitude at
    row index 0. Columns indexes may be derived from Longitude
    coordinates with minimum Longitude at column index 0.

    Inherits all of the capabilities of Hdf5GridFileManager
    """

    def __init__(self, hdf5_filepath, mode='r'):
        HourlyGridFileManager.__init__(self, hdf5_filepath, mode)

