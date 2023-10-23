# Aspect ratio

Due to the DMD geometry (diagonal vs orthogonal mirror array), the aspect ratio is modified when using native resolution:
one must correct the patterns shown

# Troubleshooting

AttributeError: /lib/x86_64-linux-gnu/libhidapi-hidraw.so.0: undefined symbol: hid_get_input_report

there are two pip packages: hidapi and hid

you need to install hidapi and remove hid 
