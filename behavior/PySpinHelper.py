import PySpin

class ReadType:
    """
    Use the following constants to determine whether nodes are read
    as Value nodes or their individual types.
    """
    VALUE = 0,
    INDIVIDUAL = 1

def print_with_indent(level, text):
    """
    Helper function for printing a string prefix with a specifc number of indents.
    :param level: Number of indents to generate
    :type level: int
    :param text: String to print after indent
    :type text: str
    """
    ind = ''
    for i in range(level):
        ind += '    '
    print("%s%s" % (ind, text))
    
def print_value_node(node, level, MAX_CHARS=35):
    """
    Retrieves and prints the display name and value of all node types as value nodes.
    A value node is a general node type that allows for the reading and writing of any node type as a string.
    :param node: Node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:
        node_value   = PySpin.CValuePtr(node)                                  # Create value node
        display_name = node_value.GetDisplayName()                             # Retrieve display name 
        value        = node_value.ToString()                                   # Retrieve value of any node type as string
        value        = value[:MAX_CHARS] + '...' if len(value) > MAX_CHARS \
                       else value                                              # Cap length at MAX_CHARS
        print_with_indent(level, "%s: %s" % (display_name, value))             # Print value; 'level' determines the indentation level of output

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)

def print_string_node(node, level, MAX_CHARS=35):
    """
    Retrieves and prints the display name and value of a string node.
    :param node: Node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:
        node_string  = PySpin.CStringPtr(node)                                 # Create string node
        display_name = node_string.GetDisplayName()                            # Retrieve string node value
        value        = node_string.GetValue()                                  # Ensure that the value length is not excessive for printing
        value        = value[:MAX_CHARS] + '...' if len(value) > MAX_CHARS \
                       else value                                              # Cap length at MAX_CHARS 
        print_with_indent(level, "%s: %s" % (display_name, value))             # Print value; 'level' determines the indentation level of output

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)

def print_integer_node(node, level, MAX_CHARS=35):
    """
    Retrieves and prints the display name and value of an integer node.
    :param node: Node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:
        node_integer = PySpin.CIntegerPtr(node)                                # Create integer node
        display_name = node_integer.GetDisplayName()                           # Get display name 
        value        = node_integer.GetValue()                                 # Retrieve integer node value 
        print_with_indent(level, "%s: %s" % (display_name, value))             # Print value; 'level' determines the indentation level of output
    
    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def print_float_node(node, level, MAX_CHARS=35):
    """
    Retrieves and prints the display name and value of a float node.
    :param node: Node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:
        node_float   = PySpin.CFloatPtr(node)                                  # Create float node
        display_name = node_float.GetDisplayName()                             # Get display name
        value        = node_float.GetValue()                                   # Retrieve float value
        print_with_indent(level, "%s: %s" % (display_name, value))             # Print value; 'level' determines the indentation level of output

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def print_boolean_node(node, level, MAX_CHARS=35):
    """
    Retrieves and prints the display name and value of a Boolean node.
    :param node: Node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:  
        node_boolean = PySpin.CBooleanPtr(node)                                # Create Boolean node
        display_name = node_boolean.GetDisplayName()                           # Get display name
        value        = node_boolean.GetValue()                                 # Retrieve Boolean value
        print_with_indent(level, "%s: %s" % (display_name, value))             # Print value; 'level' determines the indentation level of output

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def print_command_node(node, level, MAX_CHARS=35):
    """
    This function retrieves and prints the display name and tooltip of a command
    node, limiting the number of printed characters to a macro-defined maximum.
    The tooltip is printed below because command nodes do not have an intelligible
    value.
    :param node: Node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:
        node_command = PySpin.CCommandPtr(node)                                # Create command node
        display_name = node_command.GetDisplayName()                           # Get display name
        tooltip      = node_command.GetToolTip()                               # Retrieve tooltip
        tooltip      = tooltip[:MAX_CHARS] + '...' if len(tooltip) > MAX_CHARS \
                       else tooltip                                            # Ensure that the value length is not excessive for printing
        print_with_indent(level, "%s: %s" % (display_name, tooltip))           # Print name and tooltip; 'level' determines the indentation level of output

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)


def print_enumeration_node_and_current_entry(node, level, MAX_CHARS=35):
    """
    This function retrieves and prints the display names of an enumeration node
    and its current entry (which is actually housed in another node unto itself).
    :param node: Node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:
        node_enumeration = PySpin.CEnumerationPtr(node)                        # Create enumeration node
        node_enum_entry  = PySpin.CEnumEntryPtr(
                           node_enumeration.GetCurrentEntry())                 # Retrieve current entry as enumeration node
        display_name     = node_enumeration.GetDisplayName()                   # Get display name
        entry_symbolic   = node_enum_entry.GetSymbolic()                       # Retrieve current symbolic
        print_with_indent(level, "%s: %s" % (display_name, entry_symbolic))    # Print current entry symbolic; 'level' determines the indentation level of output

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        
def print_category_node_and_all_features(node, level=0, 
                                         CHOSEN_READ=ReadType.INDIVIDUAL,
                                         MAX_CHARS=35):
    
    """
    This function retrieves and prints out the display name of a category node
    before printing all child nodes. Child nodes that are also category nodes are
    printed recursively.
    :param node: Category node to get information from.
    :type node: INode
    :param level: Depth to indent output.
    :type level: int
    :param CHOSEN_READ: Determines whether nodes are read as Value nodes
    :type CHOSEN_READ: bool
    :param MAX_CHARS: Maximum characters to print
    :type MAX_CHARS: int
    """
    try:
        node_category = PySpin.CCategoryPtr(node)                              # Create category node
        display_name = node_category.GetDisplayName()                          # Get and print display name
        print_with_indent(level, display_name)
        
        for node_feature in node_category.GetFeatures():                       # Retrieve and iterate through all children 
            if not PySpin.IsAvailable(node_feature) or \
               not PySpin.IsReadable(node_feature):                            # Ensure node is available and readable
                   continue

            if node_feature.GetPrincipalInterfaceType() == \
               PySpin.intfICategory:                                           # Category nodes must be dealt with separately in order to retrieve subnodes recursively.
                   print_category_node_and_all_features(node_feature, level + 1)

            elif CHOSEN_READ == ReadType.VALUE:
                   print_value_node(node_feature, level + 1)                   # Cast all non-category nodes as value nodes

            elif CHOSEN_READ == ReadType.INDIVIDUAL:                           # Cast all non-category nodes as actual types
                if node_feature.GetPrincipalInterfaceType() == PySpin.intfIString:
                    print_string_node(node_feature, level + 1)
                elif node_feature.GetPrincipalInterfaceType() == PySpin.intfIInteger:
                    print_integer_node(node_feature, level + 1)
                elif node_feature.GetPrincipalInterfaceType() == PySpin.intfIFloat:
                    print_float_node(node_feature, level + 1)
                elif node_feature.GetPrincipalInterfaceType() == PySpin.intfIBoolean:
                    print_boolean_node(node_feature, level + 1)
                elif node_feature.GetPrincipalInterfaceType() == PySpin.intfICommand:
                    print_command_node(node_feature, level + 1)
                elif node_feature.GetPrincipalInterfaceType() == PySpin.intfIEnumeration:
                    print_enumeration_node_and_current_entry(node_feature, level + 1)

    except PySpin.SpinnakerException as ex:
        print("Error: %s" % ex)
        
def set_aquisition_params(nodemap):
    """
    This function sets the camera acquisition mode to 'Continuous' for multi-frame
    recording requiring a single trigger.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
    node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
    if PySpin.IsAvailable(node_acquisition_mode) and \
       PySpin.IsWritable(node_acquisition_mode):
        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName("Continuous")
        if PySpin.IsAvailable(node_acquisition_mode_continuous) and \
           PySpin.IsReadable(node_acquisition_mode_continuous):
            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
            print("Acquisition mode set to %s..." % node_acquisition_mode.GetCurrentEntry().GetSymbolic())
            successful_param_change = True
        else:
            print("Acquisiton mode Continuous not available...")
    else:
        print("Acquisition mode not available...")
    return successful_param_change

def set_trigger_params(nodemap):
    """
    This function turns OFF the trigger option TriggerMode for untriggered
    recordings (triggered via Python controller only).
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode("TriggerMode"))
    if PySpin.IsAvailable(node_trigger_mode) and \
       PySpin.IsReadable(node_trigger_mode):
           node_trigger_mode_off = node_trigger_mode.GetEntryByName("Off")
           if PySpin.IsAvailable(node_trigger_mode_off) and \
              PySpin.IsReadable(node_trigger_mode_off):
                  trigger_mode_off = node_trigger_mode_off.GetValue()
                  node_trigger_mode.SetIntValue(trigger_mode_off)
                  print("Trigger mode set to %s..." % node_trigger_mode.GetCurrentEntry().GetSymbolic())
                  successful_param_change = True
           else:
               print("Trigger mode control not available...")
    else:
        print("Trigger mode not available...")
    return successful_param_change

def set_pixel_params(nodemap):
    """
    This function sets the camera pixel format to mono8 (default for present
    camera set-up).
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
    if PySpin.IsAvailable(node_pixel_format) and \
       PySpin.IsWritable(node_pixel_format):
        # Retrieve the desired entry node from the enumeration node
        node_pixel_format_mono8 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName("Mono8"))
        if PySpin.IsAvailable(node_pixel_format_mono8) and PySpin.IsReadable(node_pixel_format_mono8):
            # Retrieve the integer value from the entry node
            pixel_format_mono8 = node_pixel_format_mono8.GetValue()
            # Set integer as new value for enumeration node
            node_pixel_format.SetIntValue(pixel_format_mono8)
            print("Pixel format set to %s..." % node_pixel_format.GetCurrentEntry().GetSymbolic())
            successful_param_change = True
        else:
            print("Pixel format mono 8 not available...")
    else:
        print("Pixel format not available...")
    return successful_param_change

def set_picture_width(nodemap,WIDTH=1200): 
    """
    This function sets the saved image (NOT sensor) width parameter, enabling
    ROI selection for space-efficient saving.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param WIDTH: Pixel width of desired saved images
    :type WIDTH: int
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_width = PySpin.CIntegerPtr(nodemap.GetNode("Width"))
    if PySpin.IsAvailable(node_width) and PySpin.IsWritable(node_width):
        try:
            node_width.SetValue(WIDTH)
            print("Width set to %i..." % node_width.GetValue())
            successful_param_change = True
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    else:
        print("Width not available...")
    return successful_param_change
    
def set_picture_height(nodemap,HEIGHT=900):
    """
    This function sets the saved image (NOT sensor) height parameter, enabling
    ROI selection for space-efficient saving.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param HEIGHT: Pixel height of desired saved images
    :type HEIGHT: int
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_height = PySpin.CIntegerPtr(nodemap.GetNode("Height"))
    if PySpin.IsAvailable(node_height) and PySpin.IsWritable(node_height):
        try:
            node_height.SetValue(HEIGHT)
            print("Height set to %i..." % node_height.GetValue())
            successful_param_change = True
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    else:
        print("Height not available...")
    return successful_param_change
        
def set_offset_x(nodemap,OFFSETX=624):
    """
    This function sets the saved image (NOT sensor) lateral offset parameter, 
    useful for ROI selection when not capturing the entire sensor range.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param OFFSETX: Lateral pixel offset of desired saved images (from left edge)
    :type OFFSETX: int
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_offset_x = PySpin.CIntegerPtr(nodemap.GetNode("OffsetX"))
    if PySpin.IsAvailable(node_offset_x) and PySpin.IsWritable(node_offset_x):
        try:
            node_offset_x.SetValue(OFFSETX)
            print("Offset X set to %i..." % node_offset_x.GetValue()) 
            successful_param_change = True
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    else:
        print("Offset X not available...")
    return successful_param_change
        
def set_offset_y(nodemap,OFFSETY=350):
    """
    This function sets the saved image (NOT sensor) vertical offset parameter, 
    useful for ROI selection when not capturing the entire sensor range.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param OFFSETY: Vertical pixel offset of desired saved images (from top edge)
    :type OFFSETY: int
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_offset_y = PySpin.CIntegerPtr(nodemap.GetNode("OffsetY"))
    if PySpin.IsAvailable(node_offset_y) and PySpin.IsWritable(node_offset_y):
        try:
            node_offset_y.SetValue(OFFSETY)
            print("Offset Y set to %i..." % node_offset_y.GetValue())
            successful_param_change = True
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    else:
        print("Offset Y not available...")
    return successful_param_change

def set_exposure_params(nodemap,EXPSURETIME=30000):
    """
    This function turns OFF the exposure option ExposureAuto, sets the exposure
    mode to Timed, and sets the parameter ExposureTime for fixed, optimized
    exposure time recordings.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param EXPOSURETIME: Desired exposure time (us)
    :type EXPOSURETIME: int
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_exposure_mode_auto = PySpin.CEnumerationPtr(nodemap.GetNode("ExposureAuto"))
    if PySpin.IsAvailable(node_exposure_mode_auto) and PySpin.IsWritable(node_exposure_mode_auto):
        node_exposure_mode_auto_off = node_exposure_mode_auto.GetEntryByName("Off")
        exposure_mode_auto_off = node_exposure_mode_auto_off.GetValue()
        node_exposure_mode_auto.SetIntValue(exposure_mode_auto_off)
        print("Auto exposure turned %s..." % node_exposure_mode_auto.GetCurrentEntry().GetSymbolic())
        node_exposure_mode = PySpin.CEnumerationPtr(nodemap.GetNode("ExposureMode"))
        if PySpin.IsAvailable(node_exposure_mode) and PySpin.IsWritable(node_exposure_mode):
            node_exposure_mode_timed = node_exposure_mode.GetEntryByName("Timed")
            exposure_mode_timed = node_exposure_mode_timed.GetValue()
            node_exposure_mode.SetIntValue(exposure_mode_timed)
            print("Exposure mode set to %s..." % node_exposure_mode.GetCurrentEntry().GetSymbolic())
            node_exposure_time = PySpin.CFloatPtr(nodemap.GetNode("ExposureTime"))
            if PySpin.IsAvailable(node_exposure_time) and \
               PySpin.IsWritable(node_exposure_time):
                   try:
                       node_exposure_time.SetValue(EXPSURETIME)
                       print("Exposure time set to %i..." % node_exposure_time.GetValue())
                       successful_param_change = True
                   except PySpin.SpinnakerException as ex:
                       print("Error: %s" % ex)
            else:
                   print("Exposure time not available...")
        else:
            print("Exposure mode not available...")
    else:
        print("Exposure mode not available...")
    return successful_param_change

def set_gain_params(nodemap,GAIN=10):
    """
    This function turns OFF the gain option GainAuto and sets the parameter 
    Gain for fixed, optimized gain recordings.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param GAIN: Desired gain
    :type GAIN: int
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_gain_mode_auto = PySpin.CEnumerationPtr(nodemap.GetNode("GainAuto"))
    if PySpin.IsAvailable(node_gain_mode_auto) and \
       PySpin.IsWritable(node_gain_mode_auto):
           node_gain_mode_auto_off = node_gain_mode_auto.GetEntryByName("Off")
           gain_mode_auto_off = node_gain_mode_auto_off.GetValue()
           node_gain_mode_auto.SetIntValue(gain_mode_auto_off)
           print("Auto gain turned %s..." % node_gain_mode_auto.GetCurrentEntry().GetSymbolic())
           node_gain = PySpin.CFloatPtr(nodemap.GetNode("Gain"))
           if PySpin.IsAvailable(node_gain) and PySpin.IsWritable(node_gain):
               try:
                   node_gain.SetValue(GAIN)
                   print("Gain set to %i..." % node_gain.GetValue())
                   successful_param_change = True
               except PySpin.SpinnakerException as ex:
                   print("Error: %s" % ex)
           else:
               print("Gain not available...")
    else:
           print("Gain mode not available...")
    return successful_param_change

def set_gamma(nodemap,GAMMA=0.75):
    """
    This function turns ON the Gamma option GammEnable to enable manual control
    of the Gamma and sets the parameter Gamma for fixed, optimized Gamma recordings.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param GAMMA: Desired gamma
    :type GAMMA: float
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_gamma_enable = PySpin.CBooleanPtr(nodemap.GetNode("GammaEnable"))
    if PySpin.IsAvailable(node_gamma_enable):
        node_gamma_enable.SetValue(True)
        print("Gamma enable set to %s..." % node_gamma_enable.GetValue())
    else:
        print("Gamma enable mode not available...")
    node_gamma = PySpin.CFloatPtr(nodemap.GetNode("Gamma"))
    if PySpin.IsAvailable(node_gamma) and PySpin.IsWritable(node_gamma):
        try:
            node_gamma.SetValue(GAMMA)
            print("Gamma set to %f..." % node_gamma.GetValue())
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    else:
        print("Gamma not available...")
    return successful_param_change

def set_frame_rate(nodemap,FRAMERATE=30.0):
    """
    This function turns ON the framerate option AcqusitionFrameRateEnable to enable
    manual control of the ACQUISITION framerate and sets the ACQUISITION framerate 
    for fixed framerate recordings.
    :param nodemap: Map of all SpinnakerCamera object parameters
    :type node: INodeMap
    :param FRAMERATE: Desired acuisition framerate
    :type FRAMERATE: float
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    node_frame_rate_enable = PySpin.CBooleanPtr(nodemap.GetNode("AcquisitionFrameRateEnable"))
    if PySpin.IsAvailable(node_frame_rate_enable):
        node_frame_rate_enable.SetValue(True)
        print("Frame rate enable set to %s..." % node_frame_rate_enable.GetValue())
    else:
        print("Frame rate enable mode not available...")
    node_frame_rate = PySpin.CFloatPtr(nodemap.GetNode('AcquisitionFrameRate'))
    if PySpin.IsAvailable(node_frame_rate) and \
       PySpin.IsWritable(node_frame_rate):
           node_frame_rate.SetValue(FRAMERATE)
           print("Frame rate set to %f..." % node_frame_rate.GetValue())
           successful_param_change = True
    else:
        print("Frame rate not available...")
    return successful_param_change

def set_buffer_params(s_nodemap,MAXBUFFERS=100):
    """
    This function sets the buffer handling mode option StreamBufferHandlingMode to
    OLDESTFIRST to process images in chronological order, sets the buffer count
    mode option StreamBufferCountMode to MANUAL for manual control of buffer count,
    and sets the buffer count option StreamBufferCountManual to MAXBUFFERS.
    :param s_nodemap: Map of all SpinnakerCamera object parameters
    :type s_nodemap: INodeMap
    :param MAXBUFFERS: Desired number of buffers used for image processing
    :type MAXBUFFERS: int
    :return successful_param_change: Record of successful function run with access to requested nodes
    :type successful_param_change: bool
    """
    successful_param_change = False
    # Set Buffer Handling Mode to OldestFirst
    node_buffer_handling_mode = PySpin.CEnumerationPtr(s_nodemap.GetNode('StreamBufferHandlingMode'))
    if PySpin.IsAvailable(node_buffer_handling_mode) and \
       PySpin.IsWritable(node_buffer_handling_mode):
           node_buffer_handling_mode_oldest_first = node_buffer_handling_mode.GetEntryByName('OldestFirst')
           buffer_handling_mode_oldest_first = node_buffer_handling_mode_oldest_first.GetValue()
           node_buffer_handling_mode.SetIntValue(buffer_handling_mode_oldest_first)
           print("Buffer handling mode set to OldestFirst...")
    else:
        print("Buffer handling mode not available...")
 
    # Set stream buffer Count Mode to manual
    node_stream_buffer_count_mode = PySpin.CEnumerationPtr(s_nodemap.GetNode('StreamBufferCountMode'))
    if PySpin.IsAvailable(node_stream_buffer_count_mode) and \
       PySpin.IsWritable(node_stream_buffer_count_mode):
           node_stream_buffer_count_manual = node_stream_buffer_count_mode.GetEntryByName('Manual')
           stream_buffer_count_manual = node_stream_buffer_count_manual.GetValue()
           node_stream_buffer_count_mode.SetIntValue(stream_buffer_count_manual)
           print("Buffer count mode set to Manual...")
    else:
        print("Buffer count mode not available...")
           
    # Retrieve and modify Stream Buffer Count
    node_buffer_count = PySpin.CIntegerPtr(s_nodemap.GetNode('StreamBufferCountManual'))
    if PySpin.IsAvailable(node_buffer_count) and \
       PySpin.IsWritable(node_buffer_count): 
           buffer_count = node_buffer_count.GetMax()
           if buffer_count > MAXBUFFERS:
               node_buffer_count.SetValue(MAXBUFFERS)
               print("Buffer count set to %i..." % node_buffer_count.GetValue())
               successful_param_change = True
           else:
               print("Buffer count set to %i..." % buffer_count)
    else:
        print("Buffer count not available...")
    return successful_param_change