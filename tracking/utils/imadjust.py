def imadjust(input_image,in_low,in_high,out_low,out_high,gamma=1):
    # Converts an image range from [in_low,in_high] to [out_low,out_high].
    # If gamma is equal to 1, then the line equation is used.
    # When gamma is not equal to 1, then the transformation is not linear.

    return (((input_image - in_low) / (in_high - in_low)) ** gamma) * (out_high - out_low) + out_low