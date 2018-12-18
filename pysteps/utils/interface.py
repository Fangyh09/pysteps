
from . import conversion
from . import transformation
from . import dimension

def get_method(name):
    """Return a callable function for the utility method corresponding to the
    given name.\n\

    Conversion methods:

    +-------------------+--------------------------------------------------------+
    |     Name          |              Description                               |
    +===================+========================================================+
    | mm/h or rainrate  | convert to rain rate [mm/h]                            |
    +-------------------+--------------------------------------------------------+
    | mm or raindepth   | convert to rain depth [mm]                             |
    +-------------------+--------------------------------------------------------+
    | dbz or            | convert to reflectivity [dBZ]                          |
    | reflectivity      |                                                        |
    +-------------------+--------------------------------------------------------+

    Transformation methods:

    +-------------------+--------------------------------------------------------+
    |     Name          |              Description                               |
    +===================+========================================================+
    | boxcox or box-cox | one-parameter Box-Cox transform                        |
    +-------------------+--------------------------------------------------------+
    | db or decibel     | transform to units of decibel                          |
    +-------------------+--------------------------------------------------------+
    | log               | log transform                                          |
    +-------------------+--------------------------------------------------------+
    | nqt               | Normal Quantile Transform                              |
    +-------------------+--------------------------------------------------------+
    | sqrt              | square-root transform                                  |
    +-------------------+--------------------------------------------------------+

    Dimension methods:

    +-------------------+--------------------------------------------------------+
    |     Name          |              Description                               |
    +===================+========================================================+
    |  accumulate       | aggregate fields in time                               |
    +-------------------+--------------------------------------------------------+
    |  clip             | resize the field domain by geographical coordinates    |
    +-------------------+--------------------------------------------------------+
    |  square           | either pad or crop the data to get a square domain     |
    +-------------------+--------------------------------------------------------+
    |  upscale          | upscale the field                                      |
    +-------------------+--------------------------------------------------------+

    """

    if name is None:
        name = "none"

    name = name.lower()

    def donothing(R, metadata, *args, **kwargs):
        return R.copy(), metadata.copy()

    methods_objects                 = dict()
    methods_objects["none"]         = donothing
    # conversion methods
    methods_objects["mm/h"]         = conversion.to_rainrate
    methods_objects["rainrate"]     = conversion.to_rainrate
    methods_objects["mm"]           = conversion.to_raindepth
    methods_objects["raindepth"]    = conversion.to_raindepth
    methods_objects["dbz"]          = conversion.to_reflectivity
    methods_objects["reflectivity"] = conversion.to_reflectivity
    # transformation methods
    methods_objects["boxcox"]       = transformation.boxcox_transform
    methods_objects["box-cox"]      = transformation.boxcox_transform
    methods_objects["db"]           = transformation.dB_transform
    methods_objects["decibel"]      = transformation.dB_transform
    methods_objects["log"]          = transformation.boxcox_transform
    methods_objects["nqt"]          = transformation.NQ_transform
    methods_objects["sqrt"]         = transformation.sqrt_transform
    # dimension methods
    methods_objects["accumulate"]   = dimension.aggregate_fields_time
    methods_objects["clip"]         = dimension.clip_domain
    methods_objects["square"]       = dimension.square_domain
    methods_objects["upscale"]      = dimension.aggregate_fields_space

    try:
        return methods_objects[name]

    except KeyError as e:
        raise ValueError("Unknown method %s\n" % e +
                         "Supported methods:%s" % str(methods_objects.keys()))
